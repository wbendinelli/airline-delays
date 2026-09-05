"""Comparing the re-estimated tables with the published ones -- the replication result."""

from __future__ import annotations

from typing import Any

import numpy as np

from airline_delays.estimation.specification import COEF_LABEL, COEF_ORDER

HALF_SE = 0.5

STAT_LABELS = {
    "n_obs": "Nr observations",
    "adj_r2": "Adj. R-squared",
    "rmse": "RMSE statistic",
    "j_stat": "J statistic",
    "j_p": "J p-value",
    "kp_lm": "KP statistic (rk LM)",
    "weak_kp_f": "Weak KP statistic (rk Wald F)",
    "weak_cd_f": "Weak CD statistic (Cragg-Donald F)",
    "f_stat": "F statistic",
}


def compare_column(published: dict[str, Any], replicated: dict[str, Any]) -> dict[str, Any]:
    """One column: coefficient by coefficient, plus the statistics rows."""
    coefficients: dict[str, dict[str, Any]] = {}
    for name in COEF_ORDER:
        pub_b = published.get("b", {}).get(name)
        rep_b = replicated.get("b", {}).get(name)
        if pub_b is None and rep_b is None:
            continue
        pub_se = published.get("se", {}).get(name)
        rep_se = replicated.get("se", {}).get(name)
        entry: dict[str, Any] = {
            "label": COEF_LABEL[name],
            "published_b": pub_b,
            "replicated_b": rep_b,
            "published_se": pub_se,
            "replicated_se": rep_se,
        }
        if pub_b is not None and rep_b is not None:
            difference = rep_b - pub_b
            entry["difference"] = difference
            entry["sign_agrees"] = bool(np.sign(rep_b) == np.sign(pub_b))
            if pub_se:
                entry["difference_in_se"] = abs(difference) / pub_se
                entry["within_half_se"] = bool(entry["difference_in_se"] < HALF_SE)
            if pub_se and rep_se:
                entry["se_ratio"] = rep_se / pub_se
        coefficients[name] = entry

    stats: dict[str, Any] = {}
    for key, label in STAT_LABELS.items():
        pub_value = published.get("stats", {}).get(key)
        rep_value = replicated.get("stats", {}).get(key)
        if pub_value is None and rep_value is None:
            continue
        stats[key] = {"label": label, "published": pub_value, "replicated": rep_value}
        if isinstance(pub_value, int | float) and isinstance(rep_value, int | float) and pub_value:
            stats[key]["relative_difference"] = (rep_value - pub_value) / abs(pub_value)
    return {
        "published_regressand": published.get("regressand"),
        "replicated_regressand": replicated.get("regressand"),
        "estimator": replicated.get("estimator"),
        "coefficients": coefficients,
        "stats": stats,
    }


def score(columns: dict[str, Any]) -> dict[str, Any]:
    """The scorecard for one table: how close, how many signs, how big the samples."""
    diffs, ratios, signs = [], [], []
    for column in columns.values():
        for entry in column["coefficients"].values():
            if "difference_in_se" in entry:
                diffs.append(entry["difference_in_se"])
                signs.append(entry["sign_agrees"])
            if "se_ratio" in entry:
                ratios.append(entry["se_ratio"])
    diffs_array = np.array(diffs, dtype=float)
    ratios_array = np.array(ratios, dtype=float)
    return {
        "n_coefficients": len(diffs),
        "sign_agreement": int(np.sum(signs)),
        "sign_agreement_share": float(np.mean(signs)) if signs else float("nan"),
        "within_half_se": int(np.sum(diffs_array < HALF_SE)) if len(diffs_array) else 0,
        "within_half_se_share": float(np.mean(diffs_array < HALF_SE))
        if len(diffs_array)
        else float("nan"),
        "median_difference_in_se": float(np.median(diffs_array))
        if len(diffs_array)
        else float("nan"),
        "max_difference_in_se": float(np.max(diffs_array)) if len(diffs_array) else float("nan"),
        "median_se_ratio": float(np.median(ratios_array)) if len(ratios_array) else float("nan"),
        "n_obs": {
            key: {
                "published": column["stats"].get("n_obs", {}).get("published"),
                "replicated": column["stats"].get("n_obs", {}).get("replicated"),
            }
            for key, column in columns.items()
        },
    }


HHI_VARIABLES = ("rthhi", "maxcthhi")


