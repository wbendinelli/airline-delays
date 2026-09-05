"""Hub score: how concentrated one group's operation is on one city.

The article uses Infraero's share of connecting passengers (`o_percon`,
`d_percon`), which is not public. The VRA substitute is structural, not
behavioural: a city is a hub *for a group* when the group holds a large share
of that city's movements **and** that share is much larger than the group's
share of the whole system in the same month.

The second condition is what the ratio adds, and the volume floor is what stops
it from being nonsense. Measured on 2012 (`avaliacao-vra-como-fonte.md`): the
raw ratio alone promotes a regional carrier with four monthly movements in a
small city above Gol in Rio de Janeiro, because four out of five movements is a
share of 0.8 against a system share near zero. With the floor, the same
computation returns what the sector recognises — TAM at 40% or more of
movements in Boa Vista, João Pessoa, Fortaleza, São Luís, Teresina and
Brasília; Gol at 41% or more in Rio de Janeiro, Salvador, Curitiba and
Florianópolis.

Everything here is a pure function of three counts, so the same definition
serves the panel, the city tables and the prediction features, and a leakage
test can check the window it was computed over.
"""

from __future__ import annotations

MIN_SHARE = 0.20
"""A group must hold at least this share of the city's movements to be a hub."""

MIN_RATIO = 2.0
"""...and at least twice its share of the system in the same month."""

MIN_CITY_MOVEMENTS = 100
"""Volume floor on the *city-month*: below it, no hub is declared at all.

A city with a handful of scheduled movements has no hub structure to measure;
without this floor the ratio makes every tiny operator look like a hub carrier.
"""

MIN_GROUP_MOVEMENTS = 30
"""Volume floor on the *group's own* movements in the city-month."""


def city_share(group_movements: float, city_movements: float) -> float | None:
    """The group's share of one city's movements in one month."""
    if city_movements is None or float(city_movements) <= 0:
        return None
    return float(group_movements) / float(city_movements)


def hub_score(
    group_city_movements: float,
    city_movements: float,
    group_system_movements: float,
    system_movements: float,
) -> float | None:
    """Ratio of the group's city share to its system share, in the same month.

    1.0 means the group is exactly as present in this city as it is nationally;
    3.0 means three times as concentrated. None when either denominator is
    empty or the group has no national presence to compare against.

    >>> round(hub_score(400, 1000, 1000, 10000), 3)
    4.0
    """
    share = city_share(group_city_movements, city_movements)
    system_share = city_share(group_system_movements, system_movements)
    if share is None or system_share is None or system_share <= 0:
        return None
    return share / system_share


def is_hub(
    group_city_movements: float,
    city_movements: float,
    group_system_movements: float,
    system_movements: float,
    *,
    min_share: float = MIN_SHARE,
    min_ratio: float = MIN_RATIO,
    min_city_movements: float = MIN_CITY_MOVEMENTS,
    min_group_movements: float = MIN_GROUP_MOVEMENTS,
) -> bool:
    """The hub dummy: share, ratio and both volume floors at once."""
    if float(city_movements or 0) < min_city_movements:
        return False
    if float(group_city_movements or 0) < min_group_movements:
        return False
    share = city_share(group_city_movements, city_movements)
    ratio = hub_score(
        group_city_movements, city_movements, group_system_movements, system_movements
    )
    if share is None or ratio is None:
        return False
    return share >= min_share and ratio >= min_ratio


# --------------------------------------------------------------------------- SQL


def hub_score_sql(
    group_city: str = "movements",
    city_total: str = "city_movements",
    group_system: str = "group_system_movements",
    system_total: str = "system_movements",
) -> str:
    """DuckDB translation of `hub_score`."""
    return (
        f"({group_city}::DOUBLE / nullif({city_total}::DOUBLE, 0)) / "
        f"nullif({group_system}::DOUBLE / nullif({system_total}::DOUBLE, 0), 0)"
    )


def is_hub_sql(
    group_city: str = "movements",
    city_total: str = "city_movements",
    group_system: str = "group_system_movements",
    system_total: str = "system_movements",
) -> str:
    """DuckDB translation of `is_hub`, floors included."""
    share = f"({group_city}::DOUBLE / nullif({city_total}::DOUBLE, 0))"
    return (
        f"({city_total} >= {MIN_CITY_MOVEMENTS} AND {group_city} >= {MIN_GROUP_MOVEMENTS} "
        f"AND {share} >= {MIN_SHARE} AND "
        f"{hub_score_sql(group_city, city_total, group_system, system_total)} >= {MIN_RATIO})"
    )


__all__ = [
    "MIN_CITY_MOVEMENTS",
    "MIN_GROUP_MOVEMENTS",
    "MIN_RATIO",
    "MIN_SHARE",
    "city_share",
    "hub_score",
    "hub_score_sql",
    "is_hub",
    "is_hub_sql",
]
