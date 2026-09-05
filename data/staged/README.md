# data/staged/

The canonical flight table, one partition per year:
`year=YYYY/part-0.parquet`, zstd, tight types -- the 32 columns of the staged
layer in `docs/dictionary.md`, built by `src/airline_delays/staging/`. Produced
by `just stage` from `data/raw/` plus `data/external/groups.csv`, one year at a
time: 13,652,322 flight legs over 2000-2013, with a `manifest.json` recording
the per-year row counts and timings.

Git-ignored except for this README (see `.gitignore`): the table is regenerated
locally by `just fetch && just stage` from ANAC's files and is never committed
(`DECISIONS.md` ADR-0004). The committed fixture
`tests/fixtures/vra_sample.parquet` is a small slice of it, enough for the
tests and for `just demo`.
