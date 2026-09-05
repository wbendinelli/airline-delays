"""`airline_delays.definitions.carriers`: the dated airline -> group/class map of ADR-0003 and ADR-0011."""

from __future__ import annotations

from pathlib import Path

import pytest

from airline_delays.definitions import carriers


@pytest.fixture(scope="module")
def table(groups_csv: Path) -> carriers.GroupTable:
    return carriers.GroupTable.load(groups_csv)


class TestTheTableLoads:
    def test_every_class_is_one_of_the_four_of_adr_0011(self, table: carriers.GroupTable) -> None:
        assert {period.klass for period in table.periods} <= set(carriers.CLASSES)

    def test_no_airline_has_two_overlapping_periods(self, table: carriers.GroupTable) -> None:
        # An overlap would duplicate every flight of that airline in the join.
        table.assert_no_overlap()

    def test_a_missing_required_column_is_refused(self, tmp_path: Path) -> None:
        broken = tmp_path / "groups.csv"
        broken.write_text("airline,group,start\nGLO,GOL,2001-01\n", encoding="utf-8")
        with pytest.raises(ValueError, match="missing columns"):
            carriers.GroupTable.load(broken)

    def test_an_overlap_is_refused_rather_than_joined(self, tmp_path: Path) -> None:
        broken = tmp_path / "groups.csv"
        broken.write_text(
            "airline,group,start,end,class\nGLO,GOL,2000-01,2010-12,LCC\nGLO,OTHER,2005-01,,LCC\n",
            encoding="utf-8",
        )
        with pytest.raises(ValueError, match="overlap"):
            carriers.GroupTable.load(broken)

    def test_an_unknown_class_is_refused_rather_than_becoming_a_category(
        self, tmp_path: Path
    ) -> None:
        broken = tmp_path / "groups.csv"
        broken.write_text("airline,group,start,end,class\nGLO,GOL,2000-01,,lowcost\n", "utf-8")
        with pytest.raises(ValueError, match="unknown classes"):
            carriers.GroupTable.load(broken)


class TestTheMergerDates:
    """The five transitions ADR-0003 fixes, checked on the month either side."""

    @pytest.mark.parametrize(
        ("airline", "before_ym", "before", "after_ym", "after"),
        [
            ("VRG", 200703, "VARIG", 200704, "GOL"),
            ("WEB", 201110, "WEBJET", 201111, "GOL"),
            ("PTN", 200911, "PANTANAL", 200912, "TAM"),
            ("TTL", 200710, "TOTAL", 200711, "TRIP"),
            ("TIB", 201204, "TRIP", 201205, "AZUL"),
            ("TTL", 201204, "TRIP", 201205, "AZUL"),
        ],
    )
    def test_the_group_switches_on_the_declared_month(
        self,
        table: carriers.GroupTable,
        airline: str,
        before_ym: int,
        before: str,
        after_ym: int,
        after: str,
    ) -> None:
        assert table.group_of(airline, before_ym) == before
        assert table.group_of(airline, after_ym) == after

    @pytest.mark.parametrize(
        ("airline", "ym", "expected"),
        [
            ("PTN", 200911, "regional"),
            ("PTN", 200912, "FSC"),
            ("TIB", 201204, "regional"),
            ("TIB", 201205, "LCC"),
            ("TTL", 201205, "LCC"),
            ("VRG", 200704, "LCC"),
        ],
    )
    def test_class_follows_the_absorbing_group(
        self, table: carriers.GroupTable, airline: str, ym: int, expected: str
    ) -> None:
        assert table.class_of(airline, ym) == expected


class TestTheUnlabelledAirline:
    def test_an_unknown_code_is_other_not_null(self, table: carriers.GroupTable) -> None:
        assert table.class_of("ZZZ", 200501) == carriers.DEFAULT_CLASS == "other"

    def test_an_unknown_code_keeps_its_own_icao_as_group(self, table: carriers.GroupTable) -> None:
        # Keeping the code makes it a distinguishable competitor in the HHI
        # instead of collapsing every foreign carrier into one pseudo-group.
        assert table.group_of("ZZZ", 200501) == "ZZZ"

    def test_a_labelled_airline_outside_its_period_falls_back_the_same_way(
        self, table: carriers.GroupTable
    ) -> None:
        assert table.group_of("VSP", 201301) == "VSP"
        assert table.class_of("VSP", 201301) == "other"


class TestTheBenchmarkSets:
    def test_the_article_fsc_set_is_not_the_fsc_class(self, table: carriers.GroupTable) -> None:
        fsc_class = {p.group for p in table.periods if p.klass == "FSC"}
        assert set(carriers.ARTICLE_FSC_GROUPS) < fsc_class
        assert fsc_class - set(carriers.ARTICLE_FSC_GROUPS) == {"AVIANCA_BRASIL"}

    def test_the_article_lcc_set_is_not_the_lcc_class(self, table: carriers.GroupTable) -> None:
        lcc_class = {p.group for p in table.periods if p.klass == "LCC"}
        assert set(carriers.ARTICLE_LCC_GROUPS) < lcc_class
        assert lcc_class - set(carriers.ARTICLE_LCC_GROUPS) == {"WEBJET"}


class TestTheSqlAndThePythonAgree:
    def test_the_join_labels_every_flight_the_way_the_lookup_does(
        self, duck, groups_csv: Path, staged_frame
    ) -> None:
        table = carriers.GroupTable.load(groups_csv)
        table.register(duck)
        duck.register("flights", staged_frame[["airline", "ym"]].dropna().head(500))
        query = (
            f"SELECT f.airline, f.ym, {carriers.resolved_group_sql('f.airline')} AS grp, "
            f"{carriers.resolved_class_sql()} AS cls "
            f"FROM flights f {carriers.label_sql('f.airline', 'f.ym')}"
        )
        rows = duck.execute(query).df()
        assert len(rows) == len(staged_frame[["airline", "ym"]].dropna().head(500))
        for row in rows.itertuples():
            assert row.grp == table.group_of(row.airline, int(row.ym))
            assert row.cls == table.class_of(row.airline, int(row.ym))
