"""Projections of the fact table onto coarser grains -- route-month, city-month, airline-city-month --
with the denominators of ADR-0012, the congestion and hub extensions, and the city-month table."""

from __future__ import annotations

from typing import TYPE_CHECKING

from airline_delays.definitions import carriers as carriers_mod
from airline_delays.definitions import cause_codes as cause_codes_mod
from airline_delays.definitions import concentration as concentration_mod
from airline_delays.definitions import congestion as congestion_mod
from airline_delays.definitions import hubs as hubs_mod

if TYPE_CHECKING:  # pragma: no cover - typing only
    import pandas as pd
from airline_delays.fact.build import assert_unique
from airline_delays.fact.measures import (
    AIRLINE_CITY_MONTH_KEY,
    CANCEL_CAUSES,
    CITY_MONTH_KEY,
    FACT_SUM_COLUMNS,
    FACT_UNIQUE_KEY,
    HOUR_COLUMNS,
    ROUTE_MONTH_KEY,
    Grain,
)


def delay_denominator(
    frame: pd.DataFrame, side: str, *, legacy_missing_actual_as_zero: bool
) -> pd.Series:
    """Flights a delay proportion is divided by, under one of the two conventions.

    This one function is where ADR-0012 bites. Under the 2019 vintage's rule an
    empty actual time means "on schedule", so the flight belongs in the
    denominator and not in the numerator; under this repository's own rule it is
    an absence and belongs in neither. In 2000-2009 that is the difference
    between a denominator of every realised flight and a denominator of the
    45-20% of them that had an occurrence — which is why the strict reading
    reports arrival-delay rates far above the published ones.
    """
    observed = frame[f"{side}_delay_obs"].astype("float64")
    if not legacy_missing_actual_as_zero:
        return observed
    return observed + frame[f"{side}_missing_actual"].astype("float64")


