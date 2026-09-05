# Test fixtures

Deterministic, small slices of repository data, committed so the test suite
never needs the network, `data/raw/`, or `AIRLINE_DELAYS_PRIVATE_DIR`.

The main fixture is `vra_sample.parquet`: a deterministic slice of the
staged flight table, a few megabytes, covering enough years and airlines for
`src/vra/` unit tests and for `just demo` to run an end-to-end reproduction
in seconds. It does not exist yet — it ships with the data phase (see
`ROADMAP.md`) via `scripts/make_fixture.py`, and is committed here (an
explicit exception to `data/staged/` being git-ignored, since this copy is
small and stable by construction).

Nothing under this directory is generated from `data/raw/` or
`data/private/` at test time — only checked in, once, by the script that
built it.
