# scripts/

Entry points that sit outside the `airline_delays` package because they are
tools around it, not stages of it:

- `demo.py` -- the smallest end-to-end reproduction: the committed fixture
  through the fact table and the reconstruction panel, then Table 2 on the
  article's estimation panel, offline, into the git-ignored
  `data/derived/demo/` (`just demo`).
- `make_fixture.py` -- cuts the deterministic slices committed under
  `tests/fixtures/` from `data/raw/` and `data/staged/`
  (`uv run airline-delays fixture`).
- `null_actual_by_carrier.py` -- the null actual-arrival rate by carrier and
  year behind the scope of ADR-0017, written to
  `reports/prediction/null_actual_by_carrier.csv`.
- `monograph_airports.py` -- joins `data/external/monograph_airports.csv`
  (the 38 airports of the author's 2013 undergraduate monograph) to
  `data/external/nodes.csv` and prints the three counts that
  `docs/notes/monografia-2013.md` quotes.
- `check_docs_paths.py` -- the CI guard: every path and every `just` or
  `airline-delays` command quoted in the READMEs and under `docs/` exists
  (`just check`).

The pipeline itself is the `airline-delays` command line (`uv run
airline-delays --help`), one command per stage, and the `justfile` wraps it;
the documented way to run anything is `just <recipe>`.
