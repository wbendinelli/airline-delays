#!/usr/bin/env python
"""Null actual-arrival rate by carrier and year, for the ADR-0017 scope amendment.

The sceptical reviewer of the ADR-0012 panel broke the null rate down by carrier
and found it is not one convention but many: 0% for some small regionals,
57-72% for the domestic majors, 90-100% for foreign carriers and the
non-operating side of a code-share (IAC 1504 §6.6: only the operating carrier
reports). That is why reading B is applied to FSC, LCC and regional carriers
only, and why the breakdown is published rather than described.

Writes two things and invents nothing:

``reports/prediction/null_actual_by_carrier.csv``
    One row per airline x year: realised flights of the replication universe,
    how many have no actual arrival time, the share, and the `groups.csv` class
    in force that year.

the generated block of ``docs/declared-differences.md``
    The top carriers by realised volume in the 2000-2009 layout, their class,
    and the null rate year by year -- plus the count of realised flights that
    reading B leaves out of scope.

Usage::

    uv run python scripts/null_actual_by_carrier.py
"""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:  # pragma: no cover - script bootstrap
    sys.path.insert(0, str(ROOT / "src"))

from vra import groups as groups_mod  # noqa: E402
from vra import stage as stage_mod  # noqa: E402
from vra import universe as universe_mod  # noqa: E402

if TYPE_CHECKING:  # pragma: no cover - typing only
    import pandas as pd

MARKER_START = "<!-- generated: null-actual-by-carrier -->"
MARKER_END = "<!-- /generated: null-actual-by-carrier -->"

LEGACY_YEARS: tuple[int, ...] = tuple(range(2000, 2010))
"""The layout the question is about; from 2010 the null rate is 0.0% everywhere."""

TOP_CARRIERS = 25
"""How many carriers the published table shows, by realised volume in the window."""

BAV_CLASSES: tuple[str, ...] = ("FSC", "LCC", "regional")
"""Classes reading B covers; kept here so the script does not import `ml`."""


def measure(staged_dir: Path, groups_path: Path) -> pd.DataFrame:
    """One row per airline x year: realised flights, nulls, share and class."""
    con = stage_mod.connect()
    try:
        groups_mod.GroupTable.load(groups_path).register(con)
        source = f"read_parquet('{staged_dir}/year=*/*.parquet', hive_partitioning=false)"
        label = groups_mod.label_sql("f.airline", "f.ym", alias="g")
        frame = con.execute(
            f"""
            SELECT f.airline AS airline,
                   f.year AS year,
                   any_value({groups_mod.resolved_group_sql("f.airline")}) AS "group",
                   any_value({groups_mod.resolved_class_sql()}) AS "class",
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


def markdown(frame: pd.DataFrame, years: tuple[int, ...]) -> str:
    """The generated block: the top carriers, their class, and the null rate."""
    import pandas as pd

    table = _pivot(frame, years)
    scope = frame[frame["year"].isin(years)]
    in_scope = int(scope.loc[scope["in_bav_scope"], "realized"].sum())
    out_scope = int(scope.loc[~scope["in_bav_scope"], "realized"].sum())
    out_null = int(scope.loc[~scope["in_bav_scope"], "null_actual_arr"].sum())
    carriers_out = int(scope.loc[~scope["in_bav_scope"], "airline"].nunique())
    header = ["carrier", "class", "realised", *[str(year) for year in years]]
    lines = [
        MARKER_START,
        "",
        (
            f"Generated by `uv run python scripts/null_actual_by_carrier.py` on "
            f"{datetime.now(UTC).date().isoformat()} over `data/staged/`. Share of **realised** "
            f"flights of the replication universe with no actual arrival time, by carrier and "
            f"year, for the {len(years)} years of the legacy layout; the "
            f"{TOP_CARRIERS} carriers with the most realised flights in that window. From 2010 "
            "the rate is 0.0% for every carrier. Nothing here is imputed: the cell is the "
            "share the raw files carry."
        ),
        "",
        "| " + " | ".join(header) + " |",
        "|" + "|".join(["---"] + ["---:"] * (len(header) - 1)) + "|",
    ]
    for airline, row in table.iterrows():
        cells = [f"`{airline}`", str(row["class"]), f"{int(row['realized']):,d}"]
        for year in years:
            value = row.get(year)
            cells.append("--" if pd.isna(value) else f"{value:.3f}")
        lines.append("| " + " | ".join(cells) + " |")
    lines += [
        "",
        (
            f"Reading B covers **{in_scope:,d}** realised flights of {years[0]}-{years[-1]} "
            f"(class FSC, LCC or regional). It leaves **{out_scope:,d}** out of scope, flown by "
            f"{carriers_out} carriers whose class is `other` or unlabelled; **{out_null:,d}** of "
            "those have no actual arrival time and therefore no delay target under either "
            "reading. Full detail, every carrier and every year: "
            "`reports/prediction/null_actual_by_carrier.csv`."
        ),
        "",
        MARKER_END,
    ]
    return "\n".join(lines)


def replace_block(path: Path, block: str) -> Path:
    """Swap the generated block in place, or append it when it is not there yet."""
    text = path.read_text(encoding="utf-8")
    if MARKER_START in text and MARKER_END in text:
        head = text.split(MARKER_START)[0]
        tail = text.split(MARKER_END)[1]
        text = head + block + tail
    else:
        text = text.rstrip("\n") + "\n\n" + block + "\n"
    path.write_text(text, encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staged-dir", type=Path, default=ROOT / "data" / "staged")
    parser.add_argument("--groups", type=Path, default=ROOT / "data" / "external" / "groups.csv")
    parser.add_argument(
        "--csv", type=Path, default=ROOT / "reports" / "prediction" / "null_actual_by_carrier.csv"
    )
    parser.add_argument("--doc", type=Path, default=ROOT / "docs" / "declared-differences.md")
    args = parser.parse_args(argv)

    frame = measure(args.staged_dir, args.groups)
    args.csv.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.csv, index=False, float_format="%.6g")
    replace_block(args.doc, markdown(frame, LEGACY_YEARS))
    print(f"{len(frame):,d} airline-year rows -> {args.csv}")
    print(f"generated block -> {args.doc}")
    return 0


if __name__ == "__main__":  # pragma: no cover - entry point
    raise SystemExit(main())
