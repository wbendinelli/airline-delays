"""Concrete primitives for the numeric examples of the Stackelberg congestion model.

The symbolic model in :mod:`theory.model` keeps ``c(F)`` and ``d(Q)`` generic.
The examples the chapters quote need numbers, so this module fixes three
families -- a linear and a quadratic congestion cost, and a linear inverse
demand -- plus the price, seat-cost and seat-count primitives. The values are
stylised: chosen so that the linear case has integer equilibria and so that
none of the coincidences ``s^2 dd = b`` (market-power and internalisation
terms equal in size) or ``s^2 dd = 2b`` (Stackelberg total equal to the
optimum) hides a distinction the text wants to show.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Protocol


@dataclass(frozen=True)
class Primitives:
    """Total price ``p``, cost per seat ``tau`` and seats per flight ``s``."""

    p: float = 300.0
    tau: float = 200.0
    s: float = 100.0

    @property
    def A(self) -> float:
        """Net revenue per flight before congestion, ``(p - tau) s``."""
        return (self.p - self.tau) * self.s

    def params(self) -> dict[str, float]:
        return asdict(self)


class Cost(Protocol):
    """A congestion cost per flight ``c(F)`` with its first two derivatives."""

    label: str

    def c(self, F: float) -> float: ...
    def c1(self, F: float) -> float: ...
    def c2(self, F: float) -> float: ...
    def params(self) -> dict[str, float]: ...


@dataclass(frozen=True)
class LinearCost:
    """``c(F) = a + b F``: constant marginal congestion damage per flight, ``c'' = 0``."""

    a: float = 1000.0
    b: float = 100.0
    label: str = "linear"

    def c(self, F: float) -> float:
        return self.a + self.b * F

    def c1(self, F: float) -> float:
        return self.b

    def c2(self, F: float) -> float:
        return 0.0

    def params(self) -> dict[str, float]:
        return {"a": self.a, "b": self.b}


@dataclass(frozen=True)
class QuadraticCost:
    """``c(F) = a + b F + q F^2``: rising marginal congestion damage, ``c'' = 2q > 0``."""

    a: float = 1000.0
    b: float = 50.0
    q: float = 1.0
    label: str = "quadratic"

    def c(self, F: float) -> float:
        return self.a + self.b * F + self.q * F * F

    def c1(self, F: float) -> float:
        return self.b + 2.0 * self.q * F

    def c2(self, F: float) -> float:
        return 2.0 * self.q

    def params(self) -> dict[str, float]:
        return {"a": self.a, "b": self.b, "q": self.q}


@dataclass(frozen=True)
class LinearDemand:
    """Inverse demand ``d(Q) = d0 - dd Q`` over total seats ``Q = s F``, ``d' = -dd < 0``."""

    d0: float = 400.0
    dd: float = 0.015
    label: str = "linear demand"

    def d(self, Q: float) -> float:
        return self.d0 - self.dd * Q

    def d1(self, Q: float) -> float:
        return -self.dd

    def d2(self, Q: float) -> float:
        return 0.0

    def surplus(self, Q: float) -> float:
        """``int_0^Q d(q) dq``: gross consumer benefit of ``Q`` seats."""
        return self.d0 * Q - self.dd * Q * Q / 2.0

    def params(self) -> dict[str, float]:
        return {"d0": self.d0, "dd": self.dd}
