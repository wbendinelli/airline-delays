# sql/

DuckDB views over the parquet layers (`data/staged/`, the fact table, the
replication panel) -- `views.sql`, read directly by `duckdb` or by
`src/vra/` through the `duckdb` Python package. No `.duckdb` database file
is ever committed (see `.gitignore` and `DECISIONS.md` ADR-0004): a view is
a query over parquet, not a copy of the data, so it stays in sync with
whatever `data/staged/`/`data/derived/` currently hold on disk.
