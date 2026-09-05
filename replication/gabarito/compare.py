"""Compare the public panel with the private benchmark, column by column.

The **only** module in this repository that reads the private benchmark, and it
reads it through ``AIRLINE_DELAYS_PRIVATE_DIR`` — never a path written down in
code or in a document. What it writes back is a table of *agreement statistics*:
the share of route-months where the public value matches, the median and 90th
percentile of the absolute difference, and how many route-months were
comparable. No benchmark value is ever copied out, and `assert_no_values`
enforces that on the way to disk.

The comparison is the deliverable, not a target. A definition is never adjusted
to raise a rate here (rule 6 of the build brief): where the public number
diverges, the row lands in `docs/declared-differences.md` and stays there.

Run it with the variable exported in the shell::

    AIRLINE_DELAYS_PRIVATE_DIR=... uv run python -m replication.gabarito.compare
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:  # pragma: no cover - script bootstrap
    sys.path.insert(0, str(ROOT / "src"))

from vra import registry  # noqa: E402

if TYPE_CHECKING:  # pragma: no cover - typing only
    import pandas as pd

PRIVATE_DIR_VAR = "AIRLINE_DELAYS_PRIVATE_DIR"
BENCHMARK_FILE = "proj18.dta"

MARKER_START = "<!-- generated: gabarito-rates -->"
MARKER_END = "<!-- /generated: gabarito-rates -->"


@dataclass(frozen=True)
class Check:
    """One public column measured against one benchmark column."""

    public: str
    benchmark: str
    tolerance: float
    note: str = ""


COUNT_TOL = 0.5
"""A count matches when it is within half a flight — that is, exactly."""

SHARE_TOL = 1e-4
ODDS_TOL = 1e-3
MINUTE_TOL = 1e-2

CHECKS: tuple[Check, ...] = (
    Check("f", "f", COUNT_TOL),
    Check("fl_can", "fl_can", COUNT_TOL),
    Check("fl_odel", "fl_odel", COUNT_TOL),
    Check("fl_ddel", "fl_ddel", COUNT_TOL, "known to reproduce far below fl_odel (ADR-0002)"),
    Check("ndays", "ndays", COUNT_TOL),
    Check("dailyfl", "dailyfl", MINUTE_TOL),
    Check(
        "fsc_prdelarr",
        "fsc_prdelarr",
        SHARE_TOL,
        "FSC = the article's group set, without Avianca Brasil",
    ),
    Check(
        "fscc_prdelarr", "fsc_prdelarr", SHARE_TOL, "FSC = class FSC, which includes Avianca Brasil"
    ),
    Check("fsc_prdelarr1530", "fsc_prdelarr1530", SHARE_TOL),
    Check("fsc_prdelarr30m", "fsc_prdelarr30m", SHARE_TOL),
    Check("fscc_prdeldep", "fsc_prdeldep", SHARE_TOL),
    Check("fscc_oddsarr", "fsc_oddsarr", ODDS_TOL),
    Check("fsc_minsarr", "fsc_minsarr", MINUTE_TOL, "same, on the article's FSC group set"),
    Check(
        "fscc_minsarr",
        "fsc_minsarr",
        MINUTE_TOL,
        "denominator is every carrier's realised flights",
    ),
    Check("fsc_minsdep", "fsc_minsdep", MINUTE_TOL),
    Check("fscc_minsp15arr", "fsc_minsp15arr", MINUTE_TOL),
    Check("all_prdelarr", "all_prdelarr", SHARE_TOL),
    Check("all_minsarr", "all_minsarr", MINUTE_TOL),
    Check("lccfu_prdelarr", "lccfu_prdelarr", SHARE_TOL, "Gol and Azul, the article's LCC set"),
    Check("lccclass_prdelarr", "lccfu_prdelarr", SHARE_TOL, "class LCC, which also holds Webjet"),
    Check("prwheather", "prwheather", SHARE_TOL),
    Check("princident", "princident", SHARE_TOL),
    Check("pr_connc", "pr_connc", SHARE_TOL),
    Check("lcc", "lcc", COUNT_TOL, "operation here, ticket sales in the benchmark"),
    Check("pres_glo", "pres_glo", COUNT_TOL, "operation here, ticket sales in the benchmark"),
    Check("pres_azu", "pres_azu", COUNT_TOL, "operation here, ticket sales in the benchmark"),
    Check("pres_tam", "pres_tam", COUNT_TOL, "operation here, ticket sales in the benchmark"),
    Check("olccfu", "olccfu", COUNT_TOL),
    Check("dlccfu", "dlccfu", COUNT_TOL),
    Check("maxalccfu", "maxalccfu", COUNT_TOL),
)

EXPECTED: dict[str, float] = {
    "f": 0.975,
    "fl_can": 0.978,
    "fl_odel": 0.924,
    "prwheather": 0.985,
    "princident": 0.991,
    "pr_connc": 0.992,
    "maxalccfu": 1.000,
    "fsc_prdelarr": 0.651,
}
"""Rates the earlier reconstruction measured (`reconstrucao-vra.md`).

