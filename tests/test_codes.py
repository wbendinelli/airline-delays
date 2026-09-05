"""`vra.codes`: the two taxonomies over the IAC 1504 justification codes (ADR-0005)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from vra import codes, stage  # noqa: E402


@pytest.fixture(scope="module")
def cause_codes_csv(external_dir: Path) -> Path:
    return external_dir / "cause_codes.csv"


class TestTheFileAndTheAdrAgree:
    """`data/external/cause_codes.csv` is the source; the constants are the claim."""

    def test_the_three_article_sets_match_the_file(self, cause_codes_csv: Path) -> None:
        declared = codes.sets_from_file(cause_codes_csv)
        for name, expected in codes.ARTICLE_SETS.items():
            assert declared[name] == tuple(sorted(expected)), name

    def test_the_seven_categories_match_the_file(self, cause_codes_csv: Path) -> None:
        declared = codes.categories_from_file(cause_codes_csv)
        for name, expected in codes.CATEGORIES.items():
            assert declared[name] == tuple(sorted(expected)), name

    def test_every_code_in_the_file_is_an_iac_1504_code(self, cause_codes_csv: Path) -> None:
        published = set(stage.IAC1504_CODES)
        assert {row.code for row in codes.load(cause_codes_csv)} <= published


class TestTheAdr0005Taxonomy:
    def test_the_categories_partition_the_named_codes(self) -> None:
        seen: list[str] = []
        for group in codes.CATEGORIES.values():
            seen.extend(group)
        assert len(seen) == len(set(seen)), "a code belongs to exactly one category"

    def test_an_unknown_or_missing_code_is_other(self) -> None:
        assert codes.category_of(None) == "other"
        assert codes.category_of("") == "other"
        assert codes.category_of("MX") == "other"
        assert codes.category_of("zz") == "other"

    @pytest.mark.parametrize(
        ("code", "category"),
        [
            ("AR", "airport_restricted"),
            ("WO", "weather"),
            ("RA", "rotation"),
            ("TD", "technical"),
            ("AT", "operational"),
            ("XB", "authorised"),
        ],
    )
    def test_a_representative_code_of_each_category(self, code: str, category: str) -> None:
        assert codes.category_of(code) == category

    def test_the_other_predicate_excludes_uncoded_flights(self, duck) -> None:
        # A flight with no code is uncoded, not "other": the fact table counts it
        # as `cause_none`, and mixing the two would inflate every `other` share.
        sql = codes.category_sql("code", "other")
        rows = duck.execute(
            f"SELECT code, {sql} AS is_other FROM (VALUES ('MX'), ('AR'), (NULL)) t(code)"
        ).fetchall()
        assert dict(rows) == {"MX": True, "AR": False, None: False}


class TestTheArticleSets:
    def test_prwheather_is_not_only_weather(self) -> None:
        # ADR-0005: the article's set merges weather with restricted airports and
        # aircraft rotation, and AR is its dominant code. Renaming it would
        # improve the label and destroy the replication.
        assert "AR" in codes.ARTICLE_SETS["prwheather"]
        assert "RI" in codes.ARTICLE_SETS["prwheather"]
        assert codes.category_of("AR") == "airport_restricted"
        assert codes.category_of("RI") == "rotation"

    def test_pr_connc_is_the_single_rotation_code_ra(self) -> None:
        assert codes.ARTICLE_SETS["pr_connc"] == ("RA",)

    def test_princident_is_the_technical_category(self) -> None:
        assert set(codes.ARTICLE_SETS["princident"]) == set(codes.CATEGORIES["technical"])

    def test_membership_matches_the_sql(self, duck) -> None:
        for name, wanted in codes.ARTICLE_SETS.items():
            sql = codes.article_set_sql("code", name)
            rows = duck.execute(
                f"SELECT code, {sql} AS hit FROM (VALUES ('RA'), ('AR'), ('TD'), ('ZZ')) t(code)"
            ).fetchall()
            for code, hit in rows:
                assert hit == codes.in_set(code, name), (name, code)
            del wanted
