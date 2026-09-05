# data/private/

Nothing is committed here except this file.

The private benchmark (`proj18.dta`) and the LABTAR/NECTAR laboratory bases
are never copied into this repository, in any form, under any name. Code
that needs them reads a path from the **environment variable**
`AIRLINE_DELAYS_PRIVATE_DIR` -- never a path hardcoded in source -- and only
two kinds of code are allowed to read it at all: `replication/gabarito/` and
a `scripts/verify*.py`. The only thing either of them commits back to the
repository is a derived agreement rate (`replication/gabarito/taxas.csv`),
never the private data itself.

Tests that depend on this directory carry the pytest marker `gabarito`
(see `tests/conftest.py`) and are skipped, not failed, when
`AIRLINE_DELAYS_PRIVATE_DIR` is unset -- which is the normal state for CI
and for any contributor without access to the laboratory archive. See
`CLAUDE.md`, `CONTRIBUTING.md` and `SECURITY.md` for the full policy, and
`.pre-commit-config.yaml`'s `no-private-data` hook for the automated check.
