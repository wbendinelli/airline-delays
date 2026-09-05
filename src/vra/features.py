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
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

from vra import codes as codes_mod
from vra import congestion as congestion_mod
from vra import delays as delays_mod
from vra import groups as groups_mod
from vra import hhi as hhi_mod
from vra import hub as hub_mod
from vra import stage as stage_mod
from vra import universe as universe_mod

if TYPE_CHECKING:  # pragma: no cover - typing only
    import pandas as pd

Grain = Literal["route_month", "city_month", "airline_city_month"]

FACT_KEYS: tuple[str, ...] = (
    "ym",
    "year",
    "month",
    "route",
    "origin_node",
    "dest_node",
    "group",
    "class",
)

HOURS: tuple[int, ...] = tuple(range(24))
HOUR_COLUMNS: tuple[str, ...] = tuple(f"sched_dep_h{hour:02d}" for hour in HOURS)

NIGHT_HOURS: frozenset[int] = frozenset({22, 23, 0, 1, 2, 3, 4, 5})
"""Hours counted as night departures, matching the reconstruction's `sh_noite`."""

CANCEL_CAUSES: dict[str, tuple[str, ...]] = {
    "cancel_technical": ("XN",),
    "cancel_weather": ("XO", "XT", "XS", "XI", "XJ", "XM"),
    "cancel_authorised": ("XA", "XB"),
}
"""Cancellation-reason groupings kept from the reconstruction's `canc_*` shares."""


def _delay_measures(side: str, threshold: float) -> dict[str, str]:
    """The delay aggregates for one side, ``dep`` or ``arr``.

    Every one is restricted to realised flights: a cancelled flight has no
    delay, and counting it as on time would be an imputation.
    """
    delay = f"{side}_delay_min"
    actual = f"actual_{'dep' if side == 'dep' else 'arr'}"
    scheduled = f"sched_{'dep' if side == 'dep' else 'arr'}"
    live = f"is_realized AND {delay} IS NOT NULL"
    trimmed = f"{live} AND {delay} < {threshold}"
    out = {
        f"{side}_delay_obs": f"count(*) FILTER (WHERE {live})",
        f"{side}_missing_actual": (
            f"count(*) FILTER (WHERE is_realized AND {actual} IS NULL AND {scheduled} IS NOT NULL)"
        ),
        f"{side}_delayed_gt0": f"count(*) FILTER (WHERE {live} AND {delay} > 0)",
        f"{side}_delayed_gt15": f"count(*) FILTER (WHERE {live} AND {delay} > 15)",
        f"{side}_delayed_gt30": f"count(*) FILTER (WHERE {live} AND {delay} > 30)",
        f"{side}_delayed_gt60": f"count(*) FILTER (WHERE {live} AND {delay} > 60)",
        f"{side}_early": f"count(*) FILTER (WHERE {live} AND {delay} < 0)",
        f"{side}_outliers": f"count(*) FILTER (WHERE {live} AND {delay} >= {threshold})",
        f"sum_{side}_delay_min": f"sum({delay}) FILTER (WHERE {trimmed})",
        f"sum_{side}_delay_pos_min": f"sum(greatest({delay}, 0)) FILTER (WHERE {trimmed})",
        f"sum_{side}_delay_p15_min": (
            f"sum(CASE WHEN {delay} > 15 THEN {delay} ELSE 0 END) FILTER (WHERE {trimmed})"
        ),
    }
    if side == "arr":
        out["arr_delayed_1530"] = (
            f"count(*) FILTER (WHERE {live} AND {delay} > 15 AND {delay} <= 30)"
        )
    return out


