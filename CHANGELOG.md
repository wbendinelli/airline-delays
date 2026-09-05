# Changelog

All notable changes to this repository are documented here. The format
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). This
project does not follow semantic-version releases (tier C, no package
consumed by another repository — see `.sapians-repo.yml`); dates, not
version numbers, mark progress.

## [Unreleased]

### Added

- Flight-level delay prediction (`ml/`, `just ml`, `reports/prediction/`,
  `reports/prediction.typ`, `docs/notes/prediction.md`). `ml/dataset_flights.py`
  makes one DuckDB scan per staged year and writes
  `data/derived/ml/year=YYYY/part-0.parquet`: 10,200,578 rows, one per
  **scheduled** flight of the replication universe (ADR-0002), 46 pre-departure
  features for the D-1 horizon plus 3 inbound-leg features for H-1, five
  targets, 313 MB in about 33 seconds. The delay targets are null where
  ADR-0012 leaves no actual timestamp (4.97 M of the 10.2 M rows keep one) and
  where ADR-0015 marks the timestamp suspect (|delay| >= 1,440 minutes: 5,349
  flights, 0.1%); `cancelled` is defined on every row, because the table is the
  scheduled universe. Every column is registered under the new
  `ml` layer of `src/vra/registry.py` and described in `docs/dictionary.md` and
  `datapackage.json`; the table itself stays out of git (ADR-0004), so the
  resource is a description of a table the reader rebuilds. `ml/split.py` holds
  the rolling origin 2006-2013 and the fixed 2002-2010 / 2011 / 2012-2013 split
  of ADR-0009, plus route-hash subsampling that keeps whole routes together;
  `ml/train_xgb.py` fits XGBoost `hist` with early stopping on each fold's
  validation year (LightGBM optional); `ml/evaluate.py` reports AUC, PR-AUC,
  Brier, a calibration table, the two naive baselines and permutation
  importance; `ml/run.py` writes `reports/prediction/*.json` and `results.md`.

