# docs/

The documentation of `airline-delays` that does not fit on the README. The
two entry pages -- `README.md` in English and `README.pt-BR.md` in Portuguese --
share one skeleton; everything below is reached from them.

| Path | What it holds | Language |
|---|---|---|
| `dictionary.md` | The data dictionary: 636 columns across 7 layers, from the staged flights to the flight-level modelling table, each with its type, unit, aggregation rule and definition. Generated from `src/airline_delays/schema/columns.py` by `airline-delays dictionary`; never edited by hand. | Definitions in English and Portuguese |
| `data-availability.md` | The Data Availability Statement, source by source: holder, how to obtain, restrictions, cost and time. `data/README.md` and the README's "Data availability" section are its short versions. | English |
| `editorial/` | The rules the prose follows: `style-guide.md` (seventeen rules, from tone to the naming of the two panels), `readme-outline.md` (the fixed skeleton of the two READMEs and the `reports/summary.json` key of every number) and `number-allowlist.txt` (the few numbers that are constants, not measurements). | English |
| `notes/` | The research notes behind the decisions in `DECISIONS.md`: staging, the fact table and panel, the replication, the reference tables, the prediction layer, the review panel of ADR-0017, the licence request to ANAC and the 2013 monograph. Index in `notes/README.md`. | Portuguese (ADR-0006), English index |
| `study/` | The study, the final work: an opening, eight chapters in three parts -- the economics of airport congestion; game theory, from the fundamentals to the Stackelberg congestion model derived step by step; the article, from the model to the hypotheses, the data, specification and identification, results and replication, and reception -- four appendices (the delay predictor, how to reproduce, rights and licences, extensions) and the bibliography. Compiles to `reports/pdf/study.pdf`. Index in `study/README.md`. | Portuguese (ADR-0006), English summary on the index |

Every path and every `just` or `airline-delays` command quoted under `docs/`
is checked by `scripts/check_docs_paths.py`, and every number on the entry
pages by `scripts/check_prose_numbers.py` against `reports/summary.json`.
