# ml/

Flight-level delay prediction with temporal validation (ADR-0009, ADR-0012).
Run it with `just ml` (rebuilds `data/derived/ml/` and writes
`reports/prediction/`); `just ml-dataset` stops after the table.

| module | what it owns |
|---|---|
| `dataset_flights.py` | one DuckDB scan per staged year -> `data/derived/ml/year=YYYY/part-0.parquet`: one row per scheduled flight of the replication universe (ADR-0002), pre-departure features only, the rotation link, the closed-window lags, and the five targets. |
| `split.py` | the rolling origin 2006-2013 (headline) and the fixed 2002-2010 / 2011 / 2012-2013 split (illustrative); route-hash subsampling for when a fold does not fit. |
| `train_xgb.py` | XGBoost `hist` with early stopping on the fold's validation year, for the two horizons D-1 and H-1; LightGBM as an optional second learner. |
| `evaluate.py` | AUC, PR-AUC, Brier, the calibration table, the two naive baselines and permutation importance. |
| `leakage_tests.py` | the nine checks of the ADR-0009 leakage rule, run on the fixture by `tests/test_leakage.py` and on the real dataset by `run.py`. |
| `run.py` | drives all of it and writes `reports/prediction/*.json` and `results.md`. |

Two things to know before reading any number out of this directory.

**The pre-2010 target is a selected sample.** In the 2000-2009 raw files an
actual timestamp is written only when there was an occurrence, so under
ADR-0012 (`legacy_missing_actual_as_zero=False`) 55-80% of realised flights
have no arrival target at all, and the survivors are 75-94% late. From 2010 on
almost every flight has a timestamp and the late rate is 16-25%. A metric for a
test year before 2010 describes a different population from a metric after it.

**D-1 and H-1 are different problems, not two tunings of one.** D-1 knows the
schedule and closed history; H-1 adds the inbound leg's realised arrival, which
exists for 20-39% of flights depending on the year. Mixing them is the standard
mistake, and `leakage_tests.check_horizons_are_nested` is what stops it here.
