"""`airline_delays.schema`: no column without an entry, and no entry without a column.

Rule 5 of the build brief in executable form. The registry is generated from a
description resolver rather than typed out column by column, so the risk is not
a typo — it is a column that quietly ships undocumented, or an entry that
outlives the column it described. Both directions are checked here against the
tables actually built from the fixture.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from airline_delays import fact as fact_mod
from airline_delays import schema

ROOT = Path(__file__).resolve().parents[1]
LAYERS = ("fact", "city", "airline_city", "panel")


@pytest.fixture(scope="module")
def described(built) -> dict[str, list[schema.Column]]:
    return {
        "staged": list(schema.STAGED),
        "fact": schema.describe_frame(built["fact"], "fact"),
        "city": schema.describe_frame(fact_mod.slim(built["city"]), "city"),
        "airline_city": schema.describe_frame(fact_mod.slim(built["airline_city"]), "airline_city"),
        "panel": schema.describe_frame(built["panel"], "panel"),
    }


class TestEveryColumnHasAnEntry:
    @pytest.mark.parametrize("layer", LAYERS)
    def test_the_resolver_answers_for_every_built_column(self, built, layer: str) -> None:
        frame = built[
            {"fact": "fact", "city": "city", "airline_city": "airline_city"}.get(layer, "panel")
        ]
        if layer in {"city", "airline_city"}:
            frame = fact_mod.slim(frame)
        unknown = []
        for name in frame.columns:
            try:
                schema.describe(name, layer)  # type: ignore[arg-type]
            except KeyError:
                unknown.append(name)
        assert unknown == [], f"{layer}: columns with no registry definition: {unknown}"

    def test_the_fact_list_matches_the_measures_the_builder_emits(self) -> None:
        declared = [column.name for column in schema.FACT]
        built_names = [
            *fact_mod.FACT_KEYS,
            *fact_mod.fact_measures(),
            "is_entry",
            "is_exit",
        ]
        assert declared == built_names

    def test_no_entry_describes_a_column_that_does_not_exist(self, built) -> None:
        assert [column.name for column in schema.FACT] == list(built["fact"].columns)


class TestTheEntriesAreUsable:
    @pytest.mark.parametrize("layer", LAYERS)
    def test_both_definitions_are_written_and_distinct(self, described, layer: str) -> None:
        for column in described[layer]:
            assert column.definition_en.strip(), column.name
            assert column.definition_pt.strip(), column.name
            assert column.definition_en != column.definition_pt, column.name

    @pytest.mark.parametrize("layer", LAYERS)
    def test_every_aggregation_rule_is_one_of_the_four(self, described, layer: str) -> None:
        allowed = {"sum", "mean", "recompute", "none"}
        assert {column.aggregation for column in described[layer]} <= allowed

    @pytest.mark.parametrize("layer", LAYERS)
    def test_names_are_unique_within_a_layer(self, described, layer: str) -> None:
        names = [column.name for column in described[layer]]
        assert len(names) == len(set(names))

    def test_a_proportion_is_never_declared_additive(self, described) -> None:
        # Averaging a share when rolling up is the classic silent error; ADR-0004
        # forbids it, and the registry is where that is enforced.
        for layer in LAYERS:
            for column in described[layer]:
                if column.name.startswith("sh_") or column.unit == "share":
                    assert column.aggregation in {"recompute", "none"}, column.name
                if column.unit.startswith("index"):
                    assert column.aggregation == "recompute", column.name

    def test_a_count_of_flights_is_additive(self, described) -> None:
        for column in described["fact"]:
            if column.unit == "flights" and not column.name.startswith("sh_"):
                assert column.aggregation == "sum", column.name

    def test_an_unknown_measure_raises_rather_than_shipping_undocumented(self) -> None:
        with pytest.raises(KeyError, match="no registry definition"):
            schema.describe("a_column_nobody_defined", "fact")


class TestTheGeneratedDictionary:
    def test_it_names_every_column_of_every_layer(self, described) -> None:
        markdown = schema.dictionary_markdown(described)
        for layer, columns in described.items():
            assert schema.LAYER_TITLES[layer] in markdown
            for column in columns:
                assert f"`{column.name}`" in markdown

    def test_a_pipe_in_a_definition_cannot_break_the_table(self) -> None:
        column = schema.Column(
            name="x",
            dtype="int32",
            unit="flights",
            definition_en="a | b",
            definition_pt="a | b",
            source="test",
            layer="fact",
            aggregation="sum",
            public=True,
        )
        row = schema.dictionary_markdown({"fact": [column]}).splitlines()[-2]
        assert row.count("|") == 7, row


class TestTheGeneratedDatapackage:
    @pytest.fixture()
    def package(self, described) -> dict:
        resources = [
            schema.resource(
                "panel_route_month",
                "data/analysis/panel_route_month.parquet",
                described["panel"],
                ["route", "ym"],
            )
        ]
        return schema.datapackage(resources)

    def test_it_is_json_serialisable(self, package: dict) -> None:
        assert json.loads(json.dumps(package))["name"] == "airline-delays"

    def test_it_declares_a_licence_and_the_anac_source(self, package: dict) -> None:
        assert package["licenses"][0]["name"] == "CC-BY-4.0"
        assert any("dados.gov.br" in source["path"] for source in package["sources"])

    def test_every_field_carries_both_definitions_and_its_aggregation(self, package: dict) -> None:
        fields = package["resources"][0]["schema"]["fields"]
        assert fields
        for field in fields:
            assert field["description"]
            assert field["x-definition-pt"]
            assert field["x-aggregation"] in {"sum", "mean", "recompute", "none"}

    def test_the_primary_key_is_declared(self, package: dict) -> None:
        assert package["resources"][0]["schema"]["primaryKey"] == ["route", "ym"]

    def test_a_dtype_maps_to_a_frictionless_type(self, package: dict) -> None:
        types = {field["type"] for field in package["resources"][0]["schema"]["fields"]}
        assert types <= {"integer", "number", "string", "boolean", "date", "datetime", "any"}
        assert "any" not in types, "an unmapped dtype reached the descriptor"


class TestTheStagedLayerStillValidates:
    def test_the_fixture_matches_the_staged_registry(self, staged_table) -> None:
        schema.validate_schema(staged_table)

    def test_the_staged_names_did_not_move(self) -> None:
        assert schema.STAGED_NAMES[0] == "flight_date"
        assert "universe_repl" in schema.STAGED_NAMES


def test_the_repository_dictionary_is_in_step_with_the_registry() -> None:
    """`docs/dictionary.md` is generated; a stale copy is a failing check."""
    path = ROOT / "docs" / "dictionary.md"
    if not path.exists():
        pytest.skip("docs/dictionary.md not generated yet; run `uv run airline-delays dictionary`")
    text = path.read_text(encoding="utf-8")
    assert "Generated from `src/airline_delays/schema.py`" in text
    for column in schema.FACT[:20]:
        assert f"`{column.name}`" in text
