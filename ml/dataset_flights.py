"""The flight-level modelling table: one DuckDB scan per calendar year.

One row per **scheduled** flight of the replication universe (ADR-0002: line
types N/R/E, DI 0, realised *and* cancelled), written to
``data/derived/ml/year=YYYY/part-0.parquet``. Cancellation is a target defined
on every row.

**Reading B for the delay targets (ADR-0017).** In the 2000-2009 layout an
actual time is a field of the *Boletim de Alteração de Vôo*, which IAC 1504
requires only "sempre que houver alguma alteração": an empty actual time on a
realised flight is the absence of a reported alteration, not an unknown outcome.
A panel of three reviewers read the instruction and the prediction outputs
and adopted that reading (`docs/notes/colegiado-adr0012.md`).
So a realised flight of a **pre-2010** year, operated by a carrier whose
`groups.csv` class is FSC, LCC or regional, with an empty actual time, gets a
delay of 0 and carries the flag ``on_time_no_bav``.

The scope is not the whole file. Over 2000-2009 the null actual-arrival rate is
72.9% for the 5.1 M realised flights of carriers in scope and 83.0% for the
313,368 out of it, and the sceptical reviewer of the panel measured 90-100% for
foreign carriers and code-share legs in a 2005 cross-section over all flights.
IAC 1504 §6.6 says only the operating carrier reports a code-share leg; for
`other` and unlabelled carriers an empty actual time therefore stays **unknown**
and the flight stays out of every delay target. ADR-0015's suspect-timestamp exclusion applies on top of both. Every one
of these counts is reported per year in ``manifest.json`` and in
``reports/prediction/results.md``.

Reading B is a **floor on punctuality**: a delay that was never reported counts
as on time, so the measured late rate is a lower bound before 2010. That
direction is stated in `docs/notes/prediction.md` and is not corrected for.

Leakage rule, written before the first feature (ADR-0009):

1. **Nothing from the flight after its departure.** No actual timestamp, no
   realised block time, no justification code, no cancellation status of the
   flight itself. Two staged columns are *nearly* pre-departure and are
   deliberately not reused: ``dep_hour``/``arr_hour`` fall back to the actual
   time when the schedule is missing (``vra.stage``: ``dep_ref =
   coalesce(sched_dep, actual_dep)``), so this module recomputes the hours from
   ``sched_dep``/``sched_arr`` alone and drops the rows that then have no hour.
2. **No same-period aggregate that contains the flight.** Every rate is read
   from a *closed* window: month t-1, t-12, or the three months t-3..t-1. The
   documented failure this rule exists for is the panel run where the same
   month's ``fsc_prdeldep`` lifted the R-squared from 0.58 to 0.82.
3. **The congestion threshold is closed too.** The p90 busy-hour flag compares
   the flight's scheduled day-hour with the airport's **previous calendar
   year** p90 of scheduled movements, not the current year's (which would peek
   at the rest of the year). This is the ADR-0007 proxy with the window closed.
4. **A timestamp a day or more out is not a target.** ADR-0015: the raw files
   carry month typos in the actual times, and the prediction dataset excludes
   those flights from the targets, counted per year. They stay in the table as
   rows, because a scheduled flight with a mistyped arrival still occupied its
   slot and still belongs in the movement counts.
5. **The two horizons are separated in the feature list, not in the data.**
   ``FEATURES_D1`` is what a planner knows the day before; ``FEATURES_H1`` adds
   the three columns describing the *inbound* leg's outcome. Nothing in
   ``FEATURES_H1`` is about the flight itself.

Cost: one pass per calendar year. Each year is materialised once into a temp
table and every aggregate of that year (the airport day-hour movement counts,
the flight-number monthly rates, the rotation link) is computed from it, so the
parquet is read exactly once. The monthly rates that need earlier years come
from the committed fact table (``data/analysis/fact_group_route_month.parquet``,
ADR-0014) plus a three-month carry-over kept in memory between iterations, so
no year is ever read twice.

The unit of the pass is the flight's **calendar year**, selected across the
whole staged tree, not the ``year=YYYY`` directory (ADR-0016 and
`vra.features.year_source_sql`): the directory is the year of the source file,
and a December file carries a few legs scheduled for 1 January.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from vra import congestion as congestion_mod
from vra import delays as delays_mod
from vra import features as features_mod
from vra import groups as groups_mod
from vra import stage as stage_mod
from vra import universe as universe_mod

if TYPE_CHECKING:  # pragma: no cover - typing only
    import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
DATASET_DIR = REPO_ROOT / "data" / "derived" / "ml"
FACT_PATH = REPO_ROOT / "data" / "analysis" / "fact_group_route_month.parquet"
EXTERNAL_DIR = REPO_ROOT / "data" / "external"
STAGED_DIR = REPO_ROOT / "data" / "staged"

LATE_MIN = 15.0
"""The article's late threshold and the main target's cut point, in minutes."""

LATE30_MIN = 30.0
"""ANAC's own second band, reported alongside."""

HIGH_SEASON_MONTHS: tuple[int, ...] = (1, 7, 12)
"""Brazilian school-holiday months. A convention, declared, not measured."""

SHUTTLE_ROUTES: frozenset[str] = frozenset({"MRSP-MRRJ", "MRRJ-MRSP"})
"""The Rio-Sao Paulo shuttle, the densest pair in the series."""

SUSPECT_DELAY_MIN = delays_mod.SUSPECT_DELAY_MIN
"""A delay of a whole day or more marks the timestamp as suspect (ADR-0015).

The raw files carry month typos in the actual times -- VSP 4374 in December 2003
has an actual arrival dated November, giving -43,170 minutes. ADR-0015 says the
prediction dataset excludes those flights **from the targets**, counted per
year. The rule now lives in `vra.delays` and is written once, at staging, as
the staged column `actual_time_suspect`; this module reads that column instead
of recomputing it. The feature columns are untouched -- a suspect timestamp is
still a real scheduled flight and still occupies its slot in the day-hour
movement count.
"""

BAV_LAST_LEGACY_YEAR = 2009
"""Last year of the layout in which an empty actual time means "no BAV" (ADR-0017).

The 2010 layout writes an actual time on essentially every realised flight
(0.0% missing against 59-80% before), so the reading applies to flights dated
2009 or earlier and the residual nulls of 2010+ stay null. The boundary is the
flight's own calendar year, not the source file's: 149 legs scheduled for
January 2010 sit in the 2009 files and are treated as 2010, which is the
conservative direction.
"""

BAV_CLASSES: tuple[str, ...] = ("FSC", "LCC", "regional")
"""Carrier classes reading B applies to (ADR-0017, scope amendment).

`other` and unlabelled carriers -- foreign operators and the non-operating side
of a code-share -- keep the null and stay out of every delay target. IAC 1504
§6.6: in code-share only the operating carrier reports, and the non-operator's
leg has no effect on the indices.
"""

H1_LEAD_MIN = 60.0
"""The at-gate horizon: one hour before the scheduled departure.

Used only for the ``prev_arr_known_h1`` diagnostic. ADR-0009 defines H-1 as
"with the previous leg's actual delay"; where the inbound leg actually lands
*later* than this lead time the feature is optimistic, and the share of links
in that position is measured per year rather than silently repaired.
"""