- Leakage rule as executable checks (`ml/leakage_tests.py`,
  `tests/test_leakage.py`, `reports/prediction/leakage.json`). Nine checks run
  on the committed fixture in the test suite and on the real dataset in
  `just ml`: no post-departure column in either horizon's feature list, targets
  and diagnostics kept out of both, D-1 a strict subset of H-1 whose additions
  are all about the inbound leg, every lagged rate equal to the fact table's
  `t-1` value and not its `t` value, the airport day-hour movement counts
  recounted from the staged **schedule**, the rotation link scheduled to land
  before the flight departs, no target where ADR-0012 leaves no actual
  timestamp, no busy-hour flag in the build's first year, and holidays taken
  from `data/external/holidays.csv` by date. A tenth test plants a leak (the
  same month's route prevalence) and asserts the checks catch it.

- `data/analysis/*.parquet` and `*.csv.gz` are tracked in git (`DECISIONS.md`
  ADR-0014): the fact table and panel run 8-12 MB, city and airline-city
  projections 2-4 MB, all under the pre-commit `check-added-large-files`
  threshold, raised from 5 MB to 50 MB (`.pre-commit-config.yaml`) to match; a
  reviewer can now run `just replicate` without rebuilding anything first.
  `just check-analysis` (`pytest -m analysis`, new
  `tests/test_analysis_staleness.py`) rebuilds the panel from the committed
  fact table in memory and fails a commit whose shape, column names or a
  value checksum drift from `data/analysis/panel_route_month.parquet`; it
  skips, never fails, when `data/derived/` is not present locally, which is
  the ordinary CI job (no `data/staged/`, per `CLAUDE.md`). `manifest.json`
  and `panel_manifest.json` now carry the short git commit that built them
  (`vra.stage.git_commit(..., short=True)`, `.gitattributes` marks the four
  tracked binary tables `linguist-generated`).

- Feature and panel layer (`src/vra/{groups,codes,hhi,congestion,hub,features,panel}.py`,
  `sql/views.sql`): `vra features` builds the canonical fact table
  `group x route x month` over the replication universe -- 166,203 cells, 87
  columns, one pass per year over the 13.6 M staged legs in about 12 s -- plus
  the city-month and airline-city-month projections; `vra panel` assembles the
  public route-month panel (31,760 route-months x 228 columns over the 27 nodes
  of ADR-0001) with the article's own column names, the declared variants and
  the new feature families. `aggregate(fact, grain)` is the only path to a
  coarser grain and is tested for additivity against a direct count from the
  flights (ADR-0004); the same check ships as the `v_check_additivity` view and
  returns zero rows on the full series. New definitions: dated airline groups
  and the four classes of ADR-0011 (`groups.py`), the article's three
  justification sets alongside the ADR-0005 taxonomy (`codes.py`), flight-share
  concentration with a passenger-weighted placeholder that returns null until
  ANAC's traffic data exist (`hhi.py`), the ADR-0007 p90 congestion proxy
  (`congestion.py`), and a hub score with the volume floors that stop a
  four-flight regional from outranking Gol in Rio (`hub.py`). `vra refs`
  validates `data/external` row by row against the ADRs the tables encode.

- `legacy_missing_actual_as_zero` (ADR-0012) in `delays.effective_delay_min` /
  `effective_delay_sql` and threaded through `features` and `panel`: `True` for
  the replication panel, `False` for the prediction layer. The fact table stays
  convention-free -- it carries both the observed and the missing-actual counts
  -- and the flag selects the **denominator** of every proportion and mean,
  never a count and never a sum, which the test suite pins. Per-year share of
  realised flights with no actual time, from the full series: 80.1% (2000)
  falling to 59.2% (2007), back to 77.7% (2009), then 0.01% or less from 2010
  on, when the raw layout changed.

- Benchmark comparison (`replication/gabarito/compare.py`, the only reader of
  `AIRLINE_DELAYS_PRIVATE_DIR`): writes `data/analysis/taxas.csv` and the
  generated block of `docs/declared-differences.md` with agreement rates,
  median and p90 absolute differences and row counts -- statistics only, with a
  structural guard that refuses to write anything else. Measured on 24,929
  comparable route-months: `maxalccfu`, `olccfu` and `dlccfu` at 1.000, `f` at
  0.953 and `fscb_prdelarr` at 0.649 on the stable-vintage half against the
  0.975 and 0.651 the earlier reconstruction reported from the 2019 vintage of
  the raw files. `taxas.csv` reports both a headline rate and a
  `rate_stable_vintage`, because the shortfall is the raw files having changed
  since 2019, not the definitions: agreement on `f` is 0.94-0.97 in the three
  quietest quartiles of vintage drift and 0.74 in the noisiest, correlation
  -0.45.

- Generated documentation: `docs/dictionary.md` (518 columns across five layers)
  and `datapackage.json` (Frictionless v2, four resources) are produced from
  `src/vra/registry.py` by `vra dictionary` and `vra datapackage` and are never
  hand-edited. The registry gained entries for every column of the fact, city,
  airline-city and panel layers, generated from one description resolver and
  checked in both directions against the tables actually built.

- Research note `docs/notes/features.md` (Portuguese) and the panel section of
  `docs/declared-differences.md`: the vintage effect, the FSC class against the
  article's FSC group set, the two delay conventions, and what the VRA cannot
  produce.

- Replication layer (`replication/`): Tables 2-7 of Bendinelli, Bettini &
  Oliveira (2016) reproduced column by column. `common.py` holds the `Source`
  switch (private benchmark through `AIRLINE_DELAYS_PRIVATE_DIR`, or the public
  `data/analysis/panel_route_month.parquet` once it exists), the do-files'
  sample filters, the regressor and instrument lists, the rebuilt route, time
  and seasonality dummies, and the HAC settings; `kp.py` implements the
  Kleibergen-Paap rk LM and rk Wald F and the Cragg-Donald Wald, which no Python
  package provides; `published.py` parses the published numbers out of the
  article text into `published.json`; `table2.py` through `table7.py` are one
  module per published table; `sensitivity.py` is the ADR-0008 grid; `run.py`
  writes `reports/replication/{results,summary,sensitivity}.json` and
  `tables.md`. `just replicate [private]` runs it. Report source
  `reports/replication.typ` (Portuguese), research note
  `docs/notes/replication.md` (Portuguese), divergences in
  `docs/declared-differences.md`. Tests: `tests/test_replication_kp.py` (the
  i.i.d. collapse of rk Wald onto Cragg-Donald and of rk LM onto Anderson, plus
  a `gabarito`-marked regression test against the published values) and
  `tests/test_replication_public.py` (the whole public path on a synthetic panel
  built to the published contract). Measured on the benchmark: 302 of 306
  coefficients agree in sign, 259 sit within half a published standard error,
  and no Hansen J changes its verdict.

- Data layer (`src/vra/{io,stage,keys,universe,delays,registry,cli}.py`,
  `scripts/{fetch,make_fixture,verify_reconcile}.py`): `vra fetch` downloads
  the 168 monthly ANAC VRA CSVs for 2000-2013 from the SIROS directory
  listing (2.17 GB, sha256 in `data/raw/manifest.json`, idempotent);
  `vra stage` parses both raw layouts -- 12 columns/comma/latin-1/CRLF up to
  2009, 20 columns/semicolon/UTF-8/LF from 2010, with a different column
  order and a free-text justification -- into 13,652,322 flight legs at
  `data/staged/year=YYYY/part-0.parquet` (zstd 9); `vra verify` reconciles
  the result with the private 2019 `vra.dta`; `vra layouts` measures a raw
  file instead of assuming its shape. Column registry in `registry.py`,
  offline fixtures in `tests/fixtures/`, staging note in
  `docs/notes/staging.md`, reconciliation in `reports/reconciliation.md`.

- Repository scaffold: licensing (`LICENSE` MIT, `LICENSE-CC-BY-4.0.md`),
  `CITATION.cff` (software plus the preferred citation for Bendinelli,
  Bettini & Oliveira 2016), governance docs (`CLAUDE.md`, `AGENTS.md`,
  `CONTRIBUTING.md`, `SECURITY.md`, `ROADMAP.md`), tooling
  (`pyproject.toml`, `.python-version`, `justfile`, `ruff.toml`,
  `.editorconfig`, `.gitattributes`, `.gitignore`,
  `.pre-commit-config.yaml`), CI (`.github/workflows/ci.yml`,
  `docs-lint.yml`, `security.yml`, `.github/dependabot.yml`), and the empty
  directory skeleton (`data/{raw,staged,derived,private,external}`, `sql/`,
  `reports/`, `docs/{notes,tutorial}/`, `replication/`, `ml/`, `scripts/`,
  `tests/`) described in `DECISIONS.md` and the architecture review.

### Changed

- **The prediction layer reads an empty actual time as "no alteration
  reported"** (`DECISIONS.md` ADR-0017, panel of three reviewers under
  ADR-0010, verdicts in `docs/notes/colegiado-adr0012.md`). IAC 1504 issues the
  Boletim de Alteração de Vôo only "sempre que houver alguma alteração", and the
  realised times are fields of that boletim, so an empty one on a realised flight
  of the 2000-2009 layout is the absence of a reported alteration.
  `ml/dataset_flights.py` therefore reads a delay of 0 and sets the new column
  `on_time_no_bav`, but only for realised flights of years up to 2009 whose
  carrier class in `groups.csv` is FSC, LCC or regional (`BAV_CLASSES`,
  `BAV_LAST_LEGACY_YEAR`); for `other` and unlabelled carriers -- foreign
  operators and the non-operating side of a code-share, whose null rate runs at
  90-100% against 52-75% for the domestic majors -- the empty field stays
  unknown and the flight keeps no delay target. The same reading is applied to
  the inbound leg and to the lagged rates (`monthly_lags`, `flight_number_sql`),
  so no feature measures a different quantity from the target it predicts.
  Arrival targets go from 4,965,966 to 8,686,697 of 10,200,560 rows; the pre-2010
  late rate falls from 75-94% to 18-41% and the 2009-to-2010 discontinuity
  disappears. On the 2010-2013 folds, where the two readings see exactly the same
  data, the rolling-origin day-ahead AUC rises from 0.638-0.711 to 0.715-0.724
  and the 2010 Brier from 0.250 to 0.162: the gain is in the training data, not
  the test set. `reports/prediction/results.md` prints both readings side by
  side from the preserved `reports/prediction/rolling_reading_A.json`, and
  `docs/declared-differences.md` gains the null actual-arrival rate by carrier
  and year (`scripts/null_actual_by_carrier.py`, new). The replication panel is
  unchanged: it still runs under the 2019 vintage's convention (ADR-0012), which
  is what reproduces the benchmark.

