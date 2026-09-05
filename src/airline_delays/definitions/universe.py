"""Universe filters (ADR-0002).

Two universes exist and they never mix silently. Every column that depends on
one carries the universe in its name, and `assert_single_universe` is the guard
the test suite uses.

Replication universe (``universe_repl``)
    Line types N, R and E — domestic scheduled, regional and special — with DI
    ``0``, the regular flight authorisation code. Realised **and** cancelled
    flights both count, because the benchmark panel's flight count includes
    cancellations (its cancellation rate is ``fl_can / f``).

Prediction universe (``universe_ml``)
    The realised flights of the replication universe. Extra flights (DI 1, 2),
    return flights (DI 3) and the other authorisation codes become features,
    never filters.

Evidence for the rule: regressing the benchmark panel's flight count on flight
counts by category gives a coefficient of about 1 for N/R/E with DI 0 and about
0 elsewhere; admitting DI in {0, 1, 2} drops agreement from 97% to 54%.

Declared limitation (ADR-0002): under the same rule departure-delay counts
reproduce at 92.4% and arrival-delay counts at 59.8%. The asymmetry is
declared, not resolved.
"""

from __future__ import annotations

from collections.abc import Iterable

LINE_TYPES_REPL: frozenset[str] = frozenset({"N", "R", "E"})
"""Line types inside the replication universe: national, regional, special."""

LINE_TYPES_ALL: tuple[str, ...] = ("I", "N", "R", "E", "L", "H", "C", "G")
"""Every line type the IAC 1504 defines; the staged table keeps all of them."""

DI_REPL: frozenset[int] = frozenset({0})
"""Authorisation codes (DI) inside the replication universe: the regular flight."""

STATUS_REALIZED = "realized"
STATUS_CANCELLED = "cancelled"
STATUS_OTHER = "other"
STATUSES: tuple[str, ...] = (STATUS_REALIZED, STATUS_CANCELLED, STATUS_OTHER)


def in_universe_repl(line_type: str | None, di: int | None) -> bool:
    """True when a flight belongs to the replication universe."""
    if line_type is None or di is None:
        return False
    return line_type in LINE_TYPES_REPL and int(di) in DI_REPL


def in_universe_ml(line_type: str | None, di: int | None, status: str | None) -> bool:
    """True when a flight belongs to the prediction universe."""
    return in_universe_repl(line_type, di) and status == STATUS_REALIZED


UNIVERSE_REPL_SQL = (
    "(line_type IN ("
    + ", ".join(f"'{code}'" for code in sorted(LINE_TYPES_REPL))
    + ") AND di IN ("
    + ", ".join(str(code) for code in sorted(DI_REPL))
    + "))"
)
UNIVERSE_ML_SQL = f"({UNIVERSE_REPL_SQL} AND status = '{STATUS_REALIZED}')"


UNIVERSE_SUFFIXES: tuple[str, ...] = ("_repl", "_ml")


def universe_of(column: str) -> str | None:
    """The universe a column name declares, or None when it declares none."""
    for suffix in UNIVERSE_SUFFIXES:
        if column.endswith(suffix):
            return suffix.lstrip("_")
    return None


def assert_single_universe(columns: Iterable[str]) -> str | None:
    """Fail when a set of columns mixes the two universes.

    Columns that declare no universe are ignored, so a table of keys plus one
    universe's measures passes.

    :raises ValueError: when both ``_repl`` and ``_ml`` columns are present.
    """
    found = {universe_of(name) for name in columns} - {None}
    if len(found) > 1:
        raise ValueError(f"columns mix universes {sorted(found)}: {sorted(columns)}")
    return next(iter(found), None)
