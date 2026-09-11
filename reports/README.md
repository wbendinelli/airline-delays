# reports/

The three Typst reports of `airline-delays` -- the study, the replication and
the prediction -- with the generated JSON, Markdown and figures they read, the
compiled PDFs under `pdf/`, and `summary.json`, the numbers manifest the READMEs
quote. The reports are written in **Portuguese** (`DECISIONS.md`, ADR-0006);
this page is the English index.

No number in a report is typed by hand: each report reads its inputs with
Typst's `json()` from the files a stage of the pipeline wrote. The PDFs are
tracked (ADR-0022), so the study can be read without installing Typst; `just
report` (`airline-delays report`) recompiles the three with the release date
of `CITATION.cff` as creation timestamp and printed date, so a rerun on an
unchanged tree rewrites identical bytes.

| Report | What it is | Inputs | Written by | PDF |
|---|---|---|---|---|
| `study.typ` | The study: the economics of airport congestion, the congestion game derived step by step, and the article -- hypotheses, data, specification, results, replication, reception. The Markdown edition is `docs/study/`. | `reports/theory/{model,figures}.json`, `reports/theory/figures/*.svg`, `reports/replication/{summary,results}.json`, `reports/summary.json` | `just theory`, `just estimate`, `just summary` | `pdf/study.pdf` |
| `replication.typ` | Tables 2-7 re-estimated on the article's estimation panel, cell by cell against the published values | `reports/replication/{results,summary,sensitivity}.json` | `just estimate` | `pdf/replication.pdf` |
| `prediction.typ` | The flight-level delay predictor: design, leakage checks, rolling-origin results | `reports/prediction/{rolling,fixed,calibration,importance,dataset,leakage}.json` and `rolling_reading_A.json` | `just predict` | `pdf/prediction.pdf` |

`just report` needs `typst` on the PATH (0.13 or later). One report at a time:
`uv run airline-delays report --only study`.

`sapians/` is the SAPIANS design package for Typst (`@local/sapians:0.1.0`),
vendored from `sapians-design` (MIT) so that the reports compile from a clean
clone with `--root .`. The Inter font is used when installed, with Helvetica
Neue or Arial as the fallback the package declares. The figures under
`reports/theory/figures/` are drawn by `src/airline_delays/theory/figures.py`
with matplotlib in the SAPIANS figure style
(`src/airline_delays/theory/sapians_style.py`).

## What each directory holds

- `pdf/` -- the three compiled reports, tracked.
- `replication/` -- `results.json` (every re-estimated cell of Tables 2-7 next
  to its published value), `summary.json` (the scorecard: sign agreement,
  gaps in published standard errors, the HHI sign-inversion count),
  `sensitivity.json` (the main coefficients across the seasonality cells) and
  `tables.md`, the same tables rendered for reading. Written by
  `airline-delays estimate` from the article's estimation panel.
- `prediction/` -- `rolling.json` (the headline: one entry per test year
  2006-2013, both horizons), `fixed.json` (the illustrative split, four
  targets), `calibration.json`, `importance.json`, `dataset.json` (the
  per-year accounting of the modelling table), `leakage.json` (the nine
  checks run against the real dataset), the sensitivity files
  `rolling_reading_A.json` and `dataset_reading_A.json`,
  `null_actual_by_carrier.csv` and `results.md`. Written by
  `airline-delays predict`.
- `theory/` -- `model.json` (every identity of the congestion model with
  whether it holds, the reaction-slope bounds, the tolls, numeric examples,
  comparative statics, the low-cost entrant extension, the primer's discrete
  game and the bridge to the article's published signs), `figures.json` (the
  parameters and labelled points of every figure), `figures/*.svg` (eleven
  figures) and `results.md`. Written by `airline-delays theory` without a
  timestamp, so a second run on an unchanged tree changes nothing.
- `summary.json` -- every headline number the two READMEs, `data/README.md`
  and `CONTRIBUTING.md` quote, read from the manifests, the tables and the
  report files above by `airline-delays summary`; `scripts/check_prose_numbers.py`
  accepts no other number on those pages, and `tests/test_summary.py` fails
  when the committed file is stale.