# ---------------------------------------------------------------------- columns

KEY_COLUMNS: tuple[str, ...] = (
    "flight_date",
    "year",
    "ym",
    "flight_number",
    "route",
)
"""Identifiers carried for splitting, hashing and joining; never features."""

FEATURES_CALENDAR: tuple[str, ...] = (
    "month",
    "dow",
    "is_weekend",
    "is_holiday",
    "is_observance",
    "is_holiday_window",
    "is_high_season",
)
FEATURES_SCHEDULE: tuple[str, ...] = (
    "sched_dep_hour",
    "sched_arr_hour",
    "sched_block_min",
    "leg_index",
)
FEATURES_GEOGRAPHY: tuple[str, ...] = (
    "origin_icao",
    "dest_icao",
    "origin_node",
    "dest_node",
    "route_kind",
    "distance_km",
    "origin_metro",
    "dest_metro",
    "origin_slot_coordinated",
    "dest_slot_coordinated",
)
FEATURES_CONGESTION: tuple[str, ...] = (
    "origin_movements_hour",
    "dest_movements_hour",
    "origin_movements_day",
    "dest_movements_day",
    "origin_p90_hour",
    "dest_p90_hour",
)
FEATURES_AIRLINE: tuple[str, ...] = (
    "airline",
    "group",
    "class",
    "airline_route_share_l1",
    "airline_origin_share_l1",
    "months_on_route",
    "is_new_on_route",
)
FEATURES_LAGGED: tuple[str, ...] = (
    "route_late15_l1",
    "route_obs_l1",
    "route_late15_l12",
    "group_late15_l1",
    "flight_no_late15_l3",
    "flight_no_obs_l3",
    "origin_late15_l1",
    "dest_late15_l1",
    "origin_weather_l1",
    "dest_weather_l1",
)
FEATURES_ROTATION: tuple[str, ...] = (
    "prev_leg",
    "prev_turnaround_min",
)

FEATURES_D1: tuple[str, ...] = (
    *FEATURES_CALENDAR,
    *FEATURES_SCHEDULE,
    *FEATURES_GEOGRAPHY,
    *FEATURES_CONGESTION,
    *FEATURES_AIRLINE,
    *FEATURES_LAGGED,
    *FEATURES_ROTATION,
)
"""Day-ahead horizon: everything a planner knows the evening before."""

FEATURES_H1_ONLY: tuple[str, ...] = (
    "prev_arr_delay_min",
    "prev_late15",
    "prev_cancelled",
)
"""What the gate adds at H-1: the *inbound* leg's outcome, never this flight's."""

FEATURES_H1: tuple[str, ...] = (*FEATURES_D1, *FEATURES_H1_ONLY)

CATEGORICAL: tuple[str, ...] = (
    "airline",
    "group",
    "class",
    "origin_icao",
    "dest_icao",
    "origin_node",
    "dest_node",
    "route_kind",
)
"""Features handed to XGBoost as pandas ``category`` (``enable_categorical``)."""

TARGETS: tuple[str, ...] = (
    "late15_arr",
    "late30_arr",
    "arr_delay_min",
    "late15_dep",
    "cancelled",
)
BINARY_TARGETS: tuple[str, ...] = ("late15_arr", "late30_arr", "late15_dep", "cancelled")

DIAGNOSTICS: tuple[str, ...] = (
    "is_realized",
    "has_arr_actual",
    "has_dep_actual",
    "actual_time_suspect",
    "on_time_no_bav",
    "prev_arr_known_h1",
)
"""Carried for the per-year accounting and the leakage checks; never features.

`on_time_no_bav` in particular is a fact about the *outcome* -- whether an
alteration was reported -- and handing it to a model would be leakage of the
plainest kind. `ml.leakage_tests.check_targets_are_not_features` enforces that.
"""

DATASET_COLUMNS: tuple[str, ...] = (
    *KEY_COLUMNS,
    *FEATURES_D1,
    *FEATURES_H1_ONLY,
    *DIAGNOSTICS,
    *TARGETS,
)

POST_DEPARTURE_STAGED: tuple[str, ...] = (
    "actual_dep",
    "actual_arr",
    "actual_block_min",
    "cause_code",
    "status",
    "dep_delay_min",
    "arr_delay_min",
    "is_realized",
    "universe_ml",
)
"""Staged columns that describe the flight *after* it departed.

``arr_delay_min`` and ``is_realized`` appear here and in the dataset: as
**targets and diagnostics**, never as features. `ml.leakage_tests` checks both
sides of that sentence.
"""

DTYPES: dict[str, str] = {
    "year": "int16",
    "ym": "int32",
    "flight_number": "int32",
    "month": "int8",
    "dow": "int8",
    "is_weekend": "int8",
    "is_holiday": "int8",
    "is_observance": "int8",
    "is_holiday_window": "int8",
    "is_high_season": "int8",
    "sched_dep_hour": "int8",
    "sched_arr_hour": "int8",
    "sched_block_min": "int16",
    "leg_index": "int8",
    "origin_metro": "int8",
    "dest_metro": "int8",
    "origin_slot_coordinated": "int8",
    "dest_slot_coordinated": "int8",
    "origin_movements_hour": "int16",
    "dest_movements_hour": "int16",
    "origin_movements_day": "int16",
    "dest_movements_day": "int16",
    "route_obs_l1": "int32",
    "flight_no_obs_l3": "int32",
    "is_new_on_route": "int8",
    "prev_leg": "int8",
    "cancelled": "int8",
    "is_realized": "bool",
    "has_arr_actual": "bool",
    "has_dep_actual": "bool",
    "actual_time_suspect": "bool",
    "on_time_no_bav": "bool",
}
"""Explicit dtypes; everything not listed is ``float32`` or ``category``."""


# ------------------------------------------------------------------- lag tables


