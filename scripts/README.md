# scripts/

One-off utility scripts that sit outside the `vra` package because they are
entry points, not library code: `fetch.py` (downloads the ANAC monthly VRA
CSVs into `data/raw/`, writes `manifest.json`), `verify_reconcile.py`
(private -- reconciles against the 2019 vintage `vra.dta`, reads
`AIRLINE_DELAYS_PRIVATE_DIR`, subject to the same rules as
`replication/gabarito/`), and `make_fixture.py` (cuts the deterministic
slice committed at `tests/fixtures/vra_sample.parquet`).

Each is called from a `justfile` target rather than run directly, so the
documented entry point for "how do I run this" is always `just <target>`,
not a script path (see the root `README.md`'s "Reproducing" section).
