# sql/

DuckDB views over the parquet layers -- the staged flights under `data/staged/`,
the fact table, the city projections, the reconstruction panel and the article's
estimation panel under `data/analysis/`, and the reference tables under
`data/external/` -- in `views.sql`, read directly by `duckdb` or from Python
through `airline_delays.staging.connect()`. No `.duckdb` database file is ever
committed (see `.gitignore` and `DECISIONS.md` ADR-0004): a view is a query over
parquet, not a copy of the data, so it stays in step with whatever
`data/staged/` and `data/analysis/` currently hold on disk. Paths in the views
are relative to the repository root, so run from there.
