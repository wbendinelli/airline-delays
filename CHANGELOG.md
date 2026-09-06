# Changelog

All notable changes to this repository are documented here. The format
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). This
project does not follow semantic-version releases (tier C, no package
consumed by another repository -- see `.sapians-repo.yml`); the first
publication is tagged v1.0.0 and archived on Zenodo (`ROADMAP.md`), and
dates mark progress until then.

## [Unreleased]

Nothing yet.

## [1.1.0] - 2026-09-05

The study (`DECISIONS.md` ADR-0022): `docs/` reorganised as the final work
that joins the economics of airport congestion, the game-theory model and the
article.

### Added

- `docs/study/`: the study in Portuguese -- an opening, eight chapters in three
  parts (the economics of airport congestion; game theory from the fundamentals
  to the Stackelberg congestion model derived step by step; the article: from
  the model to the hypotheses, data, specification and identification, results
  and replication, reception), four appendices (the delay predictor, how to
  reproduce, rights and licences, extensions) and the bibliography.
- `docs/study/02-teoria-dos-jogos-fundamentos.md`, a game-theory primer with
  airline examples, and the `primer` block of `reports/theory/model.json` that
  `airline-delays theory` writes for its discrete game (pinned by
  `tests/test_theory.py`).
- `reports/pdf/`: the compiled reports are tracked (`study.pdf`,
  `replication.pdf`, `prediction.pdf`); `airline-delays report` stamps the
  PDF with the release date of `CITATION.cff`, which the reports also print,
  so a rerun rewrites identical bytes.
- `scripts/check_markdown_math.py`: GitHub-safe math delimiters, a blank line
  before every table and closed fences, in `just check` and the `docs-paths`
  CI job.

### Changed

- `reports/theory.typ` -> `reports/study.typ`, the study report, extended with
  the article's part (hypotheses, data, specification, results, replication).
- Every mention of the 2013 monograph names USP alone; the source strings of
  `data/external/monograph_airports.csv`, `reports/theory/model.json` and
  `datapackage.json` were regenerated accordingly.
