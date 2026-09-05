"""Numeric solutions of the Stackelberg congestion model, for the examples the chapters quote.

Every quantity here is a plain float computed from :mod:`theory.families`
primitives: the social optimum, the Stackelberg equilibrium (follower's
reaction by bracketed root-finding, then the leader's condition), the Cournot,
atomistic and monopoly benchmarks, the tolls of equations (10)-(11), and this
repository's extension -- a Cournot game with a lower-cost entrant, which is
what makes "Pressuposição 3" of the monograph a printable statement rather
than a verbal one. Root-finding is ``scipy.optimize.brentq`` on a bracket, so
the numbers are deterministic and carry no starting-point sensitivity;
``tests/test_theory.py`` cross-checks them against ``sympy.nsolve`` and
against the closed forms of :func:`theory.model.linear_closed_forms`.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import asdict, dataclass
from typing import Any

from scipy.optimize import brentq

from airline_delays.theory.families import Cost, LinearCost, LinearDemand, Primitives, QuadraticCost

XTOL = 1e-12


@dataclass(frozen=True)
class Equilibrium:
    """One equilibrium of the two-airline game, with its tolls and welfare."""

    name: str
    f1: float
    f2: float
    F: float
    price: float
    lam: float
    MCD: float
    T1: float
    T2: float
    T1_over_MCD: float
    T2_over_MCD: float
    profit1: float
    profit2: float
    welfare: float
    soc_leader: float
    soc_follower: float
    foc_residuals: dict[str, float]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


# ------------------------------------------------------------------ pieces
class _Game:
    """The model's conditions as functions of ``(f1, f2)``, all multiplied by ``s``."""

    def __init__(self, prim: Primitives, cost: Cost, demand: LinearDemand | None) -> None:
        self.prim, self.cost, self.demand = prim, cost, demand

    # revenue per flight before congestion, and the price
    def price(self, F: float) -> float:
        if self.demand is None:
            return self.prim.p
        return self.demand.d(self.prim.s * F)

    def net(self, F: float) -> float:
        """``(price - tau) s`` at total traffic ``F``."""
        return (self.price(F) - self.prim.tau) * self.prim.s

    def d1(self, F: float) -> float:
        return 0.0 if self.demand is None else self.demand.d1(self.prim.s * F)

    def d2(self, F: float) -> float:
        return 0.0 if self.demand is None else self.demand.d2(self.prim.s * F)

    # first-order conditions, times s, as functions of the volumes
    def follower(self, f1: float, f2: float) -> float:
        """Equation (7) (or its inelastic counterpart): ``d pi2 / d f2``."""
        F, s = f1 + f2, self.prim.s
        return self.net(F) + s * s * f2 * self.d1(F) - self.cost.c(F) - f2 * self.cost.c1(F)

    def reaction_slope(self, f1: float, f2: float) -> float:
        """Equation (8), or the general inelastic slope ``-A_/B_`` of the model."""
        F, s = f1 + f2, self.prim.s
        c1, c2 = self.cost.c1(F), self.cost.c2(F)
        a_ = (c1 + f2 * c2) / s - s * self.d1(F) - s * s * f2 * self.d2(F)
        b_ = a_ + c1 / s - s * self.d1(F)
        return -a_ / b_

    def leader(self, f1: float, f2: float, slope: float) -> float:
        """Equation (9) or (12): ``d pi1 / d f1`` given the follower's reaction slope."""
        F, s = f1 + f2, self.prim.s
        return (
            self.net(F)
            + s * s * f1 * self.d1(F) * (1.0 + slope)
            - self.cost.c(F)
            - f1 * self.cost.c1(F) * (1.0 + slope)
        )

    def social(self, F: float) -> float:
        """Equation (6): ``d W / d F``."""
        return self.net(F) - self.cost.c(F) - F * self.cost.c1(F)

    def cournot_symmetric(self, f: float) -> float:
        F, s = 2.0 * f, self.prim.s
        return self.net(F) + s * s * f * self.d1(F) - self.cost.c(F) - f * self.cost.c1(F)

    def atomistic(self, F: float) -> float:
        return self.net(F) - self.cost.c(F)

    def monopoly(self, F: float) -> float:
        s = self.prim.s
        return self.net(F) + s * s * F * self.d1(F) - self.cost.c(F) - F * self.cost.c1(F)

    def profit(self, f_own: float, F: float) -> float:
        return self.net(F) * f_own - self.cost.c(F) * f_own

    def welfare(self, F: float) -> float:
        s, tau = self.prim.s, self.prim.tau
        if self.demand is None:
            return self.net(F) * F - self.cost.c(F) * F
        return self.demand.surplus(s * F) - tau * s * F - self.cost.c(F) * F


