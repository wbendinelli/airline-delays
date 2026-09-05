# Changelog

All notable changes to this repository are documented here. The format
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). This
project does not follow semantic-version releases (tier C, no package
consumed by another repository — see `.sapians-repo.yml`); dates, not
version numbers, mark progress.

## [Unreleased]

### Added

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

### Fixed

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
