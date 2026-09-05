# ml/

Flight-level delay prediction with temporal validation (ADR-0009, ADR-0015,
ADR-0017). Run it with `just ml` (rebuilds `data/derived/ml/` and writes
`reports/prediction/`); `just ml-dataset` stops after the table.

| module | what it owns |
|---|---|
| `dataset_flights.py` | one DuckDB scan per calendar year -> `data/derived/ml/year=YYYY/part-0.parquet`: one row per scheduled flight of the replication universe (ADR-0002), pre-departure features only, the rotation link, the closed-window lags, and the five targets. |
| `split.py` | the rolling origin 2006-2013 (headline) and the fixed 2002-2010 / 2011 / 2012-2013 split (illustrative); route-hash subsampling for when a fold does not fit. |
| `train_xgb.py` | XGBoost `hist` with early stopping on the fold's validation year, for the two horizons D-1 and H-1; LightGBM as an optional second learner. |
| `evaluate.py` | AUC, PR-AUC, Brier, the calibration table, the two naive baselines and permutation importance. |
| `leakage_tests.py` | the nine checks of the ADR-0009 leakage rule, run on the fixture by `tests/test_leakage.py` and on the real dataset by `run.py`. |
| `run.py` | drives all of it and writes `reports/prediction/*.json` and `results.md`. |

Two things to know before reading any number out of this directory.

**The pre-2010 target is a floor, not a measurement** (ADR-0017). In the
2000-2009 raw files an actual timestamp is a field of the Boletim de Alteração
de Vôo, which IAC 1504 requires only when there is an alteration, so an empty
one on a realised flight means no alteration was reported. Reading B takes that
at face value — delay 0, flagged `on_time_no_bav` — for realised flights of
carriers whose class is FSC, LCC or regional; `other` and unlabelled carriers
(foreign operators, the non-operating side of a code-share) keep no target,
because their null rate is a different rate: 83.0% over 2000-2009 against 72.9%
for the carriers in scope, and 90-100% for the foreign carriers the sceptical
reviewer measured outside this universe in 2005. A
delay the carrier never reported therefore counts as on time, and the pre-2010
late rate is a lower bound. `reports/prediction/results.md` carries the headline
metrics under the superseded reading A alongside, and
`docs/declared-differences.md` the null rate by carrier and year.

**D-1 and H-1 are different problems, not two tunings of one.** D-1 knows the
schedule and closed history; H-1 adds the inbound leg's realised arrival, which
exists for 20-39% of flights depending on the year. Mixing them is the standard
mistake, and `leakage_tests.check_horizons_are_nested` is what stops it here.
