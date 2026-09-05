"""The reconstruction panel, route x month: the article's columns plus everything new.

Three blocks live side by side in one table, and the names say which is which.

**The article block** carries the article's own column names (`f`, `fl_can`,
`fsc_prdelarr`, `prwheather`, `maxalccfu`, ...) computed from the public VRA
under the article's own definitions (ADR-0001, 0002, 0005, 0008, 0012, 0013)
(`reconstrucao-vra.md`). They are here to be *compared*, so they keep the
article's spelling — including `prwheather`, which is misspelled in the source
and is not renamed.

**The variant block** exists wherever this repository offers a second,
documented definition next to the article's. Two cases: `fscc_*` uses
ADR-0003's FSC *class*, which includes Avianca Brasil that the article's own
group set excludes (ADR-0013); and `*_trunc` uses the article's zero-truncated
delay against ADR-0008's signed one. Both numbers are published.

**The new-feature block** is everything the article did not use: market
structure, schedule shape, cause-code taxonomy, recovery and padding, the
city-side aggregates on both endpoints and the ADR-0007 congestion proxy.

`empty_actual_means_on_time` defaults to `True` here and only here (ADR-0012):
this is the table built under the article's own convention, which read an empty
actual time as "on schedule". The prediction layer builds its own dataset with
`False`.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from airline_delays import fact as fact_mod
from airline_delays import paths
from airline_delays import staging as staging_mod
from airline_delays.definitions import carriers as carriers_mod
from airline_delays.definitions import concentration as concentration_mod
from airline_delays.definitions import congestion as congestion_mod
from airline_delays.definitions import delays as delays_mod
from airline_delays.definitions import nodes as nodes_mod

if TYPE_CHECKING:  # pragma: no cover - typing only
    import pandas as pd
from airline_delays.panel.columns import (
    CITY_SIDE_COLUMNS,
    DROPPED_FROM_PANEL,
    NOT_IN_VRA,
    _is_published_slice_column,
)


@dataclass
class PanelResult:
    """What one `build_panel` run produced."""

    rows: int
    columns: int
    seconds: float
    parquet: Path
    csv: Path
    empty_actual_means_on_time: bool


def _sums(fact: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    columns = [name for name in fact_mod.FACT_SUM_COLUMNS if name in fact.columns]
    return fact.groupby(keys, observed=True, as_index=False)[columns].sum()


def _slice(fact: pd.DataFrame, mask: pd.Series, keys: list[str], prefix: str) -> pd.DataFrame:
    """Route-month sums over one slice of the fact table, prefixed."""
    part = _sums(fact[mask], keys)
    renamed = {name: f"{prefix}{name}" for name in part.columns if name not in keys}
    return part.rename(columns=renamed)


def _proportion(
    frame: pd.DataFrame, prefix: str, side: str, cut: str, *, legacy: bool
) -> pd.Series:
    """A delay proportion of one slice, under the ADR-0012 convention in force."""
    stub = frame[[f"{prefix}{side}_delay_obs", f"{prefix}{side}_missing_actual"]].rename(
        columns={
            f"{prefix}{side}_delay_obs": f"{side}_delay_obs",
            f"{prefix}{side}_missing_actual": f"{side}_missing_actual",
        }
    )
    denominator = fact_mod.delay_denominator(stub, side, empty_actual_means_on_time=legacy)
    numerator = frame[f"{prefix}{side}_delayed_{cut}"].astype("float64")
    return numerator / denominator.where(denominator > 0)


def _log_odds(proportion: pd.Series) -> pd.Series:
    """``ln(p / (1 - p))``; 0 and 1 become null rather than +/- infinity."""
    import numpy as np

    values = proportion.astype("float64")
    inside = (values > 0) & (values < 1)
    return np.log(values.where(inside) / (1.0 - values.where(inside)))


def build_panel(
    analysis_dir: Path,
    derived_dir: Path,
    *,
    external_dir: Path | None = None,
    empty_actual_means_on_time: bool = True,
    panel_nodes_only: bool = True,
    write: bool = True,
) -> tuple[pd.DataFrame, PanelResult | None]:
    """Assemble the route-month panel from the fact table and its projections.

    Reads only what `build_fact` wrote — no second scan of the staged flights,
    which is what keeps `just panel` in seconds after `just fact`.
    """
    import pandas as pd

    started = time.time()
    analysis_dir, derived_dir = Path(analysis_dir), Path(derived_dir)
    external_dir = external_dir or paths.EXTERNAL
    fact = pd.read_parquet(analysis_dir / "fact_group_route_month.parquet")
    context = pd.read_parquet(derived_dir / "route_month_context.parquet")
    day_hour = pd.read_parquet(derived_dir / "node_day_hour.parquet")
    # ADR-0016, checked on the way in rather than only on the way out: a
    # duplicated context row multiplies the panel row it joins onto, and the
    # copies differ in exactly the columns the join brings — which is how 866
    # duplicated route-months reached the first public panel with equal flight
    # counts and different medians.
    fact_mod.assert_unique(fact, fact_mod.FACT_UNIQUE_KEY, "committed fact table")
    fact_mod.assert_unique(context, fact_mod.ROUTE_MONTH_KEY, "committed route_month_context")
    if panel_nodes_only:
        nodes = set(nodes_mod.PANEL_NODES)
        fact = fact[fact["origin_node"].isin(nodes) & fact["dest_node"].isin(nodes)]
        fact = fact[fact["origin_node"] != fact["dest_node"]]
    city = fact_mod.city_month(
        fact, day_hour, empty_actual_means_on_time=empty_actual_means_on_time
    )
    panel = assemble(
        fact,
        context,
        city,
        external_dir=external_dir,
        empty_actual_means_on_time=empty_actual_means_on_time,
    )
    if not write:
        return panel, None
    parquet = analysis_dir / "panel_route_month.parquet"
    csv = analysis_dir / "panel_route_month.csv.gz"
    fact_mod.write_table(panel, parquet)
    # mtime=0: the gzip *header* embeds the write time, so without this a tracked
    # file whose payload is byte-identical still changes on every rebuild
    # (audit 2026-09-05, m-3). The payload was already deterministic; now the
    # whole file is.
    panel.to_csv(csv, index=False, compression={"method": "gzip", "mtime": 0}, float_format="%.6g")
    result = PanelResult(
        rows=len(panel),
        columns=panel.shape[1],
        seconds=time.time() - started,
        parquet=parquet,
        csv=csv,
        empty_actual_means_on_time=empty_actual_means_on_time,
    )
    _write_manifest(analysis_dir, result)
    return panel, result


def assemble(
    fact: pd.DataFrame,
    context: pd.DataFrame,
    city: pd.DataFrame,
    *,
    external_dir: Path,
    empty_actual_means_on_time: bool = True,
) -> pd.DataFrame:
    """The panel itself: the article's columns, the documented variants and the new features."""
    import numpy as np
    import pandas as pd

    keys = ["ym", "year", "month", "route", "origin_node", "dest_node"]
    legacy = empty_actual_means_on_time
    base = fact_mod.aggregate(fact, "route_month", empty_actual_means_on_time=legacy)
    klass = fact["class"]
    group = fact["group"]
    slices = {
        "fsc_": group.isin(carriers_mod.ARTICLE_FSC_GROUPS),
        "lccclass_": klass.eq("LCC"),
        "fscc_": klass.eq("FSC"),
        "lccfu_": group.isin(carriers_mod.ARTICLE_LCC_GROUPS),
    }
    panel = base
    for prefix, mask in slices.items():
        panel = panel.merge(_slice(fact, mask, keys, prefix), on=keys, how="left")
    sliced = [name for name in panel.columns if any(name.startswith(prefix) for prefix in slices)]
    panel[sliced] = panel[sliced].fillna(0)

    # ------------------------------------------------------------------ article block
    #
    # Built into a dictionary and attached in one `concat`: eighty separate
    # assignments on a 200-column frame make pandas copy the block manager
    # eighty times, and the panel is the widest table in the repository.
    ndays = _days_in_month(panel["ym"])
    actf = panel["realized"].astype("float64").where(panel["realized"] > 0)
    new: dict[str, Any] = {
        "f": panel["flights"],
        "fl_real": panel["realized"],
        "fl_can": panel["flights"] - panel["realized"],
        "fl_odel": panel["dep_delayed_gt0"],
        "fl_ddel": panel["arr_delayed_gt0"],
        "ndays": ndays,
        "dailyfl": panel["flights"] / ndays,
        "prcanc": (panel["flights"] - panel["realized"])
        / panel["flights"].where(panel["flights"] > 0),
    }
    new["dailyfl00"] = new["dailyfl"] / 100.0

    keep: set[str] = set()
    for prefix in slices:
        stem = prefix.rstrip("_")
        new[f"{stem}_f"] = panel[f"{prefix}flights"]
        new[f"{stem}_n"] = panel[f"{prefix}realized"]
        new[f"{stem}_prdelarr"] = _proportion(panel, prefix, "arr", "gt15", legacy=legacy)
        new[f"{stem}_prdelarr1530"] = _proportion(panel, prefix, "arr", "1530", legacy=legacy)
        new[f"{stem}_prdelarr30m"] = _proportion(panel, prefix, "arr", "gt30", legacy=legacy)
        new[f"{stem}_prdeldep"] = _proportion(panel, prefix, "dep", "gt15", legacy=legacy)
        new[f"{stem}_oddsarr"] = _log_odds(new[f"{stem}_prdelarr"])
        new[f"{stem}_oddsdep"] = _log_odds(new[f"{stem}_prdeldep"])
        new[f"{stem}_minsarr"] = panel[f"{prefix}sum_arr_delay_min"] / actf
        new[f"{stem}_minsdep"] = panel[f"{prefix}sum_dep_delay_min"] / actf
        new[f"{stem}_minsp15arr"] = panel[f"{prefix}sum_arr_delay_p15_min"] / actf
        new[f"{stem}_minsp15dep"] = panel[f"{prefix}sum_dep_delay_p15_min"] / actf
        new[f"{stem}_minsarr_trunc"] = panel[f"{prefix}sum_arr_delay_pos_min"] / actf
        new[f"{stem}_minsdep_trunc"] = panel[f"{prefix}sum_dep_delay_pos_min"] / actf
        # The slice's own sums were the raw material, not the product: they are
        # the fact table's job, and 4 x 77 of them would triple the panel. Only
        # the two denominators that make each proportion auditable survive.
        keep.update(
            {
                f"{prefix}arr_delay_obs",
                f"{prefix}dep_delay_obs",
                f"{prefix}arr_missing_actual",
                f"{prefix}dep_missing_actual",
            }
        )

    new["all_prdelarr"] = panel["sh_arr_gt15"]
    new["all_prdeldep"] = panel["sh_dep_gt15"]
    new["all_minsarr"] = panel["sum_arr_delay_min"] / actf
    new["all_minsdep"] = panel["sum_dep_delay_min"] / actf
    # `prwheather`, `princident` and `pr_connc` are not recomputed here: they
    # already arrive from `features.aggregate`, over the same denominator, and a
    # second copy would be a second definition.
    panel = pd.concat([panel, pd.DataFrame(new, index=panel.index)], axis=1)

    presence = _presence(fact, keys)
    panel = panel.merge(presence, on=keys, how="left")
    for name in presence.columns:
        if name not in keys:
            panel[name] = panel[name].fillna(0).astype("int8")

    # ------------------------------------------------------------------- new features
    panel = panel.merge(context, on=keys, how="left")
    panel["sh_extra"] = panel["n_extra"] / panel["n_rows_all"].where(panel["n_rows_all"] > 0)
    panel["rthhi_flights"] = panel["hhi_flights"]
    panel = _attach_cities(panel, city)
    panel["maxalccfu"] = panel[["olccfu", "dlccfu"]].max(axis=1).astype("int8")
    panel["maxcthhi_flights"] = np.maximum(panel["o_hhi_flights"], panel["d_hhi_flights"])
    panel["gmchhi_flights"] = np.sqrt(panel["o_hhi_flights"] * panel["d_hhi_flights"])
    panel["maxcongested"] = np.maximum(
        panel["o_sh_movements_congested"], panel["d_sh_movements_congested"]
    )
    panel["maxprdel_proxy"] = np.maximum(panel["o_sh_arr_gt15"], panel["d_sh_arr_gt15"])
    panel = _attach_distance(panel, external_dir)
    # Published as nulls on purpose: `hhi.passenger_weighted_hhi` has no traffic
    # table to read, and one row of declared capacity is not a panel (ADR-0007).
    for name in NOT_IN_VRA:
        panel[name] = pd.Series(
            concentration_mod.passenger_weighted_hhi(None), index=panel.index, dtype="float32"
        )
    panel["empty_actual_means_on_time"] = np.int8(1 if legacy else 0)
    out = _finalise(panel, slice_prefixes=tuple(slices), slice_keep=keep)
    fact_mod.assert_unique(out, fact_mod.ROUTE_MONTH_KEY, "panel_route_month")
    return out


