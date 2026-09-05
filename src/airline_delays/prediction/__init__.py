"""Flight-level delay prediction with temporal validation (ADR-0009, ADR-0012).

Five modules, in the order they run:

`dataset_flights`
    One DuckDB scan per staged year that writes `data/derived/ml/`: one row per
    scheduled flight of the replication universe, pre-departure features only.
`split`
    The rolling-origin folds 2006-2013 (the headline) and the fixed
    2002-2010 / 2011 / 2012-2013 split (illustrative).
`train_xgb`
    XGBoost `hist` with early stopping on each fold's validation year, for the
    two horizons D-1 (day before) and H-1 (at the gate).
`evaluate`
    AUC, PR-AUC, Brier, the calibration table, the two naive baselines and
    permutation importance.
`leakage_tests`
    The executable form of the leakage rule; `tests/test_leakage.py` runs it on
    the committed fixture.

`run` drives all five and writes `reports/prediction/`.
"""

from __future__ import annotations

__all__ = [
    "dataset_flights",
    "evaluate",
    "leakage_tests",
    "split",
    "train_xgb",
]
