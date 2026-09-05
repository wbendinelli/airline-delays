# docs/

The documentation of `airline-delays` that does not fit on the README. The
two entry pages -- `README.md` in English and `README.pt-BR.md` in Portuguese --
share one skeleton; everything below is reached from them.

| Path | What it holds | Language |
|---|---|---|
| `dictionary.md` | The data dictionary: 636 columns across 7 layers, from the staged flights to the flight-level modelling table, each with its type, unit, aggregation rule and definition. Generated from `src/airline_delays/schema/columns.py` by `airline-delays dictionary`; never edited by hand. | Definitions in English and Portuguese |
| `data-availability.md` | The Data Availability Statement, source by source: holder, how to obtain, restrictions, cost and time. `data/README.md` and the README's "Data availability" section are its short versions. | English |
| `editorial/` | The rules the prose follows: `style-guide.md` (fifteen rules, from tone to the naming of the two panels), `readme-outline.md` (the fixed skeleton of the two READMEs and the `reports/summary.json` key of every number) and `number-allowlist.txt` (the few numbers that are constants, not measurements). | English |
| `notes/` | The research notes behind the decisions in `DECISIONS.md`: staging, the fact table and panel, the replication, the reference tables, the prediction layer, the review panel of ADR-0017, the licence request to ANAC and the 2013 monograph. Index in `notes/README.md`. | Portuguese (ADR-0006), English index |
| `tutorial/` | Fifteen modules, M0-M14: how the article was proposed, designed, estimated, published and received, and how this repository replicates and extends it. Index in `tutorial/README.md`. | Portuguese (ADR-0006), English summary on the index |
| `theory/` | Four chapters on the theory behind the article -- the economics of airport congestion, the Stackelberg game derived and checked, the bridge to the 2016 econometrics, the reception -- plus the bibliography. Index in `theory/README.md`. | Portuguese (ADR-0006), English index |

Every path and every `just` or `airline-delays` command quoted under `docs/`
is checked by `scripts/check_docs_paths.py`, and every number on the entry
pages by `scripts/check_prose_numbers.py` against `reports/summary.json`.