def hhi_sign_inversions(results: dict[str, Any]) -> dict[str, Any]:
    """Count where OLS and 2SGMM carry opposite signs on the two HHI terms.

    The article's central argument is that instrumenting flips the sign of the
    concentration terms: OLS says concentration reduces delay, 2SGMM says the
    opposite. Table 6 is the OLS specification, Table 3 the 2SGMM one, six
    columns each, two HHI variables per column -- twelve comparisons. Three
    statements can be made about them:

    ``n_inverted_published`` / ``n_inverted_replicated``
        comparisons where an inversion actually occurs.
    ``n_pattern_agrees``
        comparisons where the replication reproduces the published *pattern* --
        an inversion where the article has one, none where it has none.
    ``n_inversion_replicates``
        comparisons where the article inverts **and** the replication inverts:
        what "the sign inversion replicates" means.

    Nothing here is a definition: the sign of a coefficient is read off
    ``results.json`` as estimated. A coefficient that is exactly zero, or
    missing on either side, is skipped and counted in ``n_skipped``.
    """

    def sign(value: Any) -> int | None:
        if value is None or not np.isfinite(value) or value == 0:
            return None
        return 1 if value > 0 else -1

    detail: list[dict[str, Any]] = []
    skipped = 0
    ols = results.get("table6")
    gmm = results.get("table3")
    if not (ols and gmm):
        return {
            "available": False,
            "reason": "needs both table3 (2SGMM) and table6 (OLS)",
            "n_comparisons": 0,
        }
    for key in sorted(gmm["published"]["columns"], key=int):
        for variable in HHI_VARIABLES:
            cell: dict[str, Any] = {"column": key, "variable": variable}
            for side, block in (("published", "published"), ("replicated", "replicated")):
                ols_b = ols[block]["columns"].get(key, {}).get("b", {}).get(variable)
                gmm_b = gmm[block]["columns"].get(key, {}).get("b", {}).get(variable)
                ols_sign, gmm_sign = sign(ols_b), sign(gmm_b)
                cell[side] = {
                    "ols": ols_b,
                    "gmm": gmm_b,
                    "inverted": None
                    if ols_sign is None or gmm_sign is None
                    else ols_sign != gmm_sign,
                }
            if cell["published"]["inverted"] is None or cell["replicated"]["inverted"] is None:
                skipped += 1
            cell["pattern_agrees"] = (
                cell["published"]["inverted"] is not None
                and cell["published"]["inverted"] == cell["replicated"]["inverted"]
            )
            cell["inversion_replicates"] = (
                cell["published"]["inverted"] is True and cell["replicated"]["inverted"] is True
            )
            cell["regressand"] = gmm["published"]["columns"].get(key, {}).get("regressand")
            detail.append(cell)
    return {
        "available": True,
        "ols_table": "table6",
        "gmm_table": "table3",
        "variables": list(HHI_VARIABLES),
        "n_comparisons": len(detail),
        "n_skipped": skipped,
        "n_inverted_published": sum(c["published"]["inverted"] is True for c in detail),
        "n_inverted_replicated": sum(c["replicated"]["inverted"] is True for c in detail),
        "n_inversion_replicates": sum(c["inversion_replicates"] for c in detail),
        "n_pattern_agrees": sum(c["pattern_agrees"] for c in detail),
        "columns_with_inversion": sorted(
            {c["column"] for c in detail if c["inversion_replicates"]}, key=int
        ),
        "detail": detail,
    }


def compare_table2(published: dict[str, Any], replicated: dict[str, Any]) -> dict[str, Any]:
    """Table 2 is descriptives: compare the four univariate rows variable by variable."""
    rows: dict[str, dict[str, Any]] = {}
    for statistic, published_values in published.get("univariate", {}).items():
        replicated_values = replicated.get("univariate", {}).get(statistic, {})
        rows[statistic] = {
            name: {
                "published": published_values.get(name),
                "replicated": replicated_values.get(name),
                "difference": (
                    replicated_values[name] - published_values[name]
                    if name in replicated_values and name in published_values
                    else None
                ),
            }
            for name in published.get("variables", [])
        }
    correlations = []
    for row, published_row in published.get("correlation", {}).items():
        for column, published_value in published_row.items():
            replicated_value = replicated.get("correlation", {}).get(row, {}).get(column)
            if replicated_value is not None:
                correlations.append(abs(replicated_value - published_value))
    return {
        "univariate": rows,
        "n_correlations": len(correlations),
        "max_abs_correlation_difference": float(np.max(correlations)) if correlations else None,
        "median_abs_correlation_difference": float(np.median(correlations))
        if correlations
        else None,
    }