def fact_measures(threshold: float = delays_mod.OUTLIER_THRESHOLD_MIN) -> dict[str, str]:
    """Every measure of the fact table, as ``name -> DuckDB aggregate``.

    One dictionary drives the SQL, the parquet schema and the additivity test,
    so a new measure cannot exist in one of the three and not the others.
    """
    measures: dict[str, str] = {
        "flights": "count(*)",
        "realized": "count(*) FILTER (WHERE is_realized)",
        "cancelled": f"count(*) FILTER (WHERE status = '{universe_mod.STATUS_CANCELLED}')",
        "n_flight_numbers": "count(DISTINCT flight_number)",
    }
    measures.update(_delay_measures("dep", threshold))
    measures.update(_delay_measures("arr", threshold))
    both = "is_realized AND dep_delay_min IS NOT NULL AND arr_delay_min IS NOT NULL"
    measures.update(
        {
            "recovery_obs": f"count(*) FILTER (WHERE {both})",
            "sum_recovery_min": f"sum(arr_delay_min - dep_delay_min) FILTER (WHERE {both})",
            "recovered_gt15": (
                f"count(*) FILTER (WHERE {both} AND dep_delay_min > 15 AND arr_delay_min <= 15)"
            ),
            "sched_block_obs": "count(*) FILTER (WHERE sched_block_min IS NOT NULL)",
            "sum_sched_block_min": "sum(sched_block_min::DOUBLE)",
            "sum_sched_block_sq": "sum(sched_block_min::DOUBLE * sched_block_min::DOUBLE)",
            "actual_block_obs": "count(*) FILTER (WHERE actual_block_min IS NOT NULL)",
            "sum_actual_block_min": "sum(actual_block_min::DOUBLE)",
            "padding_obs": (
                "count(*) FILTER (WHERE is_realized AND sched_block_min IS NOT NULL "
                "AND actual_block_min IS NOT NULL)"
            ),
            "sum_padding_min": (
                "sum(sched_block_min::DOUBLE - actual_block_min::DOUBLE) FILTER "
                "(WHERE is_realized AND sched_block_min IS NOT NULL "
                "AND actual_block_min IS NOT NULL)"
            ),
            "weekend_flights": "count(*) FILTER (WHERE dow >= 5)",
            "night_flights": (
                "count(*) FILTER (WHERE dep_hour IN ("
                + ", ".join(str(hour) for hour in sorted(NIGHT_HOURS))
                + "))"
            ),
            "cause_none": "count(*) FILTER (WHERE cause_code IS NULL)",
        }
    )
    for category in codes_mod.CATEGORY_NAMES:
        measures[f"cause_{category}"] = (
            f"count(*) FILTER (WHERE {codes_mod.category_sql('cause_code', category)})"
        )
    for set_name in codes_mod.ARTICLE_SETS:
        measures[f"cause_set_{set_name}"] = (
            f"count(*) FILTER (WHERE {codes_mod.article_set_sql('cause_code', set_name)})"
        )
    for name, cancel_codes in CANCEL_CAUSES.items():
        measures[name] = (
            f"count(*) FILTER (WHERE status = '{universe_mod.STATUS_CANCELLED}' "
            f"AND {codes_mod.in_sql('cause_code', cancel_codes)})"
        )
    for hour in HOURS:
        measures[f"sched_dep_h{hour:02d}"] = f"count(*) FILTER (WHERE dep_hour = {hour})"
    return measures


FACT_SUM_COLUMNS: tuple[str, ...] = tuple(
    name for name in fact_measures() if name != "n_flight_numbers"
)
"""Fact measures that are additive across rows; everything else is recomputed."""

CONTEXT_MEASURES: dict[str, str] = {
    "n_rows_all": "count(*)",
    "n_extra": "count(*) FILTER (WHERE di IN (1, 2))",
    "n_return": "count(*) FILTER (WHERE di = 3)",
    "n_intl_leg": "count(*) FILTER (WHERE line_type = 'I')",
    "n_cargo": "count(*) FILTER (WHERE line_type IN ('C', 'G'))",
    "n_postal": "count(*) FILTER (WHERE line_type = 'L')",
    "n_off_universe": f"count(*) FILTER (WHERE NOT {universe_mod.UNIVERSE_REPL_SQL})",
}
"""Route-month counts over **all** staged rows, not only the universe.

The universe is a filter, not a fact about the world: extras, return legs,
international legs and cargo are excluded from the replication (ADR-0002) but
they occupy the same runway in the same hour, so they belong in the panel as
context columns. They are the only measures in this module computed outside
`universe_repl`, and their names carry no universe suffix for that reason.
"""


