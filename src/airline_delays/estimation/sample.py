"""The estimation sample and the design matrix, as the do-files build them."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import scipy.linalg as sla

from airline_delays.estimation.loader import (
    FIRST_YM,
    LAST_YM,
    SEASONALITY,
    TIME_DUMMIES,
    PanelIncomplete,
    load_panel,
)
from airline_delays.estimation.specification import SINGLETON_CUTOFF


def build_sample(
    panel: Path | str | None = None,
    *,
    filter_regressand: str = "fsc_oddsarr",
) -> pd.DataFrame:
    """The do-files' opening block, in the order they run it.

    ``projbase 18 ; drop fe_* ; drop sz_* ; drop if <y>==. ; findsingletons k ;
    drop if _count_k<=5 ; panelset ; effects k ; dummymonthreg``

    `filter_regressand` is ``fsc_oddsarr`` for Tables 2-6 and ``fsc_oddsdep``
    for Table 7. It bites in *every* column of a table, including the MINS
    columns whose own regressand is never missing: that is deliberate in the
    do-files, so all columns of a table share one sample. Reproduce it.
    """
    frame = load_panel(panel)
    n_raw, routes_raw = len(frame), frame["od"].nunique()
    if filter_regressand not in frame.columns:
        raise PanelIncomplete(f"the panel does not carry the sample filter {filter_regressand!r}")
    # The article's panel is 2002m1-2013m12. A wider panel would carry rows with
    # an all-zero row of time dummies, absorbed by the constant: cut them.
    in_window = frame["ym"].between(FIRST_YM, LAST_YM)
    n_outside_window = int((~in_window).sum())
    frame = frame[in_window].copy()
    frame = frame[frame[filter_regressand].notna()].copy()
    n_after_missing = len(frame)
    counts = frame.groupby("od")["od"].transform("size")
    frame = frame[counts > SINGLETON_CUTOFF].copy()
    frame = frame.sort_values(["od", "ym"]).reset_index(drop=True)
    frame["_route_index"] = pd.factorize(frame["od"])[0]
    frame["_time_index"] = frame["_period"] - 1
    frame.attrs["filters"] = {
        "panel": load_panel(panel).attrs.get("panel_path"),
        "filter_regressand": filter_regressand,
        "n_raw": int(n_raw),
        "routes_raw": int(routes_raw),
        "n_outside_window": n_outside_window,
        "window": [FIRST_YM, LAST_YM],
        "n_after_missing_regressand": int(n_after_missing),
        "n_after_singleton_cut": len(frame),
        "routes": int(frame["od"].nunique()),
        "months": int(frame["ym"].nunique()),
        "singleton_cutoff": SINGLETON_CUTOFF,
    }
    return frame


# ---------------------------------------------------------------- design block
def route_dummies(frame: pd.DataFrame) -> tuple[np.ndarray, list[str]]:
    """``effects k``: route dummies rebuilt on the restricted sample, first one omitted."""
    codes = frame["_route_index"].to_numpy()
    n_routes = int(codes.max()) + 1
    block = np.zeros((len(frame), n_routes), dtype=np.float64)
    block[np.arange(len(frame)), codes] = 1.0
    names = [f"fe_k_{i + 1}" for i in range(n_routes)]
    return block[:, 1:], names[1:]


def drop_collinear(
    matrix: np.ndarray, names: list[str], n_protected: int, tol: float = 1e-7
) -> tuple[np.ndarray, list[str], list[str]]:
    """Rank-revealing QR: drop a column that is a linear combination of earlier ones.

    ``ivreg2`` does this silently; NumPy does not. The first `n_protected`
    columns (constant and the regressors of interest) are never dropped. In
    these samples the cut is clean -- the null ``|R_jj|`` sit around 1e-10 and
    the smallest surviving one around 1e2.
    """
    scale = matrix.std(axis=0)
    scale[scale == 0] = 1.0
    upper = sla.qr(matrix / scale, mode="r", check_finite=False)[0]
    diagonal = np.abs(np.diag(upper))
    keep = diagonal > tol * diagonal.max()
    keep[:n_protected] = True
    dropped = [names[i] for i in range(len(names)) if not keep[i]]
    return matrix[:, keep], [names[i] for i in range(len(names)) if keep[i]], dropped


def design(
    frame: pd.DataFrame, exog: list[str], *, with_seasonality: bool
) -> tuple[np.ndarray, list[str], list[str]]:
    """``[const, exog, route dummies, t_2..t_144, (sz_*)]`` with collinear columns removed."""
    n = len(frame)
    blocks = [np.ones((n, 1)), frame[exog].to_numpy(np.float64)] if exog else [np.ones((n, 1))]
    names = ["const", *exog]
    dummies, dummy_names = route_dummies(frame)
    blocks.append(dummies)
    names += dummy_names
    time_columns = [name for name in TIME_DUMMIES[1:] if frame[name].to_numpy().any()]
    blocks.append(frame[time_columns].to_numpy(np.float64))
    names += time_columns
    if with_seasonality:
        blocks.append(frame[list(SEASONALITY)].to_numpy(np.float64))
        names += list(SEASONALITY)
    return drop_collinear(np.hstack(blocks), names, 1 + len(exog))