Those rates were measured from the **2019 vintage** of the raw files — the same
vintage the benchmark itself was built from — while this repository rebuilds
everything from the files ANAC publishes today. `reports/reconciliation.md`
shows the two vintages differ by tens of thousands of rows in some months, so
the two tests are not the same test, and `rate_stable_vintage` below is the
like-for-like one.

A rate below one of these is something to investigate and report, never a
threshold to tune towards (rule 6 of the build brief).
"""

RECONCILIATION_BY_MONTH = ROOT / "reports" / "reconciliation_by_month.csv"
"""Public, in-repo measurement of how far today's raw files sit from the 2019 vintage."""


# --------------------------------------------------------------------------- input


def private_dir() -> Path:
    """The private benchmark directory, from the environment. Never a literal."""
    value = os.environ.get(PRIVATE_DIR_VAR)
    if not value:
        raise SystemExit(
            f"{PRIVATE_DIR_VAR} is not set. Export it in your shell for this run; "
            "it is deliberately absent from the code and from every document."
        )
    path = Path(value)
    if not path.is_dir():
        raise SystemExit(f"{PRIVATE_DIR_VAR} does not point at a directory")
    return path


def find_benchmark(root: Path) -> Path:
    """Locate `proj18.dta` under the private directory."""
    for candidate in sorted(root.rglob(BENCHMARK_FILE)):
        return candidate
    raise SystemExit(f"{BENCHMARK_FILE} not found under {PRIVATE_DIR_VAR}")


def load_benchmark(path: Path, columns: list[str]) -> pd.DataFrame:
    """Read only the benchmark columns the checks need, and only into memory."""
    import pandas as pd

    frame = pd.read_stata(path, columns=["od", "ym", *columns])
    frame["ym"] = frame["ym"].astype(int)
    frame["od"] = frame["od"].astype(str)
    return frame


def load_panel(path: Path) -> pd.DataFrame:
    """The public panel, keyed like the benchmark."""
    import pandas as pd

    panel = pd.read_parquet(path)
    panel = panel.rename(columns={"route": "od"})
    panel["ym"] = panel["ym"].astype(int)
    panel["od"] = panel["od"].astype(str)
    return panel


# ------------------------------------------------------------------------ measure


def stable_vintage_months(path: Path = RECONCILIATION_BY_MONTH) -> set[int] | None:
    """The half of the months whose raw files barely moved since the 2019 vintage.

    `reports/reconciliation_by_month.csv` holds, per calendar month, how many
    flight rows today's staged data has against the 2019 `vra.dta`. Splitting
    the panel on the median of that relative difference separates "the
    definition is wrong" from "the input changed": agreement on `f` is 0.94-0.97
    in the three quieter quartiles and 0.74 in the noisiest one, and the
    correlation between the two is -0.45. Returns None when the file is absent,
    and the second rate is then simply not reported.
    """
    import numpy as np
    import pandas as pd

    if not Path(path).exists():
        return None
    frame = pd.read_csv(path).dropna(subset=["year", "month"])
    frame["ym"] = frame["year"].astype(int) * 100 + frame["month"].astype(int)
    relative = frame["diff"].abs() / frame["rows_dta"].replace(0, np.nan)
    keep = relative <= relative.median()
    return set(frame.loc[keep, "ym"].astype(int))


