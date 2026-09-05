"""``[here]`` The didactic games of the study's game-theory primer, cut out of the linear example.

Chapter 2 of ``docs/study/`` teaches dominant strategies, Nash equilibrium,
best responses, backward induction and the Pigouvian toll before chapter 3
derives the continuous Stackelberg model. So that every number it quotes agrees
with the rest of the study, everything here is built from the linear example
of :mod:`airline_delays.theory.equilibrium` -- ``p = 300``, ``tau = 200``,
``s = 100``, ``c(F) = 1000 + 100 F`` -- and from the closed forms of
:func:`airline_delays.theory.model.linear_closed_forms`:

* a **2 x 2 game** in which each airline chooses between the efficient
  per-firm volume ``f* = D/(4b)`` and the Cournot volume ``D/(3b)``, with the
  profits of equations (3)-(4); the same game **with a per-flight toll**
  equal to the Cournot toll at the symmetric optimum, ``f* c'``;
* the follower's **reaction function** ``f2 = (D - b f1)/(2b)`` evaluated at
  a few volumes, and the leader's profit **along** it, which is what backward
  induction maximises;
* the **share of the marginal congestion damage** each structure internalises.

Everything is exact (sympy rationals) and converted with ``float()`` at the
end; nothing is fitted. :func:`primer` is the block ``run.py`` writes under
``primer`` in ``reports/theory/model.json``.
"""

from __future__ import annotations

from itertools import pairwise
from typing import Any

import sympy as sp

from airline_delays.theory import model
from airline_delays.theory.families import LinearCost, Primitives

LOW, HIGH = "low", "high"
STRATEGIES = (LOW, HIGH)
LABEL = "didactic games of this repository, built from examples.linear; not in the monograph"


def _rational(value: float) -> sp.Rational:
    return sp.Rational(str(value))


def _substitutions(prim: Primitives, cost: LinearCost) -> dict[sp.Symbol, sp.Rational]:
    return {
        model.p: _rational(prim.p),
        model.tau: _rational(prim.tau),
        model.s: _rational(prim.s),
        model.a: _rational(cost.a),
        model.b: _rational(cost.b),
    }


class _LinearGame:
    """Profits of equations (3)-(4) under ``c(F) = a + b F``, exact."""

    def __init__(self, prim: Primitives, cost: LinearCost) -> None:
        subs = _substitutions(prim, cost)
        forms = model.linear_closed_forms()
        self.A = sp.Rational(model.A.subs(subs))
        self.a = subs[model.a]
        self.b = subs[model.b]
        self.D = sp.Rational(forms["D"].subs(subs))
        self.f_star = sp.Rational(forms["F_star"].subs(subs)) / 2
        self.f_cournot = sp.Rational(forms["f_cournot"].subs(subs))
        self.f1_stackelberg = sp.Rational(forms["f1_stackelberg"].subs(subs))
        self.f2_stackelberg = sp.Rational(forms["f2_stackelberg"].subs(subs))
        self.F_atomistic = sp.Rational(forms["F_atomistic"].subs(subs))
        self.lam_linear = sp.Rational(1, 2)

    def cost(self, F: sp.Rational) -> sp.Rational:
        return self.a + self.b * F

    def profit(
        self, own: sp.Rational, other: sp.Rational, toll: sp.Rational = sp.Integer(0)
    ) -> sp.Rational:
        """``pi_i = A f_i - c(f_i + f_j) f_i - T f_i``: equation (3) or (4), minus a per-flight toll."""
        return (self.A - self.cost(own + other) - toll) * own

    def reaction(self, f1: sp.Rational) -> sp.Rational:
        """The follower's best response under linear cost, ``(D - b f1)/(2b)``, floored at zero."""
        return sp.Max(sp.Integer(0), (self.D - self.b * f1) / (2 * self.b))


# ------------------------------------------------------------ the 2 x 2 game
def _matrix(
    game: _LinearGame, volumes: dict[str, sp.Rational], toll: sp.Rational
) -> dict[str, Any]:
    """The four cells, airline 1's best responses, its dominant strategy and the Nash cell."""
    cells: dict[str, dict[str, Any]] = {}
    for s1 in STRATEGIES:
        for s2 in STRATEGIES:
            f1, f2 = volumes[s1], volumes[s2]
            pi1, pi2 = game.profit(f1, f2, toll), game.profit(f2, f1, toll)
            cells[f"{s1}_{s2}"] = {
                "f1": float(f1),
                "f2": float(f2),
                "F": float(f1 + f2),
                "c": float(game.cost(f1 + f2)),
                "profit1": float(pi1),
                "profit2": float(pi2),
                "total_profit": float(pi1 + pi2),
                "toll_revenue": float(toll * (f1 + f2)),
            }
    # airline 1's best response to each strategy of airline 2 (the game is symmetric)
    best_response = {}
    for s2 in STRATEGIES:
        payoffs = {s1: cells[f"{s1}_{s2}"]["profit1"] for s1 in STRATEGIES}
        best_response[f"to_{s2}"] = max(STRATEGIES, key=lambda s1: payoffs[s1])
    responses = set(best_response.values())
    dominant = next(iter(responses)) if len(responses) == 1 else None
    nash = [
        f"{s1}_{s2}"
        for s1 in STRATEGIES
        for s2 in STRATEGIES
        if best_response[f"to_{s2}"] == s1 and best_response[f"to_{s1}"] == s2
    ]
    return {
        "toll_per_flight": float(toll),
        "cells": cells,
        "best_response_of_airline_1": best_response,
        "dominant_strategy": dominant,
        "nash_cells": nash,
        "nash": nash[0] if len(nash) == 1 else None,
    }


