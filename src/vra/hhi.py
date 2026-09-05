"""Concentration indices.

The article's two endogenous variables are Herfindahl-Hirschman indices over
**paid passengers** by airline group, which the VRA does not carry: it is an
operations file, one row per flight leg, with no traffic. What the VRA does
support is an HHI over **flights**, and that is what this module computes; the
passenger-weighted version has a function with the right signature that returns
``None`` until ANAC's statistical data are collected, so the panel column
exists, is documented, and is honestly empty rather than silently substituted
by the flight-based one.

An HHI is never averaged when a table is rolled up to a coarser grain — it is
recomputed from the group shares at that grain (ADR-0004). `registry.py` marks
every index here ``recompute`` and `features.aggregate` honours it.

Shares are on 0-1, so a monopoly is 1.0 and not 10,000; multiply by 1e4 for the
antitrust convention if a report needs it.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping

MIN_SHARE_SUM = 1e-9
"""Below this total, a cell has no flights and every index is undefined."""


def shares_from_counts(counts: Iterable[float]) -> list[float]:
    """Normalise counts to shares; an empty or all-zero input gives an empty list."""
    values = [float(value) for value in counts if value is not None and float(value) > 0]
    total = sum(values)
    if total <= MIN_SHARE_SUM:
        return []
    return [value / total for value in values]


def hhi(shares: Iterable[float]) -> float | None:
    """Sum of squared shares. None when there is nothing to concentrate.

    >>> hhi([0.5, 0.5])
    0.5
    >>> hhi([1.0])
    1.0
    """
    values = [float(share) for share in shares]
    if not values or sum(values) <= MIN_SHARE_SUM:
        return None
    return float(sum(share * share for share in values))


def hhi_from_counts(counts: Iterable[float]) -> float | None:
    """HHI over shares derived from counts (flights, movements, seats).

    >>> hhi_from_counts([30, 10])
    0.625
    """
    shares = shares_from_counts(counts)
    return hhi(shares) if shares else None


def normalised_hhi(shares: Iterable[float]) -> float | None:
    """The number-equivalent-adjusted HHI, ``(H - 1/n) / (1 - 1/n)``.

    Undefined for a single competitor, where it would be 0/0; returns None.
    """
    values = [float(share) for share in shares]
    index = hhi(values)
    n = len(values)
    if index is None or n < 2:
        return None
    floor = 1.0 / n
    return float((index - floor) / (1.0 - floor))


def leader_share(counts: Iterable[float]) -> float | None:
    """Share of the largest competitor, or None when the cell is empty."""
    shares = shares_from_counts(counts)
    return max(shares) if shares else None


def max_endpoint(origin: float | None, destination: float | None) -> float | None:
    """``max`` of the two endpoint-city indices, the article's `maxcthhi` shape.

    None propagates: a route whose endpoint city has no index has no maximum.
    """
    if origin is None or destination is None:
        return None
    return max(float(origin), float(destination))


def geometric_mean(origin: float | None, destination: float | None) -> float | None:
    """``sqrt(origin * destination)``, the article's `gmchhi` shape."""
    if origin is None or destination is None:
        return None
    product = float(origin) * float(destination)
    if product < 0:
        return None
    return math.sqrt(product)


def passenger_weighted_hhi(
    paid_passengers: Mapping[str, float] | None = None,
) -> float | None:
    """The article's `rthhi`/`maxcthhi`: HHI over paid passengers by group.

    Returns ``None`` while `paid_passengers` is None, which is the state of this
    repository: ANAC's "Dados Estatísticos do Transporte Aéreo" have not been
    collected, and the VRA carries no traffic. The signature is here so that the
    panel column, the registry entry and the dictionary all exist and say
    exactly why the value is missing, instead of the flight-based HHI quietly
    taking its place (`docs/declared-differences.md`).
    """
    if not paid_passengers:
        return None
    return hhi_from_counts(paid_passengers.values())


# --------------------------------------------------------------------------- SQL

HHI_SQL = "sum(({count})::DOUBLE * {count}) / nullif(sum({count})::DOUBLE * sum({count}), 0)"
"""DuckDB fragment for ``Σ (n_i / N)²`` computed from raw counts in one pass."""


def hhi_sql(count_column: str) -> str:
    """Render `HHI_SQL` for a count column, e.g. ``hhi_sql("flights")``."""
    return HHI_SQL.format(count=count_column)


def leader_share_sql(count_column: str) -> str:
    """DuckDB fragment for the largest competitor's share."""
    return f"max({count_column})::DOUBLE / nullif(sum({count_column})::DOUBLE, 0)"


__all__ = [
    "geometric_mean",
    "hhi",
    "hhi_from_counts",
    "hhi_sql",
    "leader_share",
    "leader_share_sql",
    "max_endpoint",
    "normalised_hhi",
    "passenger_weighted_hhi",
    "shares_from_counts",
]
