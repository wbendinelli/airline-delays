# Contributing

`airline-delays` publishes the estimation panel of Bendinelli, Bettini &
Oliveira (2016, *Transportation Research Part A* 85, 39-52, doi
10.1016/j.tra.2016.01.001), re-estimates its tables, reconstructs ANAC's flight
records into an open panel, derives the article's theory and trains a delay
predictor. Corrections, extensions and independent re-estimations are welcome.
This page is the practical guide; CI checks most of it on every pull request.

## Your first contribution

1. **Fork** the repository and clone your fork.
2. **Set up the environment.** Python 3.12, managed by `uv`:

   ```bash
   uv sync
   uv run pre-commit install
   ```

3. **Run the two reproductions.** `just demo` runs the pipeline end to end on
   the committed fixture of 19,910 flight legs (staged legs to fact table to
   reconstruction panel to Table 2) in about a second, offline, writing only
   under the git-ignored `data/derived/demo/`. `just estimate` re-estimates
   Tables 2-7 on the committed article panel,
   `data/analysis/article_panel_route_month.parquet`, in under a minute, and writes
   `reports/replication/`.
4. **Branch, change, open a pull request.** `just check` runs pre-commit over
   the tree and the docs-paths check before you push.

## What CI runs

| Job | What it guarantees |
|---|---|
| `lint` | `ruff check` and `ruff format --check` over the whole tree |
| `test` | `pytest` against the committed fixture and the committed tables; no network, no `data/raw/` |
| `citation` | `CITATION.cff` is schema-valid |
| `docs-paths` | every backticked path and every `just` or `airline-delays` command in the READMEs, `docs/` and the data guides resolves to something real (`scripts/check_docs_paths.py`) |
| `metadata` | `docs/dictionary.md`, `datapackage.json`, `.zenodo.json` and `reports/summary.json` are rebuilds of the registry and the tables, and the Data Package validates |
| `docs-lint` | `README.md` matches the documentation profile declared in `.sapians-repo.yml` |
| `security` | `gitleaks` scans the full history for secrets |

A red job is fixed at its cause, never by weakening the check.

## The hard rules

1. **No column without an entry in `src/airline_delays/schema/columns.py`.**
   The dictionary, `datapackage.json` and the schema tests are generated from
   the registry; `just panel` regenerates the first two.
2. **No number on the entry pages that is not a value of `reports/summary.json`**
   (`airline-delays summary`) or marked as a transcription from an outside
   document. `scripts/check_prose_numbers.py` enforces it; a number without a
   script behind it is removed, not defended.
3. **Never commit anything under `data/raw/`, `data/staged/` or `data/derived/`**
   beyond their `README.md` and `data/raw/manifest.json`. They are regenerated
   from ANAC's files. The tracked data live in `data/analysis/` and
   `data/external/`, and `just check-analysis` fails when a tracked table
   drifts from what the code would produce.
4. **A measurement that contradicts prose changes the prose.** The correction
   is a `fix` commit, never a `docs` one, even when the diff is only text.
5. **The universe, the outlier threshold, the delay-cause taxonomy and the
   carrier sets are decisions**, recorded in `DECISIONS.md`. Changing one is a
   new ADR, not an edit to a constant.

## Documentation changes

`README.md` and `README.pt-BR.md` share one skeleton (`docs/editorial/readme-outline.md`)
and change together; `scripts/check_readme_parity.py` fails when they quote
different numbers, paths or recipes. The prose follows
`docs/editorial/style-guide.md`. Before opening a pull request that touches
prose, run the three checks:

```bash
uv run python scripts/check_docs_paths.py
uv run python scripts/check_prose_numbers.py
uv run python scripts/check_readme_parity.py
```

The Typst reports, the tutorial, the notes and the theory chapters are written
in Portuguese by decision (`DECISIONS.md`, ADR-0006); everything else is English.

## Style

Commit messages read `type(scope): summary`, with the scope a stage name:
`ingest`, `staging`, `reference`, `fact`, `panel`, `estimation`, `prediction`,
`theory`, `reporting`, `schema`, `docs` or `ci`. One line per notable change to
the code or the curated data goes into `CHANGELOG.md`.
