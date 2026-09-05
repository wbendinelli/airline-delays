"""Stage 4 -- fact: the canonical `group x route x month` fact table and its projections
(`airline-delays fact`; ADR-0004, ADR-0016)."""

from __future__ import annotations

from .build import (
    BuildResult,
    assert_unique,
    build_fact,
    out_of_window_records,
    out_of_window_rows,
    slim,
    write_table,
    year_source_sql,
)
from .measures import (
    AIRLINE_CITY_MONTH_KEY,
    CANCEL_CAUSES,
    CITY_MONTH_KEY,
    CONTEXT_MEASURES,
    FACT_KEYS,
    FACT_SUM_COLUMNS,
    FACT_UNIQUE_KEY,
    HOUR_COLUMNS,
    HOURS,
    NIGHT_HOURS,
    ROUTE_MONTH_KEY,
    Grain,
    fact_measures,
)
from .projections import (
    add_congestion,
    add_hub,
    aggregate,
    city_month,
    delay_denominator,
)

__all__ = [
    "AIRLINE_CITY_MONTH_KEY",
    "CANCEL_CAUSES",
    "CITY_MONTH_KEY",
    "CONTEXT_MEASURES",
    "FACT_KEYS",
    "FACT_SUM_COLUMNS",
    "FACT_UNIQUE_KEY",
    "HOURS",
    "HOUR_COLUMNS",
    "NIGHT_HOURS",
    "ROUTE_MONTH_KEY",
    "BuildResult",
    "Grain",
    "add_congestion",
    "add_hub",
    "aggregate",
    "assert_unique",
    "build_fact",
    "city_month",
    "delay_denominator",
    "fact_measures",
    "out_of_window_records",
    "out_of_window_rows",
    "slim",
    "write_table",
    "year_source_sql",
]