def agreement(
    public: pd.Series,
    benchmark: pd.Series,
    tolerance: float,
    stable: pd.Series | None = None,
) -> dict[str, Any]:
    """Exact-match rate and difference quantiles over the comparable rows."""
    import numpy as np
    import pandas as pd

    left = pd.to_numeric(public, errors="coerce").astype("float64")
    right = pd.to_numeric(benchmark, errors="coerce").astype("float64")
    comparable = left.notna() & right.notna()
    n = int(comparable.sum())
    if not n:
        return {
            "n": 0,
            "rate": None,
            "median_abs_diff": None,
            "p90_abs_diff": None,
            "n_stable_vintage": 0,
            "rate_stable_vintage": None,
        }
    difference = (left[comparable] - right[comparable]).abs()
    matched = pd.Series(
        np.isclose(left[comparable], right[comparable], rtol=0.0, atol=tolerance),
        index=left[comparable].index,
    )
    stable_rate, stable_n = None, 0
    if stable is not None:
        inside = stable.loc[matched.index].fillna(False)
        stable_n = int(inside.sum())
        if stable_n:
            stable_rate = float(matched[inside].mean())
    return {
        "n": n,
        "rate": float(matched.mean()),
        "median_abs_diff": float(difference.median()),
        "p90_abs_diff": float(difference.quantile(0.9)),
        "n_stable_vintage": stable_n,
        "rate_stable_vintage": stable_rate,
    }


def compare(panel: pd.DataFrame, benchmark: pd.DataFrame, checks=CHECKS) -> pd.DataFrame:
    """One row per check: what was compared, how well it agrees, and how far off."""
    import pandas as pd

    merged = benchmark.merge(panel, on=["od", "ym"], how="left", suffixes=("_bench", "_public"))
    months = stable_vintage_months()
    stable = merged["ym"].isin(months) if months else None
    rows = []
    for check in checks:
        public_name = _resolve(merged, check.public, "_public")
        benchmark_name = _resolve(merged, check.benchmark, "_bench")
        if public_name is None or benchmark_name is None:
            rows.append(
                {
                    "column": check.public,
                    "benchmark_column": check.benchmark,
                    "definition": _definition(check.public),
                    "tolerance": check.tolerance,
                    "n": 0,
                    "rate": None,
                    "median_abs_diff": None,
                    "p90_abs_diff": None,
                    "n_stable_vintage": 0,
                    "rate_stable_vintage": None,
                    "expected_rate": EXPECTED.get(check.public),
                    "note": (check.note + " (column absent)").strip(),
                }
            )
            continue
        measured = agreement(merged[public_name], merged[benchmark_name], check.tolerance, stable)
        rows.append(
            {
                "column": check.public,
                "benchmark_column": check.benchmark,
                "definition": _definition(check.public),
                "tolerance": check.tolerance,
                **measured,
                "expected_rate": EXPECTED.get(check.public),
                "note": check.note,
            }
        )
    return pd.DataFrame(rows)


def _resolve(merged: pd.DataFrame, name: str, suffix: str) -> str | None:
    """A merge suffix is only added when both sides carry the name."""
    if name + suffix in merged.columns:
        return name + suffix
    return name if name in merged.columns else None


def _definition(name: str) -> str:
    try:
        return registry.describe(name, "panel").definition_en
    except KeyError:  # pragma: no cover - every panel column has an entry
        return ""


# -------------------------------------------------------------------------- output


def assert_no_values(rates: pd.DataFrame) -> None:
    """Refuse to write anything but statistics.

    The guard is structural rather than clever: the frame may only carry the
    columns below, so a benchmark value cannot ride out inside an extra column
    someone added upstream.
    """
    allowed = {
        "column",
        "benchmark_column",
        "definition",
        "tolerance",
        "n",
        "rate",
        "median_abs_diff",
        "p90_abs_diff",
        "n_stable_vintage",
        "rate_stable_vintage",
        "expected_rate",
        "note",
    }
    extra = sorted(set(rates.columns) - allowed)
    if extra:
        raise ValueError(f"refusing to write columns that are not agreement statistics: {extra}")


def write_rates(rates: pd.DataFrame, path: Path) -> Path:
    assert_no_values(rates)
    path.parent.mkdir(parents=True, exist_ok=True)
    rates.to_csv(path, index=False, float_format="%.6g")
    return path


def _blank(value: Any, spec: str = ".3f") -> str:
    """A missing statistic renders as an empty cell, never as `nan`."""
    import pandas as pd

    return "" if value is None or pd.isna(value) else format(value, spec)