def _presence(fact: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    """Operation-based presence dummies: `lcc`, `pres_glo`, `pres_azu`, `pres_tam`.

    The article's `lcc` comes from the tariff base — who *sold tickets* on the
    route — and this one comes from the VRA — who *flew* it. Both are right
    about different questions; the name stays so the two panels can be read
    side by side.
    """

    active = fact[fact["flights"] > 0]
    wanted = {
        "pres_glo": ("GOL",),
        "pres_azu": ("AZUL",),
        "pres_tam": ("TAM",),
        "lcc": carriers_mod.ARTICLE_LCC_GROUPS,
    }
    out: pd.DataFrame | None = None
    for name, wanted_groups in wanted.items():
        part = (
            active[active["group"].isin(wanted_groups)]
            .groupby(keys, observed=True)
            .size()
            .gt(0)
            .astype("int8")
            .rename(name)
            .reset_index()
        )
        out = part if out is None else out.merge(part, on=keys, how="outer")
    assert out is not None
    return out


def _attach_cities(panel: pd.DataFrame, city: pd.DataFrame) -> pd.DataFrame:
    """Join the city-month table onto both endpoints, as `o_` and `d_`."""
    available = [name for name in CITY_SIDE_COLUMNS if name in city.columns]
    slim = city[["ym", "node", *available]]
    for prefix, node_column in (("o_", "origin_node"), ("d_", "dest_node")):
        side = slim.rename(
            columns={"node": node_column, **{name: f"{prefix}{name}" for name in available}}
        )
        panel = panel.merge(side, on=["ym", node_column], how="left")
    panel["olccfu"] = panel["o_lccfu_present"].fillna(0).astype("int8")
    panel["dlccfu"] = panel["d_lccfu_present"].fillna(0).astype("int8")
    return panel


def _attach_distance(panel: pd.DataFrame, external_dir: Path) -> pd.DataFrame:
    """Great-circle distance between the two nodes, from `distances_km.csv`."""
    import pandas as pd

    path = Path(external_dir) / "distances_km.csv"
    if not path.exists():
        panel["distance_km"] = pd.NA
        return panel
    table = pd.read_csv(path)[["origin_node", "dest_node", "distance_km"]]
    return panel.merge(table, on=["origin_node", "dest_node"], how="left")


def _days_in_month(ym: pd.Series) -> pd.Series:
    import pandas as pd

    periods = pd.PeriodIndex(
        pd.to_datetime(ym.astype(int).astype(str) + "01", format="%Y%m%d"), freq="M"
    )
    return pd.Series(periods.days_in_month, index=ym.index, dtype="int16")


def _finalise(
    panel: pd.DataFrame,
    slice_prefixes: tuple[str, ...] = (),
    slice_keep: set[str] | None = None,
) -> pd.DataFrame:
    """Drop the intermediates, tighten floats, order the columns.

    Two families go: the fact's 24 hourly counts, whose information survives as
    `peak_hour_share`, `hhi_hours` and `sh_night`; and the per-slice sums, which
    exist in `fact_group_route_month.parquet` at a finer grain than the panel.
    """
    keep = slice_keep or set()
    drop = [name for name in fact_mod.HOUR_COLUMNS if name in panel.columns]
    drop += [name for name in DROPPED_FROM_PANEL if name in panel.columns]
    drop += [
        name
        for name in panel.columns
        if name not in keep
        and any(name.startswith(prefix) for prefix in slice_prefixes)
        and not _is_published_slice_column(name, slice_prefixes)
    ]
    panel = panel.drop(columns=sorted(set(drop)))
    floats = [name for name, dtype in panel.dtypes.items() if str(dtype).startswith("float")]
    # Six decimals, not three: the city projections round harder, but this table
    # is compared with the article panel at a tolerance of 1e-4 on proportions,
    # and a rounding step coarser than the tolerance would show up as a
    # disagreement that the definition never had.
    panel[floats] = panel[floats].round(6).astype("float32")
    leading = ["route", "ym", "year", "month", "origin_node", "dest_node", "ndays", "distance_km"]
    rest = [name for name in panel.columns if name not in leading]
    return panel[[*leading, *rest]].sort_values(["route", "ym"], ignore_index=True)


def _write_manifest(analysis_dir: Path, result: PanelResult) -> Path:
    path = analysis_dir / "panel_manifest.json"
    repo_root = paths.REPO_ROOT
    document = {
        "layer": "panel",
        "grain": "one row per route x month, replication universe",
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "git_commit": staging_mod.git_commit(repo_root, short=True),
        "tool_versions": staging_mod.tool_versions(),
        "empty_actual_means_on_time": result.empty_actual_means_on_time,
        "outlier_threshold_min": delays_mod.OUTLIER_THRESHOLD_MIN,
        "rows": result.rows,
        "columns": result.columns,
        "parquet_bytes": result.parquet.stat().st_size,
        "csv_bytes": result.csv.stat().st_size,
        "seconds": round(result.seconds, 2),
    }
    path.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def capacity_note(external_dir: Path) -> str:
    """One line saying whether the declared-capacity congestion variant can run."""
    rows = congestion_mod.load_capacity(Path(external_dir) / "capacity.csv")
    if congestion_mod.declared_congestion_available(rows):
        return f"declared capacity: {len({r.icao for r in rows})} airports"
    return (
        f"declared capacity: {len(rows)} row(s); prcongested not reproduced (ADR-0007), "
        "p90 proxy published instead"
    )
