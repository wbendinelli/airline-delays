"""The IAC 1504 justification codes and the two taxonomies over them (ADR-0005).

Two partitions of the same 49 codes live side by side and must not be merged:

**The article's three sets** (`prwheather`, `princident`, `pr_connc`) are kept
exactly as published, because they are what the replication has to reproduce —
including the fact that `prwheather` is not only weather: its dominant code is
``AR``, "aeroporto com restrições operacionais", and it also carries the
aircraft-rotation codes ``RI``/``RM``. Renaming or trimming it would improve
the label and destroy the replication.

**The ADR-0005 taxonomy** (`weather`, `airport_restricted`, `rotation`,
`technical`, `operational`, `authorised`, `other`) is this repository's own,
mutually exclusive and exhaustive, so category counts sum to the number of
flights carrying any code.

`data/external/cause_codes.csv` is the source of truth for both; the constants
below are the ADR's declared expectation and `test_codes` asserts that the file
and the ADR agree. A disagreement is a finding, not a merge conflict to
silently resolve.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

ARTICLE_SETS: dict[str, tuple[str, ...]] = {
    "prwheather": (
        "AI", "AJ", "AM", "AR", "RI", "RM", "WA", "WO",
        "WR", "WT", "XI", "XJ", "XM", "XO", "XS", "XT",
    ),
    "princident": ("DF", "DG", "HB", "MA", "TD"),
    "pr_connc": ("RA",),
}  # fmt: skip
"""The three code sets the replicated article publishes (ADR-0005).

These are the article's own three sets; they are kept verbatim across
route-months respectively (`reconstrucao-vra.md`).
"""

CATEGORIES: dict[str, tuple[str, ...]] = {
    "weather": ("AM", "WA", "WI", "WO", "WR", "WS", "WT", "XO", "XS", "XT"),
    "airport_restricted": ("AI", "AJ", "AR", "XI", "XJ", "XM"),
    "rotation": ("RA", "RI", "RM"),
    "technical": ("DF", "DG", "HB", "MA", "TD"),
    "operational": ("AF", "AG", "AS", "AT", "FP", "GF"),
    "authorised": ("HA", "HD", "OA", "XA", "XB"),
}
"""The ADR-0005 taxonomy, without `other`, which is everything else."""

OTHER_CATEGORY = "other"
"""Category of any code outside the six named ones; also the label for `MX`."""

CATEGORY_NAMES: tuple[str, ...] = (*CATEGORIES, OTHER_CATEGORY)

SECTIONS: tuple[str, ...] = ("delay", "cancellation", "alteration", "schedule_change")
"""The four sub-lists of Annex 2 of the IAC 1504."""


@dataclass(frozen=True)
class CauseCode:
    """One row of `data/external/cause_codes.csv`."""

    code: str
    description_pt: str
    section: str
    category: str
    article_set: str


@lru_cache(maxsize=8)
def load(path: Path | str) -> tuple[CauseCode, ...]:
    """Read the cause-code table; cached, because it is read once per grain."""
    import pandas as pd

    frame = pd.read_csv(path, dtype=str, keep_default_na=False)
    required = ("code", "description_pt", "section", "category", "article_set")
    missing = [name for name in required if name not in frame.columns]
    if missing:
        raise ValueError(f"{path}: missing columns {missing}")
    return tuple(
        CauseCode(
            code=str(row["code"]).strip().upper(),
            description_pt=str(row["description_pt"]).strip(),
            section=str(row["section"]).strip(),
            category=str(row["category"]).strip() or OTHER_CATEGORY,
            article_set=str(row["article_set"]).strip(),
        )
        for _, row in frame.iterrows()
    )


def sets_from_file(path: Path | str) -> dict[str, tuple[str, ...]]:
    """The article sets as the CSV declares them, for comparison with `ARTICLE_SETS`."""
    out: dict[str, list[str]] = {name: [] for name in ARTICLE_SETS}
    for row in load(path):
        if row.article_set in out:
            out[row.article_set].append(row.code)
    return {name: tuple(sorted(codes)) for name, codes in out.items()}


def categories_from_file(path: Path | str) -> dict[str, tuple[str, ...]]:
    """The ADR-0005 categories as the CSV declares them."""
    out: dict[str, list[str]] = {}
    for row in load(path):
        out.setdefault(row.category, []).append(row.code)
    return {name: tuple(sorted(codes)) for name, codes in out.items()}


def category_of(code: str | None) -> str:
    """The ADR-0005 category of a code; `other` for an unknown or missing code."""
    if not code:
        return OTHER_CATEGORY
    upper = str(code).strip().upper()
    for name, codes in CATEGORIES.items():
        if upper in codes:
            return name
    return OTHER_CATEGORY


def in_set(code: str | None, set_name: str) -> bool:
    """True when `code` belongs to one of the article's three sets."""
    if not code:
        return False
    return str(code).strip().upper() in ARTICLE_SETS[set_name]


# --------------------------------------------------------------------------- SQL


def in_sql(column: str, codes: tuple[str, ...]) -> str:
    """``column IN ('AI', 'AJ', ...)`` with the quoting centralised."""
    return f"{column} IN (" + ", ".join(f"'{code}'" for code in codes) + ")"


def article_set_sql(column: str, set_name: str) -> str:
    """Membership test for one of the article's sets."""
    return in_sql(column, ARTICLE_SETS[set_name])


def category_sql(column: str, category: str) -> str:
    """Membership test for one ADR-0005 category.

    ``other`` is the complement of the six named categories *among rows that
    carry a code*: a flight with no code is not "other", it is uncoded, and the
    fact table counts it separately as `cause_none`.
    """
    if category != OTHER_CATEGORY:
        return in_sql(column, CATEGORIES[category])
    named = sorted({code for codes in CATEGORIES.values() for code in codes})
    return f"({column} IS NOT NULL AND NOT " + in_sql(column, tuple(named)) + ")"


__all__ = [
    "ARTICLE_SETS",
    "CATEGORIES",
    "CATEGORY_NAMES",
    "OTHER_CATEGORY",
    "SECTIONS",
    "CauseCode",
    "article_set_sql",
    "categories_from_file",
    "category_of",
    "category_sql",
    "in_set",
    "in_sql",
    "load",
    "sets_from_file",
]