def two_by_two(game: _LinearGame) -> dict[str, Any]:
    volumes = {LOW: game.f_star, HIGH: game.f_cournot}
    plain = _matrix(game, volumes, sp.Integer(0))
    cells = plain["cells"]
    # the prisoner's-dilemma ordering: temptation > reward > punishment > sucker
    ordering = {
        "temptation": cells[f"{HIGH}_{LOW}"]["profit1"],
        "reward": cells[f"{LOW}_{LOW}"]["profit1"],
        "punishment": cells[f"{HIGH}_{HIGH}"]["profit1"],
        "sucker": cells[f"{LOW}_{HIGH}"]["profit1"],
    }
    is_pd = all(left > right for left, right in pairwise(ordering.values()))
    # what one deviation from the cooperative cell does, in the model's own terms
    extra = game.f_cournot - game.f_star
    extra_cost = game.b * extra
    deviation = {
        "extra_flights": float(extra),
        "extra_cost_per_flight": float(extra_cost),
        "gain_to_deviator": float(
            game.profit(game.f_cournot, game.f_star) - game.profit(game.f_star, game.f_star)
        ),
        "loss_to_rival": float(
            game.profit(game.f_star, game.f_star) - game.profit(game.f_star, game.f_cournot)
        ),
        "loss_to_rival_as_extra_cost_times_rival_flights": float(extra_cost * game.f_star),
        "change_in_total_profit": float(
            game.profit(game.f_cournot, game.f_star)
            + game.profit(game.f_star, game.f_cournot)
            - 2 * game.profit(game.f_star, game.f_star)
        ),
    }
    toll = game.f_star * game.b  # the Cournot toll at the symmetric optimum, T2* = f* c'
    with_toll = _matrix(game, volumes, toll)
    return {
        "strategies": {
            LOW: {
                "volume": float(game.f_star),
                "meaning": "the efficient per-firm volume f* = D/(4b)",
            },
            HIGH: {"volume": float(game.f_cournot), "meaning": "the Cournot volume D/(3b)"},
        },
        "cell_key": "airline 1's strategy, then airline 2's; profit1 is airline 1's payoff",
        **plain,
        "cooperative": f"{LOW}_{LOW}",
        "cooperative_total_equals_welfare_star": True,
        "ordering": ordering,
        "is_prisoners_dilemma": is_pd,
        "deviation_from_cooperation": deviation,
        "with_toll": {
            "toll_meaning": "the Cournot toll at the symmetric optimum, f* c' (examples.linear.tolls_at_symmetric_optimum.T2_star)",
            **with_toll,
        },
    }


# --------------------------------------------------- reaction and backward induction
def reaction_function(game: _LinearGame) -> dict[str, Any]:
    volumes = (
        sp.Integer(0),
        game.f_star,
        game.f_cournot,
        game.f1_stackelberg,
        2 * game.f_cournot,
        game.F_atomistic,
    )
    return {
        "expression": "f2 = (D - b f1)/(2b)",
        "intercept": float(game.D / (2 * game.b)),
        "slope": float(-game.lam_linear),
        "points": [{"f1": float(f1), "f2": float(game.reaction(f1))} for f1 in volumes],
    }


def leader_profit_along_reaction(game: _LinearGame) -> list[dict[str, float]]:
    """What the leader maximises: its profit with the follower already on the reaction function."""
    rows = []
    for f1 in (game.f_star, game.f_cournot, game.f1_stackelberg, 2 * game.f_cournot):
        f2 = game.reaction(f1)
        rows.append(
            {
                "f1": float(f1),
                "f2": float(f2),
                "F": float(f1 + f2),
                "profit1": float(game.profit(f1, f2)),
                "profit2": float(game.profit(f2, f1)),
            }
        )
    return rows


def internalised_shares(game: _LinearGame) -> dict[str, float]:
    """The fraction of MCD = F c' each structure counts in its own condition, linear cost."""
    F_stack = game.f1_stackelberg + game.f2_stackelberg
    return {
        "monopoly": 1.0,
        "cournot_symmetric": float(game.f_cournot / (2 * game.f_cournot)),
        "stackelberg_leader_at_equilibrium": float(
            (1 - game.lam_linear) * game.f1_stackelberg / F_stack
        ),
        "stackelberg_follower_at_equilibrium": float(game.f2_stackelberg / F_stack),
        "atomistic": 0.0,
    }


# --------------------------------------------------------------------- block
def primer(prim: Primitives | None = None, cost: LinearCost | None = None) -> dict[str, Any]:
    """The ``primer`` block of ``model.json``."""
    game = _LinearGame(prim or Primitives(), cost or LinearCost())
    return {
        "label": LABEL,
        "primitives": {
            "A": float(game.A),
            "a": float(game.a),
            "b": float(game.b),
            "D": float(game.D),
        },
        "two_by_two": two_by_two(game),
        "reaction_function": reaction_function(game),
        "leader_profit_along_reaction": leader_profit_along_reaction(game),
        "internalised_share_of_MCD": internalised_shares(game),
    }