### Fixed

- **Duplicated route-month keys, fixed at the source** (`DECISIONS.md`
  ADR-0016). `data/staged/` is partitioned by the year of the *source file*
  while `year` and `ym` come from `flight_date`, so 3,723 rows sit in a
  directory that is not their calendar year -- mostly a December file carrying
  legs scheduled for 1 January, plus a few typed years (2099, 2020, 2088).
  `vra.features.build_fact` grouped inside each directory and concatenated the
  results, so a route-month present in two directories was emitted twice: 844
  rows over 422 `(group, route, ym)` keys in the fact table and, through the
  route-month context join, 866 rows over 433 `(route, ym)` keys in the panel,
  the copies carrying equal flight counts and different `n_rows_all`,
  `n_extra`, `sh_extra`, medians and p90s -- each copy's order statistics
  computed over part of its flights. `build_fact` now selects each **calendar
  year** across the whole staged tree (`features.year_source_sql`, parquet
  row-group statistics prune the rest) and asserts uniqueness on the way out;
  `features.aggregate` asserts the projection's own key; `panel.build_panel`
  asserts both on the way in. Rows dated outside the built years are counted in
  `data/analysis/manifest.json` (`rows_outside_years`) instead of being folded
  into a neighbour. The panel is now 31,313 rows over exactly the 168 months
  2000m1-2013m12 (was 31,760 over 169, the extra month being 18 flights dated
  January 2014 in the December 2013 file), the fact table 165,763 cells (was
  166,203), and the benchmark comparison runs over 24,551 comparable
  route-months instead of 24,929 with every rate up by a fraction of a point
  (`f` 0.901 to 0.902, `fl_odel` 0.854 to 0.857, `prwheather` 0.882 to 0.884).
  New `tests/test_keys_unique.py` rebuilds from a deliberately mis-partitioned
  staged tree and checks the committed tables under the `analysis` marker.

