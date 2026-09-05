# data/raw/

Untouched ANAC monthly VRA CSVs, exactly as downloaded, one subdirectory per
year (`vra/YYYY/VRA_*.csv`). Populated by `just fetch` (`airline-delays fetch`),
which also writes `manifest.json` -- the only other file this directory tracks
in git -- recording, per file, the source URL, the retrieval date, the size and
a sha256: 168 files, 2.17 GB, for 2000-2013, downloaded in about 17 minutes.

This directory is git-ignored (see `.gitignore`) except for this README and
`manifest.json`: the CSVs are regenerated locally from ANAC's servers, never
pulled from git and never committed. `just fetch` skips a file whose sha256
already matches the manifest, so a rerun costs only the files that changed
upstream. The records are redistributable with attribution -- "ANAC, Voo
Regular Ativo (VRA), via dados.gov.br" (`DECISIONS.md` ADR-0000) -- and the
manifest's hashes let anyone verify that a fresh download is the series this
repository was built from.

Processing reads this directory **year by year**, never two full raw scans at
once -- see `CLAUDE.md`.
