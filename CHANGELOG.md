# Changelog

All notable changes to this repository are documented here. The format
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). This
project does not follow semantic-version releases (tier C, no package
consumed by another repository — see `.sapians-repo.yml`); dates, not
version numbers, mark progress.

## [Unreleased]

### Added

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
