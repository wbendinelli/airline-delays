"""The canonical fact table `group x route x month`, and every other grain from it.

ADR-0004 fixes one fact table and makes every other table a *projection* of it,
because a second hand-built table at a different grain is a second source of
truth — exactly what `registry.py` exists to prevent. So:

* `build_fact` makes one pass per year over `data/staged/`, groups the
  replication universe to ``group x route x month`` and writes
  ``data/analysis/fact_group_route_month.parquet``.
* `aggregate(fact, grain)` projects it onto route-month, city-month (a city
  sees each flight once as a departure and once as an arrival) and
  airline-city-month. `tests/test_features.py` checks additivity: the sums of
  the projection equal the sums computed straight from the flights.

**The fact table is convention-free about missing actual times.** It carries
both the strict observation counts (`arr_delay_obs`: a real timestamp exists)
and the top-up the 2019 vintage implied (`arr_missing_actual`: realised, no
actual time, schedule known). Nothing is imputed here, and no sum changes:
under the vintage's rule those flights contribute exactly 0 minutes. What the
rule changes is the **denominator** of every proportion and mean, and that is
where `legacy_missing_actual_as_zero` acts — in `delay_denominator`, used by
`aggregate` and by `panel` (ADR-0012). `True` reproduces the benchmark; `False`
is the honest small-sample reading of 2000-2009 and what the prediction layer
uses.

Order statistics (median, p90) cannot be summed and are not in the fact table:
`build_fact` computes them straight from the flights at the route-month grain,
under whichever convention the caller declares.

**One calendar year per pass, not one directory per pass** (ADR-0016). The
staged tree is partitioned by the year of the *source file*, and `flight_date`
is the scheduled departure, so a December file carries a few legs scheduled for
1 January and a handful of rows carry an outright typo: 3,723 rows over the
series whose ``year`` differs from the directory they sit in
(`docs/notes/staging.md` section 5). Grouping inside each directory and
concatenating therefore emitted the same ``group x route x month`` cell twice —
844 rows over 422 keys in the first public fact table, and, through the
route-month context join, 866 duplicated rows over 433 keys in the panel. Each
pass now selects ``WHERE year = <target>`` across the whole staged tree (parquet
row-group statistics prune the partitions that cannot hold it), the concatenated
tables are asserted unique on their keys, and rows dated outside the requested
years are counted and reported rather than silently folded into a neighbour.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from airline_delays import paths
from airline_delays import staging as staging_mod
from airline_delays.definitions import carriers as carriers_mod
from airline_delays.definitions import delays as delays_mod
from airline_delays.definitions import universe as universe_mod

if TYPE_CHECKING:  # pragma: no cover - typing only
    import pandas as pd
from airline_delays.fact.measures import (
    CONTEXT_MEASURES,
    FACT_KEYS,
    FACT_SUM_COLUMNS,
    FACT_UNIQUE_KEY,
    HOUR_COLUMNS,
    ROUTE_MONTH_KEY,
    fact_measures,
)


@dataclass
class BuildResult:
    """What one `build_fact` run produced."""

    fact_rows: int
    context_rows: int
    day_hour_rows: int
    seconds: float
    years: tuple[int, ...]
    legacy_missing_actual_as_zero: bool
    missing_actual_by_year: pd.DataFrame
    out_of_window: pd.DataFrame
    """Staged rows dated outside `years`, by year — declared, never absorbed."""


def _select_fact(source: str, threshold: float) -> str:
    measures = fact_measures(threshold)
    projected = ",\n    ".join(f'{sql} AS "{name}"' for name, sql in measures.items())
    label = carriers_mod.label_sql("f.airline", "f.ym", alias="g")
    return f"""
WITH flights AS (
    SELECT * FROM {source}
    WHERE universe_repl AND route IS NOT NULL AND ym IS NOT NULL
),
labelled AS (
    SELECT f.*, {carriers_mod.resolved_group_sql("f.airline")} AS grp,
           {carriers_mod.resolved_class_sql()} AS cls
    FROM flights f {label}
)
SELECT
    ym, year, month, route, origin_node, dest_node,
    grp  AS "group",
    cls  AS "class",
    {projected}
