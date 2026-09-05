# data/analysis/

Route-month and city-month tables built from `data/staged/` by
`just features` and `just panel`. Unlike `data/raw/`, `data/staged/` and
`data/derived/`, this directory is **tracked** — but only its provenance
files are, because the tables themselves are too large for the build brief's
"analysis tables under a few MB" rule.

## What is in git

| File | Size | What it is |
|---|---|---|
| `manifest.json` | 4 KB | How the fact table was built: years, tool versions, outlier threshold, the ADR-0012 convention, and the per-year count of realised flights with no actual time. |
| `panel_manifest.json` | < 1 KB | The same for the panel, plus the byte sizes of the two files it wrote. |
| `taxas.csv` | 8 KB | Column-by-column agreement against the private benchmark, written by `replication/gabarito/compare.py`. Statistics only — no benchmark value is ever copied here. |

## What is not, and how to get it back

```bash
uv run vra features   # ~12 s: the fact table, the city projections, the day-hour table
uv run vra panel      # ~10 s: the public route-month panel, parquet and csv.gz
```

| File | Size | Grain |
|---|---|---|
| `fact_group_route_month.parquet` | ~8 MB | group x route x month, replication universe. The canonical table (ADR-0004); every other grain is an `aggregate()` projection of it. |
| `panel_route_month.parquet` | ~10 MB | route x month, the 27 nodes of ADR-0001. The public deliverable: the article's columns plus the new feature set. |
| `panel_route_month.csv.gz` | ~12 MB | The same panel in CSV, for readers without a parquet reader (ADR-0004). |
| `city_month.parquet` | ~2 MB | node x month, departures and arrivals both counted, with the ADR-0007 congestion proxy. |
| `airline_city_month.parquet` | ~4 MB | group x node x month, with the hub share, score and dummy. |

Both commands need `data/staged/`, which `just fetch && just stage` produces
from ANAC's published files. At publication the five tables go to Zenodo
alongside the flight table, which is where ADR-0004 sends data that does not
belong in git.

`data/derived/` holds two intermediates these commands write and read —
`route_month_context.parquet` (route-month counts outside the replication
universe, plus the order statistics a fact table cannot carry) and
`node_day_hour.parquet` (movements per node, day and scheduled hour, the input
to the congestion proxy). They are git-ignored like the rest of that layer.