# --------------------------------------------------------------------------- build


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


def _select_fact(source: str, threshold: float) -> str:
    measures = fact_measures(threshold)
    projected = ",\n    ".join(f'{sql} AS "{name}"' for name, sql in measures.items())
    label = groups_mod.label_sql("f.airline", "f.ym", alias="g")
    return f"""
WITH flights AS (
    SELECT * FROM {source}
    WHERE universe_repl AND route IS NOT NULL AND ym IS NOT NULL
),
labelled AS (
    SELECT f.*, {groups_mod.resolved_group_sql("f.airline")} AS grp,
           {groups_mod.resolved_class_sql()} AS cls
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
    live = f"universe_repl AND is_realized AND {{delay}} IS NOT NULL AND {{delay}} < {threshold}"
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
    """One pass per year over the staged flights; writes the fact and its context.

    Written year by year on purpose (rule 3 of the build brief): the machine has
    16 GB, and a single scan of all fourteen partitions with a wide GROUP BY is
    the one shape that makes it swap.
    """
    import pandas as pd

    started = time.time()
    staged_dir, out_dir, derived_dir = Path(staged_dir), Path(out_dir), Path(derived_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    derived_dir.mkdir(parents=True, exist_ok=True)
    years = years or _staged_years(staged_dir)
    owns_con = con is None
    con = con or stage_mod.connect()
    fact_parts: list[pd.DataFrame] = []
    context_parts: list[pd.DataFrame] = []
    day_hour_parts: list[pd.DataFrame] = []
    missing_rows: list[dict[str, Any]] = []
    try:
        table = groups_mod.GroupTable.load(
            groups_path or Path(__file__).resolve().parents[2] / "data/external/groups.csv"
        )
        table.register(con)
        for year in years:
            source = f"read_parquet('{staged_dir}/year={year}/*.parquet', hive_partitioning=false)"
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
    finally:
        if owns_con:
            con.close()
    fact_all = _finalise_fact(pd.concat(fact_parts, ignore_index=True))
    context_all = pd.concat(context_parts, ignore_index=True)
    day_hour_all = pd.concat(day_hour_parts, ignore_index=True)
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
    )
    _write_manifest(out_dir, result, outlier_threshold_min)
    return result


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
    repo_root = Path(__file__).resolve().parents[2]
    document = {
        "layer": "analysis",
        "grain": "one row per group x route x month, replication universe",
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "git_commit": stage_mod.git_commit(repo_root, short=True),
        "tool_versions": stage_mod.tool_versions(),
        "outlier_threshold_min": threshold,
        "legacy_missing_actual_as_zero": result.legacy_missing_actual_as_zero,
        "years": list(result.years),
        "fact_rows": result.fact_rows,
        "route_months": result.context_rows,
        "node_day_hours": result.day_hour_rows,
        "seconds": round(result.seconds, 2),
        "missing_actual_by_year": result.missing_actual_by_year.to_dict("records"),
    }
    path.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


# ----------------------------------------------------------------------- denominators


def delay_denominator(
    frame: pd.DataFrame, side: str, *, legacy_missing_actual_as_zero: bool
) -> pd.Series:
    """Flights a delay proportion is divided by, under one of the two conventions.

    This one function is where ADR-0012 bites. Under the 2019 vintage's rule an
    empty actual time means "on schedule", so the flight belongs in the
    denominator and not in the numerator; under this repository's own rule it is
    an absence and belongs in neither. In 2000-2009 that is the difference
    between a denominator of every realised flight and a denominator of the
    45-20% of them that had an occurrence — which is why the strict reading
    reports arrival-delay rates far above the published ones.
    """
    observed = frame[f"{side}_delay_obs"].astype("float64")
    if not legacy_missing_actual_as_zero:
        return observed
    return observed + frame[f"{side}_missing_actual"].astype("float64")


def _ratio(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    return numerator.astype("float64") / denominator.astype("float64").where(denominator > 0)


# ------------------------------------------------------------------------ aggregate

_DEP_SIDE: tuple[str, ...] = (
    "flights",
    "realized",
    "cancelled",
    "dep_delay_obs",
    "dep_missing_actual",
    "dep_delayed_gt0",
    "dep_delayed_gt15",
    "dep_delayed_gt30",
    "dep_delayed_gt60",
    "dep_early",
    "dep_outliers",
    "sum_dep_delay_min",
    "sum_dep_delay_pos_min",
    "sum_dep_delay_p15_min",
    "night_flights",
    "weekend_flights",
    *HOUR_COLUMNS,
)
_ARR_SIDE: tuple[str, ...] = (
    "arr_delay_obs",
    "arr_missing_actual",
    "arr_delayed_gt0",
    "arr_delayed_gt15",
    "arr_delayed_1530",
    "arr_delayed_gt30",
    "arr_delayed_gt60",
    "arr_early",
    "arr_outliers",
    "sum_arr_delay_min",
    "sum_arr_delay_pos_min",
    "sum_arr_delay_p15_min",
)
_BOTH_SIDES: tuple[str, ...] = (
    "cause_none",
    *(f"cause_{category}" for category in codes_mod.CATEGORY_NAMES),
    *(f"cause_set_{name}" for name in codes_mod.ARTICLE_SETS),
    *CANCEL_CAUSES,
)


def aggregate(
    fact: pd.DataFrame,
    grain: Grain,
    *,
    legacy_missing_actual_as_zero: bool = True,
) -> pd.DataFrame:
    """Project the fact table onto a coarser grain.

    Additive measures are summed; proportions, shares and concentration indices
    are **recomputed** from the sums at the target grain, never averaged
    (ADR-0004). `n_flight_numbers` is dropped at every grain but the fact's own,
    because two groups can reuse a number and a distinct count does not add.
    """
    if grain == "route_month":
        return _aggregate_route_month(
            fact, legacy_missing_actual_as_zero=legacy_missing_actual_as_zero
        )
    if grain in {"city_month", "airline_city_month"}:
        return _aggregate_city(
            fact,
            with_group=(grain == "airline_city_month"),
            legacy_missing_actual_as_zero=legacy_missing_actual_as_zero,
        )
    raise ValueError(f"unknown grain {grain!r}; expected one of {Grain.__args__}")  # type: ignore[attr-defined]


def _aggregate_route_month(
    fact: pd.DataFrame, *, legacy_missing_actual_as_zero: bool
) -> pd.DataFrame:
    import pandas as pd

    keys = ["ym", "year", "month", "route", "origin_node", "dest_node"]
    sums = fact.groupby(keys, observed=True, as_index=False)[list(FACT_SUM_COLUMNS)].sum()
    structure = _market_structure(fact, keys)
    out = sums.merge(structure, on=keys, how="left")
    return pd.DataFrame(
        _add_shares(out, legacy_missing_actual_as_zero=legacy_missing_actual_as_zero)
    )


def _market_structure(fact: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    """Competitor count, flight-share HHI, leader share and class shares."""
    import pandas as pd

    active = fact[fact["flights"] > 0]
    grouped = active.groupby(keys, observed=True)
    out = grouped.agg(
        n_groups=("group", "nunique"),
        hhi_flights=("flights", lambda s: hhi_mod.hhi_from_counts(s)),
        sh_leader=("flights", lambda s: hhi_mod.leader_share(s)),
        n_entries=("is_entry", "sum"),
        n_exits=("is_exit", "sum"),
    ).reset_index()
    by_class = (
        active.groupby([*keys, "class"], observed=True)["flights"].sum().unstack(fill_value=0)
    )
    totals = by_class.sum(axis=1)
    for klass in groups_mod.CLASSES:
        column = by_class.get(klass, 0)
        out[f"sh_flights_{klass.lower()}"] = (
            (column / totals.where(totals > 0)).reindex(_index_of(out, keys)).to_numpy()
        )
    lcc_entry = active[active["group"].isin(groups_mod.BENCHMARK_LCC_GROUPS)]
    entry = lcc_entry.groupby(keys, observed=True)["is_entry"].max().rename("entry_lcc")
    out = out.merge(entry.reset_index(), on=keys, how="left")
    out["entry_lcc"] = out["entry_lcc"].fillna(0).astype("int8")
    return pd.DataFrame(out)


def _index_of(frame: pd.DataFrame, keys: list[str]):
    import pandas as pd

    return pd.MultiIndex.from_frame(frame[keys]) if len(keys) > 1 else frame[keys[0]]


def _aggregate_city(
    fact: pd.DataFrame, *, with_group: bool, legacy_missing_actual_as_zero: bool
) -> pd.DataFrame:
    import pandas as pd

    extra = ["group", "class"] if with_group else []
    keys = ["ym", "year", "month", "node", *extra]
    departures = fact.rename(columns={"origin_node": "node"})
    arrivals = fact.rename(columns={"dest_node": "node"})
    dep = departures.groupby(keys, observed=True, as_index=False)[[*_DEP_SIDE, *_BOTH_SIDES]].sum()
    arr = arrivals.groupby(keys, observed=True, as_index=False)[
        ["flights", "realized", "cancelled", *_ARR_SIDE, *_BOTH_SIDES]
    ].sum()
    arr = arr.rename(
        columns={
            "flights": "arr_flights",
            "realized": "arr_realized",
            "cancelled": "arr_cancelled",
            **{name: f"_arr_{name}" for name in _BOTH_SIDES},
        }
    )
    dep = dep.rename(
        columns={"flights": "dep_flights", "realized": "dep_realized", "cancelled": "dep_cancelled"}
    )
    out = dep.merge(arr, on=keys, how="outer")
    counts = [
        name
        for name in out.columns
        if name not in keys and not name.startswith(("sh_", "hhi_", "n_groups"))
    ]
    out[counts] = out[counts].fillna(0)
    for name in _BOTH_SIDES:
        out[name] = out[name] + out.pop(f"_arr_{name}")
    out["movements"] = out["dep_flights"] + out["arr_flights"]
    out["movements_realized"] = out["dep_realized"] + out["arr_realized"]
    out["movements_cancelled"] = out["dep_cancelled"] + out["arr_cancelled"]
    if not with_group:
        structure = _city_structure(fact)
        out = out.merge(structure, on=["ym", "node"], how="left")
    out = _add_city_shares(out, legacy_missing_actual_as_zero=legacy_missing_actual_as_zero)
    return pd.DataFrame(out.sort_values(keys, ignore_index=True))


def _city_structure(fact: pd.DataFrame) -> pd.DataFrame:
    """Competitor structure of a city's movements, both sides counted."""
    import pandas as pd

    departures = fact.rename(columns={"origin_node": "node"})[["ym", "node", "group", "flights"]]
    arrivals = fact.rename(columns={"dest_node": "node"})[["ym", "node", "group", "flights"]]
    both = pd.concat([departures, arrivals], ignore_index=True)
    per_group = both.groupby(["ym", "node", "group"], observed=True, as_index=False)[
        "flights"
    ].sum()
    per_group = per_group[per_group["flights"] > 0]
    grouped = per_group.groupby(["ym", "node"], observed=True)
    return grouped.agg(
        n_groups=("group", "nunique"),
        hhi_flights=("flights", lambda s: hhi_mod.hhi_from_counts(s)),
        sh_leader=("flights", lambda s: hhi_mod.leader_share(s)),
    ).reset_index()


