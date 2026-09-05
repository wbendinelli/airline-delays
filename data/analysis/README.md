# data/analysis/

Route-month and city-month tables built from `data/staged/` by
`just fact` and `just panel`. Unlike `data/raw/`, `data/staged/` and
`data/derived/`, this directory is **tracked in full**: since DECISIONS.md
ADR-0014 its `*.parquet` and `*.csv.gz` tables are committed alongside their
provenance files, so a reviewer can run the public replication (`just
replicate`) without rebuilding anything first.

## What is in git

| File | Size | What it is |
|---|---|---|
| `fact_group_route_month.parquet` | ~8 MB | group x route x month, replication universe. The canonical table (ADR-0004); every other grain is an `aggregate()` projection of it. Unique on `(group, route, ym)` by construction and by test (ADR-0016). |
| `panel_route_month.parquet` | ~10 MB | route x month, the 27 nodes of ADR-0001. The public deliverable: the article's columns plus the new feature set. |
| `panel_route_month.csv.gz` | ~12 MB | The same panel in CSV, for readers without a parquet reader (ADR-0004). |
| `city_month.parquet` | ~2 MB | node x month, departures and arrivals both counted, with the ADR-0007 congestion proxy. |
| `airline_city_month.parquet` | ~4 MB | group x node x month, with the hub share, score and dummy. |
| `manifest.json` | 5 KB | How the fact table was built: the git commit, years, tool versions, outlier threshold, the ADR-0012 convention, the per-year count of realised flights with no actual time, and `rows_outside_years` — the staged rows dated outside the years built, which ADR-0016 counts rather than folds into a neighbouring year. |
| `panel_manifest.json` | < 1 KB | The same for the panel: git commit, tool versions, row/column counts and the byte sizes of the two files it wrote. |

All seven files sit well under the pre-commit `check-added-large-files`
threshold (50 MB, raised for exactly this in ADR-0014); the flight-level
table stays out of git regardless of size (ADR-0004) and goes to Zenodo
instead.

## Keeping it in sync: `just check-analysis`

Because these tables are committed, a stale one is a silent bug: edit
`schema/columns.py` or `panel/build.py`, forget to rerun `just panel`, and the tracked
file no longer matches what the current code would produce. `just
check-analysis` (a `pytest -m analysis` run, see
`tests/test_analysis_staleness.py`) rebuilds the panel from the committed
`fact_group_route_month.parquet` in memory and compares its shape, column
names and a value checksum against the committed
`panel_route_month.parquet`; it fails loudly on a mismatch and skips (not
fails) when the tables or `data/derived/` are not present locally.

## Regenerating from scratch

```bash
uv run airline-delays fact    # ~12 s: the fact table, the city projections, the day-hour table
uv run airline-delays panel   # ~10 s: the reconstruction panel, parquet and csv.gz
```

Both commands need `data/staged/`, which `just fetch && just stage` produces
from ANAC's published files. `just fact && just panel` runs the pair in
about 22 seconds and is what regenerates every file in the table above.

`data/derived/` holds two intermediates these commands write and read —
`route_month_context.parquet` (route-month counts outside the replication
universe, plus the order statistics a fact table cannot carry) and
`node_day_hour.parquet` (movements per node, day and scheduled hour, the input
to the congestion proxy). They stay git-ignored like the rest of that layer
(ADR-0004): they are inputs `just check-analysis` needs to rebuild the panel,
not a deliverable in their own right, and they are cheap to regenerate
alongside everything else here.
