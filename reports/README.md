# reports/

Typst sources for the three reports this repository produces --
reconstruction, replication, prediction -- plus their generated figures and
tables. Written in **Portuguese** (a deliberate exception to the
repository's English default; see `CLAUDE.md` and `DECISIONS.md` ADR-0006).

Every number in the report prose is printed by a versioned script under
`replication/` or `ml/`, never typed by hand -- the same rule the README
follows for `## Declared differences` and `## Use and limits`. Compiled
output (`reports/**/build`) is git-ignored; the Typst sources and the small
figures/tables they depend on are not.

| source | inputs | built by | compile |
|---|---|---|---|
| `reconciliation.md` | the private `vra.dta` via `AIRLINE_DELAYS_PRIVATE_DIR` | `scripts/verify_reconcile.py` | already Markdown |
| `replication.typ` | `replication/{private,public}/*.json` | `uv run python -m replication.run` | `typst compile reports/replication.typ reports/build/replication.pdf` |
| `prediction.typ` | `prediction/*.json` | `just ml` (`uv run python -m ml.run`) | `typst compile reports/prediction.typ reports/build/prediction.pdf` |

`prediction/` holds six JSON files and a `results.md`: `rolling.json` (the
headline, one entry per test year 2006-2013 and both horizons), `fixed.json`
(the illustrative split, four targets), `calibration.json`, `importance.json`,
`dataset.json` (the per-year ADR-0012 accounting) and `leakage.json` (the nine
checks of `ml/leakage_tests.py` run against the real dataset, not the fixture).