def _add_shares(out: pd.DataFrame, *, legacy_missing_actual_as_zero: bool) -> pd.DataFrame:
    """Route-month proportions and means, recomputed from the sums.

    Built into a dictionary and attached in one `concat` rather than eighty
    assignments: pandas copies the block manager on every insert past a hundred
    columns, and this function alone would otherwise dominate the build.
    """
    import pandas as pd

    flights = out["flights"]
    new: dict[str, pd.Series] = {"sh_cancel": _ratio(out["cancelled"], flights)}
    for side in ("dep", "arr"):
        denominator = delay_denominator(
            out, side, legacy_missing_actual_as_zero=legacy_missing_actual_as_zero
        )
        new[f"{side}_delay_denominator"] = denominator
        for cut in ("gt0", "gt15", "gt30", "gt60"):
            new[f"sh_{side}_{cut}"] = _ratio(out[f"{side}_delayed_{cut}"], denominator)
        new[f"sh_{side}_early"] = _ratio(out[f"{side}_early"], denominator)
        trimmed = denominator - out[f"{side}_outliers"]
        new[f"{side}_delay_mean_min"] = _ratio(out[f"sum_{side}_delay_min"], trimmed)
        new[f"{side}_delay_mean_pos_min"] = _ratio(out[f"sum_{side}_delay_pos_min"], trimmed)
    new["sh_arr_1530"] = _ratio(out["arr_delayed_1530"], new["arr_delay_denominator"])
    new["sched_block_mean_min"] = _ratio(out["sum_sched_block_min"], out["sched_block_obs"])
    new["sched_block_sd_min"] = _standard_deviation(
        out["sum_sched_block_min"], out["sum_sched_block_sq"], out["sched_block_obs"]
    )
    new["padding_mean_min"] = _ratio(out["sum_padding_min"], out["padding_obs"])
    new["recovery_mean_min"] = _ratio(out["sum_recovery_min"], out["recovery_obs"])
    new["sh_recovered"] = _ratio(out["recovered_gt15"], out["recovery_obs"])
    new["sh_night"] = _ratio(out["night_flights"], flights)
    new["sh_weekend"] = _ratio(out["weekend_flights"], flights)
    hourly = out[list(HOUR_COLUMNS)]
    hour_total = hourly.sum(axis=1)
    new["peak_hour_share"] = _ratio(hourly.max(axis=1), hour_total)
    squares = (hourly.astype("float64") ** 2).sum(axis=1)
    new["hhi_hours"] = squares / (hour_total.astype("float64") ** 2).where(hour_total > 0)
    for name in (*(f"cause_{c}" for c in codes_mod.CATEGORY_NAMES), "cause_none"):
        new[f"sh_{name}"] = _ratio(out[name], flights)
    for set_name in codes_mod.ARTICLE_SETS:
        new[set_name] = _ratio(out[f"cause_set_{set_name}"], flights)
    for name in CANCEL_CAUSES:
        new[f"sh_{name}"] = _ratio(out[name], out["cancelled"])
    return pd.concat([out, pd.DataFrame(new, index=out.index)], axis=1)


