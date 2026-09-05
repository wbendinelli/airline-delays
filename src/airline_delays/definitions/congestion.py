"""Congestion: the internal p90 proxy now, declared capacity when it exists.

ADR-0007 ships both definitions on purpose. The article's `prcongested` counts
flights scheduled in a clock hour whose movements exceed the airport's
**declared capacity**; that table lives in ANAC's seasonal capacity
declarations, and `data/external/capacity.csv` currently holds one row
(Congonhas, 33 movements/hour from 2007-08, confidence B). One row cannot carry
a national panel, so `prcongested` is *not reproduced* and says so.

The proxy that can be computed today is internal to the VRA and needs no
outside table: within a node and a calendar **year**, take the distribution of
movements per day-hour, and call congested every day-hour at or above that
distribution's 90th percentile. Two properties matter. It is relative to the
airport's own scale, so Congonhas is not congested merely for being large; and
the threshold is fixed per year, so a month can have more or fewer congested
hours than the 10% the percentile suggests — which is the point, because that
variation is the signal.

The unit is the **movement**: a departure counted at the origin node plus an
arrival counted at the destination node, both on the flight's *scheduled*
times, so the measure is knowable the day before and never leaks the outcome
into a prediction feature (ADR-0009).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - typing only
    import pandas as pd

PERCENTILE = 0.90
"""The p90 of ADR-0007; a named constant so a report can vary it deliberately."""

MIN_DAY_HOURS = 24
"""Fewer observed day-hours than this in a node-year leaves the threshold null.

A node with a handful of scheduled movements a year has no meaningful
percentile; returning one would invent congestion where there is an airstrip.
"""


@dataclass(frozen=True)
class CapacityRow:
    """One declared-capacity record from `data/external/capacity.csv`."""

    icao: str
    valid_from_ym: int | None
    valid_to_ym: int | None
    movements_per_hour: float | None

    def covers(self, ym: int) -> bool:
        if self.valid_from_ym is not None and ym < self.valid_from_ym:
            return False
        return not (self.valid_to_ym is not None and ym > self.valid_to_ym)


def _month_key(value: object) -> int | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "nat"}:
        return None
    digits = text[:7].replace("-", "")
    return int(digits) if digits.isdigit() else None


def load_capacity(path: Path | str) -> tuple[CapacityRow, ...]:
    """Read `capacity.csv`; rows without an hourly figure are dropped, not zeroed."""
    import pandas as pd

    frame = pd.read_csv(path, dtype=str, keep_default_na=False)
    rows: list[CapacityRow] = []
    for _, row in frame.iterrows():
        raw = str(row.get("movements_per_hour", "")).strip()
        if not raw:
            continue
        try:
            movements = float(raw)
        except ValueError:
            continue
        rows.append(
            CapacityRow(
                icao=str(row["icao"]).strip().upper(),
                valid_from_ym=_month_key(row.get("valid_from")),
                valid_to_ym=_month_key(row.get("valid_to")),
                movements_per_hour=movements,
            )
        )
    return tuple(rows)


def declared_capacity(rows: tuple[CapacityRow, ...], icao: str, ym: int) -> float | None:
    """Declared movements per hour for an airport at a month, or None.

    None is the honest answer for every airport but Congonhas after 2007-08;
    `prcongested` stays null wherever this returns None (ADR-0007).
    """
    for row in rows:
        if row.icao == str(icao).strip().upper() and row.covers(int(ym)):
            return row.movements_per_hour
    return None


def p90_thresholds(day_hours: pd.DataFrame) -> pd.DataFrame:
    """Per node-year congestion threshold from the node's own day-hour counts.

    `day_hours` has one row per ``node, year, ym, day, hour`` with a `movements`
    count. Returns ``node, year, threshold, n_day_hours``; the threshold is null
    where fewer than `MIN_DAY_HOURS` day-hours were observed.
    """
    grouped = day_hours.groupby(["node", "year"], observed=True)["movements"]
    out = grouped.agg(threshold=lambda s: s.quantile(PERCENTILE), n_day_hours="size")
    out = out.reset_index()
    out.loc[out["n_day_hours"] < MIN_DAY_HOURS, "threshold"] = None
    return out


def monthly_congestion(day_hours: pd.DataFrame) -> pd.DataFrame:
    """Node-month congestion measures from the node-year p90 threshold.

    Columns returned, one row per ``node, ym``:

    ``mov_hour_max``
        Busiest single day-hour of the month.
    ``mov_hour_mean``
        Mean movements over the day-hours that had any movement.
    ``congested_hours``
        Day-hours of the month at or above the node-year p90 threshold.
    ``congested_movements``
        Movements inside those day-hours.
    ``sh_movements_congested``
        Their share of the month's movements — the proxy for `prcongested`.
    """
    import pandas as pd

    thresholds = p90_thresholds(day_hours)
    merged = day_hours.merge(thresholds, on=["node", "year"], how="left")
    above = merged["movements"] >= merged["threshold"]
    merged = merged.assign(
        _above=above.fillna(False),
        _above_mov=merged["movements"].where(above.fillna(False), 0),
    )
    grouped = merged.groupby(["node", "ym"], observed=True)
    out = grouped.agg(
        mov_hour_max=("movements", "max"),
        mov_hour_mean=("movements", "mean"),
        movements=("movements", "sum"),
        congested_hours=("_above", "sum"),
        congested_movements=("_above_mov", "sum"),
    ).reset_index()
    out["sh_movements_congested"] = out["congested_movements"] / out["movements"].where(
        out["movements"] > 0
    )
    out["congested_hours"] = out["congested_hours"].astype("int32")
    out["congested_movements"] = out["congested_movements"].astype("int32")
    return pd.DataFrame(out)


def declared_congestion_available(rows: tuple[CapacityRow, ...]) -> bool:
    """Whether `capacity.csv` has enough rows for the declared-capacity variant.

    One airport is not a panel: with a single row the declared version would
    exist only for Congonhas after 2007-08 and be null everywhere else, which is
    worse than being absent and labelled. `features` writes the declared columns
    only when this is true.
    """
    return len({row.icao for row in rows}) >= 2


__all__ = [
    "MIN_DAY_HOURS",
    "PERCENTILE",
    "CapacityRow",
    "declared_capacity",
    "declared_congestion_available",
    "load_capacity",
    "monthly_congestion",
    "p90_thresholds",
]
