"""Parse the raw monthly CSVs into the canonical staged flight table.

One row per flight leg, one parquet part per year, zstd level 9, tight types.
DuckDB streams each year straight from CSV to parquet, so peak memory stays
bounded and no more than one year is ever in flight — the machine has 16 GB and
the full series is about 1.2 GB of CSV.

Reading the raw files positionally, not by header name, is deliberate. The two
layouts disagree on separator, encoding, column count *and column order*: in
2010-2013 the destination airport sits between the departure and the arrival
timestamps, so a name-blind positional read of the wrong layout would silently
swap fields. `airline_delays.ingest.layout_for` picks the layout and this module maps
positions to meanings.

Cleaning decisions, all counted and reported in ``docs/notes/staging.md``:

* ``DI``: digits become integers; the letters ``A`` and ``B`` become 10 and 11;
  anything else (the stray ``O``) becomes null.
* ``Código Tipo Linha``: ``NA`` and ``N/I`` become null; other values are kept
  uppercase even when they are outside the IAC 1504 list.
* ``Código Justificativa``: ``N/A`` and anything that is not two letters become
  null.
* 2010-2013 carry the justification as free text; `CAUSE_TEXT_TO_CODE` maps it
  back to the IAC 1504 code. The one genuinely ambiguous text, ``AUTORIZADO``,
  is resolved by status: ``XB`` for a cancelled flight, ``OA`` otherwise.
* ``flight_date`` is the date of the scheduled departure, falling back to the
  actual departure when the schedule is missing (frequent for DI 7 and DI 9).
* Timestamps that do not parse become null; the delay built on them is null
  too, never zero.
* ``actual_time_suspect`` (ADR-0015) marks a row whose departure *or* arrival
  delay is a whole calendar day or more in absolute value — a month typo in the
  raw file, not an operation. Written here so that every consumer reads one
  definition instead of recomputing the rule.

**The partition is the flight's own year, not the source file's.** ``flight_date``
comes from the scheduled departure, and a monthly file carries a handful of legs
scheduled just outside its own month: 3,723 rows over the series, most of them
across a 31 December / 1 January boundary, a few outright typos (``2099``,
``2088``). ``airline_delays.fact.build_fact`` therefore selects each calendar year by
its ``year`` column across the whole staged tree rather than trusting the
directory name — reading a partition as if it were a year is what produced the
duplicated route-months of ADR-0016.
"""

from __future__ import annotations

import json
import platform
import subprocess
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from airline_delays.ingest import layout_for, sha256_file
from airline_delays.staging.clean import AMBIGUOUS_CAUSE_TEXTS, CAUSE_TEXT_TO_CODE, normalise_text
from airline_delays.staging.select import build_select

DEFAULT_MEMORY_LIMIT = "8GB"

DEFAULT_THREADS = 8

"""Raw `Situação Voo` to normalised status; everything else becomes ``other``."""

"""ADR-free convention from the brief: the two letter DI codes become 10 and 11."""

"""Raw line-type values that mean "not informed"."""


@dataclass
class YearResult:
    """What staging one year produced."""

    year: int
    rows: int
    files: int
    path: Path
    sha256: str
    bytes: int
    seconds: float
    rows_year_mismatch: int
    rows_no_date: int
    layout: str


def _register_helpers(con: Any) -> None:
    """Register the lookup table the 2010-2013 cause mapping needs."""
    rows = []
    for key, code in CAUSE_TEXT_TO_CODE.items():
        rows.append((key, True, code))
        rows.append((key, False, code))
    for key, (cancelled_code, other_code) in AMBIGUOUS_CAUSE_TEXTS.items():
        rows.append((normalise_text(key), True, cancelled_code))
        rows.append((normalise_text(key), False, other_code))
    con.execute(
        "CREATE OR REPLACE TEMP TABLE cause_text_map (text_key VARCHAR, cancelled BOOLEAN, code VARCHAR)"
    )
    con.executemany("INSERT INTO cause_text_map VALUES (?, ?, ?)", rows)