def _add_city_shares(out: pd.DataFrame, *, legacy_missing_actual_as_zero: bool) -> pd.DataFrame:
    """City-month proportions: departures against departures, arrivals against arrivals."""
    import pandas as pd

    new: dict[str, pd.Series] = {"sh_cancel": _ratio(out["movements_cancelled"], out["movements"])}
    for side in ("dep", "arr"):
        denominator = delay_denominator(
            out, side, legacy_missing_actual_as_zero=legacy_missing_actual_as_zero
        )
        new[f"{side}_delay_denominator"] = denominator
        for cut in ("gt0", "gt15", "gt30"):
            new[f"sh_{side}_{cut}"] = _ratio(out[f"{side}_delayed_{cut}"], denominator)
        trimmed = denominator - out[f"{side}_outliers"]
        new[f"{side}_delay_mean_min"] = _ratio(out[f"sum_{side}_delay_min"], trimmed)
    for name in (*(f"cause_{c}" for c in codes_mod.CATEGORY_NAMES), "cause_none"):
        new[f"sh_{name}"] = _ratio(out[name], out["movements"])
    for set_name in codes_mod.ARTICLE_SETS:
        new[set_name] = _ratio(out[f"cause_set_{set_name}"], out["movements"])
    hourly = out[list(HOUR_COLUMNS)]
    hour_total = hourly.sum(axis=1)
    new["peak_hour_share"] = _ratio(hourly.max(axis=1), hour_total)
    squares = (hourly.astype("float64") ** 2).sum(axis=1)
    new["hhi_hours"] = squares / (hour_total.astype("float64") ** 2).where(hour_total > 0)
    return pd.concat([out, pd.DataFrame(new, index=out.index)], axis=1)