FROM labelled
GROUP BY ym, year, month, route, origin_node, dest_node, grp, cls
"""


def _select_context(source: str, threshold: float, legacy: bool) -> str:
    """Route-month context: off-universe counts and the order statistics.

    Order statistics are the one thing a fact table cannot carry, because a
    median does not add up (ADR-0004). They are computed here, at the
    route-month grain, over the *effective* delay of `delays.effective_delay_sql`
    — so the convention the caller declares is the convention they describe.
    """
    projected = ",\n    ".join(f'{sql} AS "{name}"' for name, sql in CONTEXT_MEASURES.items())
    dep = delays_mod.effective_delay_sql(
        "sched_dep", "actual_dep", legacy_missing_actual_as_zero=legacy
    )
    arr = delays_mod.effective_delay_sql(
        "sched_arr", "actual_arr", legacy_missing_actual_as_zero=legacy
    )
    inside = delays_mod.within_threshold_sql("{delay}", threshold)
    live = f"universe_repl AND is_realized AND {{delay}} IS NOT NULL AND {inside}"
    return f"""
WITH rows_all AS (
    SELECT *, {dep} AS eff_dep, {arr} AS eff_arr
    FROM {source}
    WHERE route IS NOT NULL AND ym IS NOT NULL
)
SELECT
    ym, year, month, route, origin_node, dest_node,
    {projected},
    median(eff_dep) FILTER (WHERE {live.format(delay="eff_dep")})           AS dep_delay_median_min,
    quantile_cont(eff_dep, 0.9) FILTER (WHERE {live.format(delay="eff_dep")}) AS dep_delay_p90_min,
    median(eff_arr) FILTER (WHERE {live.format(delay="eff_arr")})           AS arr_delay_median_min,
    quantile_cont(eff_arr, 0.9) FILTER (WHERE {live.format(delay="eff_arr")}) AS arr_delay_p90_min
FROM rows_all
GROUP BY ym, year, month, route, origin_node, dest_node
"""


def _select_day_hour(source: str) -> str:
    """Node x day x scheduled hour movement counts, both sides of every flight."""
    return f"""
