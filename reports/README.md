# reports/

The three Typst reports of `airline-delays` -- replication, prediction and
theory -- with the generated JSON, Markdown and figures they read, and
`summary.json`, the numbers manifest the READMEs quote. The reports are written
in **Portuguese** (`DECISIONS.md`, ADR-0006); this page is the English index.

No number in a report is typed by hand: each report reads its inputs with
Typst's `json()` from the files a stage of the pipeline wrote. Compiled PDFs
land in a git-ignored `build` directory under `reports/`.

| Report | Inputs | Written by | Compile |
|---|---|---|---|
| `replication.typ` | `reports/replication/{results,summary,sensitivity}.json` | `just estimate` | `typst compile --root . reports/replication.typ reports/build/replication.pdf` |
| `prediction.typ` | `reports/prediction/{rolling,fixed,calibration,importance,dataset,leakage}.json` and `rolling_reading_A.json` | `just predict` | `typst compile --root . reports/prediction.typ reports/build/prediction.pdf` |
| `theory.typ` | `reports/theory/{model,figures}.json` and `reports/theory/figures/*.svg` | `just theory` | `typst compile --root . reports/theory.typ reports/build/theory.pdf` |

`just report` (`airline-delays report`) compiles the three in one go; it needs
`typst` on the PATH.

`sapians/` is the SAPIANS design package for Typst (`@local/sapians:0.1.0`),
vendored from `sapians-latex` (MIT) so that `reports/theory.typ` compiles from
a clean clone with the `--root .` flag above. The Inter font is used when
installed, with Helvetica Neue or Arial as the fallback the package declares.
The figures under `reports/theory/figures/` are drawn by
`src/airline_delays/theory/figures.py` with matplotlib in the SAPIANS figure
style (`src/airline_delays/theory/sapians_style.py`).

## What each directory holds

- `replication/` -- `results.json` (every re-estimated cell of Tables 2-7 next
  to its published value), `summary.json` (the scorecard: sign agreement,
  gaps in published standard errors, the HHI sign-inversion count),
  `sensitivity.json` (the main coefficients across outlier thresholds) and
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
  comparative statics, the low-cost entrant extension and the bridge to the
  article's published signs), `figures.json` (the parameters and labelled
  points of every figure), `figures/*.svg` (eleven figures) and `results.md`.
  Written by `airline-delays theory` without a timestamp, so a second run on
  an unchanged tree changes nothing.
- `summary.json` -- every headline number the two READMEs, `data/README.md`
  and `CONTRIBUTING.md` quote, read from the manifests, the tables and the
  report files above by `airline-delays summary`; `scripts/check_prose_numbers.py`
  accepts no other number on those pages, and `tests/test_summary.py` fails
  when the committed file is stale.
