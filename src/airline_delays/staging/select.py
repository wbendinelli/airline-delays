"""The DuckDB SELECT that reads a raw layout positionally and produces the canonical flight columns."""

from __future__ import annotations

from airline_delays.definitions import delays as delays_mod
from airline_delays.definitions import nodes as nodes_mod
from airline_delays.definitions import universe as universe_mod
from airline_delays.ingest import LAYOUT_LEGACY, RawLayout
from airline_delays.staging.clean import DI_LETTERS, LINE_TYPE_NULLS, STATUS_MAP, normalise_text_sql

_LEGACY_POS = {
    "airline": "c0",
    "flight_number": "c1",
    "di": "c2",
    "line_type": "c3",
    "origin_icao": "c4",
    "dest_icao": "c5",
    "sched_dep": "c6",
    "actual_dep": "c7",
    "sched_arr": "c8",
    "actual_arr": "c9",
    "status": "c10",
    "cause": "c11",
}

_WIDE_POS = {
    "airline": "c0",
    "flight_number": "c2",
    "di": "c3",
    "line_type": "c4",
    "origin_icao": "c7",
    "sched_dep": "c9",
    "actual_dep": "c10",
    "dest_icao": "c11",
    "sched_arr": "c13",
    "actual_arr": "c14",
    "status": "c15",
    "cause": "c16",
}


def positions_for(layout: RawLayout) -> dict[str, str]:
    """Map a meaning to the positional column that carries it in `layout`."""
    return dict(_LEGACY_POS) if layout is LAYOUT_LEGACY else dict(_WIDE_POS)


def _read_csv_sql(glob: str, layout: RawLayout) -> str:
    columns = "{" + ", ".join(f"'c{i}': 'VARCHAR'" for i in range(layout.n_columns)) + "}"
    return (
        f"read_csv('{glob}', header=false, skip=1, delim='{layout.separator}', "
        f"quote='', escape='', encoding='{layout.encoding}', columns={columns}, "
        "ignore_errors=true, filename=true)"
    )


def _cause_case(pos: dict[str, str], layout: RawLayout) -> str:
    """SQL for the two-letter cause code, per layout."""
    raw = f"upper(trim({pos['cause']}))"
    if layout.cause_is_code:
        return (
            f"CASE WHEN {raw} IS NULL OR {raw} IN ('', 'N/A', 'NA') THEN NULL "
            f"WHEN regexp_matches({raw}, '^[A-Z]{{2}}$') THEN {raw} ELSE NULL END"
        )
    return "cause_text_map.code"