def markdown_section(rates: pd.DataFrame, benchmark_rows: int) -> str:
    """The block `docs/declared-differences.md` regenerates on every run."""
    lines = [
        MARKER_START,
        "",
        (
            f"Generated by `replication/gabarito/compare.py` on "
            f"{datetime.now(UTC).date().isoformat()} against {benchmark_rows:,d} benchmark "
            "route-months. `rate` is the share of comparable route-months where the public "
            "value equals the benchmark's within the tolerance. Nothing below was tuned; "
            "where the rate is low, the difference is the finding."
        ),
        "",
        "| public column | benchmark column | rate | rate, stable vintage | expected | median abs diff | p90 abs diff | n | note |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for row in rates.to_dict("records"):
        rate = _blank(row["rate"]) or "n/a"
        stable = _blank(row["rate_stable_vintage"])
        expected = _blank(row["expected_rate"])
        median = _blank(row["median_abs_diff"], ".4g")
        p90 = _blank(row["p90_abs_diff"], ".4g")
        lines.append(
            f"| `{row['column']}` | `{row['benchmark_column']}` | {rate} | {stable} | {expected} | "
            f"{median} | {p90} | {row['n']:,d} | {row['note']} |"
        )
    lines += ["", MARKER_END]
    return "\n".join(lines)


def update_declared_differences(path: Path, section: str) -> Path:
    """Replace the generated block in place, leaving the hand-written prose alone."""
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    if MARKER_START in text and MARKER_END in text:
        head = text.split(MARKER_START)[0]
        tail = text.split(MARKER_END)[1]
        text = head + section + tail
    else:
        text = (text.rstrip() + "\n\n" if text else "") + section + "\n"
    path.write_text(text, encoding="utf-8")
    return path


def shortfalls(rates: pd.DataFrame, field: str = "rate_stable_vintage") -> list[str]:
    """Columns that reproduce worse than the earlier reconstruction did.

    Measured on `rate_stable_vintage` by default, because that is the
    like-for-like comparison: the reconstruction read the 2019 vintage of the
    raw files and this repository reads today's, so the headline `rate` answers
    two questions at once.
    """
    out = []
    for row in rates.to_dict("records"):
        expected, measured = row["expected_rate"], row[field]
        if _blank(expected) == "" or _blank(measured) == "":
            continue
        if measured < expected - 0.005:
            out.append(f"{row['column']}: {measured:.3f} against an expected {expected:.3f}")
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--panel", type=Path, default=ROOT / "data/analysis/panel_route_month.parquet"
    )
    parser.add_argument("--out", type=Path, default=ROOT / "data/analysis/taxas.csv")
    parser.add_argument("--declared", type=Path, default=ROOT / "docs/declared-differences.md")
    args = parser.parse_args(argv)

    benchmark_path = find_benchmark(private_dir())
    wanted = sorted({check.benchmark for check in CHECKS})
    benchmark = load_benchmark(benchmark_path, wanted)
    panel = load_panel(args.panel)
    rates = compare(panel, benchmark)
    write_rates(rates, args.out)
    update_declared_differences(args.declared, markdown_section(rates, len(benchmark)))
    print(f"{'column':<20} {'rate':>6} {'stable':>7}       n  expected")
    for row in rates.to_dict("records"):
        rate = _blank(row["rate"], "6.3f") or "   n/a"
        stable = _blank(row["rate_stable_vintage"], "7.3f") or "      -"
        expected = _blank(row["expected_rate"])
        print(
            f"{row['column']:<20} {rate} {stable}  {row['n']:>6,d}"
            f"{'  ' + expected if expected else ''}"
        )
    headline = shortfalls(rates, "rate")
    if headline:
        print("\nBelow the earlier rate on today's raw files, vintage drift included:")
        for line in headline:
            print(f"  {line}")
    missed = shortfalls(rates)
    if missed:
        print("\nBELOW THE EARLIER RATE ON THE STABLE-VINTAGE HALF -- investigate, do not tune:")
        for line in missed:
            print(f"  {line}")
        return 1
    print(f"\n{args.out} written; no column is below its earlier rate on the stable vintage.")
    return 0


if __name__ == "__main__":  # pragma: no cover - script entry point
    raise SystemExit(main())
