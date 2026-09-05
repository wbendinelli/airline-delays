# reports/

Typst sources for the four reports this repository produces --
reconstruction, replication, prediction, theory -- plus their generated figures
and tables. Written in **Portuguese** (a deliberate exception to the
repository's English default; see `CLAUDE.md` and `DECISIONS.md` ADR-0006).

Every number in the report prose is printed by a versioned script under
`replication/`, `ml/` or `theory/`, never typed by hand -- the same rule the README
follows for `## Declared differences` and `## Use and limits`. Compiled
output (`reports/**/build`) is git-ignored; the Typst sources and the small
figures/tables they depend on are not.

| source | inputs | built by | compile |
|---|---|---|---|
| `reconciliation.md` | the private `vra.dta` via `AIRLINE_DELAYS_PRIVATE_DIR` | `scripts/verify_reconcile.py` | already Markdown |
| `replication.typ` | `replication/{private,public}/*.json` | `uv run python -m replication.run` | `typst compile reports/replication.typ reports/build/replication.pdf` |
| `prediction.typ` | `prediction/*.json` | `just ml` (`uv run python -m ml.run`) | `typst compile reports/prediction.typ reports/build/prediction.pdf` |
| `theory.typ` | `theory/{model,figures}.json`, `theory/figures/*.svg` | `just theory` (`uv run python -m theory.run`) | `typst compile reports/theory.typ reports/build/theory.pdf` |

`sapians/` is the SAPIANS design package for Typst (`@local/sapians:0.1.0`), vendored
from `sapians-latex` (MIT) so that `reports/theory.typ` compiles from a clean clone
with `typst compile --root . reports/theory.typ reports/build/theory.pdf`; the Inter
font is used when installed, with Helvetica Neue or Arial as the fallback the
package declares. `theory/figures/*.svg` are drawn by `theory/figures.py` with
matplotlib in the SAPIANS figure style (`theory/sapians_style.py`).

`theory/` holds `model.json` (every identity of the Stackelberg congestion
model with whether it holds, the reaction-slope bounds, the tolls of
Proposition 1, three numeric examples, comparative statics, the low-cost
entrant extension and the bridge to the article's published signs),
`figures.json` (the coordinates of every labelled point of the five redrawn
diagrams), `figures/*.svg` and a `results.md`; all written by `just theory`,
without a timestamp, so a second run on an unchanged tree changes nothing.

`prediction/` holds six JSON files and a `results.md`: `rolling.json` (the
headline, one entry per test year 2006-2013 and both horizons), `fixed.json`
(the illustrative split, four targets), `calibration.json`, `importance.json`,
`dataset.json` (the per-year ADR-0012 accounting) and `leakage.json` (the nine
checks of `ml/leakage_tests.py` run against the real dataset, not the fixture).
