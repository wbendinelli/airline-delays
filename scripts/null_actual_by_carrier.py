#!/usr/bin/env python
"""Null actual-arrival rate by carrier and year, for the ADR-0017 scope amendment.

The sceptical reviewer of the ADR-0012 panel broke the null rate down by carrier
and found it is not one convention but many: 0% for some small regionals,
57-72% for the domestic majors, 90-100% for foreign carriers and the
non-operating side of a code-share (IAC 1504 §6.6: only the operating carrier
reports). That is why reading B is applied to FSC, LCC and regional carriers
only, and why the breakdown is published rather than described.

Writes one file and invents nothing: ``reports/prediction/null_actual_by_carrier.csv``,
one row per airline x year with the realised flights of the replication
universe, how many have no actual arrival time, the share, and the
`groups.csv` class in force that year. ``docs/notes/prediction.md`` reads it.

Usage::

    uv run python scripts/null_actual_by_carrier.py
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import TYPE_CHECKING

from airline_delays import staging as staging_mod
from airline_delays.definitions import carriers as carriers_mod
from airline_delays.definitions import universe as universe_mod

if TYPE_CHECKING:  # pragma: no cover - typing only
    import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

LEGACY_YEARS: tuple[int, ...] = tuple(range(2000, 2010))
"""The layout the question is about; from 2010 the null rate is 0.0% everywhere."""

TOP_CARRIERS = 25
"""How many carriers the published table shows, by realised volume in the window."""

BAV_CLASSES: tuple[str, ...] = ("FSC", "LCC", "regional")
"""Classes reading B covers; kept here so the script does not import `ml`."""


def measure(staged_dir: Path, groups_path: Path) -> pd.DataFrame:
    """One row per airline x year: realised flights, nulls, share and class.

    An airline can change group and class *inside* a year -- `VRN` becomes Gol
    in 2007-04, `TTL` becomes Trip in 2007-11 -- so one label per airline-year
    is a choice, not a fact. It used to be `any_value()`, which DuckDB is free
    to answer differently on each parallel scan, and a tracked artefact was
    therefore not byte-reproducible across runs. The stated convention now is
    **the label in force in the airline's last observed month of that year**
    (`arg_max` over `ym`). This is a determinism fix, not a redefinition: the
    monthly mapping is untouched, and `in_bav_scope` is unaffected because both
    sides of every transition in this window fall on the same side of the
    scope rule.
    """
    con = staging_mod.connect()
    try:
        carriers_mod.GroupTable.load(groups_path).register(con)
        source = f"read_parquet('{staged_dir}/year=*/*.parquet', hive_partitioning=false)"
        label = carriers_mod.label_sql("f.airline", "f.ym", alias="g")
        frame = con.execute(
            f"""
            SELECT f.airline AS airline,
                   f.year AS year,
                   arg_max({carriers_mod.resolved_group_sql("f.airline")}, f.ym) AS "group",
                   arg_max({carriers_mod.resolved_class_sql()}, f.ym) AS "class",
                   count(*)::BIGINT AS realized,
                   count(*) FILTER (WHERE f.actual_arr IS NULL)::BIGINT AS null_actual_arr,
                   count(*) FILTER (WHERE f.actual_dep IS NULL)::BIGINT AS null_actual_dep
            FROM {source} f {label}
            WHERE {universe_mod.UNIVERSE_REPL_SQL} AND f.is_realized
              AND f.airline IS NOT NULL AND f.year IS NOT NULL
            GROUP BY f.airline, f.year
            ORDER BY f.airline, f.year
            """
        ).df()
    finally:
        con.close()
    frame["sh_null_arr"] = frame["null_actual_arr"] / frame["realized"]
    frame["sh_null_dep"] = frame["null_actual_dep"] / frame["realized"]
    frame["in_bav_scope"] = frame["class"].isin(BAV_CLASSES)
    return frame


def _pivot(frame: pd.DataFrame, years: tuple[int, ...]) -> pd.DataFrame:
    window = frame[frame["year"].isin(years)]
    volume = window.groupby("airline", observed=True)["realized"].sum().sort_values(ascending=False)
    top = list(volume.head(TOP_CARRIERS).index)
    table = (
        window[window["airline"].isin(top)]
        .pivot_table(index="airline", columns="year", values="sh_null_arr")
        .reindex(top)
    )
    table.insert(0, "realized", volume.reindex(top))
    classes = window.groupby("airline", observed=True)["class"].agg(
        lambda values: "/".join(sorted(set(values)))
    )
    table.insert(0, "class", classes.reindex(top))
    return table


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staged-dir", type=Path, default=ROOT / "data" / "staged")
    parser.add_argument("--groups", type=Path, default=ROOT / "data" / "external" / "groups.csv")
    parser.add_argument(
        "--csv", type=Path, default=ROOT / "reports" / "prediction" / "null_actual_by_carrier.csv"
    )
    args = parser.parse_args(argv)

    frame = measure(args.staged_dir, args.groups)
    args.csv.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.csv, index=False, float_format="%.6g")
    print(f"{len(frame):,d} airline-year rows -> {args.csv}")
    return 0


if __name__ == "__main__":  # pragma: no cover - entry point
    raise SystemExit(main())
