#!/usr/bin/env python
"""`just demo`: the smallest end-to-end reproduction, offline, in seconds.

Runs the same code path as the full pipeline (`just stage`, `just features`,
`just panel`, `just replicate`) over the committed fixture
``tests/fixtures/vra_sample.parquet`` -- three routes (SBAR-SBBR, MRSP-MRRJ,
SBCT-MRSP) cut from the 2004, 2009 and 2012 files, about 20,000 staged flight
legs, a few of them dated in the following January because the raw file month
and the scheduled date disagree (the ADR-0016 case, kept on purpose) -- so a
fresh clone can watch raw legs become the route-month panel and Table 2
without the network or ``data/raw/``.

Steps (they mirror the ``staged_tree`` and ``built`` fixtures of
``tests/conftest.py``, which is what the test-suite exercises):

1. re-partition the fixture as ``<out>/staged/year=YYYY/part-0.parquet``, the
   layout ``vra.features.build_fact`` reads one year at a time;
2. ``build_fact`` -> ``<out>/analysis/fact_group_route_month.parquet`` and the
   two ``<out>/derived`` intermediates;
3. ``build_panel`` -> ``<out>/analysis/panel_route_month.parquet`` (+ csv.gz);
4. ``replication.run`` on that panel (public source, Table 2 only, no
   sensitivity grid) -> ``<out>/replication/{results,summary}.json`` and
   ``tables.md``.

Everything lands under ``data/derived/demo/`` by default, a git-ignored
directory (``.gitignore``), and a ``summary.json`` with the counts and the
wall time is written next to it. Nothing under ``data/analysis/`` or
``reports/`` is touched: the demo never overwrites the committed tables.

Usage:
    uv run python scripts/demo.py [--out data/derived/demo] [--quiet]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

FIXTURE = ROOT / "tests" / "fixtures" / "vra_sample.parquet"
DEFAULT_OUT = ROOT / "data" / "derived" / "demo"


def repartition(fixture: Path, staged: Path) -> dict[int, int]:
    """Write the single-file fixture as ``year=YYYY/part-0.parquet`` partitions."""
    import pyarrow as pa
    import pyarrow.parquet as pq

    frame = pq.read_table(fixture).to_pandas()
    frame = frame[frame["year"].notna()]
    rows_by_year: dict[int, int] = {}
    for year, part in frame.groupby(frame["year"].astype(int)):
        directory = staged / f"year={int(year)}"
        directory.mkdir(parents=True, exist_ok=True)
        pq.write_table(
            pa.Table.from_pandas(part, preserve_index=False), directory / "part-0.parquet"
        )
        rows_by_year[int(year)] = len(part)
    return rows_by_year


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="Output directory.")
    parser.add_argument("--fixture", type=Path, default=FIXTURE, help="Staged fixture parquet.")
    parser.add_argument("--quiet", action="store_true", help="Print only the final summary.")
    args = parser.parse_args(argv)

    if not args.fixture.exists():
        print(f"demo: fixture not found at {args.fixture}", file=sys.stderr)
        return 2

    from vra import features, panel

    say = (lambda *_: None) if args.quiet else print
    started = time.time()
    out = args.out.resolve()
    staged, analysis, derived = out / "staged", out / "analysis", out / "derived"
    for directory in (staged, analysis, derived):
        directory.mkdir(parents=True, exist_ok=True)

    say(f"demo: fixture {args.fixture.relative_to(ROOT)} -> {out}")
    rows_by_year = repartition(args.fixture, staged)
    say(
        "  1. staged: "
        + ", ".join(f"{year}: {rows:,d} legs" for year, rows in sorted(rows_by_year.items()))
    )

    result = features.build_fact(
        staged,
        analysis,
        derived,
        groups_path=ROOT / "data" / "external" / "groups.csv",
        verbose=False,
    )
    say(
        f"  2. fact table: {result.fact_rows:,d} group x route x month cells "
        f"over {len(result.years)} years ({result.seconds:.1f} s)"
    )

    _, panel_result = panel.build_panel(analysis, derived, external_dir=ROOT / "data" / "external")
    assert panel_result is not None
    say(
        f"  3. panel: {panel_result.rows:,d} route-months x {panel_result.columns} columns "
        f"-> {panel_result.parquet.relative_to(out)} ({panel_result.seconds:.1f} s)"
    )

    # The replication code reads the public panel from AIRLINE_DELAYS_PANEL when
    # set; pointing it at the demo panel keeps data/analysis/ and reports/ untouched.
    os.environ["AIRLINE_DELAYS_PANEL"] = str(panel_result.parquet)
    from replication import run as replication_run

    replication_dir = out / "replication"
    output = replication_run.run(
        "public", tables=["table2"], outdir=replication_dir, with_sensitivity=False
    )
    replicated = output["results"]["table2"]["replicated"]
    computed = list(replicated["variables"])
    missing = list(replicated["missing_variables"])
    empty = list(replicated["empty_variables"])
    n_obs = replicated["sample"].get("n_after_singleton_cut")
    say(
        f"  4. Table 2 on the demo panel: {len(computed)} of 13 variables computed on "
        f"{n_obs} route-months; {len(missing)} absent and {len(empty)} entirely null, "
        f"declared rather than substituted -> {replication_dir.relative_to(out)}/tables.md"
    )

    summary = {
        "fixture": str(args.fixture.relative_to(ROOT)),
        "staged_rows_by_year": rows_by_year,
        "fact_rows": int(result.fact_rows),
        "panel_rows": int(panel_result.rows),
        "panel_columns": int(panel_result.columns),
        "table2_variables_computed": computed,
        "table2_variables_missing": missing,
        "table2_variables_empty": empty,
        "table2_n_obs": n_obs,
        "seconds": round(time.time() - started, 2),
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(
        f"demo: {summary['panel_rows']:,d} route-months from "
        f"{sum(rows_by_year.values()):,d} fixture legs in {summary['seconds']} s "
        f"-> {out / 'summary.json'}"
    )
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
