# ml/

Flight-level delay prediction: `dataset_flights.py` (builds the modelling
table from the prediction universe, ADR-0002), `split.py` (the temporal
split and the rolling-origin evaluation, ADR-0009), `train_xgb.py`,
`evaluate.py` (AUC, PR-AUC, Brier, calibration, reported separately for the
day-ahead and at-gate horizons), and `leakage_tests.py` (nothing from after
departure, no same-period aggregate containing the flight being predicted,
historical windows closed before the flight date -- part of the test suite,
not just documentation).

Nothing under this directory exists yet; it lands with the prediction
phase (see `ROADMAP.md`).
