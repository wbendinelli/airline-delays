"""Run every table, compare it with the published numbers, write the report inputs.

Outputs, all under ``reports/replication/<source>/`` (``private`` or ``public``):

``results.json``
    Everything: the sample filters, and per table per column the published
    values, the replicated values and the difference, expressed both as a raw
    difference and in published standard errors.
``summary.json``
    The side-by-side scorecard per table -- share of coefficients within half a
    published standard error, sign agreement, N published against N replicated.
``sensitivity.json``
    The ADR-0008 grid.
``tables.md``
    The same content as Markdown, published x replicated x difference.

``reports/replication.typ`` reads these files; no number in the report is typed
by hand.

Usage::

    uv run python -m replication.run --source private
    uv run python -m replication.run --source public --tables 2,3
"""

from __future__ import annotations

import argparse
import json
import time
import warnings
from pathlib import Path
from typing import Any

import numpy as np

from replication import sensitivity, table2, table3, table4, table5, table6, table7
from replication.common import (
    COEF_LABEL,
    COEF_ORDER,
    HAC_BANDWIDTH,
    REPO_ROOT,
    PublicPanelIncomplete,
    Source,
    build_sample,
)
from replication.published import PUBLISHED_JSON
from replication.published import load as load_published

REPORT_DIR = REPO_ROOT / "reports" / "replication"
REGRESSION_TABLES = {
    "table3": table3,
    "table4": table4,
    "table5": table5,
    "table6": table6,
    "table7": table7,
}
TABLE_TITLES = {
    "table2": "Table 2 - Descriptive statistics",
    "table3": "Table 3 - Estimation results (2SGMM)",
    "table4": "Table 4 - Robustness checks (2SGMM)",
    "table5": "Table 5 - Estimation results (LIML)",
    "table6": "Table 6 - Estimation results (OLS)",
    "table7": "Table 7 - Estimation results (departures)",
}
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
HALF_SE = 0.5

#: Row labels for the report: the regressor labels plus the two regressands of Table 2.
ROW_LABEL = COEF_LABEL | {"fsc_oddsarr": "ODDS", "fsc_minsarr": "MINS"}


# ----------------------------------------------------------------- comparison
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


# --------------------------------------------------------------------- report
def _fmt(value: Any, digits: int = 4) -> str:
    if value is None or (isinstance(value, float) and not np.isfinite(value)):
        return "--"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, int):
        return f"{value:,}"
    return f"{value:.{digits}f}"


