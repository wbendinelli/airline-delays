"""Run every table on the article's estimation panel, compare it with the published numbers,
write the report inputs.

Outputs, all under ``reports/replication/``:

``results.json``
    Everything: the sample filters, and per table per column the published
    values, the re-estimated values and the difference, expressed both as a raw
    difference and in published standard errors.
``summary.json``
    The scorecard per table -- share of coefficients within half a published
    standard error, sign agreement, N published against N re-estimated -- and
    the HHI sign-inversion count.
``sensitivity.json``
    The seasonality grid.
``tables.md``
    The same content as Markdown, published x re-estimated x difference.

``reports/replication.typ`` reads these files; no number in the report is typed
by hand.

Usage::

    airline-delays estimate                    # everything, about 40 s
    airline-delays estimate --tables table2,table3
    airline-delays estimate --panel other_panel.parquet --outdir /tmp/out
    airline-delays estimate --rescore          # summary.json and tables.md from results.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
import warnings
from pathlib import Path
from typing import Any

from airline_delays import paths
from airline_delays.estimation import sensitivity, table2, table3, table4, table5, table6, table7
from airline_delays.estimation.compare import (
    compare_column,
    compare_table2,
    hhi_sign_inversions,
    score,
)
from airline_delays.estimation.loader import ARTICLE_PANEL_MANIFEST, resolve_panel
from airline_delays.estimation.published import PUBLISHED_JSON
from airline_delays.estimation.published import load as load_published
from airline_delays.estimation.report import TABLE_TITLES, dump, write_markdown
from airline_delays.estimation.sample import build_sample
from airline_delays.estimation.specification import HAC_BANDWIDTH

REPORT_DIR = paths.REPLICATION_REPORTS
REGRESSION_TABLES = {
    "table3": table3,
    "table4": table4,
    "table5": table5,
    "table6": table6,
    "table7": table7,
}


def _panel_provenance(path: Path, rows: int) -> dict[str, Any]:
    """What `results.json` records about the panel it was estimated on: never a local path."""
    try:
        relative = str(path.resolve().relative_to(paths.REPO_ROOT))
    except ValueError:
        relative = path.name
    provenance: dict[str, Any] = {
        "path": relative,
        "rows": rows,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }
    if path.resolve() == resolve_panel(None).resolve() and ARTICLE_PANEL_MANIFEST.exists():
        manifest = json.loads(ARTICLE_PANEL_MANIFEST.read_text(encoding="utf-8"))
        provenance["source_header_timestamp"] = manifest.get("source", {}).get(
            "stata_header_timestamp"
        )
        provenance["source_description"] = manifest.get("source", {}).get("description")
    return provenance


def run(
    panel: Path | str | None = None,
    *,
    tables: list[str] | None = None,
    outdir: Path | None = None,
    with_sensitivity: bool = True,
) -> dict[str, Any]:
    """Estimate, compare, and write ``results.json``, ``summary.json``, ``tables.md``."""
    warnings.filterwarnings("ignore", category=FutureWarning)
    started = time.time()
    panel_path = resolve_panel(panel)
    outdir = Path(outdir) if outdir is not None else REPORT_DIR
    published = load_published()
    wanted = set(tables or ["table2", *REGRESSION_TABLES])

    arrival_sample = build_sample(panel_path, filter_regressand="fsc_oddsarr")
    departure_sample = None

    results: dict[str, Any] = {}
    summary: dict[str, Any] = {}

    if "table2" in wanted:
        replicated = table2.run(panel_path, sample=arrival_sample)
        results["table2"] = {
            "published": published["table2"],
            "replicated": replicated,
            "comparison": compare_table2(published["table2"], replicated),
        }

    for name, module in REGRESSION_TABLES.items():
        if name not in wanted:
            continue
        if name == "table7":
            if departure_sample is None:
                departure_sample = build_sample(
                    panel_path, filter_regressand=module.FILTER_REGRESSAND
                )
            replicated = module.run(panel_path, sample=departure_sample)
        else:
            replicated = module.run(panel_path, sample=arrival_sample)
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

    # The article's headline: does instrumenting flip the sign of the two HHI
    # terms, and does that flip replicate? Computed, never typed.
    summary["hhi_sign_inversions"] = hhi_sign_inversions(results)

    grid = (
        sensitivity.run(panel_path, sample=arrival_sample)
        if with_sensitivity
        else {"cells": [], "n_cells": 0}
    )

    results["meta"] = {
        "panel": _panel_provenance(panel_path, int(arrival_sample.attrs["filters"]["n_raw"])),
        "bandwidth": HAC_BANDWIDTH,
        "debiased": True,
        "with_seasonality": True,
        "published_json": str(PUBLISHED_JSON.relative_to(paths.REPO_ROOT)),
        "sample": dict(arrival_sample.attrs.get("filters", {})),
        "seconds": round(time.time() - started, 1),
    }

    outdir.mkdir(parents=True, exist_ok=True)
    for name, payload in (
        ("results.json", results),
        ("summary.json", summary),
        ("sensitivity.json", grid),
    ):
        (outdir / name).write_text(dump(payload), encoding="utf-8")
    (outdir / "tables.md").write_text(write_markdown(results, summary, grid), encoding="utf-8")
    return {"results": results, "summary": summary, "sensitivity": grid}


def rescore(outdir: Path) -> dict[str, Any]:
    """Recompute the derived scorecard from an existing ``results.json``.

    Everything in ``summary.json`` and ``tables.md`` is a pure function of
    ``results.json`` and ``sensitivity.json``, so a new derived statistic can be
    added to the committed artefacts without re-estimating and without the
    measured wall time drifting. Nothing is re-estimated here; ``results.json``
    is read, never written.
    """
    results = json.loads((outdir / "results.json").read_text(encoding="utf-8"))
    grid = json.loads((outdir / "sensitivity.json").read_text(encoding="utf-8"))
    summary: dict[str, Any] = {}
    for name in REGRESSION_TABLES:
        block = results.get(name)
        if block and "comparison" in block:
            summary[name] = score(block["comparison"])
    summary["hhi_sign_inversions"] = hhi_sign_inversions(results)
    (outdir / "summary.json").write_text(dump(summary), encoding="utf-8")
    (outdir / "tables.md").write_text(write_markdown(results, summary, grid), encoding="utf-8")
    return {"results": results, "summary": summary, "sensitivity": grid}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="airline-delays estimate",
        description="Re-estimate Tables 2-7 on the article's estimation panel and write the report inputs",
    )
    parser.add_argument(
        "--panel",
        default=None,
        help="A route-month panel carrying the estimation contract; defaults to the committed "
        "data/analysis/article_panel_route_month.parquet",
    )
    parser.add_argument("--tables", default=None, help="comma-separated, e.g. table2,table3")
    parser.add_argument("--outdir", default=None, help="Defaults to reports/replication/")
    parser.add_argument("--no-sensitivity", action="store_true")
    parser.add_argument(
        "--rescore",
        action="store_true",
        help="Rebuild summary.json and tables.md from the committed results.json, without "
        "re-estimating.",
    )
    args = parser.parse_args(argv)
    tables = args.tables.split(",") if args.tables else None
    outdir = Path(args.outdir) if args.outdir else REPORT_DIR
    if args.rescore:
        output = rescore(outdir)
    else:
        output = run(
            args.panel,
            tables=tables,
            outdir=outdir,
            with_sensitivity=not args.no_sensitivity,
        )
    for name, values in output["summary"].items():
        if name not in TABLE_TITLES:
            continue
        print(
            f"{name}: {values['sign_agreement']}/{values['n_coefficients']} signs, "
            f"{values['within_half_se']}/{values['n_coefficients']} within 0.5 s.e., "
            f"median {values['median_difference_in_se']:.3f} s.e."
        )
    hhi = output["summary"].get("hhi_sign_inversions", {})
    if hhi.get("available"):
        print(
            f"hhi sign inversion: {hhi['n_inversion_replicates']}/{hhi['n_comparisons']} "
            f"replicate (columns {', '.join(hhi['columns_with_inversion']) or 'none'}); "
            f"pattern agrees in {hhi['n_pattern_agrees']}/{hhi['n_comparisons']}"
        )
    if args.rescore:
        print(f"rescored {outdir} from results.json (nothing re-estimated)")
    else:
        print(f"wrote {outdir} in {output['results']['meta']['seconds']} s")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
