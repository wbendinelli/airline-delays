"""Universe filters and the guard against mixing them (ADR-0002)."""

from __future__ import annotations

import pytest

from airline_delays.definitions import universe


class TestReplicationUniverse:
    @pytest.mark.parametrize("line_type", ["N", "R", "E"])
    def test_the_three_line_types_with_di_zero_are_in(self, line_type: str) -> None:
        assert universe.in_universe_repl(line_type, 0)

    @pytest.mark.parametrize("line_type", ["I", "L", "H", "C", "G"])
    def test_every_other_line_type_is_out(self, line_type: str) -> None:
        assert not universe.in_universe_repl(line_type, 0)

    @pytest.mark.parametrize("di", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11])
    def test_only_di_zero_is_in(self, di: int) -> None:
        # Admitting DI 1 and 2 dropped agreement with the benchmark from 97%
        # to 54%; extras and return flights are features, never filters.
        assert not universe.in_universe_repl("N", di)

    def test_missing_fields_are_out(self) -> None:
        assert not universe.in_universe_repl(None, 0)
        assert not universe.in_universe_repl("N", None)

    def test_cancelled_flights_are_inside_the_replication_universe(self) -> None:
        # The benchmark's flight count includes cancellations: prcanc = fl_can / f.
        assert universe.in_universe_repl("N", 0)
        assert not universe.in_universe_ml("N", 0, universe.STATUS_CANCELLED)


class TestPredictionUniverse:
    def test_realised_only(self) -> None:
        assert universe.in_universe_ml("N", 0, universe.STATUS_REALIZED)
        assert not universe.in_universe_ml("N", 0, universe.STATUS_CANCELLED)
        assert not universe.in_universe_ml("N", 0, universe.STATUS_OTHER)

    def test_it_is_a_subset_of_the_replication_universe(self) -> None:
        for line_type in (*universe.LINE_TYPES_ALL, None):
            for di in (*range(12), None):
                for status in (*universe.STATUSES, None):
                    if universe.in_universe_ml(line_type, di, status):
                        assert universe.in_universe_repl(line_type, di)


class TestNoSilentMixing:
    def test_one_universe_passes(self) -> None:
        assert (
            universe.assert_single_universe(["route", "ym", "flights_repl", "cancelled_repl"])
            == "repl"
        )
        assert universe.assert_single_universe(["route", "ym", "delay_ml"]) == "ml"

    def test_keys_only_declares_nothing(self) -> None:
        assert universe.assert_single_universe(["route", "ym"]) is None

    def test_mixing_raises(self) -> None:
        with pytest.raises(ValueError, match="mix universes"):
            universe.assert_single_universe(["flights_repl", "delay_ml"])


class TestSql:
    def test_sql_and_python_agree(self, duck) -> None:
        rows = [
            (line_type, di, status)
            for line_type in ("N", "R", "E", "I", "C", "G", "L", "H")
            for di in (0, 1, 2, 3, 9)
            for status in universe.STATUSES
        ]
        duck.execute("CREATE TABLE t (line_type VARCHAR, di TINYINT, status VARCHAR)")
        duck.executemany("INSERT INTO t VALUES (?, ?, ?)", rows)
        got = duck.execute(
            f"SELECT line_type, di, status, {universe.UNIVERSE_REPL_SQL} AS repl, "
            f"{universe.UNIVERSE_ML_SQL} AS ml FROM t"
        ).fetchall()
        for line_type, di, status, repl, ml in got:
            assert repl == universe.in_universe_repl(line_type, di), (line_type, di)
            assert ml == universe.in_universe_ml(line_type, di, status), (line_type, di, status)


class TestStagedFixtureAgrees:
    def test_flags_follow_the_rule(self, staged_frame) -> None:
        import pandas as pd

        expected_repl = staged_frame["line_type"].isin(universe.LINE_TYPES_REPL) & staged_frame[
            "di"
        ].eq(0)
        assert (staged_frame["universe_repl"].fillna(False) == expected_repl).all()
        expected_ml = expected_repl & staged_frame["status"].eq(universe.STATUS_REALIZED)
        assert (staged_frame["universe_ml"].fillna(False) == expected_ml).all()
        assert not pd.isna(staged_frame["universe_repl"]).any()

    def test_ml_is_a_subset_of_repl_in_real_data(self, staged_frame) -> None:
        assert not (staged_frame["universe_ml"] & ~staged_frame["universe_repl"]).any()

    def test_the_replication_universe_keeps_cancellations(self, staged_frame) -> None:
        inside = staged_frame[staged_frame["universe_repl"]]
        assert (inside["status"] == universe.STATUS_CANCELLED).any()

    def test_status_vocabulary_is_closed(self, staged_frame) -> None:
        assert set(staged_frame["status"].dropna().unique()) <= set(universe.STATUSES)
