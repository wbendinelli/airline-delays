# CLAUDE.md — operating manual for agents in this repository

Reconstruction of Brazil's VRA flight-leg data, replication of Bendinelli,
Bettini & Oliveira (2016, *Transportation Research Part A*,
[`10.1016/j.tra.2016.01.001`](https://doi.org/10.1016/j.tra.2016.01.001)),
and flight-level delay prediction — see [README.md](README.md) and
[DECISIONS.md](DECISIONS.md). One hard rule, and everything else serves it:

> **No column exists without an entry in `src/vra/registry.py`, and no
> number in prose exists without a versioned script that prints it.**

## Language

**English** for the README, code identifiers, column names, docstrings,
comments and commit-facing text — the `research` profile of the SAPIANS
doclint requires it, and it is what lets anyone replicating the article
read this repository. **Deliberate exception:** the Typst reports under
`reports/` and the didactic material under `docs/notes/` and
`docs/tutorial/` are written in **Portuguese** (`DECISIONS.md` ADR-0006) —
do not "fix" this to English. Decision records (`DECISIONS.md`) are English
because that file is part of the public repository.

## What CI already guarantees (do not fight it, do not duplicate it)

A red CI is correct behaviour — fix the cause, never weaken the check:

- **lint** — `ruff check` and `ruff format --check` over the whole tree.
- **test** — `pytest` against the fixture committed in `tests/fixtures/`, no
  network, no `data/raw`/`data/staged`. Tests marked `gabarito` need
  `AIRLINE_DELAYS_PRIVATE_DIR` and are skipped, never run, in CI.
- **citation** — `CITATION.cff` stays schema-valid (`cffconvert
  --validate`).
- **docs** — the README matches the `research` profile declared in
  `.sapians-repo.yml` (required sections, the tier/class identity line, the
  BibTeX block, brand spelling) — see the reusable `docs-lint.yml`.
- **docs-paths** — every backticked path and every `just`/`vra` command in
  `README.md` and `docs/tutorial/*.md` resolves to something real
  (`scripts/check_docs_paths.py`).
- **security** — `gitleaks` scans the full git history for secrets.

## Duties CI does not cover (do these without being asked)

1. **Update `CHANGELOG.md`** — one line per notable change to `src/vra/`,
   `replication/`, `ml/` or `data/external/`, under the right heading.
2. **Run `just check` before committing** — `pre-commit run --all-files`,
   plus the local doclint (see `CONTRIBUTING.md`).
3. **Never commit anything from `data/raw/`, `data/staged/`,
   `data/derived/` or `data/private/`.** Only their `README.md` (and, for
   `data/raw/`, `manifest.json`) are tracked. `.gitignore` and the
   `no-private-data` pre-commit hook enforce this, but they are a safety
   net, not a substitute for checking `git status` yourself.
4. **Regenerate the dictionary and `datapackage.json` whenever
   `src/vra/registry.py` changes** — `uv run vra dictionary` and
   `uv run vra datapackage` (`just panel` already runs both). They are
   generated artefacts, never hand-edited.
5. **Process raw data year by year, never two full scans of `data/raw/` at
   once.** One machine, 16 GB RAM, 10 cores — see the README's
   "Reproducing" section.

## Things that look like an improvement and are a policy violation

- **Changing the replication universe, the outlier threshold, or the
  delay-cause taxonomy on your own.** These are ADRs (`DECISIONS.md`
  ADR-0002, ADR-0005, ADR-0008), not bugs to patch — write a new ADR
  instead of editing the constant.
- **Adding a feature table at a new grain outside `aggregate()`.** The
  canonical fact table is `group x route x month`; every other grain is a
  tested, additive projection of it. A second hand-built table at a
  different grain is a second source of truth — exactly what
  `registry.py` exists to prevent.
- **Using pandas where the rule says DuckDB** for a scan over the raw or
  staged CSV/parquet files. DuckDB is what keeps a 16 GB machine from
  swapping on 13.5 million rows.
- **"Fixing" a divergence against the benchmark by adjusting a definition
  until the numbers match.** The divergence is the result — declare it in
  `docs/declared-differences.md` and the README's "Declared differences"
  section; never absorb it into the definition silently.
- **Committing `proj18.dta`, the LABTAR/NECTAR bases, or `vra.dta`** —
  under any name, in any directory. They are reached only through the
  `AIRLINE_DELAYS_PRIVATE_DIR` environment variable, and only by
  `replication/gabarito/` or a `scripts/verify*.py`.

## Workflow

Branch -> PR -> CI green -> merge. Before opening a PR: `just check`. A
correction to a number already in prose is a `fix`, never a `docs`-only
change, even when the diff is only text.