- **The outlier threshold applies to the absolute value of the delay**
  (`DECISIONS.md` ADR-0015). The one-sided cut inherited from the laboratory
  scripts (`delay < 313.25`) trimmed the late tail and let every negative month
  typo through: VSP 4374 in December 2003 has an actual arrival dated November,
  -43,170 minutes, and one route-month reached the public panel with
  `fsc_minsarr` of -4,772. Every sum, mean and share of minutes in
  `vra/delays.py`, `features.py` and `panel.py` now tests
  `abs(delay) < threshold`, on both tails; counts of delayed flights are
  untouched, because `x > 15` is the same test whatever the tail rule.
  `fsc_minsarr` in the regenerated panel runs from -239.90 to 226.27 (1st
  percentile -4.97, 99th 38.45), inside the band by construction. Table 2 of the
  public replication moves with it: the `MINS` regressand goes from a mean of
  -1.3404 and a standard deviation of 125 to 6.8632 and 8.79, against a
  published 7.16 and 8.29, and the correlation triangle's largest disagreement
  falls from 0.642 to 0.122. Against the benchmark, `fsc_minsarr`'s
  90th-percentile absolute difference falls from 2.11 to 1.68 minutes and
  `all_minsarr`'s from 4.13 to 2.49.

- **`actual_time_suspect` is written at staging** (ADR-0015), so that one
  definition serves every consumer: true when the departure or arrival delay is
  a whole calendar day or more in absolute value, false when there is no actual
  time at all. `ml/dataset_flights.py` reads the column instead of recomputing
  the rule, and `data/derived/ml/manifest.json` counts the excluded flights per
  year (242 in 2000 to 990 in 2013).

- `ml.dataset_flights.collapse_fact` is kept as the compatibility path for a
  fact table built before ADR-0016 held. It enforces the key invariant on its
  input before joining it; against a table built by today's `build_fact` it
  returns the frame untouched.

- `registry.DTYPE_ALIASES` accepts `category` and `dictionary` as physical forms
  of a declared `string`. The flight-level table dictionary-encodes every label
  -- ten million repetitions of `MRSP-MRRJ` as Python objects is a gigabyte and
  as codes is ten megabytes -- and `validate_schema` was reading that as a type
  mismatch.

- `registry.resource` omits `primaryKey` when none is given, instead of writing
  an empty one: the flight-level table has no key that is unique in the source
  data (the raw VRA repeats rows), and declaring one would be a claim, not a
  schema.

- `fsc_*` panel columns now use the article's own FSC carrier set (TAM group,
  Varig group until 2007-03, Transbrasil, Vasp); the class-based family
  (ADR-0003, Avianca Brasil included) moves to `fscc_*` (`DECISIONS.md`
  ADR-0013). Only names moved -- no carrier list, formula or tolerance
  changed -- but the rename fixes a real mismatch: the replication engine's
  `fsc_oddsarr`/`fsc_minsarr`/`fsc_minsp15arr` (arrival) and
  `fsc_oddsdep`/`fsc_minsdep`/`fsc_minsp15dep` (departure) regressands
  (`replication/common.py`) were reading the class-based set instead of the
  article's. Against the private benchmark, `fsc_prdelarr` agreement rises
  from 0.527 (0.534 stable-vintage) to 0.610 (0.649 stable-vintage), against
  the 0.651 the earlier reconstruction measured, and the stable-vintage
  shortfall list `just gabarito` reports drops from seven columns to six
  (`data/analysis/taxas.csv`). Updated: `src/vra/{registry,panel}.py`,
  `replication/gabarito/compare.py`, `tests/{test_panel,test_gabarito}.py`,
  `docs/declared-differences.md`, `docs/notes/{features,replication}.md`.
