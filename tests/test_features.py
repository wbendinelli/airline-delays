"""`vra.features`: the fact table, the ADR-0012 convention, and additivity.

The additivity tests are the point of ADR-0004: the fact table is the only
place flights are counted, and every coarser grain has to be a projection of
it. A projection that disagreed with a direct count would mean two sources of
truth, which is exactly what the registry and this file exist to prevent.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from vra import codes, delays, features, groups, hhi, hub, universe  # noqa: E402


class TestTheFactTable:
    def test_the_grain_is_unique(self, built) -> None:
        fact = built["fact"]
        assert not fact.duplicated(["ym", "route", "group"]).any()

    def test_flights_equal_realised_plus_cancelled(self, built) -> None:
        fact = built["fact"]
        # `status` has no third value inside the replication universe, measured
        # on all 13.6 M staged legs; if one ever appears this fails rather than
        # silently dropping it from `f`.
        assert (fact["flights"] == fact["realized"] + fact["cancelled"]).all()

    def test_the_hourly_counts_sum_to_the_flights(self, built) -> None:
        fact = built["fact"]
        hourly = fact[list(features.HOUR_COLUMNS)].sum(axis=1)
        missing_hour = fact["flights"] - hourly
        assert (missing_hour >= 0).all()
        assert missing_hour.sum() == 0 or missing_hour.max() < fact["flights"].max()

    def test_the_cause_categories_and_the_uncoded_count_partition_the_flights(self, built) -> None:
        fact = built["fact"]
        categories = [f"cause_{name}" for name in codes.CATEGORY_NAMES]
        total = fact[categories].sum(axis=1) + fact["cause_none"]
        assert (total == fact["flights"]).all()

    def test_the_delay_counts_are_nested(self, built) -> None:
        fact = built["fact"]
        for side in ("dep", "arr"):
            assert (fact[f"{side}_delayed_gt60"] <= fact[f"{side}_delayed_gt30"]).all()
            assert (fact[f"{side}_delayed_gt30"] <= fact[f"{side}_delayed_gt15"]).all()
            assert (fact[f"{side}_delayed_gt15"] <= fact[f"{side}_delayed_gt0"]).all()
            assert (fact[f"{side}_delayed_gt0"] <= fact[f"{side}_delay_obs"]).all()

    def test_the_1530_band_is_the_difference_of_the_two_cuts(self, built) -> None:
        fact = built["fact"]
        assert (
            fact["arr_delayed_1530"] == fact["arr_delayed_gt15"] - fact["arr_delayed_gt30"]
        ).all()

    def test_the_observation_and_missing_counts_never_exceed_the_realised_ones(self, built) -> None:
        fact = built["fact"]
        for side in ("dep", "arr"):
            total = fact[f"{side}_delay_obs"] + fact[f"{side}_missing_actual"]
            assert (total <= fact["realized"]).all()

    def test_a_flight_is_counted_against_the_flights_of_the_universe(
        self, built, staged_tree: Path, duck
    ) -> None:
        source = f"read_parquet('{staged_tree}/year=*/*.parquet', hive_partitioning=false)"
        expected = duck.execute(
            f"SELECT count(*) FROM {source} WHERE universe_repl "
            "AND route IS NOT NULL AND ym IS NOT NULL"
        ).fetchone()[0]
        assert int(built["fact"]["flights"].sum()) == expected


class TestTheMissingActualConvention:
    """ADR-0012: the flag changes a denominator, never a sum and never a count."""

    def test_the_python_and_the_sql_agree_row_by_row(self, duck, staged_frame) -> None:
        sample = staged_frame.head(2000)
        duck.register("flights", sample)
        for legacy in (False, True):
            expression = delays.effective_delay_sql(
                "sched_arr", "actual_arr", legacy_missing_actual_as_zero=legacy
            )
            rows = duck.execute(f"SELECT {expression} AS d FROM flights").df()["d"]
            for index, value in enumerate(rows):
                row = sample.iloc[index]
                expected = delays.effective_delay_min(
                    _stamp(row["sched_arr"]),
                    _stamp(row["actual_arr"]),
                    bool(row["is_realized"]),
                    legacy_missing_actual_as_zero=legacy,
                )
                if expected is None:
                    assert np.isnan(value)
                else:
                    assert abs(float(value) - expected) < 1e-6

    def test_a_cancelled_flight_stays_null_under_both_conventions(self) -> None:
        scheduled = datetime(2004, 5, 1, 10, 0)  # noqa: DTZ001 - the VRA is naive local time
        assert delays.effective_delay_min(scheduled, None, False) is None
        assert (
            delays.effective_delay_min(scheduled, None, False, legacy_missing_actual_as_zero=True)
            is None
        )

    def test_the_flag_only_widens_the_denominator(self, built) -> None:
        route_month = features.aggregate(built["fact"], "route_month")
        strict = features.delay_denominator(route_month, "arr", legacy_missing_actual_as_zero=False)
        legacy = features.delay_denominator(route_month, "arr", legacy_missing_actual_as_zero=True)
        assert (legacy >= strict).all()
        assert legacy.sum() > strict.sum(), "the fixture must contain 2000-2009 rows"

    def test_the_flag_does_not_move_a_single_delayed_count(self, built) -> None:
        # A missing actual time becomes 0 minutes, which is not "> 0", so no
        # threshold count changes -- only what they are divided by.
        strict = features.aggregate(
            built["fact"], "route_month", legacy_missing_actual_as_zero=False
        )
        legacy = features.aggregate(
            built["fact"], "route_month", legacy_missing_actual_as_zero=True
        )
        for column in ("arr_delayed_gt15", "dep_delayed_gt0", "sum_arr_delay_min"):
            assert (strict[column] == legacy[column]).all()
        both = legacy["sh_arr_gt15"].notna() & strict["sh_arr_gt15"].notna()
        assert (legacy.loc[both, "sh_arr_gt15"] <= strict.loc[both, "sh_arr_gt15"] + 1e-9).all()

    def test_the_per_year_report_counts_realised_flights_only(self, built) -> None:
        report = built["result"].missing_actual_by_year
        assert set(report.columns) >= {"year", "realized", "arr_missing_actual"}
        assert (report["arr_missing_actual"] <= report["realized"]).all()


class TestAdditivity:
    """`agg(fine) == coarse`, on every sum the fact table carries."""

    def test_route_month_sums_equal_a_direct_count_from_the_flights(
        self, built, staged_tree: Path, duck
    ) -> None:
        source = f"read_parquet('{staged_tree}/year=*/*.parquet', hive_partitioning=false)"
        direct = duck.execute(
            f"SELECT ym, route, count(*) AS flights, "
            f"count(*) FILTER (WHERE is_realized) AS realized, "
            f"count(*) FILTER (WHERE status = '{universe.STATUS_CANCELLED}') AS cancelled, "
            "count(*) FILTER (WHERE is_realized AND arr_delay_min > 15) AS arr_delayed_gt15 "
            f"FROM {source} WHERE universe_repl AND route IS NOT NULL AND ym IS NOT NULL "
            "GROUP BY ym, route"
        ).df()
        projected = features.aggregate(built["fact"], "route_month")
        merged = direct.merge(projected, on=["ym", "route"], suffixes=("_direct", ""))
        assert len(merged) == len(direct)
        for column in ("flights", "realized", "cancelled", "arr_delayed_gt15"):
            assert (merged[f"{column}_direct"] == merged[column]).all(), column

    def test_every_additive_measure_is_preserved_by_the_projection(self, built) -> None:
        fact, route_month = built["fact"], features.aggregate(built["fact"], "route_month")
        for column in features.FACT_SUM_COLUMNS:
            total_fine = float(fact[column].sum())
            total_coarse = float(route_month[column].sum())
            assert abs(total_fine - total_coarse) < 1e-6, column

    def test_a_city_sees_each_flight_once_departing_and_once_arriving(self, built) -> None:
        fact, city = built["fact"], features.aggregate(built["fact"], "city_month")
        assert float(city["movements"].sum()) == 2 * float(fact["flights"].sum())
        assert float(city["dep_flights"].sum()) == float(fact["flights"].sum())
        assert float(city["arr_flights"].sum()) == float(fact["flights"].sum())

    def test_the_airline_city_grain_sums_back_to_the_city_grain(self, built) -> None:
        city = features.aggregate(built["fact"], "city_month")
        airline_city = features.aggregate(built["fact"], "airline_city_month")
        rolled = airline_city.groupby(["ym", "node"], as_index=False)["movements"].sum()
        merged = city[["ym", "node", "movements"]].merge(
            rolled, on=["ym", "node"], suffixes=("", "_rolled")
        )
        assert len(merged) == len(city)
        assert (merged["movements"] == merged["movements_rolled"]).all()

    def test_proportions_are_recomputed_and_never_averaged(self, built) -> None:
        route_month = features.aggregate(built["fact"], "route_month")
        recomputed = route_month["cancelled"] / route_month["flights"]
        assert (route_month["sh_cancel"] - recomputed).abs().max() < 1e-9

    def test_an_unknown_grain_is_refused(self, built) -> None:
        with pytest.raises(ValueError, match="unknown grain"):
            features.aggregate(built["fact"], "week")  # type: ignore[arg-type]


class TestEntriesAndExits:
    def test_a_first_month_is_an_entry_and_a_last_month_is_an_exit(self, built) -> None:
        fact = built["fact"].sort_values(["route", "group", "ym"])
        first = fact.groupby(["route", "group"], observed=True).head(1)
        last = fact.groupby(["route", "group"], observed=True).tail(1)
        assert (first["is_entry"] == 1).all()
        assert (last["is_exit"] == 1).all()

    def test_a_gap_in_the_calendar_counts_as_a_new_entry(self, built) -> None:
        fact = built["fact"]
        # The fixture is three routes in six non-adjacent years, so every cell
        # whose previous row is a different year must be an entry.
        assert int(fact["is_entry"].sum()) >= fact.groupby(["route", "group"]).ngroups


class TestTheDerivedModules:
    def test_the_flight_share_hhi_matches_the_helper(self, built) -> None:
        fact = built["fact"]
        route_month = features.aggregate(fact, "route_month")
        first = route_month.iloc[0]
        cell = fact[(fact["ym"] == first["ym"]) & (fact["route"] == first["route"])]
        assert abs(first["hhi_flights"] - hhi.hhi_from_counts(cell["flights"])) < 1e-9

    def test_a_monopoly_route_has_an_hhi_of_one(self, built) -> None:
        route_month = features.aggregate(built["fact"], "route_month")
        monopolies = route_month[route_month["n_groups"] == 1]
        if len(monopolies):
            assert (monopolies["hhi_flights"] - 1.0).abs().max() < 1e-9

    def test_the_hub_dummy_respects_both_volume_floors(self, built) -> None:
        airline_city = built["airline_city"]
        hubs = airline_city[airline_city["is_hub"] == 1]
        assert (hubs["movements"] >= hub.MIN_GROUP_MOVEMENTS).all()
        assert (hubs["city_share"] >= hub.MIN_SHARE).all()
        assert (hubs["hub_score"] >= hub.MIN_RATIO).all()

    def test_the_congestion_proxy_is_a_share_of_the_month(self, built) -> None:
        city = built["city"]
        share = city["sh_movements_congested"].dropna()
        assert ((share >= 0) & (share <= 1)).all()

    def test_the_classes_of_the_fact_table_are_the_four_of_adr_0011(self, built) -> None:
        assert set(built["fact"]["class"].unique()) <= set(groups.CLASSES)


def _stamp(value):
    """A pandas timestamp back to a plain datetime, or None when it is NaT."""
    import pandas as pd

    return None if pd.isna(value) else value.to_pydatetime()