- The theory chapters' mathematics rewritten in the forms GitHub renders
  (inline $`...`$, display in ```math fences).
- `tests/test_prose_vocabulary.py` also rejects the biographical vocabulary
  and the retired paths.
- `docs/notes/`: paths to the study and to `reports/pdf/`; the monograph note
  loses its biographical opening; month tokens in the `AAAA-MM` form.

### Removed

- `docs/tutorial/` (fifteen modules) and `docs/theory/`: the proposal, designs,
  dissertation, peer-review and reception modules are out of scope; the data,
  specification, replication, rights and extensions material lives on in the
  study.

## [1.0.0] - 2026-09-05

The first published release: the repository as an open research compendium of the article. The `0.1.0` entry below is the development history before publication; it was never tagged.

The restructure: the article's estimation panel published, one stage-ordered
package, one narrative in two languages (`DECISIONS.md` ADR-0020, ADR-0021).

### Added

- **The article's estimation panel** (ADR-0020): `data/analysis/article_panel_route_month.parquet`
  and `.csv.gz`, 24,589 route-months x 52 columns, curated once from the authors' final base
  (Stata, header timestamp 3 Dec 2015, 1,829 variables) by `airline-delays article-panel` --
  keys and geography, the flight counts, the six regressands, the nine exogenous regressors,
  the concentration terms, the seven instruments and the components of the two low-cost
  dummies. The generated dummies are rebuilt by `src/airline_delays/estimation/loader.py`; no
  column from a non-open source ships. `data/analysis/article_panel_manifest.json` records the
  sha256 of the source and of both files, the header timestamp and the per-column null counts,
  never a path. Registry layer `article_panel` with bilingual definitions; `tests/test_article_panel.py`.
- **Publication metadata at the Data Package v2 standard.** `datapackage.json` describes every
  published table -- both panels, the fact table, the two projections, the curated
  `data/external/` tables and the manifests -- with sha256, size, row count, licence, sources
  and field constraints, and lists the regenerated layers under `x-regenerated` with the command
  that rebuilds them. `.zenodo.json` is generated (`airline-delays zenodo-json`) from
  `src/airline_delays/schema/metadata.py`, the single source of title, version, keywords,
  creators, licences and related identifiers that `CITATION.cff` and `pyproject.toml` are
  tested against. A CI job `metadata` rebuilds the four generated files and validates the
  package with frictionless; `just validate` runs the full validation.
- **`reports/summary.json`, the numbers manifest** (`airline-delays summary`): every headline
  number the entry pages quote, read from the committed manifests, tables and reports; no
  timestamp; `tests/test_summary.py` fails when it is stale. `dictionary`, `datapackage`,
  `zenodo-json` and `summary` take `--check`; `airline-delays report` compiles the three reports.
- **The bilingual entry layer**: `README.md` (English, the main page) with `README.pt-BR.md`;
  `docs/README.md`, `data/README.md` and `CONTRIBUTING.md` with their `.pt-BR` counterparts,
  written natively and kept in parity by `scripts/check_readme_parity.py`; an English summary
  paragraph on each Portuguese index page.
- **`docs/editorial/`**: the style guide, the shared README outline with the `summary.json`
  key behind each number, and the number allowlist.
- **The prose checks**: `scripts/check_prose_numbers.py` with `tests/test_prose_numbers.py`,
  `tests/test_prose_vocabulary.py`, and `scripts/check_docs_paths.py` extended to the READMEs,
  every page under `docs/` and the data guides.
- **ADR-0020** and **ADR-0021**.

### Changed

- **One stage-ordered package.** `src/vra/`, `replication/`, `ml/` and `theory/` become
  `src/airline_delays/` with the subpackages `ingest`, `staging`, `reference`, `fact`, `panel`,
  `estimation`, `prediction`, `theory` and `reporting`, plus the cross-cutting `definitions/`
  and `schema/`. The console script is `airline-delays`, one command per stage in pipeline
  order; the `justfile` recipes follow the same names, grouped by stage, with `just pipeline`
  and `just pipeline-full`. Tests are renamed with their modules.
- **Single-source estimation.** `airline-delays estimate` runs Tables 2-7 on the article's
  estimation panel (or any panel carrying the contract, `--panel`), writes `reports/replication/`
  flat and records the panel's path, row count and sha256 in `results.json`; `estimation/common.py`
  becomes `specification`, `loader`, `sample` and `estimators`. Every re-estimated value equals
  the previous run to the last digit (1,097 values compared); the Kleibergen-Paap test against
  the published Table 3 and the replication freshness test run in CI; the demo's last step runs
  Table 2 on the article panel.
- **`empty_actual_means_on_time`** replaces `legacy_missing_actual_as_zero` as the name of the
  ADR-0012 convention -- parameter, CLI flag, manifest key and panel column; the reconstruction
  panel is regenerated with the one column renamed and every value unchanged.
- **The prose, rewritten as one narrative**: `README.md`, `CLAUDE.md`, `AGENTS.md`,
  `CONTRIBUTING.md`, `SECURITY.md`, `ROADMAP.md`, `DECISIONS.md`, `docs/data-availability.md`.
  In `DECISIONS.md` the evidence of ADR-0001, 0002, 0005, 0012, 0013 and 0017 becomes "Basis"
  and states the article's definitions, restated by its first author; ADR-0019 follows the
  package paths. Registry definitions that quoted agreement rates are reworded; the dictionary
  and the data package are regenerated.
- **This changelog is consolidated**: the history before the restructure is the 0.1.0 entry.

### Removed

- **The verification layer against the authors' final base**, superseded by publishing the
  base itself (ADR-0020): the comparison package under `replication/` and its pytest marker,
  the reconciliation script with its report and by-month table, the agreement-rate table under
  `data/analysis/`, the private-data directory and the environment variable that pointed outside
  the repository, the `public/`/`private/` split of `reports/replication/`, the page of
  divergences and the audit directory under `docs/`, `scripts/verify_reconcile.py`,
  `scripts/check_no_private_paths.py`, the `vra verify` command with its recipes, and the two
  `no-private-data` pre-commit hooks.

## [0.1.0] - 2026-09-05

The repository before the restructure: reconstruction, replication, prediction and theory, built between the scaffold and the pre-publication audit.

### Added

- Repository scaffold: `LICENSE` (MIT) and `LICENSE-CC-BY-4.0.md`, `CITATION.cff` with the article as preferred citation, the governance pages, `pyproject.toml`, `justfile`, `ruff.toml`, pre-commit, CI (`ci.yml`, `docs-lint.yml`, `security.yml`) and Dependabot.
- Ingest and staging: the 168 monthly ANAC VRA CSVs for 2000-2013 downloaded from the SIROS listing (2.17 GB, sha256 per file in `data/raw/manifest.json`, idempotent), a command that measures a raw file's layout instead of assuming it, and both raw layouts -- 12 columns, comma, latin-1, CRLF to 2009; 20 columns, semicolon, UTF-8, free-text justification from 2010 -- parsed into 13,652,322 flight legs at `data/staged/year=YYYY/part-0.parquet` (zstd 9); offline fixtures cut byte for byte from the real files; `docs/notes/staging.md`.
- Reference tables under `data/external/`, every row with a source, a URL, a retrieval date and a confidence grade: node map and distances (OurAirports), dated airline groups and events, IAC 1504 code tables, federal holidays and computed observances, capacity and slot rows; `docs/notes/references.md`.
- The fact table `group x route x month` over the replication universe (87 columns, one scan per staged year) with its city-month and airline-city-month projections through `aggregate()`, tested for additivity and shipped as the `v_check_additivity` view in `sql/views.sql`; the route-month reconstruction panel (228 columns over the 27 nodes of ADR-0001) with the article's column names, the declared variants and the new feature families; `docs/notes/features.md`.
- Definitions: dated groups and four classes (ADR-0011), the article's three justification sets beside the ADR-0005 taxonomy, flight-share concentration with a passenger-weighted placeholder, the ADR-0007 p90 congestion proxy, a hub score with volume floors.
- The ADR-0012 convention as a named parameter selecting the denominator of every proportion and mean -- `True` for the reconstruction panel, `False` for prediction -- and the per-year share of realised flights with no actual time.
- The column registry and the documentation generated from it, `docs/dictionary.md` and `datapackage.json` (Frictionless v2), never hand-edited and checked in both directions against the tables built.
- The replication layer: Tables 2-7 of Bendinelli, Bettini & Oliveira (2016), one module per table; the do-files' sample filters, regressor and instrument lists, rebuilt route, time and seasonality dummies and HAC settings; `reports/replication.typ`; `docs/notes/replication.md`.
- The Kleibergen-Paap rk LM and rk Wald F and the Cragg-Donald Wald, which no Python package provides, with the i.i.d. collapses tested; the published numbers parsed into `published.json`; the ADR-0008 sensitivity grid.
- `data/analysis/*.parquet` and `*.csv.gz` tracked in git (ADR-0014) with the pre-commit large-file threshold raised to 50 MB; `just check-analysis` rebuilds the panel from the committed fact table and fails on drift; manifests stamped with the short git commit.
- Flight-level delay prediction: the modelling table of 10,200,560 scheduled flights with 46 D-1 features, 3 inbound-leg features for H-1 and five targets, one DuckDB scan per year; the rolling origin 2006-2013 and the fixed split of ADR-0009; XGBoost with early stopping on each fold's validation year; AUC, PR-AUC, Brier, calibration, two naive baselines and permutation importance; `reports/prediction/`, `reports/prediction.typ`, `docs/notes/prediction.md`.
- The leakage rule as nine executable checks, run on the fixture in the test suite and on the real dataset in the prediction run, plus a test that plants a leak and asserts the checks catch it.
- `just demo` (`scripts/demo.py`, `tests/test_demo.py`): the committed fixture through the same code path as the full pipeline in about one second, offline, writing only under the git-ignored `data/derived/demo/`.
- The theory layer (ADR-0019): the Stackelberg congestion model of the author's 2013 undergraduate monograph re-derived with sympy -- equations (1)-(12), the reaction-slope bounds, the leader's toll at three quarters of the marginal damage under linear cost, the inelastic-demand condition, 29 identities pinned by `tests/test_theory.py` -- with numeric examples, comparative statics, a low-cost-entrant extension and the join of each theory object to the article's published signs; eleven figures drawn with matplotlib in the SAPIANS style; `reports/theory.typ` as a SAPIANS report on the design package vendored under `reports/sapians/`; the four Portuguese chapters of `docs/theory/` with `bibliografia.md`; tutorial module M14.
- The data side of the 2013 monograph: `data/external/monograph_airports.csv` (its 38 listed airports, grade A) with `scripts/monograph_airports.py` and its test; `docs/notes/monografia-2013.md`; source 15 of `docs/data-availability.md`.
- Documentation: the README with cited numbers, the Data Availability Statement source by source, the Portuguese tutorial (M0-M13), `docs/notes/`; `scripts/check_docs_paths.py` in CI over the README and the tutorial.
- An earlier verification layer compared the reconstruction with the authors' final base column by column and committed agreement statistics only; retired in the restructure above.

### Changed

- The prediction layer reads an empty actual time on a realised pre-2010 flight as "no alteration reported" (ADR-0017, a panel of three reviewers under ADR-0010, `docs/notes/colegiado-adr0012.md`): delay 0 and the flag `on_time_no_bav`, for carriers of class FSC, LCC or regional only; arrival targets go from 4,965,966 to 8,686,697 of 10,200,560 rows, and `reports/prediction/results.md` prints both readings side by side. The reconstruction panel is unchanged (ADR-0012).
- `fsc_*` panel columns use the article's own FSC carrier set; the class-based family moves to `fscc_*` (ADR-0013). Only names moved; the rename fixed the regressands the estimation read.
- The outlier threshold applies to the absolute value of the delay (ADR-0015): every sum, mean and share of minutes tests `abs(delay) < threshold`; `actual_time_suspect` is written at staging and the modelling table counts the excluded flights per year.
- `docs/data-availability.md` sources 1, 3, 9, 12 and 13 amended with what the monograph documents about the VRA's composition and the RPE series; tutorial modules M0, M1, M2, M5, M11 and M13 point to the theory chapters.

### Fixed

- The 2002 fixture lost its CRLF on every fresh clone, so the suite failed for everyone but the author (audit B-1): the fixtures are `-text` in `.gitattributes`, re-added with their bytes, and a test names the file if a fixture arrives normalised again.
- Absolute paths into the author's private research archive were committed in `data/external/` (audit B-2): the rows now cite "author's research notes (private, not redistributed)" with a public URL where the fact has one, and a content scan over every tracked text file guards the archive's layout.
- The README generalised the article's central result (audit M-1): the OLS-to-2SGMM sign inversion of the HHI terms occurs in 4 of the 12 comparisons, the `ODDS` columns, and all 4 replicate; the agreement on whether the sign flips holds in 12 of 12. Both statements are computed by the estimation code, never hand-derived.
- The ADR-0017 accounting was counted twice, differently, with one column mislabelled (audit M-2, M-3): one canonical `accounting` block in `reports/prediction/dataset.json`, quoted everywhere and computed nowhere else.
- The prediction runtime in the README was printed by nothing (audit M-4): a `runtime` block in `reports/prediction/dataset.json`.
- Two placeholder DOIs would have shipped (audit M-5): `datapackage.json` omits `id` until a DOI exists, the README badge renders no dead link, `CITATION.cff` carries no `doi:` of its own.
- Smaller audit corrections (m-1 to m-12): dead internal paths, a mistyped AUC bound, byte-reproducible `csv.gz` and `null_actual_by_carrier.csv` (deterministic labels instead of `any_value()`), superseded counts in this file, the ruff hook pinned to the locked version, a non-existent path filter dropped from `docs-lint.yml`, the sign-disagreement rows in one order.
- Duplicated route-month keys fixed at the source (ADR-0016): the fact table selects each calendar year across the whole staged tree instead of grouping inside the source-file directory, and asserts uniqueness; the panel is 31,313 rows over exactly the 168 months 2000m1-2013m12, the fact table 165,763 cells; `tests/test_keys_unique.py`.
- `registry.DTYPE_ALIASES` accepts `category` and `dictionary` as physical forms of a declared `string`; `registry.resource` omits `primaryKey` when none is given; `collapse_fact` is kept as the compatibility path for a fact table built before ADR-0016 held.
