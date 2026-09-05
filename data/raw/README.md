# data/raw/

Untouched ANAC monthly VRA CSVs, exactly as downloaded, one subdirectory per
source (`vra/YYYY/VRA_*.csv`). Populated by `just fetch` (`scripts/fetch.py`),
which also writes `manifest.json` — the only other file this directory
tracks in git — recording, per file, the source URL, the retrieval date, and
a sha256.

This directory is git-ignored (see `.gitignore`) except for this README and
`manifest.json`: the raw CSVs themselves are regenerated locally, never
pulled from git, and never committed even though their licence permits
redistribution (`DECISIONS.md` ADR-0000) — that redistribution happens
through a Zenodo deposit (`ROADMAP.md`, phase 7), not through this
repository's git history.

Processing reads this directory **year by year**, never two full raw scans
at once — see `CLAUDE.md`.
