"""The estimators: one column of one table, with everything the article prints."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats as _stats

from airline_delays.estimation import kp as kpmod
from airline_delays.estimation.loader import PanelIncomplete
from airline_delays.estimation.sample import build_sample, design
from airline_delays.estimation.specification import (
    COEF_ORDER,
    DEBIASED,
    HAC_BANDWIDTH,
    WITH_SEASONALITY,
    ColumnSpec,
    Estimator,
)


@dataclass
class ColumnResult:
    """Coefficients, standard errors and the statistics the article prints."""

    column: int
    regressand: str
    estimator: Estimator
    coefficients: dict[str, dict[str, float]]
    stats: dict[str, Any]
    dropped_collinear: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "column": self.column,
            "regressand": self.regressand,
            "estimator": self.estimator,
            "b": {name: values["b"] for name, values in self.coefficients.items()},
            "se": {name: values["se"] for name, values in self.coefficients.items()},
            "stats": self.stats,
            "n_dropped_collinear": len(self.dropped_collinear),
        }


def hansen_j(
    residuals: np.ndarray,
    instruments: np.ndarray,
    *,
    bandwidth: int = HAC_BANDWIDTH,
    panel: tuple[np.ndarray, np.ndarray] | None = None,
    n_params_overid: int,
) -> tuple[float, float, int]:
    """Hansen's J with the HAC optimal weight matrix, evaluated at given residuals.

    ``ivreg2`` prints this for every robust estimator, GMM or not, which is why
    Table 5 (LIML) reports a J barely different from Table 3's. ``linearmodels``
    exposes ``j_stat`` only on the GMM results, so LIML gets it from here.
    """
    moments = instruments * residuals[:, None]
    n = moments.shape[0]
    cov = kpmod.hac_moment_cov(moments, bandwidth, *(panel if panel else (None, None)))
    mean = moments.mean(axis=0)
    stat = float(n * mean @ np.linalg.pinv(cov) @ mean)
    df = int(n_params_overid)
    p = float(_stats.chi2.sf(stat, df)) if df > 0 else float("nan")
    return stat, p, df


def fit(
    sample: pd.DataFrame,
    spec: ColumnSpec,
    *,
    with_seasonality: bool = WITH_SEASONALITY,
    debiased: bool = DEBIASED,
    bandwidth: int = HAC_BANDWIDTH,
    panel_hac: bool = False,
) -> ColumnResult:
    """Estimate one column of one table and collect everything the article prints."""
    from linearmodels.iv import IV2SLS, IVGMM, IVLIML

    regressand = spec.regressand
    exog = list(spec.exog)
    endog = list(spec.endog)
    instruments = list(spec.instruments) if spec.is_iv else []
    needed = [regressand, *exog, *endog, *instruments]
    absent = [name for name in needed if name not in sample.columns]
    if absent:
        raise PanelIncomplete(
            f"this column of the published specification needs {absent}, which the panel does "
            "not carry. A near-equivalent column is not a substitute."
        )
    data = sample.dropna(subset=needed).copy()
    data = data.sort_values(["od", "ym"]).reset_index(drop=True)
    data["_route_index"] = pd.factorize(data["od"])[0]

    included = exog if spec.is_iv else exog + endog
    x_included, included_names, dropped = design(data, included, with_seasonality=with_seasonality)
    y = data[regressand].to_numpy(np.float64)
    panel = (data["_route_index"].to_numpy(), data["_time_index"].to_numpy()) if panel_hac else None

    dep = pd.Series(y, name=regressand)
    exog_frame = pd.DataFrame(x_included, columns=included_names)
    kernel = {"cov_type": "kernel", "kernel": "bartlett", "bandwidth": bandwidth}

    if spec.is_iv:
        endog_frame = pd.DataFrame(data[endog].to_numpy(np.float64), columns=endog)
        instr_frame = pd.DataFrame(data[instruments].to_numpy(np.float64), columns=instruments)
        if spec.estimator == "gmm2s":
            model = IVGMM(
                dep,
                exog_frame,
                endog_frame,
                instr_frame,
                weight_type="kernel",
                kernel="bartlett",
                bandwidth=bandwidth,
            )
            result = model.fit(iter_limit=2, debiased=debiased, **kernel)
            j_stat, j_p, j_df = (
                float(result.j_stat.stat),
                float(result.j_stat.pval),
                int(result.j_stat.df),
            )
        else:
            result = IVLIML(dep, exog_frame, endog_frame, instr_frame).fit(
                debiased=debiased, **kernel
            )
            all_instruments = np.hstack([x_included, instr_frame.to_numpy()])
            j_stat, j_p, j_df = hansen_j(
                result.resids.to_numpy(),
                all_instruments,
                bandwidth=bandwidth,
                panel=panel,
                n_params_overid=len(instruments) - len(endog),
            )
    else:
        result = IV2SLS(dep, exog_frame, None, None).fit(debiased=debiased, **kernel)
        j_stat = j_p = float("nan")
        j_df = 0

    params, errors = result.params, result.std_errors
    coefficients = {
        name: {"b": float(params[name]), "se": float(errors[name])}
        for name in COEF_ORDER
        if name in params.index
    }

    residuals = result.resids.to_numpy()
    n_obs = len(data)
    n_params = x_included.shape[1] + (len(endog) if spec.is_iv else 0)
    rss = float(residuals @ residuals)
    tss = float(((y - y.mean()) ** 2).sum())
    r2 = 1 - rss / tss
    stats: dict[str, Any] = {
        "n_obs": n_obs,
        "n_params": int(n_params),
        "n_routes": int(data["od"].nunique()),
        "adj_r2": float(1 - (1 - r2) * (n_obs - 1) / (n_obs - n_params)),
        "rmse": float(np.sqrt(rss / (n_obs - n_params))),
        "rmse_large_sample": float(np.sqrt(rss / n_obs)),
        "j_stat": j_stat,
        "j_p": j_p,
        "j_df": j_df,
        # `ivreg2`'s F statistic is a different quantity under `linearmodels`
        # and is left empty rather than filled with a number that does not mean
        # the same thing (docs/notes/replication.md).
        "f_stat": None,
    }

    if spec.is_iv:
        endog_partialled = kpmod.partial_out(data[endog].to_numpy(np.float64), x_included)
        instr_partialled = kpmod.partial_out(data[instruments].to_numpy(np.float64), x_included)
        rk = kpmod.rk_statistics(
            endog_partialled, instr_partialled, bandwidth=bandwidth, panel=panel
        )
        cd = kpmod.cragg_donald(endog_partialled, instr_partialled)
        stats.update(
            {
                "kp_lm": rk.lm,
                "kp_p": rk.lm_pvalue,
                "kp_df": rk.df,
                "kp_wald": rk.wald,
                "weak_kp_f": rk.wald_f,
                "weak_cd_f": cd["wald_f"],
                "cd_lambda_min": cd["lambda_min"],
            }
        )
    return ColumnResult(
        column=spec.column,
        regressand=regressand,
        estimator=spec.estimator,
        coefficients=coefficients,
        stats=stats,
        dropped_collinear=dropped,
    )


def run_table(
    specs: list[ColumnSpec],
    *,
    panel: Path | str | None = None,
    filter_regressand: str = "fsc_oddsarr",
    sample: pd.DataFrame | None = None,
    **fit_kwargs: Any,
) -> dict[str, Any]:
    """Estimate every column of one table on one shared sample."""
    if sample is None:
        sample = build_sample(panel, filter_regressand=filter_regressand)
    columns = {str(spec.column): fit(sample, spec, **fit_kwargs).as_dict() for spec in specs}
    return {"sample": dict(sample.attrs.get("filters", {})), "columns": columns}