def _root(fn: Any, lo: float = 0.0) -> float:
    """Root of a condition that is positive at ``lo`` and eventually negative."""
    hi = max(lo, 1.0)
    for _ in range(80):
        if fn(hi) < 0.0:
            break
        hi *= 2.0
    else:  # pragma: no cover - the primitives never reach here
        raise ValueError("no sign change found; the condition never turns negative")
    return float(brentq(fn, lo, hi, xtol=XTOL, maxiter=500))


def _derivative(fn: Any, at: float, h: float = 1e-5) -> float:
    return (fn(at + h) - fn(at - h)) / (2.0 * h)


# ----------------------------------------------------------------- solvers
def social_optimum(
    prim: Primitives, cost: Cost, demand: LinearDemand | None = None
) -> dict[str, float]:
    game = _Game(prim, cost, demand)
    F = _root(game.social)
    return {"F_star": F, "f_star": F / 2.0, "welfare_star": game.welfare(F), "price": game.price(F)}


def follower_response(game: _Game, f1: float) -> float:
    if game.follower(f1, 0.0) <= 0.0:
        return 0.0
    return _root(lambda f2: game.follower(f1, f2))


def stackelberg(prim: Primitives, cost: Cost, demand: LinearDemand | None = None) -> Equilibrium:
    game = _Game(prim, cost, demand)

    def leader_condition(f1: float) -> float:
        f2 = follower_response(game, f1)
        return game.leader(f1, f2, game.reaction_slope(f1, f2))

    f1 = _root(leader_condition, lo=1e-9)
    f2 = follower_response(game, f1)
    return _equilibrium("stackelberg", game, f1, f2, leader_condition)


def cournot(prim: Primitives, cost: Cost, demand: LinearDemand | None = None) -> Equilibrium:
    game = _Game(prim, cost, demand)
    f = _root(game.cournot_symmetric)
    return _equilibrium("cournot", game, f, f, None)


def atomistic(prim: Primitives, cost: Cost, demand: LinearDemand | None = None) -> dict[str, float]:
    game = _Game(prim, cost, demand)
    F = _root(game.atomistic)
    return {"F": F, "price": game.price(F), "welfare": game.welfare(F), "MCD": F * cost.c1(F)}


def monopoly(prim: Primitives, cost: Cost, demand: LinearDemand | None = None) -> dict[str, float]:
    game = _Game(prim, cost, demand)
    F = _root(game.monopoly)
    return {"F": F, "price": game.price(F), "welfare": game.welfare(F)}


