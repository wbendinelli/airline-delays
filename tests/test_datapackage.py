"""`datapackage.json`: in step with the registry and the files, valid against the v2 schema."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from airline_delays.schema import datapackage as dp  # the submodule (no function shares its name)

ROOT = Path(__file__).resolve().parents[1]
DESCRIPTOR = ROOT / "datapackage.json"


@pytest.fixture(scope="module")
def committed() -> dict:
    return json.loads(DESCRIPTOR.read_text(encoding="utf-8"))


def test_the_committed_descriptor_is_a_rebuild(committed: dict) -> None:
    assert dp.render(ROOT) == DESCRIPTOR.read_text(encoding="utf-8")


def test_every_resource_hash_and_size_match_the_file(committed: dict) -> None:
    for resource in committed["resources"]:
        path = ROOT / resource["path"]
        assert path.exists(), resource["path"]
        size = resource.get("bytes", resource.get("x-bytes"))
        assert path.stat().st_size == size, resource["path"]
        digest = "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
        assert digest == resource["hash"], resource["path"]


def test_every_resource_path_is_tracked_and_every_regenerated_pattern_is_ignored(
    committed: dict,
) -> None:
    tracked = set(
        subprocess.run(
            ["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True
        ).stdout.split()
    )
    for resource in committed["resources"]:
        assert resource["path"] in tracked, resource["path"]
    for entry in committed["x-regenerated"]:
        pattern = entry["x-path-pattern"]
        top = pattern.split("/")[0] + "/" + pattern.split("/")[1]
        assert not any(name.startswith(top) and name.endswith(".parquet") for name in tracked), top


def test_the_descriptor_validates_against_the_data_package_v2_schema(committed: dict) -> None:
    import jsonschema

    schema = json.loads((ROOT / "tests" / "fixtures" / "datapackage-2.0.schema.json").read_text())
    jsonschema.Draft7Validator.check_schema(schema)
    validator = jsonschema.Draft7Validator(schema)
    errors = sorted(validator.iter_errors(committed), key=lambda e: list(e.path))
    assert errors == [], [f"{'/'.join(map(str, e.path))}: {e.message[:120]}" for e in errors[:10]]


def test_the_tabular_resources_carry_the_registry_schema(committed: dict) -> None:
    by_name = {resource["name"]: resource for resource in committed["resources"]}
    article = by_name["article_panel_route_month"]
    assert article["schema"]["primaryKey"] == ["od", "ym"]
    assert len(article["schema"]["fields"]) == 52
    assert article["x-rows"] == 24_589
    assert by_name["panel_route_month"]["x-rows"] == 31_313
    assert by_name["fact_group_route_month"]["x-rows"] == 165_763
    for name in ("panel_route_month", "panel_route_month_csv"):
        assert [f["name"] for f in by_name[name]["schema"]["fields"]] == [
            f["name"] for f in by_name["panel_route_month"]["schema"]["fields"]
        ]
    assert {r["name"] for r in committed["resources"] if r["name"].startswith("external_")} == {
        f"external_{stem}" for stem in dp.EXTERNAL_TABLES
    }


def test_no_placeholder_identifier(committed: dict) -> None:
    text = json.dumps(committed)
    assert "PENDING" not in text and "XXXX" not in text
    assert ("id" in committed) != committed.get("x-pending-doi", False)
