"""Signed delays, block times and the outlier rule (ADR-0008).

Sign convention, which is the whole point of ADR-0008: a delay is
``actual - scheduled`` in minutes and **keeps its sign**. An aircraft that
arrives eight minutes early carries ``arr_delay_min = -8.0``, not ``0``. Code
that wants the truncated quantity asks for it explicitly with
`positive_delay`. When the actual timestamp is missing — every cancelled
flight, and some realised ones — the delay is null, never zero.

The outlier threshold is a named parameter with default 313.25 minutes. The
laboratory used 313.25 in one script and 117.10 (arrival) with 111.75
(departure) in another; the benchmark panel trims nothing. Because the evidence
does not settle it, no default trimming happens during staging: the staged
table keeps every delay, and the replication report carries a sensitivity table
across thresholds.
"""

from __future__ import annotations

from datetime import datetime

OUTLIER_THRESHOLD_MIN: float = 313.25
"""Default outlier threshold in minutes (ADR-0008), from the project-01 script."""

OUTLIER_THRESHOLD_ARR_ALT_MIN: float = 117.10
"""Alternative arrival threshold used by the project-02 script; for sensitivity."""

OUTLIER_THRESHOLD_DEP_ALT_MIN: float = 111.75
"""Alternative departure threshold used by the project-02 script; for sensitivity."""

DELAY_THRESHOLDS_MIN: tuple[float, ...] = (0.0, 15.0, 30.0, 60.0, 120.0, 240.0)
"""Delay cut points reported throughout: strictly greater than each value.

``0`` is the benchmark panel's own late definition — its departure-delay counts
match "more than 0 minutes", not "15 or more" (agreement 92.4%). ``15`` is the
article's definition for the delay *proportions*. The remaining cut points
mirror ANAC's own published bands.
"""


def signed_delay_min(scheduled: datetime | None, actual: datetime | None) -> float | None:
    """``actual - scheduled`` in minutes, signed, or None when either is missing.

    >>> from datetime import datetime as dt
    >>> signed_delay_min(dt(2012, 3, 1, 10, 0), dt(2012, 3, 1, 9, 52))
    -8.0
    """
    if scheduled is None or actual is None:
        return None
    return (actual - scheduled).total_seconds() / 60.0


def positive_delay(delay_min: float | None) -> float | None:
    """``max(delay, 0)``: the truncated delay, for code that wants it explicitly."""
    if delay_min is None:
        return None
    return max(delay_min, 0.0)


def block_min(departure: datetime | None, arrival: datetime | None) -> float | None:
    """Block time in minutes between a departure and an arrival, or None."""
    if departure is None or arrival is None:
        return None
    return (arrival - departure).total_seconds() / 60.0


def is_late(delay_min: float | None, threshold_min: float = 0.0) -> bool | None:
    """True when the delay is strictly greater than `threshold_min`."""
    if delay_min is None:
        return None
    return delay_min > threshold_min


def is_outlier(delay_min: float | None, threshold_min: float = OUTLIER_THRESHOLD_MIN) -> bool:
    """True when a delay is at or above the outlier threshold.

    Null delays are not outliers: they are absences, and the caller decides
    what to do with them.
    """
    if delay_min is None:
        return False
    return delay_min >= threshold_min


# --------------------------------------------------------------------------- SQL

SIGNED_DELAY_SQL = "CAST(date_diff('second', {sched}, {actual}) / 60.0 AS FLOAT)"
"""DuckDB fragment for a signed delay in minutes; null propagates on its own."""


def signed_delay_sql(scheduled: str, actual: str) -> str:
    """Render `SIGNED_DELAY_SQL` for two timestamp columns."""
    return SIGNED_DELAY_SQL.format(sched=scheduled, actual=actual)


def block_sql(departure: str, arrival: str) -> str:
    """DuckDB fragment for a block time in whole minutes, as SMALLINT."""
    return f"TRY_CAST(date_diff('minute', {departure}, {arrival}) AS SMALLINT)"


# ------------------------------------------------- the 2019-vintage empty-time rule

LEGACY_MISSING_ACTUAL_AS_ZERO: bool = False
"""Default for `legacy_missing_actual_as_zero` (ADR-0012): keep nulls.

`True` reproduces the private 2019 vintage, which read an empty actual time on
a realised flight as "operated on schedule" (actual = scheduled, delay 0). In
the 2000-2009 raw files that is the *normal* case: an actual time is written
only when there was an occurrence, so 55-80% of realised flights have empty
actual times, against about 0.02% from 2010 on. `False` is the repository's
own convention everywhere else, including the prediction dataset: an absent
timestamp stays an absence.
"""


def effective_delay_min(
    scheduled: datetime | None,
    actual: datetime | None,
    is_realized: bool,
    *,
    legacy_missing_actual_as_zero: bool = LEGACY_MISSING_ACTUAL_AS_ZERO,
) -> float | None:
    """The signed delay under one of the two conventions of ADR-0012.

    With `legacy_missing_actual_as_zero`, a **realised** flight whose actual
    timestamp is missing but whose schedule is known counts as 0 minutes; a
    cancelled flight stays null under both conventions, because it never
    operated.

    >>> from datetime import datetime as dt
    >>> effective_delay_min(dt(2004, 5, 1, 10, 0), None, True)  # returns None
    >>> effective_delay_min(dt(2004, 5, 1, 10, 0), None, True, legacy_missing_actual_as_zero=True)
    0.0
    >>> effective_delay_min(
    ...     dt(2004, 5, 1, 10, 0), None, False, legacy_missing_actual_as_zero=True
    ... )  # cancelled: None
    """
    if actual is None:
        if legacy_missing_actual_as_zero and is_realized and scheduled is not None:
            return 0.0
        return None
    return signed_delay_min(scheduled, actual)


def effective_delay_sql(
    scheduled: str,
    actual: str,
    realized: str = "is_realized",
    *,
    legacy_missing_actual_as_zero: bool = LEGACY_MISSING_ACTUAL_AS_ZERO,
) -> str:
    """DuckDB translation of `effective_delay_min`.

    `test_delays` checks that the two agree row by row on the fixture, so the
    convention can never drift between the Python and the SQL path.
    """
    signed = signed_delay_sql(scheduled, actual)
    if not legacy_missing_actual_as_zero:
        return signed
    return (
        f"CASE WHEN {actual} IS NULL AND {realized} AND {scheduled} IS NOT NULL "
        f"THEN CAST(0.0 AS FLOAT) ELSE {signed} END"
    )