def _equilibrium(
    name: str, game: _Game, f1: float, f2: float, leader_condition: Any
) -> Equilibrium:
    F = f1 + f2
    c1 = game.cost.c1(F)
    lam = -game.reaction_slope(f1, f2)
    MCD = F * c1
    T1 = (f2 + lam * f1) * c1 if name == "stackelberg" else f2 * c1
    T2 = f1 * c1
    residuals = {"follower": game.follower(f1, f2)}
    if leader_condition is not None:
        residuals["leader"] = leader_condition(f1)
        soc_leader = _derivative(leader_condition, f1)
    else:
        residuals["cournot_1"] = game.cournot_symmetric(f1)
        soc_leader = _derivative(game.cournot_symmetric, f1)
    soc_follower = _derivative(lambda v: game.follower(f1, v), f2)
    return Equilibrium(
        name=name,
        f1=f1,
        f2=f2,
        F=F,
        price=game.price(F),
        lam=lam,
        MCD=MCD,
        T1=T1,
        T2=T2,
        T1_over_MCD=T1 / MCD,
        T2_over_MCD=T2 / MCD,
        profit1=game.profit(f1, F),
        profit2=game.profit(f2, F),
        welfare=game.welfare(F),
        soc_leader=soc_leader,
        soc_follower=soc_follower,
        foc_residuals=residuals,
    )


def tolls_at_symmetric_optimum(
    prim: Primitives, cost: Cost, demand: LinearDemand | None = None
) -> dict[str, float]:
    """Equation (11): the tolls evaluated at ``f1 = f2 = f*``."""
    game = _Game(prim, cost, demand)
    opt = social_optimum(prim, cost, demand)
    f = opt["f_star"]
    lam = -game.reaction_slope(f, f)
    MCD = opt["F_star"] * cost.c1(opt["F_star"])
    return {
        "F_star": opt["F_star"],
        "f_star": f,
        "lambda_star": lam,
        "MCD_star": MCD,
        "T1_star": 0.5 * (1.0 + lam) * MCD,
        "T1_star_over_MCD": 0.5 * (1.0 + lam),
        "T2_star": 0.5 * MCD,
        "atomistic_toll": MCD,
        "monopoly_toll": 0.0,
        "welfare_star": opt["welfare_star"],
    }


def welfare_loss(eq: Equilibrium | dict[str, float], optimum: dict[str, float]) -> dict[str, float]:
    welfare = eq.welfare if isinstance(eq, Equilibrium) else eq["welfare"]
    loss = optimum["welfare_star"] - welfare
    return {"loss": loss, "loss_share": loss / optimum["welfare_star"]}


def cournot_asymmetric(prims: Sequence[Primitives], cost: LinearCost) -> dict[str, Any]:
    """``[here]`` Cournot with heterogeneous seat costs under linear congestion cost.

    Firm ``i`` solves ``D_i - b F - b f_i = 0`` with ``D_i = (p - tau_i) s - a``, so
    ``F = sum(D_i) / ((n + 1) b)`` and ``f_i = D_i / b - F``. The share ``f_i / F``
    is the fraction of the marginal congestion damage firm ``i`` internalises.
    """
    n = len(prims)
    D = [pr.A - cost.a for pr in prims]
    F = sum(D) / ((n + 1) * cost.b)
    flights = [Di / cost.b - F for Di in D]
    return {
        "n_firms": n,
        "tau": [pr.tau for pr in prims],
        "D": D,
        "F": F,
        "flights": flights,
        "internalised_share": [f / F for f in flights],
        "MCD": F * cost.b,
        "welfare": sum(
            (pr.p - pr.tau) * pr.s * f - cost.c(F) * f for pr, f in zip(prims, flights, strict=True)
        ),
    }


