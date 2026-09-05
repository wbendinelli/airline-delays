"""Node map, route key and year-month key (ADR-0001)."""

from __future__ import annotations

import pytest

from airline_delays.definitions import nodes


class TestNodeMap:
    @pytest.mark.parametrize(
        ("airport", "expected"),
        [
            ("SBSP", "MRSP"),
            ("SBGR", "MRSP"),
            ("SBKP", "MRSP"),
            ("SBGL", "MRRJ"),
            ("SBRJ", "MRRJ"),
            ("SBBH", "MRBH"),
            ("SBCF", "MRBH"),
        ],
    )
    def test_the_seven_grouped_airports(self, airport: str, expected: str) -> None:
        assert nodes.node(airport) == expected

    def test_exactly_seven_airports_are_grouped(self) -> None:
        # ADR-0001 groups six airports into three nodes plus Viracopos into
        # São Paulo. A regrouping must be a decision, not a drive-by edit.
        assert len(nodes.METRO_NODES) == 7
        assert set(nodes.METRO_MEMBERS) == {"MRSP", "MRRJ", "MRBH"}

    def test_viracopos_is_inside_sao_paulo(self) -> None:
        assert nodes.node("SBKP") == "MRSP"
        assert "SBKP" in nodes.METRO_MEMBERS["MRSP"]

    @pytest.mark.parametrize("airport", ["SBAR", "SBBR", "SBCT", "SBPA", "KMIA", "SAEZ", "LIRF"])
    def test_every_other_airport_keeps_its_icao(self, airport: str) -> None:
        assert nodes.node(airport) == airport

    def test_no_airport_is_dropped(self) -> None:
        # The staged layer keeps every airport, including foreign ones.
        for airport in ("KJFK", "LPPT", "SUMU", "SBXX"):
            assert nodes.node(airport) is not None

    def test_case_and_padding_are_normalised(self) -> None:
        assert nodes.node(" sbgr ") == "MRSP"
        assert nodes.node("sbar") == "SBAR"

    def test_missing_airport_is_none(self) -> None:
        assert nodes.node(None) is None
        assert nodes.node("") is None
        assert nodes.node("   ") is None

    def test_members_and_map_agree(self) -> None:
        expanded = {
            airport: metro for metro, members in nodes.METRO_MEMBERS.items() for airport in members
        }
        assert expanded == nodes.METRO_NODES

    def test_sql_and_python_agree(self, duck) -> None:
        airports = [*nodes.METRO_NODES, "SBAR", "SBBR", "KMIA"]
        for airport in airports:
            got = duck.execute(f"SELECT {nodes.node_sql(chr(39) + airport + chr(39))}").fetchone()[
                0
            ]
            assert got == nodes.node(airport), airport


class TestRoute:
    def test_route_is_directional(self) -> None:
        assert nodes.route("MRSP", "SBAR") == "MRSP-SBAR"
        assert nodes.route("SBAR", "MRSP") == "SBAR-MRSP"
        assert nodes.route("MRSP", "SBAR") != nodes.route("SBAR", "MRSP")

    def test_route_is_built_on_nodes_not_airports(self) -> None:
        assert nodes.route(nodes.node("SBGR"), nodes.node("SBGL")) == "MRSP-MRRJ"
        assert nodes.route(nodes.node("SBSP"), nodes.node("SBRJ")) == "MRSP-MRRJ"

    def test_missing_side_is_none(self) -> None:
        assert nodes.route(None, "SBAR") is None
        assert nodes.route("SBAR", None) is None


class TestYearMonth:
    def test_shape(self) -> None:
        assert nodes.ym(2012, 3) == 201203
        assert nodes.ym(2000, 1) == 200001
        assert nodes.ym(2013, 12) == 201312

    def test_no_int16_overflow(self) -> None:
        # int16 * 100 overflowed in an earlier reconstruction and produced keys
        # that matched nothing; the key must stay a plain Python int.
        import numpy as np

        year = np.int16(2013)
        assert nodes.ym(int(year), 12) == 201312
        assert nodes.ym(2013, 12) > 32767

    def test_ordering_is_chronological(self) -> None:
        series = [nodes.ym(y, m) for y in range(2000, 2014) for m in range(1, 13)]
        assert series == sorted(series)
        assert len(set(series)) == 14 * 12

    def test_ym_of_date(self) -> None:
        from datetime import date

        assert nodes.ym_of(date(2009, 7, 4)) == 200907


class TestStagedFixtureAgrees:
    def test_nodes_in_the_fixture_follow_the_map(self, staged_frame) -> None:
        for icao, node_code in zip(
            staged_frame["origin_icao"], staged_frame["origin_node"], strict=True
        ):
            assert node_code == nodes.node(icao)

    def test_routes_in_the_fixture_are_node_pairs(self, staged_frame) -> None:
        rebuilt = staged_frame["origin_node"] + "-" + staged_frame["dest_node"]
        assert (rebuilt == staged_frame["route"]).all()

    def test_ym_in_the_fixture_matches_year_and_month(self, staged_frame) -> None:
        # A handful of real rows carry an unparseable date and so have no
        # year, month or ym at all; the three must be null together.
        dated = staged_frame.dropna(subset=["flight_date"])
        rebuilt = dated["year"].astype("int64") * 100 + dated["month"].astype("int64")
        assert (rebuilt == dated["ym"].astype("int64")).all()
        undated = staged_frame[staged_frame["flight_date"].isna()]
        assert undated[["year", "month", "ym"]].isna().all().all()