def _register_groups(con: Any, groups_path: Path | None) -> bool:
    """Register ``data/external/groups.csv`` when it exists. Returns whether it did."""
    if groups_path is None or not Path(groups_path).exists():
        return False
    con.execute(
        "CREATE OR REPLACE TEMP TABLE groups_tbl AS "
        f"SELECT * FROM read_csv('{groups_path}', header=true, auto_detect=true)"
    )
    names = {row[0] for row in con.execute("DESCRIBE groups_tbl").fetchall()}
    required = {"airline", "group", "start", "end", "class"}
    if not required.issubset(names):
        con.execute("DROP TABLE groups_tbl")
        return False
    # `start` and `end` are dated to the month ("2007-03") in ADR-0003's table,
    # but a full date is accepted too. Both collapse to a YYYYMM integer; a
    # TRY_CAST to DATE would silently null every "YYYY-MM" value and turn the
    # interval test into "always true", duplicating every row of an airline
    # that changed group.
    month_key = (
        "CAST(nullif(regexp_replace(substr(trim(CAST({col} AS VARCHAR)), 1, 7), '-', '', 'g'), '') "
        "AS INTEGER)"
    )
    con.execute(
        "CREATE OR REPLACE TEMP TABLE groups_tbl AS SELECT "
        'upper(trim(airline)) AS airline, "group", "class", '
        f"{month_key.format(col='start')} AS start_ym, "
        f"{month_key.format(col=chr(34) + 'end' + chr(34))} AS end_ym FROM groups_tbl"
    )
    overlaps = con.execute(
        "SELECT count(*) FROM groups_tbl a JOIN groups_tbl b "
        "ON a.airline = b.airline AND a.rowid < b.rowid "
        "AND coalesce(a.start_ym, 0) <= coalesce(b.end_ym, 999912) "
        "AND coalesce(b.start_ym, 0) <= coalesce(a.end_ym, 999912)"
    ).fetchone()[0]
    if overlaps:
        raise ValueError(
            f"{groups_path}: {overlaps} overlapping airline intervals; the join "
            "would duplicate flights. Fix the table, do not widen the join."
        )
    return True


def connect(memory_limit: str = DEFAULT_MEMORY_LIMIT, threads: int = DEFAULT_THREADS) -> Any:
    """A DuckDB connection configured for one-year-at-a-time scans."""
    import duckdb

    con = duckdb.connect()
    con.execute(f"SET memory_limit='{memory_limit}'")
    con.execute(f"SET threads={threads}")
    con.execute("SET preserve_insertion_order=false")
    return con


def stage_year(
    year: int,
    raw_dir: Path,
    out_dir: Path,
    groups_path: Path | None = None,
    con: Any = None,
) -> YearResult:
    """Stage one year of raw CSVs into ``out_dir/year=YYYY/part-0.parquet``."""
    import time

    started = time.time()
    raw_dir, out_dir = Path(raw_dir), Path(out_dir)
    year_dir = raw_dir / "vra" / str(year)
    sources = sorted(year_dir.glob("*.csv"))
    if not sources:
        raise FileNotFoundError(f"no raw CSV for {year} under {year_dir}")
    layout = layout_for(year)
    owns_con = con is None
    con = con or connect()
    try:
        _register_helpers(con)
        has_groups = _register_groups(con, groups_path)
        select_sql = build_select(str(year_dir / "*.csv"), layout, with_groups=has_groups)
        target_dir = out_dir / f"year={year}"
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / "part-0.parquet"
        con.execute(
            f"COPY ({select_sql}) TO '{target}' "
            "(FORMAT PARQUET, COMPRESSION zstd, COMPRESSION_LEVEL 9, ROW_GROUP_SIZE 262144)"
        )
        # hive_partitioning=false is load-bearing here: the directory name
        # "year=YYYY" would otherwise add a second `year` column that shadows
        # the one derived from flight_date, and the mismatch count below would
        # be zero by construction.
        stats = con.execute(
            f"SELECT count(*), count(*) FILTER (WHERE year IS DISTINCT FROM {year}), "
            "count(*) FILTER (WHERE flight_date IS NULL) "
            f"FROM read_parquet('{target}', hive_partitioning=false)"
        ).fetchone()
    finally:
        if owns_con:
            con.close()
    return YearResult(
        year=year,
        rows=int(stats[0]),
        files=len(sources),
        path=target,
        sha256=sha256_file(target),
        bytes=target.stat().st_size,
        seconds=time.time() - started,
        rows_year_mismatch=int(stats[1]),
        rows_no_date=int(stats[2]),
        layout=layout.name,
    )


