"""Airline economic groups and business-model classes, dated to the month.

`data/external/groups.csv` is the source of truth (ADR-0003): one row per
``airline, group, start, end, class``, with ``start``/``end`` written as
``YYYY-MM`` and compared as ``YYYYMM`` integers, never as dates — a
``TRY_CAST`` to ``DATE`` nulls every ``"2007-03"`` and turns the interval test
into "always true", duplicating every flight of an airline that changed group.

Two rules that look like details and are not:

*Class follows the absorbing group after a merger.* Pantanal inside TAM is FSC
from 2009-12; Trip and Total inside Azul are LCC from 2012-05. The table
already encodes this, one row per period, so nothing downstream needs a
special case.

*An unlabelled airline is ``other``, never null* (ADR-0011). Most unlabelled
codes are foreign carriers whose domestic legs surface in the VRA; dropping
them would silently shrink the denominator of every share, and calling them
``regional`` would be a claim about a business model nobody checked. Their
`group` falls back to their own ICAO code, so they stay distinguishable and
the flight-share HHI keeps counting them as separate competitors.

The article's own sets are kept as named constants next to the table,
because they are *not* the same thing as the classes (ADR-0013):
the article's FSC set excludes Avianca Brasil, which ADR-0003 classes as FSC,
and its "LCC" set is the two groups Gol and Azul, not the class, which also
holds Webjet while it was independent.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import pairwise
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover - typing only
    import pandas as pd

CLASSES: tuple[str, ...] = ("FSC", "LCC", "regional", "other")
"""The four business-model classes (ADR-0003, amended by ADR-0011)."""

DEFAULT_CLASS = "other"
"""Class of an airline that `groups.csv` does not label (ADR-0011)."""

BENCHMARK_FSC_GROUPS: tuple[str, ...] = ("TAM", "VARIG", "TRANSBRASIL", "VASP")
"""The article's FSC set, as groups: TA2, VR2, TB2 and VSP of the laboratory code.

Differs from ``class == "FSC"`` by exactly one group, ``AVIANCA_BRASIL``
(ICAO ``ONE``), which ADR-0003 classes as FSC and the article's set omits.
Both are computed and both are published; neither is adjusted to fit the other.
"""

BENCHMARK_LCC_GROUPS: tuple[str, ...] = ("GOL", "AZUL")
"""The article's ``lccfu``/``olccfu`` set: the Gol and Azul groups.

