"""The leakage rule of ADR-0009, executable.

Every check here answers a question that can only be answered by looking, and
each one exists because the corresponding mistake has been made in print:

`check_features_exclude_post_departure`
    The BTS-style failure: ``CarrierDelay``/``WeatherDelay`` as features, or
    ANAC's own ``cause_code``, which does not exist until after the delay.
`check_targets_are_not_features`
    The same column on both sides. Trivial, and it has happened.
`check_horizons_are_nested`
    D-1 must be a strict subset of H-1, and everything H-1 adds must be about
    the *inbound* leg. A single column of this flight's own outcome leaking into
    the H-1 list would make the whole horizon comparison a tautology.
`check_lag_windows_closed`
    The failure this repository has measured on itself: the same month's
    ``fsc_prdeldep`` lifted a panel R-squared from 0.58 to 0.82. The check
    compares the feature against the fact table at ``t-1`` **and** at ``t`` and
    demands it match the first and not the second.
`check_movements_from_schedule`
    Recounts the airport day-hour movements from the staged schedule. It is the
    one check that would catch the subtle version: the staged ``dep_hour`` falls
    back to the *actual* departure when the schedule is missing
    (``vra.stage``), so a dataset that reused it would carry a post-departure
    hour for those rows and the recount would not match.
`check_previous_leg_precedes_departure`
    The rotation link must be to a leg scheduled to land before this one leaves.
`check_targets_null_without_actual`
    ADR-0012 and ADR-0015: a realised flight with no actual timestamp, or with
    one a whole day out, has no target, and those rows must be absent from the
    target rather than imputed as on time.
`check_first_year_has_no_p90`
    The congestion threshold reads the previous calendar year, so the first year
    of any build must have none. A build whose first year *does* have one is
    reading the year it is predicting.
`check_calendar_matches_the_table`
    Holidays come from `data/external/holidays.csv` by date, not from a rule.

`run_all` returns every result rather than raising on the first, so one run
reports every problem; `assert_all` is what the test suite calls.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ml import dataset_flights as ds

if TYPE_CHECKING:  # pragma: no cover - typing only
    import pandas as pd

FORBIDDEN_PREFIXES: tuple[str, ...] = ("actual_", "cause_", "status")
"""Feature-name prefixes that describe the flight after it departed."""

FORBIDDEN_EXACT: frozenset[str] = frozenset(ds.POST_DEPARTURE_STAGED) | frozenset(ds.TARGETS)

INBOUND_PREFIX = "prev_"
"""Everything the H-1 horizon adds must describe the inbound leg."""

MATCH_TOLERANCE = 1e-5
LAG_MATCH_MIN = 0.999
"""Share of comparable rows whose lag feature must equal the ``t-1`` rate."""


@dataclass(frozen=True)
class Check:
    """One leakage check and what it found."""

    name: str
    passed: bool
    detail: str

    def __str__(self) -> str:  # pragma: no cover - display only
        return f"{'ok  ' if self.passed else 'FAIL'} {self.name}: {self.detail}"


def check_features_exclude_post_departure() -> Check:
    """No feature of either horizon describes the flight after it departed."""
    offenders = sorted(
        name
        for name in ds.FEATURES_H1
        if name in FORBIDDEN_EXACT
        or (name.startswith(FORBIDDEN_PREFIXES) and not name.startswith(INBOUND_PREFIX))
    )
    return Check(
        "features_exclude_post_departure",
        not offenders,
        f"{len(ds.FEATURES_H1)} features checked against "
        f"{len(FORBIDDEN_EXACT)} forbidden names and {len(FORBIDDEN_PREFIXES)} prefixes"
        + (f"; offenders: {offenders}" if offenders else ""),
    )


def check_targets_are_not_features() -> Check:
    """The targets and the carried diagnostics never appear in a feature list."""
    clash = sorted((set(ds.TARGETS) | set(ds.DIAGNOSTICS)) & set(ds.FEATURES_H1))
    return Check(
        "targets_are_not_features",
        not clash,
        f"{len(ds.TARGETS)} targets and {len(ds.DIAGNOSTICS)} diagnostics"
        + (f"; also used as features: {clash}" if clash else " kept out of both horizons"),
    )


def check_horizons_are_nested() -> Check:
    """D-1 is a strict subset of H-1, and H-1 adds only inbound-leg columns."""
    missing = sorted(set(ds.FEATURES_D1) - set(ds.FEATURES_H1))
    added = tuple(name for name in ds.FEATURES_H1 if name not in set(ds.FEATURES_D1))
    not_inbound = sorted(name for name in added if not name.startswith(INBOUND_PREFIX))
    passed = not missing and not not_inbound and set(added) == set(ds.FEATURES_H1_ONLY)
    return Check(
        "horizons_are_nested",
        passed,
        f"H-1 adds {list(added)} to D-1's {len(ds.FEATURES_D1)} features"
        + (f"; missing from H-1: {missing}" if missing else "")
        + (f"; not about the inbound leg: {not_inbound}" if not_inbound else ""),
    )


def check_lag_windows_closed(frame: pd.DataFrame, fact: pd.DataFrame) -> Check:
    """``route_late15_l1`` is the previous month's rate, not this month's."""
    import numpy as np
    import pandas as pd

    collapsed = ds.collapse_fact(fact)
    # The same denominator `monthly_lags` uses (ADR-0017 reading B), so that a
    # window that *is* closed cannot fail this check for using another rule.
    collapsed = collapsed.assign(arr_delay_obs=ds.bav_denominator(collapsed, "arr"))
    rate = collapsed.groupby(["route", "ym"], observed=True)[
        ["arr_delay_obs", "arr_delayed_gt15"]
    ].sum()
    rate = rate.reset_index()
    rate["rate"] = rate["arr_delayed_gt15"] / rate["arr_delay_obs"].where(rate["arr_delay_obs"] > 0)
    same = rate.rename(columns={"rate": "rate_t"})[["route", "ym", "rate_t"]]
    previous = rate.assign(ym=ds._shift_ym(rate["ym"], 1)).rename(columns={"rate": "rate_t1"})
    previous = previous[["route", "ym", "rate_t1"]]
    joined = frame[["route", "ym", "route_late15_l1"]].copy()
    joined["route"] = joined["route"].astype(str)
    for side in (same, previous):
        side["route"] = side["route"].astype(str)
    joined = joined.merge(same, on=["route", "ym"], how="left").merge(
        previous, on=["route", "ym"], how="left"
    )
    comparable = joined["rate_t1"].notna() & joined["rate_t"].notna()
    distinguishing = comparable & ((joined["rate_t1"] - joined["rate_t"]).abs() > MATCH_TOLERANCE)
    if not bool(distinguishing.any()):
        return Check(
            "lag_windows_closed",
            False,
            "no route-month where the t-1 and t rates differ, so the check is blind",
        )
    subset = joined[distinguishing]
    matches_t1 = float(
        np.isclose(subset["route_late15_l1"], subset["rate_t1"], atol=MATCH_TOLERANCE).mean()
    )
    matches_t = float(
        np.isclose(subset["route_late15_l1"], subset["rate_t"], atol=MATCH_TOLERANCE).mean()
    )
    passed = matches_t1 >= LAG_MATCH_MIN and matches_t < 1 - LAG_MATCH_MIN
    return Check(
        "lag_windows_closed",
        passed,
        f"over {len(subset):,d} rows where t-1 and t differ: "
        f"{matches_t1:.4f} match t-1, {matches_t:.4f} match t "
        f"(pandas {pd.__version__})",
    )


def check_movements_from_schedule(frame: pd.DataFrame, staged: pd.DataFrame) -> Check:
    """Recount the airport day-hour movements from the staged *schedule*."""
    import numpy as np
    import pandas as pd

    departures = staged.loc[
        staged["sched_dep"].notna() & staged["origin_icao"].notna(),
        ["origin_icao", "sched_dep"],
    ].rename(columns={"origin_icao": "icao", "sched_dep": "stamp"})
    arrivals = staged.loc[
        staged["sched_arr"].notna() & staged["dest_icao"].notna(),
        ["dest_icao", "sched_arr"],
    ].rename(columns={"dest_icao": "icao", "sched_arr": "stamp"})
    sides = pd.concat([departures, arrivals], ignore_index=True)
    stamps = pd.to_datetime(sides["stamp"])
    sides["day"] = stamps.dt.date
    sides["hour"] = stamps.dt.hour.astype("int8")
    counts = sides.groupby(["icao", "day", "hour"], observed=True).size()
    counts = counts.rename("recount").reset_index()
    check = frame[["origin_icao", "flight_date", "sched_dep_hour", "origin_movements_hour"]].copy()
    check["icao"] = check["origin_icao"].astype(str)
    check["day"] = pd.to_datetime(check["flight_date"]).dt.date
    check["hour"] = check["sched_dep_hour"].astype("int8")
    counts["icao"] = counts["icao"].astype(str)
    merged = check.merge(counts, on=["icao", "day", "hour"], how="left")
    agree = float(
        np.isclose(
            merged["origin_movements_hour"], merged["recount"].fillna(0), atol=MATCH_TOLERANCE
        ).mean()
    )
    return Check(
        "movements_from_schedule",
        agree >= LAG_MATCH_MIN,
        f"{agree:.4f} of {len(merged):,d} rows match a recount from sched_dep/sched_arr "
        "(a dataset reusing the staged dep_hour, which falls back to actual_dep, would not)",
    )


def check_previous_leg_precedes_departure(frame: pd.DataFrame) -> Check:
    """The linked inbound leg is scheduled to land before this flight leaves."""
    linked = frame["prev_leg"] == 1
    turnaround = frame.loc[linked, "prev_turnaround_min"]
    negative = int((turnaround < 0).sum())
    missing = int(turnaround.isna().sum())
    stray = int(frame.loc[~linked, "prev_turnaround_min"].notna().sum())
    return Check(
        "previous_leg_precedes_departure",
        negative == 0 and missing == 0 and stray == 0,
        f"{int(linked.sum()):,d} linked legs, {negative} with a negative turnaround, "
        f"{missing} with none, {stray} turnarounds on unlinked flights",
    )


def check_targets_null_without_actual(frame: pd.DataFrame) -> Check:
    """Every arrival target is accounted for: ADR-0015 and ADR-0017 together.

    A target exists exactly where the flight was realised, its timestamps are
    not suspect, and either an actual arrival was written or reading B applies
    (`on_time_no_bav`). Everything else — a cancelled flight, a month typo, a
    realised flight of an `other` carrier with no actual time — has none.
    """
    has_target = frame["late15_arr"].notna()
    usable = frame["has_arr_actual"] | frame["on_time_no_bav"]
    should = frame["is_realized"] & usable & ~frame["actual_time_suspect"]
    mismatch = int((has_target != should).sum())
    missing = int((frame["is_realized"] & ~usable).sum())
    imputed = int((frame["is_realized"] & ~frame["has_arr_actual"] & frame["on_time_no_bav"]).sum())
    suspect = int((frame["is_realized"] & frame["actual_time_suspect"]).sum())
    return Check(
        "targets_null_without_actual",
        mismatch == 0,
        f"{missing:,d} realised flights out of scope for reading B keep no arrival target "
        f"(ADR-0017), {imputed:,d} are read as no alteration reported, and {suspect:,d} "
        f"suspect timestamps are excluded (ADR-0015); {mismatch} rows disagreeing",
    )


def check_first_year_has_no_p90(frame: pd.DataFrame) -> Check:
    """The busy-hour flag is null in the first year: its window has not opened."""
    first = int(frame["year"].min())
    flags = frame.loc[frame["year"] == first, "origin_p90_hour"]
    known = int(flags.notna().sum())
    later = frame.loc[frame["year"] > first, "origin_p90_hour"]
    known_later = int(later.notna().sum())
    passed = known == 0 and (len(later) == 0 or known_later > 0)
    return Check(
        "first_year_has_no_p90",
        passed,
        f"{first}: {known} rows carry a p90 flag (must be 0); "
        f"later years: {known_later:,d} of {len(later):,d}",
    )


def check_calendar_matches_the_table(frame: pd.DataFrame, external_dir: Path) -> Check:
    """``is_holiday`` is true exactly on the dates `holidays.csv` lists."""
    import pandas as pd

    path = Path(external_dir) / "holidays.csv"
    if not path.exists():  # pragma: no cover - defensive
        return Check("calendar_matches_the_table", False, f"missing {path}")
    listed = set(pd.to_datetime(pd.read_csv(path, usecols=["date"])["date"]).dt.date)
    days = pd.to_datetime(frame["flight_date"]).dt.date
    flagged = frame["is_holiday"].astype(bool)
    wrong = int((flagged != days.isin(listed)).sum())
    return Check(
        "calendar_matches_the_table",
        wrong == 0,
        f"{len(listed)} dated holidays, {int(flagged.sum()):,d} flagged flights, {wrong} wrong",
    )


def run_all(
    frame: pd.DataFrame,
    fact: pd.DataFrame,
    staged: pd.DataFrame,
    external_dir: Path = ds.EXTERNAL_DIR,
) -> list[Check]:
    """Every check, in one pass, without stopping at the first failure."""
    return [
        check_features_exclude_post_departure(),
        check_targets_are_not_features(),
        check_horizons_are_nested(),
        check_lag_windows_closed(frame, fact),
        check_movements_from_schedule(frame, staged),
        check_previous_leg_precedes_departure(frame),
        check_targets_null_without_actual(frame),
        check_first_year_has_no_p90(frame),
        check_calendar_matches_the_table(frame, external_dir),
    ]


def assert_all(checks: list[Check]) -> None:
    """Raise with every failure listed, or return silently."""
    failures = [check for check in checks if not check.passed]
    if failures:
        raise AssertionError(
            "leakage checks failed:\n  " + "\n  ".join(str(check) for check in failures)
        )


def as_records(checks: list[Check]) -> list[dict[str, Any]]:
    """The checks as JSON-ready records, for `reports/prediction/`."""
    return [
        {"name": check.name, "passed": check.passed, "detail": check.detail} for check in checks
    ]


__all__ = [
    "FORBIDDEN_EXACT",
    "FORBIDDEN_PREFIXES",
    "Check",
    "as_records",
    "assert_all",
    "check_calendar_matches_the_table",
    "check_features_exclude_post_departure",
    "check_first_year_has_no_p90",
    "check_horizons_are_nested",
    "check_lag_windows_closed",
    "check_movements_from_schedule",
    "check_previous_leg_precedes_departure",
    "check_targets_are_not_features",
    "check_targets_null_without_actual",
    "run_all",
]
