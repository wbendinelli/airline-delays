-- DuckDB views over the parquet layers of this repository.
--
-- A view is a query over parquet, not a copy of the data, so it stays in step
-- with whatever data/staged/ and data/analysis/ currently hold. No .duckdb file
-- is ever committed (ADR-0004).
--
--   duckdb -c ".read sql/views.sql" -c "SELECT * FROM v_panel LIMIT 5"
--
-- or, from Python:
--
--   con = vra.stage.connect(); con.execute(open("sql/views.sql").read())
--
-- Paths are relative to the repository root, so run from there.

-- ---------------------------------------------------------------- staged flights
--
-- hive_partitioning=false is load-bearing: the directory name `year=YYYY` would
-- otherwise add a second `year` column shadowing the one derived from
-- flight_date, and every year filter would silently read the partition name
-- instead of the data.

CREATE OR REPLACE VIEW v_flights AS
SELECT *
FROM read_parquet('data/staged/year=*/*.parquet', hive_partitioning = false);

-- The replication universe of ADR-0002: line types N, R and E with DI 0,
-- realised and cancelled both counted.
CREATE OR REPLACE VIEW v_flights_repl AS
SELECT * FROM v_flights WHERE universe_repl;

-- The prediction universe: the realised flights of the same universe.
CREATE OR REPLACE VIEW v_flights_ml AS
SELECT * FROM v_flights WHERE universe_ml;

-- ------------------------------------------------------------------ fact table
--
-- The canonical grain: one row per group x route x month over the replication
-- universe. Everything below is a projection of this, never a second scan.

CREATE OR REPLACE VIEW v_fact AS
SELECT * FROM read_parquet('data/analysis/fact_group_route_month.parquet');

-- Route-month sums, the additive half of what `vra.features.aggregate` returns.
-- The proportions are deliberately absent: a share of sums is not the sum of
-- shares, and recomputing them belongs in one place (ADR-0004).
CREATE OR REPLACE VIEW v_route_month AS
SELECT
    ym,
    year,
    month,
    route,
    origin_node,
    dest_node,
    count(DISTINCT "group")                    AS n_groups,
    sum(flights)                               AS f,
    sum(realized)                              AS fl_real,
    sum(flights) - sum(realized)               AS fl_can,
    sum(dep_delayed_gt0)                       AS fl_odel,
    sum(arr_delayed_gt0)                       AS fl_ddel,
    sum(arr_delayed_gt15)                      AS arr_delayed_gt15,
    sum(arr_delay_obs)                         AS arr_delay_obs,
    sum(arr_missing_actual)                    AS arr_missing_actual,
    sum(sum_arr_delay_min)                     AS sum_arr_delay_min,
    sum(cause_set_prwheather)                  AS cause_set_prwheather,
    sum(cause_set_princident)                  AS cause_set_princident,
    sum(cause_set_pr_connc)                    AS cause_set_pr_connc
FROM v_fact
GROUP BY ym, year, month, route, origin_node, dest_node;

-- Flight-share concentration on the route-month, straight from the group rows.
CREATE OR REPLACE VIEW v_route_hhi AS
SELECT
    ym,
    route,
    sum(flights::DOUBLE * flights) / nullif(sum(flights)::DOUBLE * sum(flights), 0) AS hhi_flights,
    max(flights)::DOUBLE / nullif(sum(flights)::DOUBLE, 0)                          AS sh_leader
FROM v_fact
WHERE flights > 0
GROUP BY ym, route;

-- A city sees each flight twice: once as a departure at the origin node and
-- once as an arrival at the destination. Both sides are unioned, then summed.
CREATE OR REPLACE VIEW v_node_movements AS
SELECT origin_node AS node, ym, year, month, "group", "class", flights, realized, cancelled,
       dep_delayed_gt15 AS delayed_gt15, 'departure' AS side
FROM v_fact
UNION ALL
SELECT dest_node AS node, ym, year, month, "group", "class", flights, realized, cancelled,
       arr_delayed_gt15 AS delayed_gt15, 'arrival' AS side
FROM v_fact;

CREATE OR REPLACE VIEW v_city_month AS
SELECT
    node,
    ym,
    year,
    month,
    sum(flights)          AS movements,
    sum(realized)         AS movements_realized,
    sum(cancelled)        AS movements_cancelled,
    sum(delayed_gt15)     AS movements_delayed_gt15,
    count(DISTINCT "group") AS n_groups
FROM v_node_movements
GROUP BY node, ym, year, month;

-- ----------------------------------------------------------------- public panel

CREATE OR REPLACE VIEW v_panel AS
SELECT * FROM read_parquet('data/analysis/panel_route_month.parquet');

-- The article's own regression sample: the 27 nodes, 2002-2013, route-months
-- with at least one scheduled flight.
CREATE OR REPLACE VIEW v_panel_article AS
SELECT * FROM v_panel WHERE ym BETWEEN 200201 AND 201312 AND f > 0;

-- ------------------------------------------------------------------ city tables

CREATE OR REPLACE VIEW v_city AS
SELECT * FROM read_parquet('data/analysis/city_month.parquet');

CREATE OR REPLACE VIEW v_airline_city AS
SELECT * FROM read_parquet('data/analysis/airline_city_month.parquet');

CREATE OR REPLACE VIEW v_hubs AS
SELECT ym, node, "group", movements, city_share, hub_score
FROM v_airline_city
WHERE is_hub = 1;

-- --------------------------------------------------------------- reference data

CREATE OR REPLACE VIEW v_groups AS
SELECT * FROM read_csv('data/external/groups.csv', header = true, auto_detect = true);

CREATE OR REPLACE VIEW v_cause_codes AS
SELECT * FROM read_csv('data/external/cause_codes.csv', header = true, auto_detect = true);

CREATE OR REPLACE VIEW v_nodes AS
SELECT * FROM read_csv('data/external/nodes.csv', header = true, auto_detect = true);

CREATE OR REPLACE VIEW v_distances AS
SELECT * FROM read_csv('data/external/distances_km.csv', header = true, auto_detect = true);

-- ------------------------------------------------------------------- one check
--
-- Additivity, as one query: the fact table summed to route-month must equal the
-- flights counted straight from the staged rows. Any row returned is a bug.

CREATE OR REPLACE VIEW v_check_additivity AS
SELECT
    a.ym,
    a.route,
    a.f          AS fact_flights,
    b.n_flights  AS staged_flights
FROM v_route_month a
FULL OUTER JOIN (
    SELECT ym, route, count(*) AS n_flights
    FROM v_flights_repl
    WHERE route IS NOT NULL AND ym IS NOT NULL
    GROUP BY ym, route
) b USING (ym, route)
WHERE a.f IS DISTINCT FROM b.n_flights;