WITH flights AS (
    SELECT origin_node, dest_node, flight_date, ym, year, dep_hour, arr_hour
    FROM {source} WHERE universe_repl AND ym IS NOT NULL AND flight_date IS NOT NULL
),
sides AS (
    SELECT origin_node AS node, flight_date, ym, year, dep_hour AS hour FROM flights
    WHERE origin_node IS NOT NULL AND dep_hour IS NOT NULL
    UNION ALL
    SELECT dest_node AS node, flight_date, ym, year, arr_hour AS hour FROM flights
    WHERE dest_node IS NOT NULL AND arr_hour IS NOT NULL
)
SELECT node, year, ym, flight_date AS day, hour, count(*)::INTEGER AS movements
FROM sides GROUP BY node, year, ym, flight_date, hour
"""


def year_source_sql(staged_dir: Path, year: int) -> str:
    """The staged rows of one **calendar year**, wherever they were partitioned.

    The directory name is the year of the *source file*; `year` is the year of
    `flight_date`. They disagree on 3,723 rows, and reading the directory as if
    it were the year is what produced the duplicated keys of ADR-0016. Parquet
    row-group statistics on `year` prune the partitions that cannot hold the
    target, so the filter costs a metadata read per partition rather than a
    scan.
    """
    tree = f"read_parquet('{staged_dir}/year=*/*.parquet', hive_partitioning=false)"
    return f"(SELECT * FROM {tree} WHERE year = {int(year)})"


def out_of_window_rows(con: Any, staged_dir: Path, years: tuple[int, ...]) -> pd.DataFrame:
    """Staged rows whose `year` is outside `years`, or null, one row per value.

    Declared rather than absorbed: these rows exist, they are not in any
    published table, and the count says how many. The typo years (2020, 2088,
    2099) carry no flight of the replication universe; the boundary year does.
    """
    import pandas as pd

    wanted = ", ".join(str(int(year)) for year in years)
    tree = f"read_parquet('{staged_dir}/year=*/*.parquet', hive_partitioning=false)"
    frame = con.execute(
        f"""
        SELECT year, count(*)::BIGINT AS rows,
               count(*) FILTER (WHERE {universe_mod.UNIVERSE_REPL_SQL}
                                AND route IS NOT NULL AND ym IS NOT NULL)::BIGINT AS universe_rows
        FROM {tree}
        WHERE year IS NULL OR year NOT IN ({wanted})
        GROUP BY year ORDER BY year
        """
    ).df()
    frame["year"] = frame["year"].astype("Int64")
    return pd.DataFrame(frame)


def assert_unique(frame: pd.DataFrame, keys: tuple[str, ...] | list[str], what: str) -> None:
    """ADR-0016: fail loudly when a table is not unique on its declared key.

    An assertion rather than a repair on purpose. A duplicate here always means
    a grain was assembled from parts that did not partition the key, and
    de-duplicating after the fact would hide which part was wrong — the
    route-month medians of the first public panel were each computed over half
    their flights, and summing the copies would not have fixed that.
    """
    keys = list(keys)
    duplicated = frame.duplicated(subset=keys, keep=False)
    count = int(duplicated.sum())
    if not count:
        return
    sample = frame.loc[duplicated, keys].drop_duplicates().head(5).to_dict("records")
    raise ValueError(
        f"{what} is not unique on {keys}: {count} rows over "
        f"{frame.loc[duplicated, keys].drop_duplicates().shape[0]} keys, e.g. {sample}"
    )


def build_fact(
    staged_dir: Path,
    out_dir: Path,
    derived_dir: Path,
    *,
    years: tuple[int, ...] | None = None,
    groups_path: Path | None = None,
    outlier_threshold_min: float = delays_mod.OUTLIER_THRESHOLD_MIN,
    legacy_missing_actual_as_zero: bool = True,
    con: Any = None,
    verbose: bool = True,
) -> BuildResult:
    """One pass per calendar year over the staged flights; writes fact and context.

    Written year by year on purpose (rule 3 of the build brief): the machine has
    16 GB, and a single scan of all fourteen partitions with a wide GROUP BY is
    the one shape that makes it swap. The unit of the pass is the **calendar
    year of the flight**, not the staged directory — see `year_source_sql` and
    ADR-0016.
    """
    import pandas as pd

    started = time.time()
    staged_dir, out_dir, derived_dir = Path(staged_dir), Path(out_dir), Path(derived_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    derived_dir.mkdir(parents=True, exist_ok=True)
    years = years or _staged_years(staged_dir)
    owns_con = con is None
    con = con or staging_mod.connect()
    fact_parts: list[pd.DataFrame] = []
    context_parts: list[pd.DataFrame] = []
    day_hour_parts: list[pd.DataFrame] = []
    missing_rows: list[dict[str, Any]] = []
    try:
        table = carriers_mod.GroupTable.load(groups_path or paths.EXTERNAL / "groups.csv")
        table.register(con)
        for year in years:
            source = year_source_sql(staged_dir, year)
            fact = con.execute(_select_fact(source, outlier_threshold_min)).df()
            context = con.execute(
                _select_context(source, outlier_threshold_min, legacy_missing_actual_as_zero)
            ).df()
            day_hour = con.execute(_select_day_hour(source)).df()
            fact_parts.append(fact)
            context_parts.append(context)
            day_hour_parts.append(day_hour)
            missing_rows.append(_missing_actual_summary(year, fact))
            if verbose:
                print(
                    f"{year}: {len(fact):>7,d} fact cells, {len(context):>7,d} route-months, "
                    f"{len(day_hour):>8,d} node-day-hours  ({time.time() - started:5.1f}s)",
                    flush=True,
                )
        outside = out_of_window_rows(con, staged_dir, tuple(years))
    finally:
        if owns_con:
            con.close()
    fact_all = _finalise_fact(pd.concat(fact_parts, ignore_index=True))
    context_all = pd.concat(context_parts, ignore_index=True)
    day_hour_all = pd.concat(day_hour_parts, ignore_index=True)
    assert_unique(fact_all, FACT_UNIQUE_KEY, "fact_group_route_month")
    assert_unique(context_all, ROUTE_MONTH_KEY, "route_month_context")
    assert_unique(day_hour_all, ("node", "day", "hour"), "node_day_hour")
    write_table(fact_all, out_dir / "fact_group_route_month.parquet")
    write_table(context_all, derived_dir / "route_month_context.parquet")
    write_table(day_hour_all, derived_dir / "node_day_hour.parquet")
    missing = pd.DataFrame(missing_rows)
    result = BuildResult(
        fact_rows=len(fact_all),
        context_rows=len(context_all),
        day_hour_rows=len(day_hour_all),
        seconds=time.time() - started,
        years=tuple(years),
        legacy_missing_actual_as_zero=legacy_missing_actual_as_zero,
        missing_actual_by_year=missing,
        out_of_window=outside,
    )
    _write_manifest(out_dir, result, outlier_threshold_min)
    return result


def out_of_window_records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    """`out_of_window` as JSON-safe records; the null year becomes `None`."""
    import pandas as pd

    if frame.empty:
        return []
    return [
        {
            "year": None if pd.isna(record["year"]) else int(record["year"]),
            "rows": int(record["rows"]),
            "universe_rows": int(record["universe_rows"]),
        }
        for record in frame.to_dict("records")
    ]


def _staged_years(staged_dir: Path) -> tuple[int, ...]:
    found = sorted(
        int(path.name.split("=")[1])
        for path in Path(staged_dir).glob("year=*")
        if path.is_dir() and path.name.split("=")[1].isdigit()
    )
    if not found:
        raise FileNotFoundError(f"no year=YYYY partitions under {staged_dir}")
    return tuple(found)


def _missing_actual_summary(year: int, fact: pd.DataFrame) -> dict[str, Any]:
    """Per-year count of realised flights with no actual time (ADR-0012)."""
    realized = int(fact["realized"].sum())
    dep_missing = int(fact["dep_missing_actual"].sum())
    arr_missing = int(fact["arr_missing_actual"].sum())
    return {
        "year": year,
        "realized": realized,
        "dep_missing_actual": dep_missing,
        "arr_missing_actual": arr_missing,
        "sh_dep_missing": dep_missing / realized if realized else None,
        "sh_arr_missing": arr_missing / realized if realized else None,
    }


def _finalise_fact(fact: pd.DataFrame) -> pd.DataFrame:
    """Tight types, entry/exit flags, stable ordering."""
    for name in FACT_SUM_COLUMNS:
        if name.startswith("sum_"):
            fact[name] = fact[name].astype("float64").fillna(0.0)
        else:
            fact[name] = fact[name].fillna(0).astype("int32")
    fact["n_flight_numbers"] = fact["n_flight_numbers"].fillna(0).astype("int32")
    fact["year"] = fact["year"].astype("int16")
    fact["month"] = fact["month"].astype("int8")
    fact["ym"] = fact["ym"].astype("int32")
    fact = fact.sort_values(["route", "group", "ym"], ignore_index=True)
    keyed = fact.groupby(["route", "group"], observed=True)["ym"]
    previous, following = keyed.shift(1), keyed.shift(-1)
    # "Entry" is a gap in the calendar, not just a missing neighbouring row: a
    # group that skipped a month and came back entered twice, and a table that
    # merely compared adjacent rows would count that as continuous operation.
    fact["is_entry"] = (
        (previous.isna() | (previous != _previous_ym(fact["ym"]))).to_numpy().astype("int8")
    )
    fact["is_exit"] = (
        (following.isna() | (following != _next_ym(fact["ym"]))).to_numpy().astype("int8")
    )
    ordered = [*FACT_KEYS, *fact_measures().keys(), "is_entry", "is_exit"]
    return fact[ordered].sort_values(["ym", "route", "group"], ignore_index=True)


def _previous_ym(ym: pd.Series) -> pd.Series:
    """The `YYYYMM` key of the month before, in integer arithmetic."""
    import numpy as np

    return ym - np.where(ym % 100 == 1, 89, 1)


def _next_ym(ym: pd.Series) -> pd.Series:
    """The `YYYYMM` key of the month after."""
    import numpy as np

    return ym + np.where(ym % 100 == 12, 89, 1)


def slim(frame: pd.DataFrame, *, drop_hours: bool = True, round_floats: int = 3) -> pd.DataFrame:
    """Shrink a table for publication: drop the hourly detail, round the floats.

    The 24 hourly counts are the raw material of `peak_hour_share`, `hhi_hours`
    and `sh_night`, all three of which the caller has already computed; keeping
    them in a projection duplicates the fact table, which is where they belong.
    Three decimals is far below what a monthly aggregate of a minute-resolution
    source can mean, and the noise below it is a third of the compressed file.
    """
    out = frame.drop(columns=[name for name in HOUR_COLUMNS if name in frame.columns])
    if drop_hours is False:
        out = frame.copy()
    floats = [name for name, dtype in out.dtypes.items() if str(dtype).startswith("float")]
    out[floats] = out[floats].round(round_floats).astype("float32")
    return out


def write_table(frame: pd.DataFrame, path: Path) -> Path:
    """Parquet, zstd 9, tight types — the storage rule of ADR-0004."""
    import pyarrow as pa
    import pyarrow.parquet as pq

    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(
        pa.Table.from_pandas(frame, preserve_index=False),
        path,
        compression="zstd",
        compression_level=9,
    )
    return path


def _write_manifest(out_dir: Path, result: BuildResult, threshold: float) -> Path:
    path = out_dir / "manifest.json"
    repo_root = paths.REPO_ROOT
    document = {
        "layer": "analysis",
        "grain": "one row per group x route x month, replication universe",
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "git_commit": staging_mod.git_commit(repo_root, short=True),
        "tool_versions": staging_mod.tool_versions(),
        "outlier_threshold_min": threshold,
        "legacy_missing_actual_as_zero": result.legacy_missing_actual_as_zero,
        "years": list(result.years),
        "fact_rows": result.fact_rows,
        "route_months": result.context_rows,
        "node_day_hours": result.day_hour_rows,
        "seconds": round(result.seconds, 2),
        "missing_actual_by_year": result.missing_actual_by_year.to_dict("records"),
        "rows_outside_years": out_of_window_records(result.out_of_window),
    }
    path.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path
