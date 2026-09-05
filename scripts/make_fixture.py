#!/usr/bin/env python
"""Build the test fixtures from real data.

Three files, all small enough to live in git and all cut from the real series
so that the tests exercise the actual quirks rather than an invented file:

``tests/fixtures/vra_raw_sample_2002.csv``
    Up to 3,000 rows of the legacy 12-column layout (comma, latin-1), header
    included, bytes copied verbatim so the encoding and the CRLF endings
    survive.

``tests/fixtures/vra_raw_sample_2012.csv``
    The same for the 20-column layout (semicolon, UTF-8).

``tests/fixtures/vra_sample.parquet``
    Staged rows for the routes SBAR-SBBR, MRSP-MRRJ and SBCT-MRSP in 2004,
    2009 and 2012, capped at about 30,000 rows. Three years on purpose: 2004
    and 2009 come from the legacy layout, 2012 from the wide one, so a test can
    compare the two.

The raw samples are stratified across the month: rows are taken every k-th line
rather than from the top, so a sample is not one single day.

Usage:
    uv run python scripts/make_fixture.py [--out-dir tests/fixtures]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from vra.io import layout_for
from vra.stage import connect

ROOT = Path(__file__).resolve().parents[1]

FIXTURE_ROUTES = ("SBAR-SBBR", "MRSP-MRRJ", "SBCT-MRSP")
FIXTURE_YEARS = (2004, 2009, 2012)
FIXTURE_ROW_CAP = 30_000

RAW_SAMPLES = {
    2002: "VRA_20026.csv",
    2012: "VRA_2012_06.csv",
}


def sample_raw(source: Path, target: Path, max_rows: int) -> int:
    """Copy the header plus a stratified sample of at most `max_rows` data lines.

    Works on bytes, so latin-1 files stay latin-1 and CRLF endings survive.
    """
    layout = layout_for(int(source.parent.name))
    with source.open("rb") as handle:
        lines = handle.readlines()
    header, body = lines[0], lines[1:]
    step = max(1, len(body) // max_rows)
    kept = body[::step][:max_rows]
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("wb") as handle:
        handle.write(header)
        handle.writelines(kept)
    print(
        f"{target.name}: {len(kept):,d} of {len(body):,d} rows (every {step}th), "
        f"{layout.name}, {target.stat().st_size / 1024:.0f} KiB"
    )
    return len(kept)


def sample_staged(staged_dir: Path, target: Path) -> int:
    """Write the staged fixture: three routes, three years, capped rows.

    Stratified by (year, route): each of the nine cells contributes at most
    ``FIXTURE_ROW_CAP / 9`` rows, taken at a fixed stride through the cell
    ordered by scheduled departure. A plain ``LIMIT`` would have filled the
    whole cap with the first year and left 2012 — the only wide-layout year —
    out of the fixture entirely.
    """
    per_cell = FIXTURE_ROW_CAP // (len(FIXTURE_YEARS) * len(FIXTURE_ROUTES))
    con = connect(memory_limit="4GB", threads=4)
    try:
        globs = ", ".join(f"'{staged_dir}/year={year}/*.parquet'" for year in FIXTURE_YEARS)
        routes = ", ".join(f"'{route}'" for route in FIXTURE_ROUTES)
        target.parent.mkdir(parents=True, exist_ok=True)
        con.execute(
            f"""COPY (
            WITH picked AS (
                SELECT * FROM read_parquet([{globs}], hive_partitioning=false)
                WHERE route IN ({routes})
            ),
            numbered AS (
                SELECT *,
                    row_number() OVER (
                        PARTITION BY year, route
                        ORDER BY sched_dep, airline, flight_number, origin_icao, dest_icao
                    ) - 1 AS rn,
                    count(*) OVER (PARTITION BY year, route) AS cell_rows
                FROM picked
            )
            SELECT * EXCLUDE (rn, cell_rows) FROM numbered
            WHERE rn % greatest(1, CAST(ceil(cell_rows / {per_cell}.0) AS BIGINT)) = 0
            ORDER BY year, month, route, sched_dep, airline, flight_number
            ) TO '{target}' (FORMAT PARQUET, COMPRESSION zstd, COMPRESSION_LEVEL 9)"""
        )
        rows = con.execute(f"SELECT count(*) FROM read_parquet('{target}')").fetchone()[0]
        breakdown = con.execute(
            f"SELECT year, route, count(*) FROM read_parquet('{target}') GROUP BY 1, 2 ORDER BY 1, 2"
        ).fetchall()
    finally:
        con.close()
    print(f"{target.name}: {rows:,d} rows, {target.stat().st_size / 1024:.0f} KiB")
    for year, route, count in breakdown:
        print(f"    {year} {route}: {count:,d}")
    return int(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "tests" / "fixtures")
    parser.add_argument("--raw-dir", type=Path, default=ROOT / "data" / "raw")
    parser.add_argument("--staged-dir", type=Path, default=ROOT / "data" / "staged")
    parser.add_argument("--max-rows", type=int, default=3000)
    args = parser.parse_args(argv)

    for year, name in RAW_SAMPLES.items():
        source = args.raw_dir / "vra" / str(year) / name
        if not source.exists():
            print(f"missing raw file {source}; run `vra fetch` first", file=sys.stderr)
            return 1
        sample_raw(source, args.out_dir / f"vra_raw_sample_{year}.csv", args.max_rows)

    if not (args.staged_dir / f"year={FIXTURE_YEARS[0]}").exists():
        print(
            f"missing staged data under {args.staged_dir}; run `vra stage` first", file=sys.stderr
        )
        return 1
    sample_staged(args.staged_dir, args.out_dir / "vra_sample.parquet")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