# ---------------------------------------------------------------- examples
def example(name: str) -> dict[str, Any]:
    """One block of ``model.json``: primitives, optimum, Stackelberg, benchmarks, tolls."""
    prim = Primitives()
    if name == "linear":
        cost: Cost = LinearCost()
        demand: LinearDemand | None = None
    elif name == "quadratic":
        cost, demand = QuadraticCost(), None
    elif name == "inelastic_linear_demand":
        cost, demand = LinearCost(), LinearDemand()
    else:  # pragma: no cover
        raise KeyError(name)
    opt = social_optimum(prim, cost, demand)
    stack = stackelberg(prim, cost, demand)
    cour = cournot(prim, cost, demand)
    atom = atomistic(prim, cost, demand)
    mono = monopoly(prim, cost, demand)
    block: dict[str, Any] = {
        "primitives": prim.params(),
        "cost": {"family": cost.label, **cost.params()},
        "demand": None if demand is None else {"family": demand.label, **demand.params()},
        "social_optimum": opt,
        "tolls_at_symmetric_optimum": tolls_at_symmetric_optimum(prim, cost, demand),
        "stackelberg": stack.as_dict() | welfare_loss(stack, opt),
        "cournot": cour.as_dict() | welfare_loss(cour, opt),
        "atomistic": atom | welfare_loss(atom, opt),
        "monopoly": mono | welfare_loss(mono, opt),
    }
    if demand is not None:
        s = prim.s
        F = stack.F
        block["equation_12_terms_at_stackelberg"] = {
            "market_power_term": s * stack.f1 * demand.d1(s * F) * (1.0 - stack.lam),
            "uninternalised_term": stack.f1 * cost.c1(F) * (1.0 - stack.lam) / s,
            "atomistic_toll_per_seat": F * cost.c1(F) / s,
            "F_star": opt["F_star"],
            "F_exceeds_optimum_by": F - opt["F_star"],
        }
    return block


def lcc_extension() -> dict[str, Any]:
    """``[here]`` Two incumbents at ``tau = 200`` and an entrant at ``tau = 170``."""
    incumbent = Primitives()
    entrant = Primitives(tau=170.0)
    cost = LinearCost()
    triopoly = cournot_asymmetric([entrant, incumbent, incumbent], cost)
    duopoly = cournot_asymmetric([incumbent, incumbent], cost)
    return {
        "label": "extension of this repository, not of the monograph",
        "entrant_tau": entrant.tau,
        "incumbent_tau": incumbent.tau,
        "cost": {"family": cost.label, **cost.params()},
        "triopoly": triopoly,
        "duopoly_cournot": duopoly,
        "stackelberg_duopoly_F": stackelberg(incumbent, cost).F,
    }


def comparative_statics() -> dict[str, Any]:
    """``[here]`` How lambda, the leader's toll and the loss move with curvature and demand slope."""
    prim = Primitives()
    curvature = []
    for q in (0.0, 0.25, 0.5, 1.0, 2.0, 4.0):
        cost: Cost = (
            LinearCost(a=1000.0, b=50.0) if q == 0.0 else QuadraticCost(a=1000.0, b=50.0, q=q)
        )
        opt = social_optimum(prim, cost)
        tolls = tolls_at_symmetric_optimum(prim, cost)
        stack = stackelberg(prim, cost)
        curvature.append(
            {
                "q": q,
                "F_star": opt["F_star"],
                "lambda_star": tolls["lambda_star"],
                "T1_star_over_MCD": tolls["T1_star_over_MCD"],
                "stackelberg_lambda": stack.lam,
                "f1_over_f2": stack.f1 / stack.f2,
                "T1_over_MCD": stack.T1_over_MCD,
                "loss_share": welfare_loss(stack, opt)["loss_share"],
            }
        )
    slopes = []
    for dd in (0.0, 0.005, 0.015, 0.03):
        demand = None if dd == 0.0 else LinearDemand(dd=dd)
        cost = LinearCost()
        opt = social_optimum(prim, cost, demand)
        stack = stackelberg(prim, cost, demand)
        s = prim.s
        slopes.append(
            {
                "dd": dd,
                "f1": stack.f1,
                "f2": stack.f2,
                "F": stack.F,
                "F_star": opt["F_star"],
                "price": stack.price,
                "lambda": stack.lam,
                "market_power_term": (
                    0.0
                    if demand is None
                    else s * stack.f1 * demand.d1(s * stack.F) * (1.0 - stack.lam)
                ),
                "uninternalised_term": stack.f1 * cost.c1(stack.F) * (1.0 - stack.lam) / s,
                "loss_share": welfare_loss(stack, opt)["loss_share"],
            }
        )
    return {"cost_curvature": curvature, "demand_slope": slopes}
