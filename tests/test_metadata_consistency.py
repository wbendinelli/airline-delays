"""One metadata source: CITATION.cff, pyproject.toml, datapackage.json and .zenodo.json agree."""

from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path

import pytest
import yaml

from airline_delays.schema import metadata, zenodo

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def cff() -> dict:
    return yaml.safe_load((ROOT / "CITATION.cff").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def zenodo_json() -> dict:
    return json.loads((ROOT / ".zenodo.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def descriptor() -> dict:
    return json.loads((ROOT / "datapackage.json").read_text(encoding="utf-8"))


def test_the_committed_zenodo_json_is_a_rebuild() -> None:
    assert zenodo.render() == (ROOT / ".zenodo.json").read_text(encoding="utf-8")


def test_version_is_typed_once(cff: dict, zenodo_json: dict, descriptor: dict) -> None:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        pyproject = tomllib.load(handle)["project"]["version"]
    assert pyproject == metadata.version() == cff["version"] == zenodo_json["version"]
    assert descriptor["version"] == pyproject


def test_title_and_keywords_agree(cff: dict, zenodo_json: dict, descriptor: dict) -> None:
    assert cff["title"] == metadata.TITLE == zenodo_json["title"] == descriptor["title"]
    assert list(cff["keywords"]) == list(metadata.KEYWORDS) == zenodo_json["keywords"]
    assert descriptor["keywords"] == list(metadata.KEYWORDS)


def test_the_creator_is_the_same_person(cff: dict, zenodo_json: dict, descriptor: dict) -> None:
    creator = metadata.CREATORS[0]
    assert cff["authors"][0]["family-names"] == creator["family_names"]
    assert zenodo_json["creators"][0]["name"] == creator["name"]
    assert descriptor["contributors"][0]["familyName"] == creator["family_names"]


def test_zenodo_enumerations_are_valid(zenodo_json: dict) -> None:
    assert zenodo_json["upload_type"] in {
        "publication",
        "poster",
        "presentation",
        "dataset",
        "image",
        "video",
        "software",
        "lesson",
        "physicalobject",
        "other",
    }
    assert zenodo_json["access_right"] in {"open", "embargoed", "restricted", "closed"}
    assert zenodo_json["license"] == "cc-by-4.0"
    for item in zenodo_json["related_identifiers"]:
        assert item["relation"] in {
            "isCitedBy",
            "cites",
            "isSupplementTo",
            "isSupplementedBy",
            "isContinuedBy",
            "continues",
            "isDescribedBy",
            "describes",
            "hasMetadata",
            "isMetadataFor",
            "isNewVersionOf",
            "isPreviousVersionOf",
            "isPartOf",
            "hasPart",
            "isReferencedBy",
            "references",
            "isDocumentedBy",
            "documents",
            "isCompiledBy",
            "compiles",
            "isVariantFormOf",
            "isOriginalFormof",
            "isIdenticalTo",
            "isAlternateIdentifier",
            "isReviewedBy",
            "reviews",
            "isDerivedFrom",
            "isSourceOf",
            "requires",
            "isRequiredBy",
            "isObsoletedBy",
            "obsoletes",
        }
        assert item["scheme"] in {"doi", "url", "isbn", "arxiv", "pmid", "handle", "urn"}
    assert "doi" not in zenodo_json  # Zenodo assigns it


def test_no_placeholder_leaks_into_the_machine_readable_files(cff: dict, zenodo_json: dict) -> None:
    for payload in (json.dumps(zenodo_json), json.dumps(cff)):
        assert not re.search(r"0000-0000-0000-0000|PENDING|XXXX|\[DOI", payload)
    assert "doi" not in cff, "the software DOI enters CITATION.cff only when Zenodo has minted it"
