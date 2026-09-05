"""`reports/summary.json` is complete, finite, and fresh against the committed artefacts."""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from airline_delays import reporting

ROOT = Path(__file__).resolve().parents[1]
GROUPS = (
    "reconstruction",
    "article_panel",
    "published",
    "estimation",
    "prediction",
    "theory",
    "registry",
    "external",
    "fixture",
    "decisions",
    "meta",
)


def _leaves(node, prefix=""):
    if isinstance(node, dict):
        for key, value in node.items():
            yield from _leaves(value, f"{prefix}{key}.")
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from _leaves(value, f"{prefix}{index}.")
    else:
        yield prefix.rstrip("."), node


@pytest.fixture(scope="module")
def built() -> dict:
    return reporting.build()


def test_every_group_is_present(built: dict) -> None:
    assert set(built) == set(GROUPS)


def test_every_number_is_finite(built: dict) -> None:
    for key, value in _leaves(built):
        if isinstance(value, float):
            assert math.isfinite(value), key


def test_the_headline_values_are_what_the_artefacts_say(built: dict) -> None:
    assert built["article_panel"]["rows"] == 24_589
    assert built["article_panel"]["columns"] == 52
    assert built["estimation"]["totals"]["coefficients"] == 306
    assert built["estimation"]["hhi"]["n_comparisons"] == 12
    assert built["reconstruction"]["panel"]["nodes"] == 27
    assert built["theory"]["n_identities"] == built["theory"]["n_holding"]
    assert built["prediction"]["rolling"]["folds"] == 8
    assert built["registry"]["columns_by_layer"]["article_panel"] == 52


def test_the_committed_summary_is_fresh() -> None:
    assert reporting.check() == []


def test_the_summary_carries_no_timestamp() -> None:
    text = (ROOT / "reports" / "summary.json").read_text(encoding="utf-8")
    payload = json.loads(text)
    assert "generated_at" not in json.dumps(payload["meta"])