def tool_versions() -> dict[str, str]:
    """Versions of everything that shaped the staged files."""
    import duckdb
    import pyarrow

    return {
        "python": platform.python_version(),
        "duckdb": duckdb.__version__,
        "pyarrow": pyarrow.__version__,
        "platform": f"{platform.system()} {platform.machine()}",
    }


def git_commit(root: Path, *, short: bool = False) -> str:
    """The current commit, or the placeholder the brief asks for when there is none.

    ``short=True`` runs ``git rev-parse --short HEAD`` instead -- what
    `data/analysis/manifest.json` and `panel_manifest.json` embed (ADR-0014),
    against the full hash this module's own staged-layer manifest carries.
    """
    args = ["git", "-C", str(root), "rev-parse", *(["--short"] if short else []), "HEAD"]
    try:
        out = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        pass
    return "UNCOMMITTED"


def stage(
    raw_dir: Path,
    out_dir: Path,
    years: tuple[int, ...] = tuple(range(2000, 2014)),
    groups_path: Path | None = None,
    root: Path | None = None,
) -> list[YearResult]:
    """Stage every year in `years`, one at a time, and write the staged manifest."""
    raw_dir, out_dir = Path(raw_dir), Path(out_dir)
    root = root or raw_dir.parent.parent
    results: list[YearResult] = []
    con = connect()
    try:
        for year in years:
            result = stage_year(year, raw_dir, out_dir, groups_path=groups_path, con=con)
            results.append(result)
            print(
                f"{year}: {result.rows:>9,d} rows from {result.files} files "
                f"({result.layout}) -> {result.bytes / 1e6:6.1f} MB in {result.seconds:5.1f}s",
                file=sys.stderr,
                flush=True,
            )
    finally:
        con.close()
    write_manifest(
        out_dir, results, root=root, groups_applied=bool(groups_path and Path(groups_path).exists())
    )
    return results


def write_manifest(
    out_dir: Path,
    results: list[YearResult],
    root: Path,
    groups_applied: bool = False,
) -> Path:
    """Write ``data/staged/manifest.json``."""
    out_dir = Path(out_dir)
    path = out_dir / "manifest.json"
    document = {
        "layer": "staged",
        "grain": "one row per flight leg",
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "git_commit": git_commit(root),
        "tool_versions": tool_versions(),
        "compression": {"codec": "zstd", "level": 9},
        "groups_applied": groups_applied,
        "total_rows": sum(result.rows for result in results),
        "years": [
            {
                "year": result.year,
                "rows": result.rows,
                "source_files": result.files,
                "raw_layout": result.layout,
                "path": str(result.path.relative_to(out_dir.parent.parent)),
                "bytes": result.bytes,
                "sha256": result.sha256,
                "rows_year_mismatch": result.rows_year_mismatch,
                "rows_without_flight_date": result.rows_no_date,
                "seconds": round(result.seconds, 2),
            }
            for result in sorted(results, key=lambda item: item.year)
        ],
    }
    path.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def read_staged(out_dir: Path, years: tuple[int, ...] | None = None, con: Any = None) -> Any:
    """A DuckDB relation over the staged parquet.

    ``hive_partitioning`` is off on purpose: the directory name ``year=YYYY``
    would otherwise add a second `year` column that collides with the data
    column derived from `flight_date`.
    """
    out_dir = Path(out_dir)
    con = con or connect()
    if years:
        globs = ", ".join(f"'{out_dir}/year={year}/*.parquet'" for year in years)
        source = f"read_parquet([{globs}], hive_partitioning=false)"
    else:
        source = f"read_parquet('{out_dir}/year=*/*.parquet', hive_partitioning=false)"
    return con.sql(f"SELECT * FROM {source}")