def build_select(glob: str, layout: RawLayout, with_groups: bool = False) -> str:
    """The SELECT that turns one year of raw CSV into the staged schema.

    With `with_groups`, `group` and `class` come from the temporary table
    `groups_tbl` that `_register_groups` builds; without it they are null and
    `airline_delays.definitions.carriers` fills them later.
    """
    pos = positions_for(layout)
    status_case = (
        "CASE upper(trim({col})) "
        + " ".join(f"WHEN '{raw}' THEN '{clean}'" for raw, clean in STATUS_MAP.items())
        + f" ELSE '{universe_mod.STATUS_OTHER}' END"
    ).format(col=pos["status"])
    di_case = (
        f"CASE WHEN regexp_matches(upper(trim({pos['di']})), '^[0-9]$') "
        f"THEN CAST(trim({pos['di']}) AS TINYINT) "
        + " ".join(
            f"WHEN upper(trim({pos['di']})) = '{letter}' THEN CAST({value} AS TINYINT)"
            for letter, value in DI_LETTERS.items()
        )
        + " ELSE NULL END"
    )
    line_type_case = (
        f"CASE WHEN upper(trim({pos['line_type']})) IN ("
        + ", ".join(f"'{value}'" for value in LINE_TYPE_NULLS)
        + f") THEN NULL ELSE nullif(upper(trim({pos['line_type']})), '') END"
    )
    fmt = layout.datetime_format

    def ts(col: str) -> str:
        return f"try_strptime(nullif(trim({col}), ''), '{fmt}')"

    # ADR-0015, written at staging so that every consumer reads one definition
    # rather than recomputing the rule on the delay columns it happens to hold.
    suspect = delays_mod.suspect_time_sql(
        delays_mod.signed_delay_sql("sched_dep", "actual_dep"),
        delays_mod.signed_delay_sql("sched_arr", "actual_arr"),
    )

    group_select = 'CAST(NULL AS VARCHAR) AS "group",\n    CAST(NULL AS VARCHAR) AS "class"'
    group_join = ""
    if with_groups:
        group_select = 'g."group" AS "group",\n    g."class" AS "class"'
        # The groups table is dated to the month (ADR-0003), so the interval
        # test runs on the year-month key, never on the day.
        group_join = (
            " LEFT JOIN groups_tbl g ON g.airline = dated.airline "
            "AND (g.start_ym IS NULL OR (year(dated.flight_date) * 100 + month(dated.flight_date)) >= g.start_ym) "
            "AND (g.end_ym IS NULL OR (year(dated.flight_date) * 100 + month(dated.flight_date)) <= g.end_ym)"
        )

    join = ""
    if not layout.cause_is_code:
        join = (
            " LEFT JOIN cause_text_map ON cause_text_map.text_key = "
            f"{normalise_text_sql(pos['cause'])} "
            f"AND cause_text_map.cancelled = ({status_case} = '{universe_mod.STATUS_CANCELLED}')"
        )

    return f"""
WITH src AS (
    SELECT * FROM {_read_csv_sql(glob, layout)}
),
typed AS (
    SELECT
        nullif(upper(trim({pos["airline"]})), '')                       AS airline,
        TRY_CAST(trim({pos["flight_number"]}) AS INTEGER)               AS flight_number,
        {line_type_case}                                                AS line_type,
        {di_case}                                                       AS di,
        nullif(upper(trim({pos["origin_icao"]})), '')                   AS origin_icao,
        nullif(upper(trim({pos["dest_icao"]})), '')                     AS dest_icao,
        {status_case}                                                   AS status,
        {_cause_case(pos, layout)}                                      AS cause_code,
        CAST({ts(pos["sched_dep"])} AS TIMESTAMP_S)                     AS sched_dep,
        CAST({ts(pos["actual_dep"])} AS TIMESTAMP_S)                    AS actual_dep,
        CAST({ts(pos["sched_arr"])} AS TIMESTAMP_S)                     AS sched_arr,
        CAST({ts(pos["actual_arr"])} AS TIMESTAMP_S)                    AS actual_arr
    FROM src{join}
),
dated AS (
    SELECT *,
        CAST(coalesce(sched_dep, actual_dep) AS DATE) AS flight_date,
        coalesce(sched_dep, actual_dep)               AS dep_ref,
        coalesce(sched_arr, actual_arr)               AS arr_ref
    FROM typed
)
SELECT
    dated.flight_date AS flight_date,
    CAST(year(dated.flight_date) AS SMALLINT)                                     AS year,
    CAST(month(dated.flight_date) AS TINYINT)                                     AS month,
    CAST(year(dated.flight_date) * 100 + month(dated.flight_date) AS INTEGER)           AS ym,
    dated.airline AS airline,
    dated.flight_number AS flight_number,
    dated.line_type AS line_type,
    dated.di AS di,
    dated.origin_icao AS origin_icao,
    dated.dest_icao AS dest_icao,
    {nodes_mod.node_sql("origin_icao")}                                      AS origin_node,
    {nodes_mod.node_sql("dest_icao")}                                        AS dest_node,
    {nodes_mod.node_sql("origin_icao")} || '-' || {nodes_mod.node_sql("dest_icao")} AS route,
    dated.status AS status,
    dated.cause_code AS cause_code,
    dated.sched_dep AS sched_dep,
    dated.actual_dep AS actual_dep,
    dated.sched_arr AS sched_arr,
    dated.actual_arr AS actual_arr,
    {delays_mod.signed_delay_sql("sched_dep", "actual_dep")}                AS dep_delay_min,
    {delays_mod.signed_delay_sql("sched_arr", "actual_arr")}                AS arr_delay_min,
    {delays_mod.block_sql("sched_dep", "sched_arr")}                        AS sched_block_min,
    {delays_mod.block_sql("actual_dep", "actual_arr")}                      AS actual_block_min,
    CAST(hour(dated.dep_ref) AS TINYINT)                                          AS dep_hour,
    CAST(hour(dated.arr_ref) AS TINYINT)                                          AS arr_hour,
    CAST((dayofweek(dated.flight_date) + 6) % 7 AS TINYINT)                       AS dow,
    {group_select},
    {universe_mod.UNIVERSE_REPL_SQL}                                        AS universe_repl,
    {universe_mod.UNIVERSE_ML_SQL}                                          AS universe_ml,
    dated.status = '{universe_mod.STATUS_REALIZED}'                               AS is_realized,
    {suspect}                                                               AS actual_time_suspect
FROM dated{group_join}
"""
