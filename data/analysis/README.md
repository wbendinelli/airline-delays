# data/analysis/

The analysis tables of `airline-delays`, **tracked in full** (`DECISIONS.md`
ADR-0014): the fact table, the reconstruction panel and its two city
projections built from `data/staged/` by `just fact` and `just panel`, and the
article's estimation panel -- the panel the authors of Bendinelli, Bettini &
Oliveira (2016, *Transportation Research Part A* 85, 39-52, doi
10.1016/j.tra.2016.01.001) estimated Tables 2-7 on, curated once into this
directory (ADR-0020). A reader runs `just estimate` on a fresh clone without
rebuilding anything. Every column is defined in `docs/dictionary.md`; every
table is a resource of `datapackage.json`.

## What is in git

| File | What it is | Rows x columns | Bytes |
|---|---|---|---|
| `fact_group_route_month.parquet` | airline group x route x month, replication universe. The canonical table (ADR-0004); every other grain is an `aggregate()` projection of it. Unique on `(group, route, ym)` by construction and by test (ADR-0016). | 165,763 x 87 | -- |
| `panel_route_month.parquet` | route x month, 2000-2013, the 27 nodes of ADR-0001: the reconstruction panel, the article's columns that the VRA supports plus the new feature set. Unique on `(route, ym)`. | 31,313 x 228 | 9,941,210 |
| `panel_route_month.csv.gz` | the reconstruction panel in CSV, for readers without a parquet reader (ADR-0004). | 31,313 x 228 | 11,788,959 |
| `article_panel_route_month.parquet` | route x month, 2002-2013: the article's estimation panel, curated from the authors' final base of December 2015 (a Stata file of 24,589 route-months x 1,829 variables). The 52 columns kept are the keys and geography, the flight counts, the six regressands, the exogenous regressors, the concentration terms, the seven instruments and the components of the two low-cost dummies; the route, time and seasonality dummies are rebuilt by code. | 24,589 x 52 | 2,202,177 |
| `article_panel_route_month.csv.gz` | the article's estimation panel in CSV. | 24,589 x 52 | 2,916,686 |
| `city_month.parquet` | city node x month, departures and arrivals both counted, with the congestion proxy of ADR-0007. Unique on `(node, ym)`. | 21,231 x 91 | -- |
| `airline_city_month.parquet` | airline group x city node x month, with the hub share, score and dummy. | 49,801 x 81 | -- |
| `manifest.json` | how the fact table was built: git commit, years, tool versions, the outlier threshold, the ADR-0012 convention, the per-year count of realised flights with no actual time, and the staged rows dated outside the built years (ADR-0016). | -- | -- |
| `panel_manifest.json` | the same for the reconstruction panel: commit, tool versions, shape, the byte sizes of the two files. | -- | -- |
| `article_panel_manifest.json` | the provenance of the article panel: the source's sha256 and header timestamp, the columns kept and excluded, the per-column null counts, the sha256 of both files. Never a path. | -- | -- |

The rows, columns and byte counts above are values of `reports/summary.json`;
the tables without a byte count are described by shape only. Everything stays
under the pre-commit large-file threshold raised for this directory in
ADR-0014; flight-level tables stay out of git regardless of size (ADR-0004).

## Keeping it in sync: `just check-analysis`

A tracked table that no longer matches the code is a silent error.
`just check-analysis` (`pytest -m analysis`, `tests/test_analysis_staleness.py`)
rebuilds the reconstruction panel from the committed fact table in memory and
compares shape, column names and a value checksum with the committed
`panel_route_month.parquet`; it fails on a mismatch and skips when the tables
or `data/derived/` are not present locally. CI's `metadata` job checks in the
same spirit that `docs/dictionary.md`, `datapackage.json` and
`reports/summary.json` are rebuilds of the registry and of these tables.

## Regenerating

```bash
uv run airline-delays fact     # about 11 s: the fact table, the city projections, the day-hour intermediate
uv run airline-delays panel    # about 8 s: the reconstruction panel, parquet and csv.gz
```

Both need `data/staged/`, which `just fetch && just stage` produces from
ANAC's files; `just fact && just panel` runs the pair, then regenerates
`docs/dictionary.md` and `datapackage.json`. The article's estimation panel is
not produced by the pipeline: `airline-delays article-panel` curates it from
the authors' base on the owner's machine only, and the tracked files are the
release (ADR-0020). `data/derived/` holds the two intermediates `just fact`
writes and `just check-analysis` reads (`route_month_context.parquet` and
`node_day_hour.parquet`); they stay git-ignored like the rest of that layer.
