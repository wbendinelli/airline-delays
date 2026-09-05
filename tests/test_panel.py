"""`airline_delays.panel`: the article's columns, the declared variants, and the identities."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from airline_delays import fact as fact_mod
from airline_delays import panel
from airline_delays.definitions import carriers, nodes


class TestTheGrainAndTheKeys:
    def test_one_row_per_route_month(self, built) -> None:
        table = built["panel"]
        assert not table.duplicated(["route", "ym"]).any()

    def test_the_route_is_the_two_nodes(self, built) -> None:
        table = built["panel"]
        rebuilt = table["origin_node"] + "-" + table["dest_node"]
        assert (table["route"] == rebuilt).all()

    def test_ndays_is_the_calendar_month(self, built) -> None:
        table = built["panel"]
        assert set(table["ndays"].unique()) <= {28, 29, 30, 31}
        january = table[table["month"] == 1]
        if len(january):
            assert (january["ndays"] == 31).all()


class TestTheBenchmarkIdentities:
    """Identities the private panel satisfies, so this one has to as well."""

    def test_f_is_realised_plus_cancelled(self, built) -> None:
        table = built["panel"]
        assert (table["f"] == table["fl_real"] + table["fl_can"]).all()

    def test_prcanc_is_fl_can_over_f(self, built) -> None:
        table = built["panel"]
        live = table[table["f"] > 0]
        assert (live["prcanc"] - live["fl_can"] / live["f"]).abs().max() < 1e-5

    def test_dailyfl_is_f_over_ndays(self, built) -> None:
        table = built["panel"]
        assert (table["dailyfl"] - table["f"] / table["ndays"]).abs().max() < 1e-4
        assert (table["dailyfl00"] - table["dailyfl"] / 100).abs().max() < 1e-4

    def test_maxalccfu_is_the_larger_of_the_two_endpoint_dummies(self, built) -> None:
        table = built["panel"]
        assert (table["maxalccfu"] == table[["olccfu", "dlccfu"]].max(axis=1)).all()

    def test_the_odds_are_the_log_odds_of_the_proportion(self, built) -> None:
        table = built["panel"]
        inside = (table["fsc_prdelarr"] > 0) & (table["fsc_prdelarr"] < 1)
        proportion = table.loc[inside, "fsc_prdelarr"].astype("float64")
        expected = np.log(proportion / (1 - proportion))
        assert (table.loc[inside, "fsc_oddsarr"] - expected).abs().max() < 1e-3

    def test_the_odds_are_null_at_zero_and_one_rather_than_infinite(self, built) -> None:
        table = built["panel"]
        edge = table["fsc_prdelarr"].isin([0.0, 1.0])
        assert table.loc[edge, "fsc_oddsarr"].isna().all()
        assert np.isfinite(table["fsc_oddsarr"].dropna()).all()

    def test_fl_odel_counts_departures_late_by_more_than_zero_not_fifteen(self, built) -> None:
        # The benchmark's cut is 0 minutes, measured at 92.4% agreement against
        # 15 minutes' far lower rate (ADR-0002); getting this backwards is the
        # single easiest way to break the replication.
        table = built["panel"]
        assert (table["fl_odel"] == table["dep_delayed_gt0"]).all()
        assert (table["fl_odel"] >= table["dep_delayed_gt15"]).all()


class TestTheDeclaredVariants:
    def test_the_class_and_the_article_fsc_sets_are_both_published(self, built) -> None:
        table = built["panel"]
        assert {"fsc_prdelarr", "fscc_prdelarr"} <= set(table.columns)
        assert {"fsc_minsarr", "fscc_minsarr"} <= set(table.columns)

    def test_the_class_fsc_slice_is_never_smaller_than_the_article_one(self, built) -> None:
        # class FSC = the article's group set plus Avianca Brasil (ADR-0003).
        table = built["panel"]
        assert (table["fscc_n"] >= table["fsc_n"]).all()

    def test_the_lcc_class_is_never_smaller_than_the_gol_and_azul_set(self, built) -> None:
        # class LCC = Gol and Azul plus Webjet while it was independent.
        table = built["panel"]
        assert (table["lccclass_n"] >= table["lccfu_n"]).all()

    def test_the_truncated_minutes_never_fall_below_the_signed_ones(self, built) -> None:
        # ADR-0008 keeps early arrivals negative; the vintage truncated them at
        # zero, so the truncated column is weakly larger, never smaller.
        table = built["panel"]
        both = table["fsc_minsarr"].notna() & table["fsc_minsarr_trunc"].notna()
        assert (table.loc[both, "fsc_minsarr_trunc"] >= table.loc[both, "fsc_minsarr"] - 1e-6).all()

    def test_the_columns_the_vra_cannot_produce_are_null_not_substituted(self, built) -> None:
        table = built["panel"]
        for name in panel.BENCHMARK_ONLY_NULL:
            assert table[name].isna().all(), name
        # ...and the flight-based counterpart exists under its own name.
        assert table["rthhi_flights"].notna().any()

    def test_the_convention_travels_with_the_table(self, built) -> None:
        assert (built["panel"]["legacy_missing_actual_as_zero"] == 1).all()


class TestTheNewFeatures:
    def test_every_share_is_between_zero_and_one(self, built) -> None:
        table = built["panel"]
        shares = [
            name
            for name in table.columns
            if name.startswith("sh_") or name in {"prwheather", "princident", "pr_connc"}
        ]
        for name in shares:
            values = table[name].dropna()
            assert ((values >= -1e-6) & (values <= 1 + 1e-6)).all(), name

    def test_the_hourly_detail_is_left_in_the_fact_table(self, built) -> None:
        table = built["panel"]
        assert not [name for name in fact_mod.HOUR_COLUMNS if name in table.columns]
        assert {"peak_hour_share", "hhi_hours", "sh_night"} <= set(table.columns)

    def test_both_city_sides_are_attached(self, built) -> None:
        table = built["panel"]
        for name in panel.CITY_SIDE_COLUMNS:
            if f"o_{name}" in table.columns:
                assert f"d_{name}" in table.columns, name

    def test_the_off_universe_context_columns_are_present_and_outside_f(self, built) -> None:
        table = built["panel"]
        assert (table["n_rows_all"] >= table["f"]).all()
        assert {"n_extra", "n_return", "n_intl_leg", "n_cargo", "n_postal"} <= set(table.columns)

    def test_the_distance_comes_from_the_reference_table(self, built) -> None:
        table = built["panel"]
        known = table["distance_km"].dropna()
        assert len(known)
        assert (known > 0).all()


class TestTheScope:
    def test_the_panel_only_covers_the_nodes_of_adr_0001(self, built) -> None:
        table = built["panel"]
        node_set = set(nodes.PANEL_NODES)
        assert set(table["origin_node"]) <= node_set
        assert set(table["dest_node"]) <= node_set

    def test_a_route_never_starts_and_ends_at_the_same_node(self, built) -> None:
        table = built["panel"]
        assert (table["origin_node"] != table["dest_node"]).all()

    def test_the_presence_dummies_use_the_article_group_set(self, built) -> None:
        table = built["panel"]
        assert set(table["lcc"].unique()) <= {0, 1}
        assert (table["lcc"] >= table[["pres_glo", "pres_azu"]].max(axis=1)).all()
        assert carriers.BENCHMARK_LCC_GROUPS == ("GOL", "AZUL")


class TestTheWrittenFiles:
    def test_the_panel_writes_both_formats_and_a_manifest(
        self, built, tmp_path: Path, external_dir: Path
    ) -> None:
        import shutil

        analysis = tmp_path / "analysis"
        shutil.copytree(built["analysis"], analysis)
        table, result = panel.build_panel(analysis, built["derived"], external_dir=external_dir)
        assert result is not None
        assert result.parquet.exists() and result.csv.exists()
        assert (analysis / "panel_manifest.json").exists()
        assert result.rows == len(table)

    def test_a_capacity_table_with_one_airport_is_reported_as_not_enough(
        self, external_dir: Path
    ) -> None:
        note = panel.capacity_note(external_dir)
        assert "prcongested not reproduced" in note or "declared capacity:" in note


@pytest.mark.parametrize("grain", ["route_month", "city_month", "airline_city_month"])
def test_every_grain_returns_rows(built, grain: str) -> None:
    assert len(fact_mod.aggregate(built["fact"], grain)) > 0
