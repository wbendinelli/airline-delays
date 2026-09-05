"""The leakage rule of ADR-0009, run on the committed fixture.

Fixture only, offline, and fast: the whole module builds the fact table and the
modelling table from `tests/fixtures/vra_sample.parquet` once and then asks nine
questions of them. Nothing here reads `data/staged/`, `data/derived/` or the
network, so it runs in CI exactly as it runs locally.

The checks themselves live in `src/airline_delays/prediction/leakage.py` -- they are part of the
pipeline, not of the test suite, because `src/airline_delays/prediction/run.py` runs the same nine against
the *real* dataset and writes the answers to `reports/prediction/leakage.json`.
This module is the guarantee that they keep passing on data small enough to
reason about.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from airline_delays import schema
from airline_delays.prediction import dataset as ds
from airline_delays.prediction import leakage as lk
from airline_delays.prediction import split as sp
from airline_delays.prediction import train as tx

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def ml_dataset(tmp_path_factory, staged_tree: Path, built, groups_csv: Path, external_dir: Path):
    """The modelling table built from the fixture, plus what the checks compare it to."""
    import pandas as pd

    out = tmp_path_factory.mktemp("ml")
    result = ds.build_dataset(
        staged_tree,
        out,
        fact_path=Path(built["analysis"]) / "fact_group_route_month.parquet",
        external_dir=external_dir,
        groups_path=groups_csv,
        verbose=False,
    )
    frame = ds.read_dataset(out)
    staged = pd.concat(
        [pd.read_parquet(path) for path in sorted(staged_tree.glob("year=*/*.parquet"))],
        ignore_index=True,
    )
    return {"dir": out, "result": result, "frame": frame, "fact": built["fact"], "staged": staged}


class TestLeakage:
    """Every check of `ml.leakage_tests`, one test each, with its own message."""

    @pytest.mark.parametrize(
        "name",
        [
            "features_exclude_post_departure",
            "targets_are_not_features",
            "horizons_are_nested",
            "lag_windows_closed",
            "movements_from_schedule",
            "previous_leg_precedes_departure",
            "targets_null_without_actual",
            "first_year_has_no_p90",
            "calendar_matches_the_table",
        ],
    )
    def test_check(self, ml_dataset, external_dir: Path, name: str) -> None:
        checks = lk.run_all(
            ml_dataset["frame"], ml_dataset["fact"], ml_dataset["staged"], external_dir
        )
        found = {check.name: check for check in checks}
        assert name in found, f"{name} is not among {sorted(found)}"
        assert found[name].passed, str(found[name])

    def test_all_of_them_pass_together(self, ml_dataset, external_dir: Path) -> None:
        lk.assert_all(
            lk.run_all(ml_dataset["frame"], ml_dataset["fact"], ml_dataset["staged"], external_dir)
        )

    def test_a_planted_leak_is_caught(self, ml_dataset) -> None:
        """The checks are not vacuous: replacing t-1 with t must fail.

        Without this, every check above could be passing because it never looks.
        """
        frame = ml_dataset["frame"].copy()
        rate = (
            ds.collapse_fact(ml_dataset["fact"])
            .groupby(["route", "ym"], observed=True)[["arr_delay_obs", "arr_delayed_gt15"]]
            .sum()
        )
        rate = rate.reset_index()
        rate["leaked"] = rate["arr_delayed_gt15"] / rate["arr_delay_obs"].where(
            rate["arr_delay_obs"] > 0
        )
        frame["route"] = frame["route"].astype(str)
        rate["route"] = rate["route"].astype(str)
        frame = frame.drop(columns=["route_late15_l1"]).merge(
            rate[["route", "ym", "leaked"]].rename(columns={"leaked": "route_late15_l1"}),
            on=["route", "ym"],
            how="left",
        )
        assert not lk.check_lag_windows_closed(frame, ml_dataset["fact"]).passed


class TestDatasetShape:
    """What the modelling table must be before any model is trained on it."""

    def test_the_columns_are_exactly_the_declared_ones(self, ml_dataset) -> None:
        assert list(ml_dataset["frame"].columns) == list(ds.DATASET_COLUMNS)

    def test_the_registry_declares_the_same_columns_in_the_same_order(self) -> None:
        """Rule 5 of the build brief, closed in both directions for the `ml` layer.

        `src/airline_delays/schema.py` cannot import `airline_delays.prediction` -- the dependency runs the
        other way -- so the two lists are written twice and this is what keeps
        them one list.
        """
        assert list(schema.ML_NAMES) == list(ds.DATASET_COLUMNS)

    def test_every_built_column_resolves_to_a_definition(self, ml_dataset) -> None:
        described = schema.describe_frame(ml_dataset["frame"], "ml")
        assert [column.name for column in described] == list(ds.DATASET_COLUMNS)
        assert all(column.definition_en and column.definition_pt for column in described)

    def test_the_registry_dtypes_match_the_built_table(self, ml_dataset) -> None:
        schema.validate_schema(ml_dataset["frame"], schema.ML)

    def test_every_row_is_one_scheduled_flight_of_the_replication_universe(
        self, ml_dataset
    ) -> None:
        summary = ml_dataset["result"].summary_frame()
        assert (summary["rows"] == summary["universe_rows"] - summary["dropped_no_schedule"]).all()

    def test_the_arrival_target_never_covers_a_cancelled_flight(self, ml_dataset) -> None:
        frame = ml_dataset["frame"]
        assert frame.loc[frame["cancelled"] == 1, "late15_arr"].notna().sum() == 0

    def test_the_targets_are_binary_or_null(self, ml_dataset) -> None:
        frame = ml_dataset["frame"]
        for name in ds.BINARY_TARGETS:
            values = set(frame[name].dropna().unique().tolist())
            assert values <= {0.0, 1.0}, f"{name} carries {sorted(values)[:5]}"

    def test_no_feature_is_constant_everywhere(self, ml_dataset) -> None:
        """A feature with one value in the fixture is fine; in every year is not.

        Catches the join that silently produced nulls: a column that is null for
        every row of every year is a broken merge, not a feature.
        """
        frame = ml_dataset["frame"]
        empty = [name for name in ds.FEATURES_H1 if frame[name].notna().sum() == 0]
        assert empty == [], f"features null in every fixture row: {empty}"

    def test_dtypes_stay_tight(self, ml_dataset) -> None:
        frame = ml_dataset["frame"]
        wide = [
            name
            for name in frame.columns
            if str(frame[name].dtype) in {"float64", "int64", "object"} and name != "flight_date"
        ]
        assert wide == [], f"columns wider than declared: {wide}"


class TestSplit:
    """ADR-0009's two designs, and the sampling rule that protects them."""

    def test_rolling_folds_never_fit_on_their_test_year(self) -> None:
        for fold in sp.rolling_origin():
            fold.check()
            assert fold.valid_year == fold.test_years[0] - 1
            assert max(fold.train_years) < fold.valid_year

    def test_the_fixed_split_is_the_one_the_adr_declares(self) -> None:
        fold = sp.fixed_split()
        assert fold.train_years == tuple(range(2002, 2011))
        assert fold.valid_year == 2011
        assert fold.test_years == (2012, 2013)

    def test_a_test_year_inside_the_training_years_is_refused(self) -> None:
        bad = sp.Fold("bad", "rolling", (2002, 2003), 2003, (2004,))
        with pytest.raises(ValueError, match="validation year"):
            bad.check()

    def test_route_buckets_are_stable_and_whole(self, ml_dataset) -> None:
        """The same route lands in the same bucket in every year it flies."""
        frame = ml_dataset["frame"]
        buckets = sp.route_bucket(frame["route"])
        per_route = {}
        for route, bucket in zip(frame["route"].astype(str), buckets, strict=True):
            per_route.setdefault(route, set()).add(int(bucket))
        assert all(len(values) == 1 for values in per_route.values())

    def test_subsampling_keeps_whole_routes(self, ml_dataset) -> None:
        frame = ml_dataset["frame"]
        mask = sp.subsample_mask(frame, 0.5)
        kept = set(frame.loc[mask, "route"].astype(str))
        dropped = set(frame.loc[~mask, "route"].astype(str))
        assert not (kept & dropped), "a route was split across the sample boundary"


