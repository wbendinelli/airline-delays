"""Which columns the route-month panel carries: the city-side aggregates, the article variables the VRA
cannot compute, the slice suffixes and the fact-table columns the panel drops."""

from __future__ import annotations

CITY_SIDE_COLUMNS: tuple[str, ...] = (
    "movements",
    "movements_realized",
    "sh_cancel",
    "sh_dep_gt0",
    "sh_dep_gt15",
    "sh_arr_gt0",
    "sh_arr_gt15",
    "arr_delay_mean_min",
    "pr_connc",
    "prwheather",
    "n_groups",
    "hhi_flights",
    "sh_leader",
    "sh_movements_lcc",
    "lccfu_present",
    "mov_hour_max",
    "congested_hours",
    "sh_movements_congested",
    "n_hub_groups",
    "hub_max_score",
)

"""City-month columns carried onto both endpoints of a route, as `o_`/`d_`."""

NOT_IN_VRA: tuple[str, ...] = ("rthhi", "maxcthhi", "gmchhi", "prcongested")

"""Article columns the VRA cannot produce; published as nulls, never substituted.

`rthhi`, `maxcthhi` and `gmchhi` are concentration over **paid passengers**,
which lives in ANAC's statistical data and not in an operations file; the
flight-based indices are published next to them under different names
(`rthhi_flights`, ...) so nobody can mistake one for the other.
`prcongested` needs declared hourly capacity by airport, of which
`data/external/capacity.csv` currently holds one row (ADR-0007); the p90 proxy
is published as `o_sh_movements_congested`/`d_sh_movements_congested`.
"""

SLICE_SUFFIXES: tuple[str, ...] = (
    "f",
    "n",
    "prdelarr",
    "prdelarr1530",
    "prdelarr30m",
    "prdeldep",
    "oddsarr",
    "oddsdep",
    "minsarr",
    "minsdep",
    "minsp15arr",
    "minsp15dep",
    "minsarr_trunc",
    "minsdep_trunc",
)

"""Every derived column a carrier slice can have; all of them are computed."""

PUBLISHED_SLICE_SUFFIXES: dict[str, tuple[str, ...]] = {
    "fsc_": SLICE_SUFFIXES,
    "fscc_": ("n", "prdelarr", "prdeldep", "oddsarr", "minsarr", "minsp15arr"),
    "lccfu_": ("n", "f", "prdelarr", "prdeldep", "oddsarr", "minsarr"),
    "lccclass_": ("n", "prdelarr", "minsarr"),
}

"""What each slice *publishes*. Only `fsc_` gets the full set.

The other three exist to expose a definitional difference, not to be a second
panel: `fscc_` is ADR-0003's FSC class against the article's own group set
(ADR-0013), `lccclass_` is the LCC class against the article's Gol-and-Azul
set, and `lccfu_` is that set itself. Six columns each show the gap; forty
would only triple the file. Everything omitted is one `groupby` away in
`fact_group_route_month.parquet`, which keeps the finer grain.
"""

DROPPED_FROM_PANEL: tuple[str, ...] = (
    "sum_dep_delay_pos_min",
    "sum_dep_delay_p15_min",
    "sum_arr_delay_pos_min",
    "sum_arr_delay_p15_min",
    "sum_recovery_min",
    "sum_sched_block_min",
    "sum_sched_block_sq",
    "sum_actual_block_min",
    "sum_padding_min",
)

"""Raw sums whose mean is published instead; the sums live in the fact table."""


def _is_published_slice_column(name: str, prefixes: tuple[str, ...]) -> bool:
    return any(
        name.startswith(prefix) and name[len(prefix) :] in PUBLISHED_SLICE_SUFFIXES.get(prefix, ())
        for prefix in prefixes
    )