def _standard_deviation(total: pd.Series, squares: pd.Series, n: pd.Series) -> pd.Series:
    """Sample standard deviation from the two sums the fact table carries."""
    import numpy as np

    count = n.astype("float64")
    mean = total.astype("float64") / count.where(count > 0)
    variance = (squares.astype("float64") - count * mean * mean) / (count - 1).where(count > 1)
    return np.sqrt(variance.clip(lower=0))


# ------------------------------------------------------------------- city extensions


def add_congestion(city_month: pd.DataFrame, day_hour: pd.DataFrame) -> pd.DataFrame:
    """Attach the ADR-0007 p90 proxy to a city-month table."""
    congestion = congestion_mod.monthly_congestion(day_hour).drop(columns=["movements"])
    return city_month.merge(congestion, on=["node", "ym"], how="left")


def add_hub(airline_city_month: pd.DataFrame) -> pd.DataFrame:
    """Attach the hub share, score and dummy to an airline-city-month table."""
    import pandas as pd

    frame = airline_city_month.copy()
    city_totals = frame.groupby(["ym", "node"], observed=True)["movements"].sum().rename("_city")
    group_totals = frame.groupby(["ym", "group"], observed=True)["movements"].sum().rename("_group")
    system = frame.groupby("ym", observed=True)["movements"].sum().rename("_system")
    frame = frame.merge(city_totals.reset_index(), on=["ym", "node"], how="left")
    frame = frame.merge(group_totals.reset_index(), on=["ym", "group"], how="left")
    frame = frame.merge(system.reset_index(), on="ym", how="left")
    frame["city_share"] = _ratio(frame["movements"], frame["_city"])
    frame["hub_score"] = frame["city_share"] / _ratio(frame["_group"], frame["_system"]).where(
        frame["_group"] > 0
    )
    frame["is_hub"] = (
        (frame["_city"] >= hub_mod.MIN_CITY_MOVEMENTS)
        & (frame["movements"] >= hub_mod.MIN_GROUP_MOVEMENTS)
        & (frame["city_share"] >= hub_mod.MIN_SHARE)
        & (frame["hub_score"] >= hub_mod.MIN_RATIO)
    ).astype("int8")
    return pd.DataFrame(frame.drop(columns=["_city", "_group", "_system"]))


__all__ = [
    "CANCEL_CAUSES",
    "CONTEXT_MEASURES",
    "FACT_KEYS",
    "FACT_SUM_COLUMNS",
    "HOUR_COLUMNS",
    "BuildResult",
    "add_congestion",
    "add_hub",
    "aggregate",
    "build_fact",
    "delay_denominator",
    "fact_measures",
    "write_table",
]