class TestHorizons:
    """The two horizons, as feature lists and as trained models."""

    def test_the_horizon_lists_match_the_dataset(self) -> None:
        assert set(tx.HORIZONS["D-1"]) == set(ds.FEATURES_D1)
        assert set(tx.HORIZONS["H-1"]) - set(tx.HORIZONS["D-1"]) == set(ds.FEATURES_H1_ONLY)

    def test_an_unknown_horizon_is_refused(self, ml_dataset) -> None:
        frame = ml_dataset["frame"]
        with pytest.raises(KeyError, match="unknown horizon"):
            tx.train(frame, frame, horizon="D-3")

    def test_a_model_trains_and_scores_on_the_fixture(self, ml_dataset) -> None:
        """End to end on 6,000 rows: fit, early-stop, predict a probability."""
        from airline_delays.prediction import evaluate as ev

        frame = ml_dataset["frame"]
        usable = frame[frame["late15_arr"].notna()]
        train_frame = usable[usable["year"] <= 2009]
        test_frame = usable[usable["year"] >= 2012]
        if len(train_frame) < 100 or len(test_frame) < 100:  # pragma: no cover - fixture guard
            pytest.skip("fixture too small for a model")
        fitted = tx.train(
            train_frame,
            test_frame,
            horizon="D-1",
            params={"n_estimators": 30, "max_depth": 3},
            n_jobs=2,
        )
        predicted = fitted.predict(test_frame)
        assert predicted.min() >= 0.0 and predicted.max() <= 1.0
        metrics = ev.binary_metrics(test_frame["late15_arr"].to_numpy(), predicted)
        assert metrics["n"] == len(test_frame)
        assert metrics["brier"] is not None


class TestEvaluate:
    """The metric helpers, on inputs whose answer is known by hand."""

    def test_a_perfect_ranking_scores_one(self) -> None:
        from airline_delays.prediction import evaluate as ev

        metrics = ev.binary_metrics([0, 0, 1, 1], [0.1, 0.2, 0.8, 0.9])
        assert metrics["auc"] == 1.0
        assert metrics["base_rate"] == 0.5

    def test_one_class_only_returns_none_instead_of_raising(self) -> None:
        from airline_delays.prediction import evaluate as ev

        metrics = ev.binary_metrics([1, 1, 1], [0.4, 0.5, 0.6])
        assert metrics["auc"] is None
        assert metrics["brier"] is not None

    def test_the_calibration_table_covers_every_row(self) -> None:
        from airline_delays.prediction import evaluate as ev

        rows = ev.calibration_table([0, 1, 0, 1, 1], [0.05, 0.95, 0.4, 0.6, 0.99])
        assert sum(row["n"] for row in rows) == 5
        assert all(row["bin_low"] <= row["mean_predicted"] <= row["bin_high"] for row in rows)

    def test_the_baseline_falls_back_to_the_training_rate(self, ml_dataset) -> None:
        import numpy as np

        from airline_delays.prediction import evaluate as ev

        frame = ml_dataset["frame"]
        values = ev.naive_predictions(frame, 0.25)["route_prevalence_l1"]
        missing = frame["route_late15_l1"].isna().to_numpy()
        assert np.all(values[missing] == 0.25)
        assert np.isfinite(values).all()