def _shift_ym(ym: Any, months: int) -> Any:
    """Move a ``YYYYMM`` key by `months`, in integer arithmetic.

    >>> _shift_ym(200712, 1)
    200801
    >>> _shift_ym(200401, -1)
    200312
    """
    index = (ym // 100) * 12 + (ym % 100) - 1 + months
    return (index // 12) * 100 + (index % 12) + 1


def _rate(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    return numerator.astype("float64") / denominator.astype("float64").where(denominator > 0)


def bav_scope_sql(alias: str, class_expr: str) -> str:
    """Rows reading B applies to: realised, pre-2010, carrier class in scope."""
    classes = ", ".join(f"'{name}'" for name in BAV_CLASSES)
    return (
        f"({alias}.is_realized AND {alias}.year <= {BAV_LAST_LEGACY_YEAR} "
        f"AND {class_expr} IN ({classes}))"
    )


def effective_delay_sql(alias: str, side: str, class_expr: str) -> str:
    """The ADR-0017 delay of one side: the measured one, or 0 where no BAV exists.

    Written once and used by the targets, by the inbound leg and by the
    flight-number lag, so a rate can never be a rate of one reading while the
    target it predicts is the other.
    """
    actual = "actual_arr" if side == "arr" else "actual_dep"
    delay = f"{side}_delay_min"
    scope = bav_scope_sql(alias, class_expr)
    return (
        f"CASE WHEN {alias}.{delay} IS NOT NULL THEN {alias}.{delay} "
        f"WHEN {scope} AND {alias}.{actual} IS NULL THEN 0.0 END"
    )


def bav_denominator(fact: pd.DataFrame, side: str) -> pd.Series:
    """Flights a lagged delay rate is divided by under reading B (ADR-0017).

    The fact table is convention-free: it carries the strict observation count
    and, separately, the realised flights the legacy files left without an
    actual time. Reading B puts the second group back into the denominator —
    but only for the cells in scope, which the fact table's own `class` and
    `year` keys decide. The numerator never moves: a flight imputed at 0 minutes
    is not more than 15 minutes late.
    """
    in_scope = (fact["year"] <= BAV_LAST_LEGACY_YEAR) & fact["class"].isin(BAV_CLASSES)
    observed = fact[f"{side}_delay_obs"].astype("int64")
    return observed + fact[f"{side}_missing_actual"].astype("int64").where(in_scope, 0)


@dataclass(frozen=True)
class LagTables:
    """Monthly rates, each keyed by the month they are a *feature of*.

    Every frame's ``ym`` is the **target** month, not the month the rate was
    measured in: ``route_late15_l1`` at ``ym = 200704`` is March 2007's rate.
    Shifting once, here, is what makes the join downstream a plain equality and
    the leakage check a one-liner.
    """

    route: pd.DataFrame
    group: pd.DataFrame
    node: pd.DataFrame
    group_route: pd.DataFrame
    group_node: pd.DataFrame


FACT_CELL_KEYS: tuple[str, ...] = ("ym", "route", "origin_node", "dest_node", "group", "class")
"""The keys a fact cell is unique on *after* `collapse_fact`."""


def collapse_fact(fact: pd.DataFrame) -> pd.DataFrame:
    """Make the fact table one row per ``group x route x month``.

    ADR-0016 makes that key a tested invariant of the fact table, and
    `vra.features.build_fact` now asserts it, so against a freshly built table
    this function returns the frame untouched. It stays as the compatibility
    path for an older committed fact table, where `build_fact` grouped within
    each **file** year and concatenated: the 3,723 staged rows whose derived
    year differs from the year of their source file (`docs/notes/staging.md`
    section 5) emitted the same cell twice, 844 rows over 422 keys. Joining a
    lag table with two rows for one key duplicates every flight in that cell:
    1,128 extra rows in 2001 alone, measured before this existed. Counts add;
    ``is_entry``/``is_exit`` take the minimum, because a cell that is a
    continuation in one partition is a continuation.
    """
    duplicated = fact.duplicated(subset=list(FACT_CELL_KEYS), keep=False)
    if not bool(duplicated.any()):
        return fact
    flags = ["is_entry", "is_exit"]
    skip = {*FACT_CELL_KEYS, "year", "month", "n_flight_numbers", *flags}
    how: dict[str, str] = {name: "sum" for name in fact.columns if name not in skip}
    how.update({"year": "min", "month": "min", "n_flight_numbers": "max"})
    how.update(dict.fromkeys(flags, "min"))
    return fact.groupby(list(FACT_CELL_KEYS), as_index=False, observed=True).agg(how)


def monthly_lags(fact: pd.DataFrame) -> LagTables:
    """Closed-window monthly rates from the committed fact table.

    The fact table is the canonical ``group x route x month`` aggregate
    (ADR-0004) and carries counts only, so the convention is chosen here rather
    than inherited. It is ADR-0017's reading B, the same one the targets use:
    the denominator is ``*_delay_obs`` plus, for a realised pre-2010 cell of a
    carrier in scope, the flights that reported no alteration
    (`bav_denominator`). A lagged rate on a different reading from the target it
    predicts would be a feature measuring another quantity.
    """
    import pandas as pd

    fact = collapse_fact(fact)
    fact = fact.assign(
        arr_delay_obs=bav_denominator(fact, "arr"), dep_delay_obs=bav_denominator(fact, "dep")
    )
    route = fact.groupby(["route", "ym"], observed=True)[
        ["flights", "arr_delay_obs", "arr_delayed_gt15"]
    ].sum()
    route = route.reset_index()
    route["late15"] = _rate(route["arr_delayed_gt15"], route["arr_delay_obs"])
    lag1 = route.assign(ym=_shift_ym(route["ym"], 1))[["route", "ym", "late15", "arr_delay_obs"]]
    lag1 = lag1.rename(columns={"late15": "route_late15_l1", "arr_delay_obs": "route_obs_l1"})
    lag12 = route.assign(ym=_shift_ym(route["ym"], 12))[["route", "ym", "late15"]]
    lag12 = lag12.rename(columns={"late15": "route_late15_l12"})
    route_lag = lag1.merge(lag12, on=["route", "ym"], how="outer")
    route_lag["route_obs_l1"] = route_lag["route_obs_l1"].fillna(0).astype("int32")

    grp = fact.groupby(["group", "ym"], observed=True)[["arr_delay_obs", "arr_delayed_gt15"]].sum()
    grp = grp.reset_index()
    grp["group_late15_l1"] = _rate(grp["arr_delayed_gt15"], grp["arr_delay_obs"])
    group_lag = grp.assign(ym=_shift_ym(grp["ym"], 1))[["group", "ym", "group_late15_l1"]]

    origin = fact.groupby(["origin_node", "ym"], observed=True)[
        ["flights", "dep_delay_obs", "dep_delayed_gt15", "cause_weather"]
    ].sum()
    origin = origin.reset_index().rename(columns={"origin_node": "node"})
    origin["node_dep_late15_l1"] = _rate(origin["dep_delayed_gt15"], origin["dep_delay_obs"])
    origin["node_weather_dep_l1"] = _rate(origin["cause_weather"], origin["flights"])
    dest = fact.groupby(["dest_node", "ym"], observed=True)[
        ["flights", "arr_delay_obs", "arr_delayed_gt15", "cause_weather"]
    ].sum()
    dest = dest.reset_index().rename(columns={"dest_node": "node"})
    dest["node_arr_late15_l1"] = _rate(dest["arr_delayed_gt15"], dest["arr_delay_obs"])
    dest["node_weather_arr_l1"] = _rate(dest["cause_weather"], dest["flights"])
    node = origin[["node", "ym", "node_dep_late15_l1", "node_weather_dep_l1"]].merge(
        dest[["node", "ym", "node_arr_late15_l1", "node_weather_arr_l1"]],
        on=["node", "ym"],
        how="outer",
    )
    node_lag = node.assign(ym=_shift_ym(node["ym"], 1))

    pair = fact.groupby(["group", "route", "ym"], observed=True)["flights"].sum().reset_index()
    totals = route[["route", "ym", "flights"]].rename(columns={"flights": "route_flights"})
    pair = pair.merge(totals, on=["route", "ym"], how="left")
    pair["airline_route_share_l1"] = _rate(pair["flights"], pair["route_flights"])
    pair = pair.merge(_months_on_route(fact), on=["group", "route", "ym"], how="left")
    group_route_lag = pair.assign(ym=_shift_ym(pair["ym"], 1))[
        ["group", "route", "ym", "airline_route_share_l1", "months_on_route"]
    ]

    at_node = (
        fact.groupby(["group", "origin_node", "ym"], observed=True)["flights"].sum().reset_index()
    )
    node_totals = (
        origin[["node", "ym", "flights"]]
        .rename(columns={"node": "origin_node", "flights": "node_flights"})
        .copy()
    )
    at_node = at_node.merge(node_totals, on=["origin_node", "ym"], how="left")
    at_node["airline_origin_share_l1"] = _rate(at_node["flights"], at_node["node_flights"])
    group_node_lag = at_node.assign(ym=_shift_ym(at_node["ym"], 1))[
        ["group", "origin_node", "ym", "airline_origin_share_l1"]
    ]
    group_node_lag = group_node_lag.rename(columns={"origin_node": "node"})

    return LagTables(
        route=pd.DataFrame(route_lag),
        group=pd.DataFrame(group_lag),
        node=pd.DataFrame(node_lag),
        group_route=pd.DataFrame(group_route_lag),
        group_node=pd.DataFrame(group_node_lag),
    )


def _months_on_route(fact: pd.DataFrame) -> pd.DataFrame:
    """Months the group had been continuously on the route, as of each month.

    Uses the fact table's own ``is_entry`` (ADR-0004: an entry is a *gap in the
    calendar*, not merely a missing neighbouring row), so a group that left and
    came back starts counting again.
    """
    import pandas as pd

    spell = fact[["group", "route", "ym", "is_entry"]].sort_values(["group", "route", "ym"])
    index = (spell["ym"] // 100) * 12 + (spell["ym"] % 100) - 1
    start = index.where(spell["is_entry"].astype(bool))
    spell["start"] = start.groupby([spell["group"], spell["route"]], observed=True).ffill()
    spell["months_on_route"] = (index - spell["start"] + 1).astype("float32")
    return pd.DataFrame(spell[["group", "route", "ym", "months_on_route"]])


# ---------------------------------------------------------------- small tables


def calendar_frame(external_dir: Path, years: tuple[int, ...]) -> pd.DataFrame:
    """One row per calendar day: holiday, observance, adjacency, high season.

    ``holidays.csv`` holds only the days that are national holidays by federal
    law; Carnival, Good Friday and Corpus Christi live in ``observances.csv``
    because they are not (`data/external/README.md`). Both move airline
    schedules, so both are features, and they stay separate columns rather than
    being merged into one "holiday" that would misdescribe either.
    """
    import pandas as pd

    external_dir = Path(external_dir)
    first, last = min(years), max(years)
    days = pd.date_range(f"{first - 1}-01-01", f"{last + 1}-12-31", freq="D")
    frame = pd.DataFrame({"day": days})
    holidays = _dates(external_dir / "holidays.csv")
    observances = _dates(external_dir / "observances.csv")
    frame["is_holiday"] = frame["day"].isin(holidays).astype("int8")
    frame["is_observance"] = frame["day"].isin(observances).astype("int8")
    special = frame["is_holiday"].astype(bool) | frame["is_observance"].astype(bool)
    adjacent = special | special.shift(1, fill_value=False) | special.shift(-1, fill_value=False)
    frame["is_holiday_window"] = adjacent.astype("int8")
    frame["is_high_season"] = frame["day"].dt.month.isin(HIGH_SEASON_MONTHS).astype("int8")
    frame["day"] = frame["day"].dt.date
    return frame


def _dates(path: Path) -> set[Any]:
    import pandas as pd

    if not path.exists():
        return set()
    column = pd.read_csv(path, usecols=["date"])["date"]
    return set(pd.to_datetime(column, errors="coerce").dropna())


def node_frame(external_dir: Path) -> pd.DataFrame:
    """``icao -> node, metropolitan`` from `data/external/nodes.csv`."""
    import pandas as pd

    path = Path(external_dir) / "nodes.csv"
    if not path.exists():
        return pd.DataFrame({"icao": [], "is_metro": []})
    table = pd.read_csv(path, usecols=["icao", "metropolitan"])
    table["is_metro"] = (
        table["metropolitan"].astype(str).str.strip().str.lower().eq("true").astype("int8")
    )
    return pd.DataFrame(table[["icao", "is_metro"]].drop_duplicates("icao"))


def slot_frame(external_dir: Path) -> pd.DataFrame:
    """``icao -> first coordinated month`` from `data/external/slots.csv`.

    Two airports only (SBGR from 2009-01, SBRJ from 2009-03). Congonhas is
    absent because no act or date was found for it, and inventing one to make
    the column look complete is exactly what ADR-0010 forbids.
    """
    import pandas as pd

    path = Path(external_dir) / "slots.csv"
    if not path.exists():
        return pd.DataFrame({"icao": [], "slot_from_ym": []})
    table = pd.read_csv(path, usecols=["icao", "coordinated_from"], dtype=str)
    table["slot_from_ym"] = (
        table["coordinated_from"].str[:7].str.replace("-", "", regex=False).astype("int32")
    )
    return pd.DataFrame(table[["icao", "slot_from_ym"]])


def distance_frame(external_dir: Path) -> pd.DataFrame:
    """``origin_node, dest_node -> distance_km`` from `distances_km.csv`."""
    import pandas as pd

    path = Path(external_dir) / "distances_km.csv"
    if not path.exists():
        return pd.DataFrame({"origin_node": [], "dest_node": [], "distance_km": []})
    table = pd.read_csv(path, usecols=["origin_node", "dest_node", "distance_km"])
    return pd.DataFrame(table)


# ------------------------------------------------------------------------- SQL

_YEAR_COLUMNS = """
    flight_date, year, month, ym, airline, flight_number, line_type, di,
    origin_icao, dest_icao, origin_node, dest_node, route, status, cause_code,
    sched_dep, sched_arr, actual_dep, actual_arr, dep_delay_min, arr_delay_min,
    sched_block_min, universe_repl, is_realized, actual_time_suspect
"""

MOVEMENTS_SQL = """
CREATE OR REPLACE TEMP TABLE mov_hour AS
WITH sides AS (
    SELECT origin_icao AS icao, CAST(sched_dep AS DATE) AS day, hour(sched_dep) AS hour
    FROM ml_year WHERE sched_dep IS NOT NULL AND origin_icao IS NOT NULL
    UNION ALL
    SELECT dest_icao AS icao, CAST(sched_arr AS DATE) AS day, hour(sched_arr) AS hour
    FROM ml_year WHERE sched_arr IS NOT NULL AND dest_icao IS NOT NULL
)
SELECT icao, day, hour, count(*)::INTEGER AS movements
FROM sides GROUP BY icao, day, hour;

CREATE OR REPLACE TEMP TABLE mov_day AS
SELECT icao, day, sum(movements)::INTEGER AS movements FROM mov_hour GROUP BY icao, day;
"""
"""Scheduled movements per airport-day-hour, from the schedule itself.

Counted over **every** staged row of the year, not only the universe: an extra
section, an international leg and a cargo flight occupy the same runway in the
same hour as the flight being predicted. Both sides of every flight count, on
its *scheduled* times, so the whole table is knowable the day before.
"""

UNIVERSE_COUNT_SQL = f"""
SELECT
    count(*) FILTER (WHERE {universe_mod.UNIVERSE_REPL_SQL})::BIGINT AS universe_rows,
    count(*) FILTER (WHERE {universe_mod.UNIVERSE_REPL_SQL} AND (
        sched_dep IS NULL OR sched_arr IS NULL OR route IS NULL
        OR origin_icao IS NULL OR dest_icao IS NULL OR ym IS NULL))::BIGINT AS no_schedule
FROM ml_year
"""
"""How many universe rows the year has, and how many carry no usable schedule.

A flight with no scheduled departure cannot be predicted the day before -- there
is no day before -- so it is dropped, and the count is reported rather than
absorbed into the row total.
"""


def flight_number_sql() -> str:
    """Monthly arrival-delay counts per flight number, under reading B.

    Same effective delay as the target (`effective_delay_sql`), so
    ``flight_no_late15_l3`` is the three closed months of exactly the quantity
    the model is asked to predict.
    """
    label = groups_mod.label_sql("m.airline", "m.ym", alias="g")
    effective = effective_delay_sql("m", "arr", groups_mod.resolved_class_sql())
    return f"""
SELECT m.airline AS airline, m.flight_number AS flight_number, m.ym AS ym,
       count(*) FILTER (WHERE m.is_realized AND ({effective}) IS NOT NULL)::INTEGER AS obs,
       count(*) FILTER (WHERE m.is_realized AND ({effective}) > {LATE_MIN})::INTEGER AS late
FROM ml_year m {label}
WHERE m.universe_repl AND m.airline IS NOT NULL
  AND m.flight_number IS NOT NULL AND m.ym IS NOT NULL
GROUP BY m.airline, m.flight_number, m.ym
"""


P90_SQL = f"""
SELECT icao,
       quantile_cont(movements, {congestion_mod.PERCENTILE}) AS threshold,
       count(*)::INTEGER AS n_day_hours
FROM mov_hour GROUP BY icao
HAVING count(*) >= {congestion_mod.MIN_DAY_HOURS}
"""
"""The ADR-0007 p90 proxy with the window closed.

`congestion.p90_thresholds` computes the threshold within the node's own
calendar year; here it is computed on the *previous* year, because a threshold
that reads the rest of the current year is a window that has not closed
(ADR-0009). Same percentile, same minimum number of observed day-hours, one
year earlier -- and at the airport rather than the node, because a runway is
not shared between Congonhas and Guarulhos.
"""


def _flight_sql() -> str:
    """The one query that turns a materialised staged year into feature rows."""
    label = groups_mod.label_sql("b.airline", "b.ym", alias="g")
    late = LATE_MIN
    late30 = LATE30_MIN
    classes = ", ".join(f"'{name}'" for name in BAV_CLASSES)
    # ADR-0017, reading B, written once and applied to the flight and to its
    # inbound leg alike: a realised pre-2010 flight of an FSC/LCC/regional
    # carrier with no actual time reported no alteration, so its delay is 0.
    # Outside that scope the null stays a null.
    bav = (
        f"(b.is_realized AND b.year <= {BAV_LAST_LEGACY_YEAR} "
        f"AND {groups_mod.resolved_class_sql()} IN ({classes}))"
    )
    # A target exists only for a realised flight whose timestamps are usable:
    # ADR-0015 removes the ones written with a month typo, and ADR-0017 leaves
    # `other` and unlabelled carriers without one where the actual time is
    # absent. `cancelled` is a status, not a time, and is defined on every row.
    no_target = "(NOT l.is_realized OR l.actual_time_suspect)"
    return f"""
WITH base AS (
    SELECT * FROM ml_year
    WHERE {universe_mod.UNIVERSE_REPL_SQL}
      AND sched_dep IS NOT NULL AND sched_arr IS NOT NULL
      AND route IS NOT NULL AND ym IS NOT NULL
      AND origin_icao IS NOT NULL AND dest_icao IS NOT NULL
),
labelled AS (
    SELECT b.*,
           row_number() OVER () AS flight_id,
           CAST(b.sched_dep AS DATE) AS sched_date,
           {groups_mod.resolved_group_sql("b.airline")} AS grp,
           {groups_mod.resolved_class_sql()} AS cls,
           {bav} AND (b.actual_arr IS NULL OR b.actual_dep IS NULL) AS no_bav,
           CASE WHEN b.arr_delay_min IS NOT NULL THEN b.arr_delay_min
                WHEN {bav} AND b.actual_arr IS NULL THEN 0.0 END AS eff_arr_delay,
           CASE WHEN b.dep_delay_min IS NOT NULL THEN b.dep_delay_min
                WHEN {bav} AND b.actual_dep IS NULL THEN 0.0 END AS eff_dep_delay,
           CASE WHEN b.actual_arr IS NOT NULL THEN b.actual_arr
                WHEN {bav} THEN b.sched_arr END AS eff_actual_arr
    FROM base b {label}
),
chain AS (
    SELECT *, CAST(row_number() OVER (
                  PARTITION BY airline, flight_number, sched_date ORDER BY sched_dep
              ) AS TINYINT) AS leg_index
    FROM labelled
),
prev AS (
    SELECT flight_id AS p_id, airline, flight_number, sched_date,
           dest_icao AS icao, sched_arr AS p_sched_arr, eff_actual_arr AS p_actual_arr,
           eff_arr_delay AS p_arr_delay, status AS p_status
    FROM labelled WHERE sched_arr IS NOT NULL
),
linked AS (
    SELECT c.*, p.p_sched_arr, p.p_actual_arr, p.p_arr_delay, p.p_status,
           row_number() OVER (PARTITION BY c.flight_id ORDER BY p.p_sched_arr DESC) AS rn
    FROM chain c
    LEFT JOIN prev p
      ON p.airline = c.airline AND p.flight_number = c.flight_number
     AND p.sched_date = c.sched_date AND p.icao = c.origin_icao
     AND p.p_sched_arr <= c.sched_dep AND p.p_id <> c.flight_id
)
SELECT
    l.sched_date                                            AS flight_date,
    CAST(year(l.sched_date) AS SMALLINT)                    AS year,
    CAST(year(l.sched_date) * 100 + month(l.sched_date) AS INTEGER) AS ym,
    l.flight_number                                         AS flight_number,
    l.route                                                 AS route,
    CAST(month(l.sched_date) AS TINYINT)                    AS month,
    CAST((dayofweek(l.sched_date) + 6) % 7 AS TINYINT)      AS dow,
    CAST(((dayofweek(l.sched_date) + 6) % 7) >= 5 AS TINYINT) AS is_weekend,
    coalesce(cal.is_holiday, 0)::TINYINT                    AS is_holiday,
    coalesce(cal.is_observance, 0)::TINYINT                 AS is_observance,
    coalesce(cal.is_holiday_window, 0)::TINYINT             AS is_holiday_window,
    coalesce(cal.is_high_season, 0)::TINYINT                AS is_high_season,
    CAST(hour(l.sched_dep) AS TINYINT)                      AS sched_dep_hour,
    CAST(hour(l.sched_arr) AS TINYINT)                      AS sched_arr_hour,
    l.sched_block_min                                       AS sched_block_min,
    l.leg_index                                             AS leg_index,
    l.origin_icao                                           AS origin_icao,
    l.dest_icao                                             AS dest_icao,
    l.origin_node                                           AS origin_node,
    l.dest_node                                             AS dest_node,
    CASE
        WHEN l.route IN ({", ".join(f"'{r}'" for r in sorted(SHUTTLE_ROUTES))}) THEN 'shuttle'
        WHEN coalesce(no_.is_metro, 0) = 1 AND coalesce(nd.is_metro, 0) = 1   THEN 'metro'
        WHEN no_.icao IS NOT NULL AND nd.icao IS NOT NULL                     THEN 'capital'
        WHEN no_.icao IS NOT NULL OR nd.icao IS NOT NULL                      THEN 'mixed'
        ELSE 'other'
    END                                                     AS route_kind,
    CAST(dist.distance_km AS FLOAT)                         AS distance_km,
    coalesce(no_.is_metro, 0)::TINYINT                      AS origin_metro,
    coalesce(nd.is_metro, 0)::TINYINT                       AS dest_metro,
    CAST(so.slot_from_ym IS NOT NULL AND l.ym >= so.slot_from_ym AS TINYINT) AS origin_slot_coordinated,
    CAST(sd.slot_from_ym IS NOT NULL AND l.ym >= sd.slot_from_ym AS TINYINT) AS dest_slot_coordinated,
    coalesce(mo.movements, 0)::SMALLINT                     AS origin_movements_hour,
    coalesce(md.movements, 0)::SMALLINT                     AS dest_movements_hour,
    coalesce(do_.movements, 0)::SMALLINT                    AS origin_movements_day,
    coalesce(dd.movements, 0)::SMALLINT                     AS dest_movements_day,
    CAST(CASE WHEN po.threshold IS NULL THEN NULL
              ELSE coalesce(mo.movements, 0) >= po.threshold END AS FLOAT) AS origin_p90_hour,
    CAST(CASE WHEN pd.threshold IS NULL THEN NULL
              ELSE coalesce(md.movements, 0) >= pd.threshold END AS FLOAT) AS dest_p90_hour,
    l.airline                                               AS airline,
    l.grp                                                   AS "group",
    l.cls                                                   AS "class",
    CAST(gr.airline_route_share_l1 AS FLOAT)                AS airline_route_share_l1,
    CAST(gn.airline_origin_share_l1 AS FLOAT)               AS airline_origin_share_l1,
    CAST(gr.months_on_route AS FLOAT)                       AS months_on_route,
    CAST(gr.months_on_route IS NULL AS TINYINT)             AS is_new_on_route,
    CAST(rt.route_late15_l1 AS FLOAT)                       AS route_late15_l1,
    coalesce(rt.route_obs_l1, 0)::INTEGER                   AS route_obs_l1,
    CAST(rt.route_late15_l12 AS FLOAT)                      AS route_late15_l12,
    CAST(gp.group_late15_l1 AS FLOAT)                       AS group_late15_l1,
    CAST(fn.late15 AS FLOAT)                                AS flight_no_late15_l3,
    coalesce(fn.obs, 0)::INTEGER                            AS flight_no_obs_l3,
    CAST(nlo.node_dep_late15_l1 AS FLOAT)                   AS origin_late15_l1,
    CAST(nld.node_arr_late15_l1 AS FLOAT)                   AS dest_late15_l1,
    CAST(nlo.node_weather_dep_l1 AS FLOAT)                  AS origin_weather_l1,
    CAST(nld.node_weather_arr_l1 AS FLOAT)                  AS dest_weather_l1,
    CAST(l.p_sched_arr IS NOT NULL AS TINYINT)              AS prev_leg,
    CAST(date_diff('second', l.p_sched_arr, l.sched_dep) / 60.0 AS FLOAT) AS prev_turnaround_min,
    CAST(l.p_arr_delay AS FLOAT)                            AS prev_arr_delay_min,
    CAST(CASE WHEN l.p_arr_delay IS NULL THEN NULL
              ELSE l.p_arr_delay > {late} END AS FLOAT)     AS prev_late15,
    CAST(CASE WHEN l.p_sched_arr IS NULL THEN NULL
              ELSE l.p_status = '{universe_mod.STATUS_CANCELLED}' END AS FLOAT) AS prev_cancelled,
    l.is_realized                                           AS is_realized,
    l.actual_arr IS NOT NULL                                AS has_arr_actual,
    l.actual_dep IS NOT NULL                                AS has_dep_actual,
    l.actual_time_suspect                                   AS actual_time_suspect,
    coalesce(l.no_bav, FALSE)                               AS on_time_no_bav,
    CAST(CASE WHEN l.p_actual_arr IS NULL THEN NULL
              ELSE date_diff('second', l.p_actual_arr, l.sched_dep) / 60.0 >= {H1_LEAD_MIN}
         END AS FLOAT)                                      AS prev_arr_known_h1,
    CAST(CASE WHEN {no_target} OR l.eff_arr_delay IS NULL THEN NULL
              ELSE l.eff_arr_delay > {late} END AS FLOAT)   AS late15_arr,
    CAST(CASE WHEN {no_target} OR l.eff_arr_delay IS NULL THEN NULL
              ELSE l.eff_arr_delay > {late30} END AS FLOAT) AS late30_arr,
    CAST(CASE WHEN {no_target} THEN NULL ELSE l.eff_arr_delay END AS FLOAT) AS arr_delay_min,
    CAST(CASE WHEN {no_target} OR l.eff_dep_delay IS NULL THEN NULL
              ELSE l.eff_dep_delay > {late} END AS FLOAT)   AS late15_dep,
    CAST(l.status = '{universe_mod.STATUS_CANCELLED}' AS TINYINT) AS cancelled
FROM linked l
LEFT JOIN cal_tbl  cal ON cal.day = l.sched_date
LEFT JOIN nodes_tbl no_ ON no_.icao = l.origin_icao
LEFT JOIN nodes_tbl nd  ON nd.icao  = l.dest_icao
LEFT JOIN slots_tbl so  ON so.icao  = l.origin_icao
LEFT JOIN slots_tbl sd  ON sd.icao  = l.dest_icao
LEFT JOIN dist_tbl dist ON dist.origin_node = l.origin_node AND dist.dest_node = l.dest_node
LEFT JOIN mov_hour mo   ON mo.icao = l.origin_icao AND mo.day = l.sched_date
                       AND mo.hour = hour(l.sched_dep)
LEFT JOIN mov_hour md   ON md.icao = l.dest_icao AND md.day = CAST(l.sched_arr AS DATE)
                       AND md.hour = hour(l.sched_arr)
LEFT JOIN mov_day do_   ON do_.icao = l.origin_icao AND do_.day = l.sched_date
LEFT JOIN mov_day dd    ON dd.icao = l.dest_icao AND dd.day = CAST(l.sched_arr AS DATE)
LEFT JOIN p90_tbl po    ON po.icao = l.origin_icao
LEFT JOIN p90_tbl pd    ON pd.icao = l.dest_icao
LEFT JOIN lag_route rt  ON rt.route = l.route AND rt.ym = l.ym
LEFT JOIN lag_group gp  ON gp."group" = l.grp AND gp.ym = l.ym
LEFT JOIN lag_node nlo  ON nlo.node = l.origin_node AND nlo.ym = l.ym
LEFT JOIN lag_node nld  ON nld.node = l.dest_node AND nld.ym = l.ym
LEFT JOIN lag_group_route gr ON gr."group" = l.grp AND gr.route = l.route AND gr.ym = l.ym
LEFT JOIN lag_group_node gn  ON gn."group" = l.grp AND gn.node = l.origin_node AND gn.ym = l.ym
LEFT JOIN lag_flight_number fn ON fn.airline = l.airline
                             AND fn.flight_number = l.flight_number AND fn.ym = l.ym
WHERE l.rn = 1
"""


# ----------------------------------------------------------------------- build


def staged_years(staged_dir: Path) -> tuple[int, ...]:
    """The ``year=YYYY`` partitions present under a staged tree, ascending."""
    found = sorted(
        int(path.name.split("=")[1])
        for path in Path(staged_dir).glob("year=*")
        if path.is_dir() and path.name.split("=")[1].isdigit()
    )
    if not found:
        raise FileNotFoundError(f"no year=YYYY partitions under {staged_dir}")
    return tuple(found)


@dataclass
class YearSummary:
    """The per-year accounting the report and ADR-0012 both need."""

    year: int
    rows: int
    universe_rows: int
    realized: int
    cancelled: int
    dropped_no_schedule: int
    target_rows: int
    target_excluded_missing_actual: int
    target_excluded_suspect: int
    on_time_no_bav: int
    on_time_no_bav_share: float | None
    realized_no_arr_actual: int
    late15_arr_rate: float | None
    cancelled_rate: float | None
    prev_leg_share: float
    prev_arr_known_share: float | None
    prev_arr_known_h1_share: float | None

    def as_dict(self) -> dict[str, Any]:
        return {key: getattr(self, key) for key in self.__dataclass_fields__}


@dataclass
class BuildResult:
    """What one `build_dataset` run produced."""

    rows: int
    years: tuple[int, ...]
    seconds: float
    out_dir: Path
    by_year: list[YearSummary] = field(default_factory=list)

    def summary_frame(self) -> pd.DataFrame:
        import pandas as pd

        return pd.DataFrame([row.as_dict() for row in self.by_year])


def build_dataset(
    staged_dir: Path = STAGED_DIR,
    out_dir: Path = DATASET_DIR,
    *,
    fact_path: Path = FACT_PATH,
    external_dir: Path = EXTERNAL_DIR,
    years: tuple[int, ...] | None = None,
    groups_path: Path | None = None,
    outlier_threshold_min: float = delays_mod.OUTLIER_THRESHOLD_MIN,
    con: Any = None,
    verbose: bool = True,
) -> BuildResult:
    """Build ``data/derived/ml/year=YYYY/part-0.parquet``, one scan per year.

    Years are processed in ascending order because the three-month
    flight-number window and the p90 threshold carry forward from the previous
    iteration; that carry is what keeps the whole build to a single read of
    each staged partition.
    """

    started = time.time()
    staged_dir, out_dir = Path(staged_dir), Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    years = tuple(sorted(years or staged_years(staged_dir)))
    owns_con = con is None
    con = con or stage_mod.connect()
    summaries: list[YearSummary] = []
    total_rows = 0
    try:
        _register_static(con, external_dir, fact_path, years, groups_path)
        carry: pd.DataFrame | None = None
        for year in years:
            con.execute(
                f"CREATE OR REPLACE TEMP TABLE ml_year AS SELECT {_YEAR_COLUMNS} "
                f"FROM {features_mod.year_source_sql(staged_dir, year)}"
            )
            con.execute(MOVEMENTS_SQL)
            carry = _register_flight_number_lags(con, carry)
            frame = con.execute(_flight_sql()).df()
            frame = _finalise(frame)
            counts = con.execute(UNIVERSE_COUNT_SQL).fetchone()
            summaries.append(_summarise(year, frame, int(counts[0]), int(counts[1])))
            _write_year(frame, out_dir, year)
            total_rows += len(frame)
            con.execute("CREATE OR REPLACE TEMP TABLE p90_tbl AS " + P90_SQL)
            if verbose:
                print(
                    f"{year}: {len(frame):>9,d} flights, "
                    f"{summaries[-1].target_rows:>9,d} with an arrival target "
                    f"({summaries[-1].prev_leg_share:.1%} linked)  "
                    f"({time.time() - started:5.1f}s)",
                    flush=True,
                )
    finally:
        if owns_con:
            con.close()
    result = BuildResult(
        rows=total_rows,
        years=years,
        seconds=time.time() - started,
        out_dir=out_dir,
        by_year=summaries,
    )
    _write_manifest(out_dir, result, outlier_threshold_min)
    return result


def _register_static(
    con: Any,
    external_dir: Path,
    fact_path: Path,
    years: tuple[int, ...],
    groups_path: Path | None,
) -> None:
    """Register everything that does not change from year to year."""
    import pandas as pd

    table = groups_mod.GroupTable.load(groups_path or Path(external_dir) / "groups.csv")
    table.register(con)
    fact = pd.read_parquet(fact_path)
    lags = monthly_lags(fact)
    for name, frame in (
        ("cal_tbl", calendar_frame(external_dir, years)),
        ("nodes_tbl", node_frame(external_dir)),
        ("slots_tbl", slot_frame(external_dir)),
        ("dist_tbl", distance_frame(external_dir)),
        ("lag_route", lags.route),
        ("lag_group", lags.group),
        ("lag_node", lags.node),
        ("lag_group_route", lags.group_route),
        ("lag_group_node", lags.group_node),
    ):
        _register(con, name, frame)
    con.execute(
        "CREATE OR REPLACE TEMP TABLE p90_tbl AS "
        "SELECT NULL::VARCHAR AS icao, NULL::DOUBLE AS threshold, "
        "NULL::INTEGER AS n_day_hours WHERE false"
    )


def _register(con: Any, name: str, frame: pd.DataFrame) -> None:
    con.register(f"_{name}_view", frame)
    con.execute(f"CREATE OR REPLACE TEMP TABLE {name} AS SELECT * FROM _{name}_view")
    con.unregister(f"_{name}_view")


def _register_flight_number_lags(con: Any, carry: pd.DataFrame | None) -> pd.DataFrame:
    """The closed three-month flight-number window, and the carry for next year.

    The window for month t is t-3, t-2, t-1. Two of those months can belong to
    the year being built, so the year's own monthly counts are computed from the
    materialised scan and appended to the tail carried over from the previous
    iteration -- never by re-reading last year's parquet.
    """
    import pandas as pd

    current = con.execute(flight_number_sql()).df()
    store = current if carry is None else pd.concat([carry, current], ignore_index=True)
    store = store.groupby(["airline", "flight_number", "ym"], as_index=False, observed=True).sum()
    shifted = [store.assign(ym=_shift_ym(store["ym"], lag)) for lag in (1, 2, 3)]
    window = pd.concat(shifted, ignore_index=True)
    window = window.groupby(["airline", "flight_number", "ym"], as_index=False, observed=True).sum()
    window["late15"] = _rate(window["late"], window["obs"])
    _register(con, "lag_flight_number", window[["airline", "flight_number", "ym", "late15", "obs"]])
    keep = sorted(store["ym"].unique())[-3:]
    return pd.DataFrame(store[store["ym"].isin(keep)])


def _finalise(frame: pd.DataFrame) -> pd.DataFrame:
    """Tight dtypes and the declared column order."""
    for name, dtype in DTYPES.items():
        if name in frame.columns:
            if dtype.startswith("int"):
                frame[name] = frame[name].fillna(0).astype(dtype)
            else:
                frame[name] = frame[name].astype(dtype)
    for name in CATEGORICAL:
        frame[name] = frame[name].astype("category")
    floats = [
        name
        for name in frame.columns
        if name not in DTYPES and name not in CATEGORICAL and name not in {"flight_date", "route"}
    ]
    for name in floats:
        frame[name] = frame[name].astype("float32")
    frame["route"] = frame["route"].astype("category")
    return frame[list(DATASET_COLUMNS)]


def _summarise(year: int, frame: pd.DataFrame, universe_rows: int, no_schedule: int) -> YearSummary:
    """The per-year accounting ADR-0015 and ADR-0017 both need.

    `target_excluded_missing_actual` is what reading B does **not** cover: a
    realised flight with no actual arrival time whose carrier is `other` or
    unlabelled, so the null stays a null. `on_time_no_bav` is what it does
    cover.
    """
    target = frame["late15_arr"].notna()
    realized = frame["is_realized"]
    suspect = frame["actual_time_suspect"]
    no_bav = frame["on_time_no_bav"]
    linked = frame["prev_leg"] == 1
    known = frame.loc[linked, "prev_arr_known_h1"]
    prev_known = frame.loc[linked, "prev_arr_delay_min"].notna()
    return YearSummary(
        year=int(year),
        rows=len(frame),
        universe_rows=universe_rows,
        realized=int(realized.sum()),
        cancelled=int(frame["cancelled"].sum()),
        dropped_no_schedule=no_schedule,
        target_rows=int(target.sum()),
        target_excluded_missing_actual=int((realized & ~target & ~suspect).sum()),
        target_excluded_suspect=int((realized & suspect).sum()),
        on_time_no_bav=int(no_bav.sum()),
        on_time_no_bav_share=float((no_bav & realized).sum() / realized.sum())
        if realized.any()
        else None,
        realized_no_arr_actual=int((realized & ~frame["has_arr_actual"]).sum()),
        late15_arr_rate=float(frame.loc[target, "late15_arr"].mean()) if target.any() else None,
        cancelled_rate=float(frame["cancelled"].mean()) if len(frame) else None,
        prev_leg_share=float(linked.mean()) if len(frame) else 0.0,
        prev_arr_known_share=float(prev_known.mean()) if linked.any() else None,
        prev_arr_known_h1_share=float(known.mean()) if known.notna().any() else None,
    )


def _write_year(frame: pd.DataFrame, out_dir: Path, year: int) -> Path:
    """Parquet, zstd 9 (ADR-0004), with ``flight_date`` narrowed to date32.

    DuckDB hands the date back as a microsecond timestamp and pyarrow would keep
    it that way; the registry declares a date, and eight bytes per row for a
    field with no time in it is eight bytes per row of noise.
    """
    import pyarrow as pa
    import pyarrow.parquet as pq

    directory = Path(out_dir) / f"year={year}"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "part-0.parquet"
    table = pa.Table.from_pandas(frame, preserve_index=False)
    index = table.schema.get_field_index("flight_date")
    table = table.set_column(
        index, pa.field("flight_date", pa.date32()), table.column(index).cast(pa.date32())
    )
    pq.write_table(table, path, compression="zstd", compression_level=9)
    return path


def _write_manifest(out_dir: Path, result: BuildResult, threshold: float) -> Path:
    path = Path(out_dir) / "manifest.json"
    document = {
        "layer": "ml",
        "grain": (
            "one row per scheduled flight of the replication universe "
            "(ADR-0002), pre-departure features only"
        ),
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "git_commit": stage_mod.git_commit(REPO_ROOT, short=True),
        "tool_versions": stage_mod.tool_versions(),
        "reading": "B (ADR-0017): empty actual time on a realised in-scope flight is no alteration",
        "bav_last_legacy_year": BAV_LAST_LEGACY_YEAR,
        "bav_classes": list(BAV_CLASSES),
        "outlier_threshold_min": threshold,
        "late_threshold_min": LATE_MIN,
        "suspect_delay_min": SUSPECT_DELAY_MIN,
        "rows": result.rows,
        "years": list(result.years),
        "seconds": round(result.seconds, 2),
        "features_d1": list(FEATURES_D1),
        "features_h1_only": list(FEATURES_H1_ONLY),
        "targets": list(TARGETS),
        "by_year": [row.as_dict() for row in result.by_year],
    }
    path.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


# ------------------------------------------------------------------------ read


def read_dataset(
    dataset_dir: Path = DATASET_DIR,
    years: tuple[int, ...] | None = None,
    columns: list[str] | None = None,
) -> pd.DataFrame:
    """Read whole years of the modelling table, with the categories realigned.

    Reading year by year gives each partition its own category dictionary, so
    the concatenation has to re-cast: XGBoost's ``enable_categorical`` compares
    category *codes*, and two frames whose dictionaries differ would silently
    mean different airlines by the same code.
    """
    import pandas as pd

    dataset_dir = Path(dataset_dir)
    found = sorted(
        int(path.name.split("=")[1])
        for path in dataset_dir.glob("year=*")
        if path.is_dir() and path.name.split("=")[1].isdigit()
    )
    if not found:
        raise FileNotFoundError(f"no year=YYYY partitions under {dataset_dir}; run `just ml`")
    wanted = [year for year in found if years is None or year in set(years)]
    if not wanted:
        raise FileNotFoundError(f"none of the years {years} exist under {dataset_dir}")
    parts = [
        _read_year(dataset_dir / f"year={year}" / "part-0.parquet", columns) for year in wanted
    ]
    return pd.concat(align_categories(parts), ignore_index=True)


def _read_year(path: Path, columns: list[str] | None) -> pd.DataFrame:
    """One partition, with ``flight_date`` as a datetime rather than 5 M date objects."""
    import pyarrow.parquet as pq

    return pq.read_table(path, columns=columns).to_pandas(date_as_object=False)


def align_categories(frames: list[pd.DataFrame]) -> list[pd.DataFrame]:
    """Give every frame one shared dictionary per categorical column.

    Without this ``pd.concat`` falls back to ``object`` -- 5 million Python
    strings per column -- and, worse, a frame built from one year and scored by
    a model trained on another would compare category *codes* that mean
    different airlines. Unioning the categories first is both the cheap path and
    the correct one.
    """
    import pandas as pd

    categorical = [name for name in frames[0].columns if str(frames[0][name].dtype) == "category"]
    for name in categorical:
        levels = pd.api.types.union_categoricals(
            [frame[name] for frame in frames], ignore_order=True
        ).categories
        for frame in frames:
            frame[name] = frame[name].cat.set_categories(levels)
    return frames


__all__ = [
    "BINARY_TARGETS",
    "CATEGORICAL",
    "DATASET_COLUMNS",
    "DATASET_DIR",
    "FEATURES_D1",
    "FEATURES_H1",
    "FEATURES_H1_ONLY",
    "POST_DEPARTURE_STAGED",
    "SUSPECT_DELAY_MIN",
    "TARGETS",
    "BuildResult",
    "LagTables",
    "YearSummary",
    "align_categories",
    "build_dataset",
    "calendar_frame",
    "collapse_fact",
    "monthly_lags",
    "read_dataset",
]