def write_markdown(results: dict[str, Any], summary: dict[str, Any], grid: dict[str, Any]) -> str:
    """`reports/replication/tables.md`: published x replicated x difference, table by table."""
    meta = results["meta"]
    lines: list[str] = [
        "# Replication of Tables 2-7 -- published against replicated",
        "",
        (
            "Generated by `uv run python -m replication.run` "
            f"(`--source {meta['source']}`, {meta['seconds']:.1f} s). "
            "Published values are parsed from the article by `replication/published.py` into "
            "`replication/published.json`; nothing here is typed by hand, and nothing is tuned "
            "to match (`CLAUDE.md`, `DECISIONS.md` ADR-0010)."
        ),
        "",
        (
            f"Source: **{meta['source']}**. HAC: Bartlett kernel, bandwidth "
            f"{meta['bandwidth']} in the `linearmodels` convention (= Stata `bw(5)`), "
            f"finite-sample correction {'on' if meta['debiased'] else 'off'}, seasonality "
            f"dummies {'in' if meta['with_seasonality'] else 'out'}."
        ),
        "",
        "## Scorecard",
        "",
        (
            "`diff/s.e.` is the difference between the replicated and the published "
            "coefficient, measured in *published* standard errors -- the column that decides "
            "whether an estimate is materially different."
        ),
        "",
        (
            "| Table | coefficients | signs equal | within 0.5 s.e. | median diff/s.e. | "
            "max diff/s.e. | median s.e. ratio |"
        ),
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for name, values in summary.items():
        if name == "table2":
            continue
        lines.append(
            f"| {TABLE_TITLES[name]} | {values['n_coefficients']} | "
            f"{values['sign_agreement']}/{values['n_coefficients']} | "
            f"{values['within_half_se']}/{values['n_coefficients']} "
            f"({values['within_half_se_share'] * 100:.0f}%) | "
            f"{values['median_difference_in_se']:.3f} | "
            f"{values['max_difference_in_se']:.3f} | "
            f"{values['median_se_ratio']:.3f} |"
        )

    if meta.get("tables_not_estimated"):
        lines += ["", "### Tables this source cannot estimate", ""]
        for name, reason in meta["tables_not_estimated"].items():
            lines.append(f"- **{TABLE_TITLES[name]}** -- {reason}")

    table2_block = results.get("table2")
    if table2_block:
        comparison = table2_block["comparison"]
        lines += [
            "",
            f"## {TABLE_TITLES['table2']}",
            "",
            (
                f"Sample: "
                f"{_fmt(table2_block['replicated']['sample'].get('n_after_singleton_cut'))} "
                f"observations, {table2_block['replicated']['sample'].get('routes')} routes. "
                f"Correlation triangle: {comparison['n_correlations']} cells compared, median "
                f"absolute difference "
                f"{_fmt(comparison['median_abs_correlation_difference'], 3)}, maximum "
                f"{_fmt(comparison['max_abs_correlation_difference'], 3)}."
            ),
            "",
            (
                "| Variable | mean pub | mean rep | s.d. pub | s.d. rep | min pub | min rep | "
                "max pub | max rep |"
            ),
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
        for name in table2_block["published"]["variables"]:
            cells = [ROW_LABEL.get(name, name)]
            for statistic in ("mean", "sd", "min", "max"):
                entry = comparison["univariate"].get(statistic, {}).get(name, {})
                cells += [_fmt(entry.get("published"), 2), _fmt(entry.get("replicated"), 4)]
            lines.append("| " + " | ".join(cells) + " |")

    for name, module_block in results.items():
        if name in {"meta", "table2"} or "comparison" not in module_block:
            continue
        lines += ["", f"## {TABLE_TITLES[name]}", ""]
        columns = module_block["comparison"]
        header = list(columns)
        lines += [
            "Coefficients, with published standard errors in brackets.",
            "",
            "| Variable | "
            + " | ".join(f"({key}) pub | ({key}) rep | ({key}) diff/s.e." for key in header)
            + " |",
            "|---" + "|---:" * (3 * len(header)) + "|",
        ]
        for variable in COEF_ORDER:
            if not any(variable in columns[key]["coefficients"] for key in header):
                continue
            cells = [COEF_LABEL[variable]]
            for key in header:
                entry = columns[key]["coefficients"].get(variable, {})
                published_b, published_se = entry.get("published_b"), entry.get("published_se")
                replicated_b = entry.get("replicated_b")
                replicated_se = entry.get("replicated_se")
                cells += [
                    "--"
                    if published_b is None
                    else f"{published_b:+.4f} [{_fmt(published_se, 3)}]",
                    "--"
                    if replicated_b is None
                    else f"{replicated_b:+.4f} [{_fmt(replicated_se, 4)}]",
                    _fmt(entry.get("difference_in_se"), 2),
                ]
            lines.append("| " + " | ".join(cells) + " |")
        lines += [
            "",
            "| Statistic | " + " | ".join(f"({key}) pub | ({key}) rep" for key in header) + " |",
            "|---" + "|---:" * (2 * len(header)) + "|",
        ]
        for key_stat, label in STAT_LABELS.items():
            if not any(key_stat in columns[key]["stats"] for key in header):
                continue
            cells = [label]
            for key in header:
                entry = columns[key]["stats"].get(key_stat, {})
                digits = 0 if key_stat == "n_obs" else 4
                cells += [
                    _fmt(entry.get("published"), digits),
                    _fmt(entry.get("replicated"), digits),
                ]
            lines.append("| " + " | ".join(cells) + " |")

    lines += [
        "",
        "## Sensitivity (ADR-0008)",
        "",
        (
            "Main coefficients of Table 3 columns (1) and (2) across the flight-level outlier "
            "threshold and the seasonality dummies. A threshold row is *unavailable* when the "
            "panel does not carry the regressand rebuilt at that threshold -- it is reported "
            "as missing, never approximated."
        ),
        "",
        (
            "| Col | outlier threshold | seasonality | N | HHI city-pair | HHI max endpoint | "
            "Adj. R-squared | J |"
        ),
        "|---:|---|---|---:|---:|---:|---:|---:|",
    ]
    for cell in grid["cells"]:
        if not cell["available"]:
            lines.append(
                f"| ({cell['column']}) | {cell['outlier_threshold']} | "
                f"{'yes' if cell['with_seasonality'] else 'no'} | "
                "unavailable | unavailable | unavailable | unavailable | unavailable |"
            )
            continue
        stats = cell["stats"]
        lines.append(
            f"| ({cell['column']}) | {cell['outlier_threshold']} | "
            f"{'yes' if cell['with_seasonality'] else 'no'} | {stats['n_obs']:,} | "
            f"{cell['b'].get('rthhi', float('nan')):+.4f} "
            f"[{cell['se'].get('rthhi', float('nan')):.4f}] | "
            f"{cell['b'].get('maxcthhi', float('nan')):+.4f} "
            f"[{cell['se'].get('maxcthhi', float('nan')):.4f}] | "
            f"{stats['adj_r2']:.4f} | {stats['j_stat']:.4f} |"
        )
    if not any(cell["available"] for cell in grid["cells"]):
        lines.append("")
        lines.append("No cell of the sensitivity grid can be estimated on this source.")
    if grid["unavailable_thresholds"]:
        lines += [
            "",
            "Unavailable thresholds on this source: "
            + ", ".join(grid["unavailable_thresholds"])
            + " -- "
            + next(cell["reason"] for cell in grid["cells"] if not cell["available"])
            + ".",
        ]
    return "\n".join(lines) + "\n"


def _finite(payload: Any) -> Any:
    """Replace NaN and infinities with ``null``: strict JSON has no literal for them.

    `reports/replication.typ` parses these files with Typst's ``json()``, which
    rejects the ``NaN`` token Python's ``json`` is happy to emit.
    """
    if isinstance(payload, dict):
        return {key: _finite(value) for key, value in payload.items()}
    if isinstance(payload, list):
        return [_finite(value) for value in payload]
    if isinstance(payload, float) and not np.isfinite(payload):
        return None
    return payload


def _dump(payload: Any) -> str:
    return json.dumps(_finite(payload), indent=1, ensure_ascii=False, default=float) + "\n"


# ------------------------------------------------------------------------ main
def run(
    source: Source | str = Source.PRIVATE,
    *,
    tables: list[str] | None = None,
    outdir: Path | None = None,
    with_sensitivity: bool = True,
) -> dict[str, Any]:
    """Estimate, compare, and write ``results.json``, ``summary.json``, ``tables.md``."""
    warnings.filterwarnings("ignore", category=FutureWarning)
    started = time.time()
    source = Source(source)
    outdir = Path(outdir) if outdir is not None else REPORT_DIR / source.value
    published = load_published()
    wanted = set(tables or ["table2", *REGRESSION_TABLES])

    arrival_sample = build_sample(source, filter_regressand="fsc_oddsarr")
    departure_sample = None

    results: dict[str, Any] = {}
    summary: dict[str, Any] = {}

    if "table2" in wanted:
        replicated = table2.run(source, sample=arrival_sample)
        results["table2"] = {
            "published": published["table2"],
            "replicated": replicated,
            "comparison": compare_table2(published["table2"], replicated),
        }

    unavailable: dict[str, str] = {}
    for name, module in REGRESSION_TABLES.items():
        if name not in wanted:
            continue
        try:
            if name == "table7":
                if departure_sample is None:
                    departure_sample = build_sample(
                        source, filter_regressand=module.FILTER_REGRESSAND
                    )
                replicated = module.run(source, sample=departure_sample)
            else:
                replicated = module.run(source, sample=arrival_sample)
        except PublicPanelIncomplete as exc:
            # The panel does not carry every variable this table needs. Say so and
            # move on: an empty table is a result, a substituted column is not.
            unavailable[name] = str(exc)
            continue
        published_columns = published[name]["columns"]
        comparison = {
            key: compare_column(published_columns.get(key, {}), value)
            for key, value in replicated["columns"].items()
        }
        results[name] = {
            "published": published[name],
            "replicated": replicated,
            "comparison": comparison,
        }
        summary[name] = score(comparison)

    grid = (
        sensitivity.run(source, sample=arrival_sample)
        if with_sensitivity
        else {"cells": [], "unavailable_thresholds": [], "n_cells": 0, "n_available": 0}
    )

    results["meta"] = {
        "source": source.value,
        "tables_not_estimated": unavailable,
        "bandwidth": HAC_BANDWIDTH,
        "debiased": True,
        "with_seasonality": True,
        "published_json": str(PUBLISHED_JSON.relative_to(REPO_ROOT)),
        "sample": dict(arrival_sample.attrs.get("filters", {})),
        "seconds": round(time.time() - started, 1),
    }

    outdir.mkdir(parents=True, exist_ok=True)
    for name, payload in (
        ("results.json", results),
        ("summary.json", summary),
        ("sensitivity.json", grid),
    ):
        (outdir / name).write_text(_dump(payload), encoding="utf-8")
    (outdir / "tables.md").write_text(write_markdown(results, summary, grid), encoding="utf-8")
    return {"results": results, "summary": summary, "sensitivity": grid}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Replicate Tables 2-7 and write the report inputs")
    parser.add_argument("--source", default=Source.PRIVATE.value, choices=[s.value for s in Source])
    parser.add_argument("--tables", default=None, help="comma-separated, e.g. table2,table3")
    parser.add_argument("--outdir", default=None, help="Defaults to reports/replication/<source>/")
    parser.add_argument("--no-sensitivity", action="store_true")
    args = parser.parse_args(argv)
    tables = args.tables.split(",") if args.tables else None
    output = run(
        args.source,
        tables=tables,
        outdir=Path(args.outdir) if args.outdir else None,
        with_sensitivity=not args.no_sensitivity,
    )
    for name, values in output["summary"].items():
        print(
            f"{name}: {values['sign_agreement']}/{values['n_coefficients']} signs, "
            f"{values['within_half_se']}/{values['n_coefficients']} within 0.5 s.e., "
            f"median {values['median_difference_in_se']:.3f} s.e."
        )
    print(f"wrote {args.outdir or (REPORT_DIR / args.source)} in {output['results']['meta']['seconds']} s")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
