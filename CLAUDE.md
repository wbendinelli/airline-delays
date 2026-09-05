# CLAUDE.md -- operating manual for agents in this repository

`airline-delays` reconstructs Brazil's VRA flight-leg records (ANAC,
2000-2013), publishes the estimation panel of Bendinelli, Bettini & Oliveira
(2016, *Transportation Research Part A* 85, 39-52, doi
10.1016/j.tra.2016.01.001) and re-estimates its Tables 2-7, derives the
article's congestion model, and trains a flight-level delay predictor -- see
`README.md` and `DECISIONS.md`. One hard rule, and everything else serves it:

> **No column exists without an entry in `src/airline_delays/schema/columns.py`,
> and no number in the entry pages exists that is not a value of
> `reports/summary.json` or marked as an outside document.**

## Language

**English** for `README.md`, code identifiers, column names, docstrings,
comments, decision records and commit text. **Portuguese** for
`README.pt-BR.md` and the other `.pt-BR` pages, `docs/notes/`,
`docs/tutorial/`, `docs/theory/` and the Typst reports `reports/*.typ`
(ADR-0006 and ADR-0021). Do not "fix" the Portuguese to English. Column
names, commands and paths are identical in both languages; the style guide
is `docs/editorial/style-guide.md`.

## What CI already guarantees (do not fight it, do not duplicate it)

A red CI is correct behaviour -- fix the cause, never weaken the check.

- **lint** -- `ruff check` and `ruff format --check` over the whole tree.
- **test** -- `pytest` against the fixture in `tests/fixtures/` and the
  tables committed under `data/analysis/`; no network, no `data/raw/`. The
  suite includes the replication freshness test (Tables 2-7 re-estimated on
  the committed article panel and compared with `reports/replication/results.json`),
  the vocabulary and prose-number tests and the README parity test.
- **citation** -- `CITATION.cff` stays schema-valid.
- **docs-paths** -- every backticked path and `just`/`airline-delays` command
  in the READMEs, `docs/` and the data guides resolves (`scripts/check_docs_paths.py`).
- **metadata** -- `docs/dictionary.md`, `datapackage.json`, `.zenodo.json` and
  `reports/summary.json` are rebuilds of the registry, the tables and the
  reports (`--check`), and frictionless validates the data package.
- **docs-lint** -- `README.md` matches the `research` profile of `.sapians-repo.yml`.
- **security** -- `gitleaks` scans the full git history for secrets.

## Duties CI does not cover (do these without being asked)

1. **Update `CHANGELOG.md`** -- one line per notable change to
   `src/airline_delays/`, `data/external/` or a committed table, under
   `[Unreleased]`.
2. **Run `just check` before committing** -- pre-commit over the whole tree
   plus the docs-path check; `just test` for the suite.
3. **Never commit anything from `data/raw/`, `data/staged/` or `data/derived/`**
   beyond their `README.md` and `data/raw/manifest.json`. `.gitignore` is a
   safety net, not a substitute for reading `git status`.
4. **Regenerate the generated files** whenever the registry, a committed
   table or a report changes: `airline-delays dictionary`, `datapackage`,
   `summary` and `zenodo-json`. `just panel` runs the first two and
   `just publish` checks all four. They are never hand-edited.
5. **Process raw data year by year**, never two full scans of `data/raw/` at
   once: one machine, 16 GB RAM, 10 cores (README, "Reproducing").
6. **Edit both READMEs together.** `README.md` and `README.pt-BR.md` share one
   outline (`docs/editorial/readme-outline.md`); `scripts/check_readme_parity.py`
   fails when they quote different numbers, paths or recipes. The same holds
   for `docs/README.md`, `data/README.md` and `CONTRIBUTING.md` with their
   `.pt-BR` counterparts.

## Things that look like an improvement and are a policy violation

- **Changing the universe, the outlier threshold, the delay-cause taxonomy or
  a carrier set** without a new ADR (`DECISIONS.md` ADR-0002, ADR-0008,
  ADR-0005, ADR-0003 and ADR-0013). These are the article's definitions; a
  change is a decision, not a patch.
- **A feature table at a new grain outside `aggregate()`.** The canonical
  fact table is `group x route x month`; every other grain is a tested,
  additive projection of it. A second hand-built table is a second source of truth.
- **pandas over a scan of the raw or staged files.** DuckDB is what keeps a
  16 GB machine from swapping on 13,652,322 staged legs.
- **A hand-typed number.** A number in an entry page is a value of
  `reports/summary.json` or a transcription marked "(article, Table 1)" or
  "(monografia -- documento externo)"; `scripts/check_prose_numbers.py`
  enforces it. Never recompute in prose.
- **The retired vocabulary.** The names of the verification layer that
  preceded ADR-0020 do not appear (`tests/test_prose_vocabulary.py`; style
  guide, rule 7). The two panels are "the article's estimation panel" and
  "the reconstruction panel", related by shared definitions.
- **Editing one README without the other.**
- **Writing a placeholder DOI.** `src/airline_delays/schema/metadata.py`
  carries `DOI = None` until Zenodo mints one; `datapackage.json` then has no
  `id` and `CITATION.cff` no `doi:`. `[DOI-MONOGRAFIA]` is the one sanctioned
  placeholder, for the monograph's own deposit.

## Workflow

Branch -> PR -> CI green -> merge. Before opening a PR: `just check`. Commit
messages `type(scope): summary`; a correction to a number already in prose is
a `fix`, never a `docs`-only change, even when the diff is only text.
