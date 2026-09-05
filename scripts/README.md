# scripts/

One-off utility scripts that sit outside the `vra` package because they are
entry points, not library code:

- `fetch.py` — downloads the ANAC monthly VRA CSVs into `data/raw/` and
  writes its `manifest.json` (`just fetch`).
- `demo.py` — the smallest end-to-end reproduction: the committed fixture
  through features, panel and Table 2, offline, into the git-ignored
  `data/derived/demo/` (`just demo`).
- `make_fixture.py` — cuts the deterministic slices committed under
  `tests/fixtures/` (`uv run vra fixture`).
- `verify_reconcile.py` — private: reconciles the staged data against the
  2019 vintage `vra.dta`, reads `AIRLINE_DELAYS_PRIVATE_DIR`, subject to
  the same rules as `replication/gabarito/` (`just verify`).
- `null_actual_by_carrier.py` — private: the null actual-arrival rate by
  carrier and year that `docs/declared-differences.md` publishes
  (ADR-0017).
- `check_docs_paths.py` and `check_no_private_paths.py` — CI and
  pre-commit guards: every path and `just` target quoted in the docs
  exists, and no absolute path into a private directory is committed.

Each is called from a `justfile` target rather than run directly, so the
documented entry point for "how do I run this" is always `just <target>`,
not a script path (see the root `README.md`'s "Reproducing" section).
