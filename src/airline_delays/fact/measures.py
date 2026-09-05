"""The measures of the fact table: keys, the delay counts and sums per side and threshold, the
scheduled-hour columns and the context measures a fact table cannot carry (ADR-0004)."""

from __future__ import annotations

from typing import Literal

from airline_delays.definitions import cause_codes as cause_codes_mod
from airline_delays.definitions import delays as delays_mod
from airline_delays.definitions import universe as universe_mod

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

FACT_UNIQUE_KEY: tuple[str, ...] = ("group", "route", "ym")

"""ADR-0016: the fact table's key, unique by construction and by test."""

ROUTE_MONTH_KEY: tuple[str, ...] = ("route", "ym")

"""ADR-0016: the key of the route-month context, the projection and the panel."""

CITY_MONTH_KEY: tuple[str, ...] = ("node", "ym")

"""ADR-0016: the key of the city-month projection."""

AIRLINE_CITY_MONTH_KEY: tuple[str, ...] = ("group", "node", "ym")

"""ADR-0016: the key of the airline-city-month projection."""

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

    The outlier rule is symmetric (ADR-0015): the counts of delayed flights are
    untouched, and every **sum of minutes** is taken over
    ``abs(delay) < threshold``, so a month typo cannot enter a sum from either
    tail. ``{side}_outliers`` counts both tails for the same reason.
    """
    delay = f"{side}_delay_min"
    actual = f"actual_{'dep' if side == 'dep' else 'arr'}"
    scheduled = f"sched_{'dep' if side == 'dep' else 'arr'}"
    live = f"is_realized AND {delay} IS NOT NULL"
    trimmed = f"{live} AND {delays_mod.within_threshold_sql(delay, threshold)}"
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
        f"{side}_outliers": (
            f"count(*) FILTER (WHERE {live} AND {delays_mod.is_outlier_sql(delay, threshold)})"
        ),
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
    for category in cause_codes_mod.CATEGORY_NAMES:
        measures[f"cause_{category}"] = (
            f"count(*) FILTER (WHERE {cause_codes_mod.category_sql('cause_code', category)})"
        )
    for set_name in cause_codes_mod.ARTICLE_SETS:
        measures[f"cause_set_{set_name}"] = (
            f"count(*) FILTER (WHERE {cause_codes_mod.article_set_sql('cause_code', set_name)})"
        )
    for name, cancel_codes in CANCEL_CAUSES.items():
        measures[name] = (
            f"count(*) FILTER (WHERE status = '{universe_mod.STATUS_CANCELLED}' "
            f"AND {cause_codes_mod.in_sql('cause_code', cancel_codes)})"
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
