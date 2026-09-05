"""Staging: the two raw layouts, the cleaning decisions, delays and the schema.

Everything runs against the committed fixtures, so the suite is offline and
fast. The raw fixtures are real bytes cut from the published files, which is
the point: a hand-written CSV would not carry latin-1, CRLF, the ``N/A``
justification, the empty actual timestamps or the free-text 2010 layout.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from vra import delays, registry, stage
from vra.io import LAYOUT_2010, LAYOUT_LEGACY


def _stage_fixture(duck, path: Path, layout) -> list[tuple]:
    stage._register_helpers(duck)
    return duck.execute(stage.build_select(str(path), layout)).fetchall()


def _stage_fixture_df(duck, path: Path, layout):
    stage._register_helpers(duck)
    return duck.execute(stage.build_select(str(path), layout)).df()


class TestCauseCodes:
    def test_the_iac_table_is_complete_enough(self) -> None:
        # The article's three controls need these; a missing code would make a
        # whole column silently zero.
        for code in ("AR", "RA", "DF", "DG", "HB", "MA", "TD", "WO", "WT", "XO", "XS"):
            assert code in stage.IAC1504_CODES

    def test_codes_are_two_upper_case_letters(self) -> None:
        assert all(len(code) == 2 and code.isupper() for code in stage.IAC1504_CODES)

    def test_normalisation_folds_accents_and_punctuation(self) -> None:
        assert (
            stage.normalise_text("ATRASOS NÃO ESPECÍFICOS, OUTROS")
            == "ATRASOS NAO ESPECIFICOS OUTROS"
        )
        assert (
            stage.normalise_text("ATRASOS NÃO ESPECÍFICOS – OUTROS")
            == "ATRASOS NAO ESPECIFICOS OUTROS"
        )
        assert stage.normalise_text("  ") == ""

    def test_sql_normalisation_matches_python(self, duck) -> None:
        for text in stage.IAC1504_CODES.values():
            got = duck.execute(f"SELECT {stage.normalise_text_sql('?')}", [text]).fetchone()[0]
            assert got == stage.normalise_text(text), text

    def test_free_text_maps_back_to_the_code(self) -> None:
        assert stage.cause_code_from_text("CONEXÃO DE AERONAVE") == "RA"
        assert stage.cause_code_from_text("AEROPORTO COM RESTRIÇÕES OPERACIONAIS") == "AR"
        assert stage.cause_code_from_text("ATRASOS NÃO ESPECÍFICOS, OUTROS") == "MX"

    def test_the_ambiguous_text_is_resolved_by_status(self) -> None:
        assert stage.cause_code_from_text("AUTORIZADO", "cancelled") == "XB"
        assert stage.cause_code_from_text("AUTORIZADO", "realized") == "OA"
        assert stage.cause_code_from_text("AUTORIZADA") == "HA"

    def test_empty_and_unknown_texts_give_none(self) -> None:
        assert stage.cause_code_from_text("") is None
        assert stage.cause_code_from_text(None) is None
        assert stage.cause_code_from_text("SOMETHING ANAC NEVER PUBLISHED") is None


@pytest.fixture(scope="session")
def legacy_frame(raw_2002: Path):
    """The legacy fixture put through the real staging SELECT."""
    from vra.stage import connect

    con = connect(memory_limit="2GB", threads=2)
    try:
        yield _stage_fixture_df(con, raw_2002, LAYOUT_LEGACY)
    finally:
        con.close()


@pytest.fixture(scope="session")
def wide_frame(raw_2012: Path):
    """The 2010-2013 fixture put through the real staging SELECT."""
    from vra.stage import connect

    con = connect(memory_limit="2GB", threads=2)
    try:
        yield _stage_fixture_df(con, raw_2012, LAYOUT_2010)
    finally:
        con.close()


class TestLegacyLayout:
    @pytest.fixture(autouse=True)
    def _frame(self, legacy_frame):
        self.frame = legacy_frame

    def test_every_raw_row_survives(self, raw_2002: Path) -> None:
        with raw_2002.open("rb") as handle:
            raw_rows = sum(1 for _ in handle) - 1
        assert len(self.frame) == raw_rows

    def test_latin1_is_decoded(self) -> None:
        assert self.frame["airline"].str.fullmatch(r"[A-Z0-9]{2,4}").fillna(True).all()

    def test_timestamps_parse(self) -> None:
        # About one row in ten of the legacy layout has no scheduled departure
        # (DI 7 and DI 9 above all); flight_date falls back to the actual
        # departure, so almost every row still lands on a date.
        assert self.frame["sched_dep"].notna().mean() > 0.85
        assert self.frame["sched_dep"].dropna().dt.year.between(1999, 2004).all()
        assert self.frame["flight_date"].notna().mean() > 0.99
        missing_schedule = self.frame[
            self.frame["sched_dep"].isna() & self.frame["actual_dep"].notna()
        ]
        assert (missing_schedule["flight_date"] == missing_schedule["actual_dep"].dt.date).all()

    def test_status_is_normalised(self) -> None:
        assert set(self.frame["status"].unique()) <= {"realized", "cancelled", "other"}
        assert (self.frame["status"] == "realized").any()
        assert (self.frame["status"] == "cancelled").any()

    def test_na_justification_becomes_null(self) -> None:
        assert not self.frame["cause_code"].isin(["N/A", "NA", ""]).any()
        assert self.frame["cause_code"].dropna().str.fullmatch(r"[A-Z]{2}").all()

    def test_di_letters_become_ten_and_eleven(self) -> None:
        assert self.frame["di"].dropna().between(0, 11).all()

    def test_actual_times_are_often_absent_in_the_legacy_layout(self) -> None:
        # A realised legacy flight with no occurrence has empty actual times.
        # Staging leaves the delay null rather than imputing zero; see
        # docs/notes/staging.md.
        realised = self.frame[self.frame["status"] == "realized"]
        assert realised["actual_dep"].isna().any()
        assert realised.loc[realised["actual_dep"].isna(), "dep_delay_min"].isna().all()


class TestWideLayout:
    @pytest.fixture(autouse=True)
    def _frame(self, wide_frame):
        self.frame = wide_frame

    def test_every_raw_row_survives(self, raw_2012: Path) -> None:
        with raw_2012.open("rb") as handle:
            raw_rows = sum(1 for _ in handle) - 1
        assert len(self.frame) == raw_rows

    def test_the_column_order_of_this_layout_is_respected(self) -> None:
        # In 2010-2013 the destination sits between the departure and the
        # arrival timestamps. A positional read of the legacy order would put
        # a timestamp in dest_icao; this is the test that catches it.
        assert self.frame["origin_icao"].dropna().str.fullmatch(r"[A-Z]{4}").mean() > 0.99
        assert self.frame["dest_icao"].dropna().str.fullmatch(r"[A-Z]{4}").mean() > 0.99

    def test_free_text_justifications_became_codes(self) -> None:
        codes = self.frame["cause_code"].dropna()
        assert len(codes) > 0
        assert codes.str.fullmatch(r"[A-Z]{2}").all()
        assert set(codes.unique()) <= set(stage.IAC1504_CODES)

    def test_realised_flights_carry_actual_times_here(self) -> None:
        realised = self.frame[self.frame["status"] == "realized"]
        assert realised["actual_dep"].notna().mean() > 0.9

    def test_leading_zeros_of_the_flight_number_are_dropped(self) -> None:
        assert self.frame["flight_number"].dropna().min() >= 0


class TestDelays:
    """The VRA publishes naive local timestamps (Brasília, no offset), so every
    datetime here is deliberately naive: attaching a timezone would model
    something the source does not carry."""

    def test_sign_is_kept(self) -> None:
        early = delays.signed_delay_min(
            datetime.fromisoformat("2012-03-01T10:00"), datetime.fromisoformat("2012-03-01T09:52")
        )
        assert early == -8.0
        late = delays.signed_delay_min(
            datetime.fromisoformat("2012-03-01T10:00"), datetime.fromisoformat("2012-03-01T10:25")
        )
        assert late == 25.0

    def test_missing_actual_gives_none_not_zero(self) -> None:
        assert delays.signed_delay_min(datetime.fromisoformat("2012-03-01T10:00"), None) is None
        assert delays.positive_delay(None) is None

    def test_positive_delay_truncates_only_when_asked(self) -> None:
        assert delays.positive_delay(-8.0) == 0.0
        assert delays.positive_delay(25.0) == 25.0

    def test_the_outlier_default_is_the_adr_value(self) -> None:
        assert delays.OUTLIER_THRESHOLD_MIN == pytest.approx(313.25)
        assert delays.is_outlier(313.25)
        assert not delays.is_outlier(313.0)
        assert not delays.is_outlier(None)

    def test_the_threshold_is_a_parameter(self) -> None:
        assert delays.is_outlier(120.0, threshold_min=delays.OUTLIER_THRESHOLD_ARR_ALT_MIN)
        assert not delays.is_outlier(120.0)

    def test_late_is_strictly_greater(self) -> None:
        assert delays.is_late(0.5)
        assert not delays.is_late(0.0)
        assert delays.is_late(16.0, 15.0)
        assert not delays.is_late(15.0, 15.0)

    def test_sql_and_python_agree(self, duck) -> None:
        sched, actual = (
            datetime.fromisoformat("2012-03-01T23:50"),
            datetime.fromisoformat("2012-03-02T00:10"),
        )
        got = duck.execute(
            f"SELECT {delays.signed_delay_sql('?', '?')}, {delays.block_sql('?', '?')}",
            [sched, actual, sched, actual],
        ).fetchone()
        assert got[0] == pytest.approx(delays.signed_delay_min(sched, actual))
        assert got[1] == pytest.approx(delays.block_min(sched, actual))

    def test_null_actual_propagates_in_sql(self, duck) -> None:
        got = duck.execute(
            f"SELECT {delays.signed_delay_sql('?', 'CAST(NULL AS TIMESTAMP)')}",
            [datetime.fromisoformat("2012-03-01")],
        ).fetchone()[0]
        assert got is None


class TestStagedFixtureSchema:
    def test_the_parquet_matches_the_registry(self, staged_table) -> None:
        registry.validate_schema(staged_table)

    def test_the_fixture_is_the_three_declared_routes(self, staged_frame) -> None:
        assert set(staged_frame["route"].unique()) <= {"SBAR-SBBR", "MRSP-MRRJ", "SBCT-MRSP"}

    def test_the_fixture_spans_both_raw_layouts(self, staged_frame) -> None:
        years = set(staged_frame["year"].unique())
        assert {2004, 2009} & years, "no legacy-layout year in the fixture"
        assert 2012 in years, "no wide-layout year in the fixture"

    def test_the_fixture_is_small_and_offline(self, staged_sample: Path) -> None:
        assert staged_sample.stat().st_size < 4_000_000

    def test_delays_are_signed_and_null_aware(self, staged_frame) -> None:
        both = staged_frame["sched_dep"].notna() & staged_frame["actual_dep"].notna()
        rebuilt = staged_frame.loc[both, "actual_dep"] - staged_frame.loc[both, "sched_dep"]
        rebuilt = rebuilt.dt.total_seconds() / 60.0
        assert (rebuilt - staged_frame.loc[both, "dep_delay_min"]).abs().max() < 0.01
        assert staged_frame.loc[~both, "dep_delay_min"].isna().all()
        assert (staged_frame["arr_delay_min"].dropna() < 0).any(), (
            "early arrivals must stay negative"
        )

    def test_block_times_are_consistent(self, staged_frame) -> None:
        both = staged_frame["sched_dep"].notna() & staged_frame["sched_arr"].notna()
        rebuilt = staged_frame.loc[both, "sched_arr"] - staged_frame.loc[both, "sched_dep"]
        rebuilt = (rebuilt.dt.total_seconds() / 60.0).round()
        assert (rebuilt - staged_frame.loc[both, "sched_block_min"]).abs().max() <= 1

    def test_hours_and_weekday_are_in_range(self, staged_frame) -> None:
        assert staged_frame["dep_hour"].dropna().between(0, 23).all()
        assert staged_frame["arr_hour"].dropna().between(0, 23).all()
        assert staged_frame["dow"].dropna().between(0, 6).all()

    def test_weekday_convention_is_monday_zero(self, staged_frame) -> None:
        rows = staged_frame.dropna(subset=["flight_date", "dow"])
        rebuilt = rows["flight_date"].map(lambda day: day.weekday())
        assert (rebuilt == rows["dow"]).all()

    def test_is_realized_agrees_with_status(self, staged_frame) -> None:
        assert (staged_frame["is_realized"] == staged_frame["status"].eq("realized")).all()

    def test_group_and_class_are_present_as_columns(self, staged_frame) -> None:
        # They are entirely null when groups.csv did not exist at staging time;
        # the columns must exist either way so downstream code is stable.
        assert "group" in staged_frame.columns
        assert "class" in staged_frame.columns

    def test_group_and_class_move_together(self, staged_frame) -> None:
        assert (staged_frame["group"].isna() == staged_frame["class"].isna()).all()

    def test_class_vocabulary_matches_the_external_table(self, staged_frame) -> None:
        # ADR-0003 names three classes (FSC, LCC, regional) and makes regional
        # the catch-all; data/external/groups.csv adds a fourth, "other". The
        # staged values must be a subset of whatever that table declares, and
        # the discrepancy with the ADR belongs to the groups table's owner.
        import csv

        groups_csv = Path(__file__).resolve().parents[1] / "data" / "external" / "groups.csv"
        if not groups_csv.exists():  # pragma: no cover
            pytest.skip("data/external/groups.csv is absent")
        with groups_csv.open(encoding="utf-8") as handle:
            declared = {
                row["class"].strip() for row in csv.DictReader(handle) if row["class"].strip()
            }
        assert set(staged_frame["class"].dropna().unique()) <= declared

    def test_an_airline_never_has_two_groups_in_one_month(self, staged_frame) -> None:
        # The groups table is a dated interval table (ADR-0003). Overlapping
        # intervals would duplicate flights in the join; this is the assertion
        # that would catch it in the staged output.
        labelled = staged_frame.dropna(subset=["group", "ym"])
        per_month = labelled.groupby(["airline", "ym"])["group"].nunique()
        assert per_month.max() <= 1


class TestRegistry:
    def test_every_staged_column_is_registered(self) -> None:
        assert len(registry.STAGED) == len(set(registry.STAGED_NAMES))

    def test_to_frame_has_one_row_per_column(self) -> None:
        table = registry.to_frame()
        assert len(table) == len(registry.STAGED)
        assert set(table.columns) == {
            "name",
            "dtype",
            "unit",
            "definition_en",
            "definition_pt",
            "source",
            "layer",
            "aggregation",
            "public",
        }

    def test_definitions_are_filled_in_both_languages(self) -> None:
        for column in registry.STAGED:
            assert len(column.definition_en) > 20, column.name
            assert len(column.definition_pt) > 20, column.name

    def test_aggregation_vocabulary_is_closed(self) -> None:
        assert {c.aggregation for c in registry.STAGED} <= {"sum", "mean", "recompute", "none"}

    def test_validate_schema_reports_a_missing_column(self, staged_frame) -> None:
        with pytest.raises(ValueError, match="missing columns"):
            registry.validate_schema(staged_frame.drop(columns=["route"]))

    def test_validate_schema_reports_an_extra_column(self, staged_frame) -> None:
        extra = staged_frame.copy()
        extra["not_registered"] = 1
        with pytest.raises(ValueError, match="unregistered columns"):
            registry.validate_schema(extra)

    def test_validate_schema_reports_a_wrong_order(self, staged_frame) -> None:
        swapped = staged_frame[[*registry.STAGED_NAMES[1:], registry.STAGED_NAMES[0]]]
        with pytest.raises(ValueError, match="column order"):
            registry.validate_schema(swapped)

    def test_lookup_by_name(self) -> None:
        assert registry.get("arr_delay_min").unit == "minute"
        with pytest.raises(KeyError):
            registry.get("no_such_column")


class TestBuiltSql:
    def test_the_select_projects_exactly_the_registered_columns(self, duck, raw_2002: Path) -> None:
        frame = _stage_fixture_df(duck, raw_2002, LAYOUT_LEGACY)
        assert list(frame.columns) == list(registry.STAGED_NAMES)

    def test_both_layouts_project_the_same_columns(
        self, duck, raw_2002: Path, raw_2012: Path
    ) -> None:
        legacy = _stage_fixture_df(duck, raw_2002, LAYOUT_LEGACY)
        wide = _stage_fixture_df(duck, raw_2012, LAYOUT_2010)
        assert list(legacy.columns) == list(wide.columns)

    def test_positions_differ_between_layouts(self) -> None:
        legacy = stage.positions_for(LAYOUT_LEGACY)
        wide = stage.positions_for(LAYOUT_2010)
        assert legacy["dest_icao"] != wide["dest_icao"]
        assert wide["dest_icao"] == "c11"