def _ratio(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    return numerator.astype("float64") / denominator.astype("float64").where(denominator > 0)


_DEP_SIDE: tuple[str, ...] = (
    "flights",
    "realized",
    "cancelled",
    "dep_delay_obs",
    "dep_missing_actual",
    "dep_delayed_gt0",
    "dep_delayed_gt15",
    "dep_delayed_gt30",
    "dep_delayed_gt60",
    "dep_early",
    "dep_outliers",
    "sum_dep_delay_min",
    "sum_dep_delay_pos_min",
    "sum_dep_delay_p15_min",
    "night_flights",
    "weekend_flights",
    *HOUR_COLUMNS,
)

_ARR_SIDE: tuple[str, ...] = (
    "arr_delay_obs",
    "arr_missing_actual",
    "arr_delayed_gt0",
    "arr_delayed_gt15",
    "arr_delayed_1530",
    "arr_delayed_gt30",
    "arr_delayed_gt60",
    "arr_early",
    "arr_outliers",
    "sum_arr_delay_min",
    "sum_arr_delay_pos_min",
    "sum_arr_delay_p15_min",
)

_BOTH_SIDES: tuple[str, ...] = (
    "cause_none",
    *(f"cause_{category}" for category in cause_codes_mod.CATEGORY_NAMES),
    *(f"cause_set_{name}" for name in cause_codes_mod.ARTICLE_SETS),
    *CANCEL_CAUSES,
)


def aggregate(
    fact: pd.DataFrame,
    grain: Grain,
    *,
    legacy_missing_actual_as_zero: bool = True,
) -> pd.DataFrame:
    """Project the fact table onto a coarser grain.

    Additive measures are summed; proportions, shares and concentration indices
    are **recomputed** from the sums at the target grain, never averaged
    (ADR-0004). `n_flight_numbers` is dropped at every grain but the fact's own,
    because two groups can reuse a number and a distinct count does not add.
    """
    assert_unique(fact, FACT_UNIQUE_KEY, "fact table handed to aggregate()")
    if grain == "route_month":
        out = _aggregate_route_month(
            fact, legacy_missing_actual_as_zero=legacy_missing_actual_as_zero
        )
        assert_unique(out, ROUTE_MONTH_KEY, "route_month projection")
        return out
    if grain in {"city_month", "airline_city_month"}:
        with_group = grain == "airline_city_month"
        out = _aggregate_city(
            fact,
            with_group=with_group,
            legacy_missing_actual_as_zero=legacy_missing_actual_as_zero,
        )
        assert_unique(
            out, AIRLINE_CITY_MONTH_KEY if with_group else CITY_MONTH_KEY, f"{grain} projection"
        )
        return out
    raise ValueError(f"unknown grain {grain!r}; expected one of {Grain.__args__}")  # type: ignore[attr-defined]


def _aggregate_route_month(
    fact: pd.DataFrame, *, legacy_missing_actual_as_zero: bool
) -> pd.DataFrame:
    import pandas as pd

    keys = ["ym", "year", "month", "route", "origin_node", "dest_node"]
    sums = fact.groupby(keys, observed=True, as_index=False)[list(FACT_SUM_COLUMNS)].sum()
    structure = _market_structure(fact, keys)
    out = sums.merge(structure, on=keys, how="left")
    return pd.DataFrame(
        _add_shares(out, legacy_missing_actual_as_zero=legacy_missing_actual_as_zero)
    )


def _market_structure(fact: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    """Competitor count, flight-share HHI, leader share and class shares."""
    import pandas as pd

    active = fact[fact["flights"] > 0]
    grouped = active.groupby(keys, observed=True)
    out = grouped.agg(
        n_groups=("group", "nunique"),
        hhi_flights=("flights", lambda s: concentration_mod.hhi_from_counts(s)),
        sh_leader=("flights", lambda s: concentration_mod.leader_share(s)),
        n_entries=("is_entry", "sum"),
        n_exits=("is_exit", "sum"),
    ).reset_index()
    by_class = (
        active.groupby([*keys, "class"], observed=True)["flights"].sum().unstack(fill_value=0)
    )
    totals = by_class.sum(axis=1)
    for klass in carriers_mod.CLASSES:
        column = by_class.get(klass, 0)
        out[f"sh_flights_{klass.lower()}"] = (
            (column / totals.where(totals > 0)).reindex(_index_of(out, keys)).to_numpy()
        )
    lcc_entry = active[active["group"].isin(carriers_mod.BENCHMARK_LCC_GROUPS)]
    entry = lcc_entry.groupby(keys, observed=True)["is_entry"].max().rename("entry_lcc")
    out = out.merge(entry.reset_index(), on=keys, how="left")
    out["entry_lcc"] = out["entry_lcc"].fillna(0).astype("int8")
    return pd.DataFrame(out)


def _index_of(frame: pd.DataFrame, keys: list[str]):
    import pandas as pd

    return pd.MultiIndex.from_frame(frame[keys]) if len(keys) > 1 else frame[keys[0]]


def _aggregate_city(
    fact: pd.DataFrame, *, with_group: bool, legacy_missing_actual_as_zero: bool
) -> pd.DataFrame:
    import pandas as pd

    extra = ["group", "class"] if with_group else []
    keys = ["ym", "year", "month", "node", *extra]
    departures = fact.rename(columns={"origin_node": "node"})
    arrivals = fact.rename(columns={"dest_node": "node"})
    dep = departures.groupby(keys, observed=True, as_index=False)[[*_DEP_SIDE, *_BOTH_SIDES]].sum()
    arr = arrivals.groupby(keys, observed=True, as_index=False)[
        ["flights", "realized", "cancelled", *_ARR_SIDE, *_BOTH_SIDES]
    ].sum()
    arr = arr.rename(
        columns={
            "flights": "arr_flights",
            "realized": "arr_realized",
            "cancelled": "arr_cancelled",
            **{name: f"_arr_{name}" for name in _BOTH_SIDES},
        }
    )
    dep = dep.rename(
        columns={"flights": "dep_flights", "realized": "dep_realized", "cancelled": "dep_cancelled"}
    )
    out = dep.merge(arr, on=keys, how="outer")
    counts = [
        name
        for name in out.columns
        if name not in keys and not name.startswith(("sh_", "hhi_", "n_groups"))
    ]
    out[counts] = out[counts].fillna(0)
    for name in _BOTH_SIDES:
        out[name] = out[name] + out.pop(f"_arr_{name}")
    out["movements"] = out["dep_flights"] + out["arr_flights"]
    out["movements_realized"] = out["dep_realized"] + out["arr_realized"]
    out["movements_cancelled"] = out["dep_cancelled"] + out["arr_cancelled"]
    if not with_group:
        structure = _city_structure(fact)
        out = out.merge(structure, on=["ym", "node"], how="left")
    out = _add_city_shares(out, legacy_missing_actual_as_zero=legacy_missing_actual_as_zero)
    return pd.DataFrame(out.sort_values(keys, ignore_index=True))


def _city_structure(fact: pd.DataFrame) -> pd.DataFrame:
    """Competitor structure of a city's movements, both sides counted."""
    import pandas as pd

    departures = fact.rename(columns={"origin_node": "node"})[["ym", "node", "group", "flights"]]
    arrivals = fact.rename(columns={"dest_node": "node"})[["ym", "node", "group", "flights"]]
    both = pd.concat([departures, arrivals], ignore_index=True)
    per_group = both.groupby(["ym", "node", "group"], observed=True, as_index=False)[
        "flights"
    ].sum()
    per_group = per_group[per_group["flights"] > 0]
    grouped = per_group.groupby(["ym", "node"], observed=True)
    return grouped.agg(
        n_groups=("group", "nunique"),
        hhi_flights=("flights", lambda s: concentration_mod.hhi_from_counts(s)),
        sh_leader=("flights", lambda s: concentration_mod.leader_share(s)),
    ).reset_index()


def _add_shares(out: pd.DataFrame, *, legacy_missing_actual_as_zero: bool) -> pd.DataFrame:
    """Route-month proportions and means, recomputed from the sums.

    Built into a dictionary and attached in one `concat` rather than eighty
    assignments: pandas copies the block manager on every insert past a hundred
    columns, and this function alone would otherwise dominate the build.
    """
    import pandas as pd

    flights = out["flights"]
    new: dict[str, pd.Series] = {"sh_cancel": _ratio(out["cancelled"], flights)}
    for side in ("dep", "arr"):
        denominator = delay_denominator(
            out, side, legacy_missing_actual_as_zero=legacy_missing_actual_as_zero
        )
        new[f"{side}_delay_denominator"] = denominator
        for cut in ("gt0", "gt15", "gt30", "gt60"):
            new[f"sh_{side}_{cut}"] = _ratio(out[f"{side}_delayed_{cut}"], denominator)
        new[f"sh_{side}_early"] = _ratio(out[f"{side}_early"], denominator)
        trimmed = denominator - out[f"{side}_outliers"]
        new[f"{side}_delay_mean_min"] = _ratio(out[f"sum_{side}_delay_min"], trimmed)
        new[f"{side}_delay_mean_pos_min"] = _ratio(out[f"sum_{side}_delay_pos_min"], trimmed)
    new["sh_arr_1530"] = _ratio(out["arr_delayed_1530"], new["arr_delay_denominator"])
    new["sched_block_mean_min"] = _ratio(out["sum_sched_block_min"], out["sched_block_obs"])
    new["sched_block_sd_min"] = _standard_deviation(
        out["sum_sched_block_min"], out["sum_sched_block_sq"], out["sched_block_obs"]
    )
    new["padding_mean_min"] = _ratio(out["sum_padding_min"], out["padding_obs"])
    new["recovery_mean_min"] = _ratio(out["sum_recovery_min"], out["recovery_obs"])
    new["sh_recovered"] = _ratio(out["recovered_gt15"], out["recovery_obs"])
    new["sh_night"] = _ratio(out["night_flights"], flights)
    new["sh_weekend"] = _ratio(out["weekend_flights"], flights)
    hourly = out[list(HOUR_COLUMNS)]
    hour_total = hourly.sum(axis=1)
    new["peak_hour_share"] = _ratio(hourly.max(axis=1), hour_total)
    squares = (hourly.astype("float64") ** 2).sum(axis=1)
    new["hhi_hours"] = squares / (hour_total.astype("float64") ** 2).where(hour_total > 0)
    for name in (*(f"cause_{c}" for c in cause_codes_mod.CATEGORY_NAMES), "cause_none"):
        new[f"sh_{name}"] = _ratio(out[name], flights)
    for set_name in cause_codes_mod.ARTICLE_SETS:
        new[set_name] = _ratio(out[f"cause_set_{set_name}"], flights)
    for name in CANCEL_CAUSES:
        new[f"sh_{name}"] = _ratio(out[name], out["cancelled"])
    return pd.concat([out, pd.DataFrame(new, index=out.index)], axis=1)


def _add_city_shares(out: pd.DataFrame, *, legacy_missing_actual_as_zero: bool) -> pd.DataFrame:
    """City-month proportions: departures against departures, arrivals against arrivals."""
    import pandas as pd

    new: dict[str, pd.Series] = {"sh_cancel": _ratio(out["movements_cancelled"], out["movements"])}
    for side in ("dep", "arr"):
        denominator = delay_denominator(
            out, side, legacy_missing_actual_as_zero=legacy_missing_actual_as_zero
        )
        new[f"{side}_delay_denominator"] = denominator
        for cut in ("gt0", "gt15", "gt30"):
            new[f"sh_{side}_{cut}"] = _ratio(out[f"{side}_delayed_{cut}"], denominator)
        trimmed = denominator - out[f"{side}_outliers"]
        new[f"{side}_delay_mean_min"] = _ratio(out[f"sum_{side}_delay_min"], trimmed)
    for name in (*(f"cause_{c}" for c in cause_codes_mod.CATEGORY_NAMES), "cause_none"):
        new[f"sh_{name}"] = _ratio(out[name], out["movements"])
    for set_name in cause_codes_mod.ARTICLE_SETS:
        new[set_name] = _ratio(out[f"cause_set_{set_name}"], out["movements"])
    hourly = out[list(HOUR_COLUMNS)]
    hour_total = hourly.sum(axis=1)
    new["peak_hour_share"] = _ratio(hourly.max(axis=1), hour_total)
    squares = (hourly.astype("float64") ** 2).sum(axis=1)
    new["hhi_hours"] = squares / (hour_total.astype("float64") ** 2).where(hour_total > 0)
    return pd.concat([out, pd.DataFrame(new, index=out.index)], axis=1)


def _standard_deviation(total: pd.Series, squares: pd.Series, n: pd.Series) -> pd.Series:
    """Sample standard deviation from the two sums the fact table carries."""
    import numpy as np

    count = n.astype("float64")
    mean = total.astype("float64") / count.where(count > 0)
    variance = (squares.astype("float64") - count * mean * mean) / (count - 1).where(count > 1)
    return np.sqrt(variance.clip(lower=0))


def add_congestion(city_month: pd.DataFrame, day_hour: pd.DataFrame) -> pd.DataFrame:
    """Attach the ADR-0007 p90 proxy to a city-month table."""
    congestion = congestion_mod.monthly_congestion(day_hour).drop(columns=["movements"])
    return city_month.merge(congestion, on=["node", "ym"], how="left")


def add_hub(airline_city_month: pd.DataFrame) -> pd.DataFrame:
    """Attach the hub share, score and dummy to an airline-city-month table."""
    import pandas as pd

    frame = airline_city_month.copy()
    city_totals = frame.groupby(["ym", "node"], observed=True)["movements"].sum().rename("_city")
    group_totals = frame.groupby(["ym", "group"], observed=True)["movements"].sum().rename("_group")
    system = frame.groupby("ym", observed=True)["movements"].sum().rename("_system")
    frame = frame.merge(city_totals.reset_index(), on=["ym", "node"], how="left")
    frame = frame.merge(group_totals.reset_index(), on=["ym", "group"], how="left")
    frame = frame.merge(system.reset_index(), on="ym", how="left")
    frame["city_share"] = _ratio(frame["movements"], frame["_city"])
    frame["hub_score"] = frame["city_share"] / _ratio(frame["_group"], frame["_system"]).where(
        frame["_group"] > 0
    )
    frame["is_hub"] = (
        (frame["_city"] >= hubs_mod.MIN_CITY_MOVEMENTS)
        & (frame["movements"] >= hubs_mod.MIN_GROUP_MOVEMENTS)
        & (frame["city_share"] >= hubs_mod.MIN_SHARE)
        & (frame["hub_score"] >= hubs_mod.MIN_RATIO)
    ).astype("int8")
    return pd.DataFrame(frame.drop(columns=["_city", "_group", "_system"]))


def city_month(
    fact: pd.DataFrame,
    day_hour: pd.DataFrame,
    *,
    legacy_missing_actual_as_zero: bool = True,
) -> pd.DataFrame:
    """City-month table with class shares, the LCC presence dummy, congestion and hubs."""
    import pandas as pd

    city = aggregate(
        fact, "city_month", legacy_missing_actual_as_zero=legacy_missing_actual_as_zero
    )
    airline_city = aggregate(
        fact, "airline_city_month", legacy_missing_actual_as_zero=legacy_missing_actual_as_zero
    )
    airline_city = add_hub(airline_city)
    by_class = (
        airline_city.groupby(["ym", "node", "class"], observed=True)["movements"]
        .sum()
        .unstack(fill_value=0)
    )
    totals = by_class.sum(axis=1)
    shares = pd.DataFrame(index=by_class.index)
    for klass in carriers_mod.CLASSES:
        shares[f"sh_movements_{klass.lower()}"] = by_class.get(klass, 0) / totals.where(totals > 0)
    city = city.merge(shares.reset_index(), on=["ym", "node"], how="left")
    lccfu = airline_city[
        airline_city["group"].isin(carriers_mod.BENCHMARK_LCC_GROUPS)
        & (airline_city["movements"] > 0)
    ]
    presence = (
        lccfu.groupby(["ym", "node"], observed=True)
        .size()
        .gt(0)
        .astype("int8")
        .rename("lccfu_present")
        .reset_index()
    )
    city = city.merge(presence, on=["ym", "node"], how="left")
    city["lccfu_present"] = city["lccfu_present"].fillna(0).astype("int8")
    hubs = (
        airline_city.groupby(["ym", "node"], observed=True)
        .agg(n_hub_groups=("is_hub", "sum"), hub_max_score=("hub_score", "max"))
        .reset_index()
    )
    city = city.merge(hubs, on=["ym", "node"], how="left")
    city = add_congestion(city, day_hour)
    assert_unique(city, CITY_MONTH_KEY, "city_month")
    return city