Differs from ``class == "LCC"`` by ``WEBJET``, an independent low-cost carrier
between 2005-07 and 2011-10 and part of the Gol group afterwards.
"""

REQUIRED_COLUMNS: tuple[str, ...] = ("airline", "group", "start", "end", "class")


def _month_key(value: Any) -> int | None:
    """``"2007-03"`` or ``"2007-03-15"`` to ``200703``; blanks to None."""
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "nat"}:
        return None
    digits = text[:7].replace("-", "")
    return int(digits) if digits.isdigit() else None


@dataclass(frozen=True)
class GroupPeriod:
    """One dated row of `groups.csv`."""

    airline: str
    group: str
    klass: str
    start_ym: int | None
    end_ym: int | None

    def covers(self, ym: int) -> bool:
        if self.start_ym is not None and ym < self.start_ym:
            return False
        return not (self.end_ym is not None and ym > self.end_ym)


@dataclass(frozen=True)
class GroupTable:
    """The dated airline -> (group, class) map, with no overlapping periods."""

    periods: tuple[GroupPeriod, ...]

    @classmethod
    def load(cls, path: Path | str) -> GroupTable:
        """Read `groups.csv` and check that no airline has overlapping periods."""
        import pandas as pd

        frame = pd.read_csv(path, dtype=str, keep_default_na=False)
        missing = [name for name in REQUIRED_COLUMNS if name not in frame.columns]
        if missing:
            raise ValueError(f"{path}: missing columns {missing}")
        periods = tuple(
            GroupPeriod(
                airline=str(row["airline"]).strip().upper(),
                group=str(row["group"]).strip(),
                klass=(str(row["class"]).strip() or DEFAULT_CLASS),
                start_ym=_month_key(row["start"]),
                end_ym=_month_key(row["end"]),
            )
            for _, row in frame.iterrows()
        )
        table = cls(periods=periods)
        table.assert_no_overlap()
        table.assert_known_classes()
        return table

    def assert_no_overlap(self) -> None:
        """Fail when one airline has two overlapping periods.

        An overlap would duplicate every flight of that airline in the join, so
        the right answer is to fix the table, never to widen the join.
        """
        by_airline: dict[str, list[GroupPeriod]] = {}
        for period in self.periods:
            by_airline.setdefault(period.airline, []).append(period)
        problems: list[str] = []
        for airline, rows in by_airline.items():
            ordered = sorted(rows, key=lambda p: (p.start_ym or 0, p.end_ym or 999912))
            for first, second in pairwise(ordered):
                if (first.end_ym or 999912) >= (second.start_ym or 0):
                    problems.append(f"{airline}: {first.group} and {second.group} overlap")
        if problems:
            raise ValueError("overlapping airline periods:\n  " + "\n  ".join(problems))

    def assert_known_classes(self) -> None:
        """Fail on a class outside `CLASSES` — a typo must not become a category."""
        unknown = sorted({p.klass for p in self.periods} - set(CLASSES))
        if unknown:
            raise ValueError(f"unknown classes {unknown}; allowed: {list(CLASSES)}")

    # ------------------------------------------------------------------ lookups

    def _find(self, airline: str | None, ym: int | None) -> GroupPeriod | None:
        if airline is None or ym is None:
            return None
        code = str(airline).strip().upper()
        for period in self.periods:
            if period.airline == code and period.covers(int(ym)):
                return period
        return None

    def group_of(self, airline: str | None, ym: int | None) -> str | None:
        """The economic group at `ym`; falls back to the airline's own code."""
        found = self._find(airline, ym)
        if found is not None:
            return found.group
        return str(airline).strip().upper() if airline else None

    def class_of(self, airline: str | None, ym: int | None) -> str:
        """The business-model class at `ym`; `other` when unlabelled (ADR-0011)."""
        found = self._find(airline, ym)
        return found.klass if found is not None else DEFAULT_CLASS

    # ------------------------------------------------------------------ frames

    def to_frame(self) -> pd.DataFrame:
        """The table as a data frame with integer month keys."""
        import pandas as pd

        return pd.DataFrame(
            {
                "airline": [p.airline for p in self.periods],
                "group": [p.group for p in self.periods],
                "class": [p.klass for p in self.periods],
                "start_ym": [p.start_ym for p in self.periods],
                "end_ym": [p.end_ym for p in self.periods],
            }
        )

    def register(self, con: Any, name: str = "groups_tbl") -> str:
        """Register the table in a DuckDB connection and return its name."""
        con.register(f"_{name}_view", self.to_frame())
        con.execute(f"CREATE OR REPLACE TEMP TABLE {name} AS SELECT * FROM _{name}_view")
        con.unregister(f"_{name}_view")
        return name


def label_sql(
    airline: str = "airline",
    ym: str = "ym",
    table: str = "groups_tbl",
    alias: str = "g",
) -> str:
    """The LEFT JOIN that dates the group/class labels onto a flight table.

    Written as a join rather than a per-row lookup because the alternative —
    a CASE tree — is exactly the hard-coded merger rule that ADR-0003 replaced
    with a reviewable CSV.
    """
    return (
        f"LEFT JOIN {table} {alias} ON {alias}.airline = {airline} "
        f"AND ({alias}.start_ym IS NULL OR {ym} >= {alias}.start_ym) "
        f"AND ({alias}.end_ym IS NULL OR {ym} <= {alias}.end_ym)"
    )


def resolved_group_sql(airline: str = "airline", alias: str = "g") -> str:
    """Group expression with the ICAO-code fallback for an unlabelled airline."""
    return f'coalesce({alias}."group", {airline})'


def resolved_class_sql(alias: str = "g") -> str:
    """Class expression with the `other` fallback of ADR-0011."""
    return f"coalesce({alias}.\"class\", '{DEFAULT_CLASS}')"


def in_set_sql(column: str, values: tuple[str, ...]) -> str:
    """``column IN ('A', 'B')`` with the quoting done once, in one place."""
    return f"{column} IN (" + ", ".join(f"'{value}'" for value in values) + ")"


__all__ = [
    "BENCHMARK_FSC_GROUPS",
    "BENCHMARK_LCC_GROUPS",
    "CLASSES",
    "DEFAULT_CLASS",
    "GroupPeriod",
    "GroupTable",
    "in_set_sql",
    "label_sql",
    "resolved_class_sql",
    "resolved_group_sql",
]
