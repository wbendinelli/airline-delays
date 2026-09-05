"""The Stackelberg congestion model of the 2013 monograph, as symbolic algebra.

Source: Bendinelli (2013), undergraduate monograph, USP/ESALQ, Piracicaba,
section 4 ("Modelo econômico para um líder de Stackelberg"), which follows
Brueckner and Van Dender (2008, *Journal of Urban Economics* 64, 288-295) and
Brueckner (2002, *American Economic Review* 92, 1357-1375). Equation numbers
below are the monograph's, (1) to (12).

Two airlines, 1 and 2, serve a congested airport in its peak period and choose
flight volumes ``f1`` and ``f2``. Passengers pay a fixed total price ``p`` (a
horizontal demand curve in the base case), a flight carries ``s`` seats, all
sold, and a seat costs ``tau`` to produce. Congestion adds a time cost per
passenger ``t(F)`` and an operating cost per flight ``g(F)``, both functions of
total traffic ``F = f1 + f2``; the monograph folds them into one function
``c(F) = s t(F) + g(F)`` with ``c' > 0`` and ``c'' >= 0`` (equation 5).

Everything here is a sympy expression. :data:`IDENTITIES` lists the algebraic
statements the monograph makes -- and the ones this repository adds, labelled
``[here]`` -- each with a callable that checks it; :func:`verify_identities`
runs them all and is what ``theory/run.py`` prints. :data:`ASSUMPTIONS` lists
what is assumed rather than proved. sympy checks that the algebra follows from
the assumptions; it says nothing about whether the assumptions hold.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import sympy as sp

# ------------------------------------------------------------------- symbols
#: Flight volumes of the two airlines, total traffic, total price, seat cost, seats.
f1, f2, F, p, tau, s = sp.symbols("f1 f2 F p tau s", positive=True)
#: ``lambda = -df2/df1``: how many of its own flights the follower cuts per extra leader flight.
lam = sp.Symbol("lambda", positive=True)
#: ``x = f2 c''/c'``: the one ratio every bound on lambda depends on (zero under linear cost).
x = sp.Symbol("x", nonnegative=True)
#: The congestion cost per flight, ``c(F)``, and the inverse demand, ``d(Q)``, kept generic.
c = sp.Function("c")
d = sp.Function("d")
#: ``c(F)``, ``c'(F)``, ``c''(F)`` as plain symbols, with the monograph's sign assumptions.
c0, c1 = sp.symbols("c0 c1", positive=True)
c2 = sp.Symbol("c2", nonnegative=True)
#: ``d(Q)``, ``d'(Q) < 0``, ``d''(Q)`` (unsigned) for the inelastic-demand case.
d0 = sp.Symbol("d0", positive=True)
d1 = sp.Symbol("d1", negative=True)
d2 = sp.Symbol("d2", real=True)
#: The follower's reaction ``df2/df1``, left free where the monograph leaves it free.
slope = sp.Symbol("slope", real=True)
#: The symmetric efficient volume ``f*`` of equation (11).
f_star = sp.Symbol("f_star", positive=True)
#: Linear-cost parameters ``c(F) = a + b F`` and ``D = (p - tau) s - a``.
a, b = sp.symbols("a b", positive=True)
#: Linear inverse demand ``d(Q) = d0 - dd Q``, slope magnitude ``dd > 0``.
dd = sp.Symbol("dd", positive=True)
#: Net revenue per flight before congestion, ``(p - tau) s``.
A = (p - tau) * s
#: The follower as a function of the leader's choice, for the leader's problem.
f2_of_f1 = sp.Function("f2")(f1)
#: Integration variable for the consumer surplus under inelastic demand.
q = sp.Symbol("q", positive=True)


# ---------------------------------------------------------------- utilities
def as_symbols(expr: sp.Expr) -> sp.Expr:
    """Replace ``c(.)``, ``c'``, ``c''``, ``d(.)``, ``d'``, ``d''`` and ``f2(f1)`` by plain symbols.

    Differentiating ``c(f1 + f2(f1))`` produces ``Subs``/``Derivative`` atoms;
    this maps them onto ``c0, c1, c2``, ``d0, d1, d2``, ``f2`` and ``slope`` so
    two expressions can be compared with ``simplify(lhs - rhs) == 0``.
    """
    expr = sp.sympify(expr).doit()
    replacements: dict[sp.Basic, sp.Basic] = {}
    for der in expr.atoms(sp.Derivative):
        order = sum(int(count) for _, count in der.variable_count)
        fn = der.expr.func
        if fn == c:
            replacements[der] = {1: c1, 2: c2}[order]
        elif fn == d:
            replacements[der] = {1: d1, 2: d2}[order]
        elif der.expr == f2_of_f1:
            replacements[der] = slope
    expr = expr.xreplace(replacements).doit()
    applied: dict[sp.Basic, sp.Basic] = {}
    for app in expr.atoms(sp.core.function.AppliedUndef):
        if app.func == c:
            applied[app] = c0
        elif app.func == d:
            applied[app] = d0
        elif app == f2_of_f1:
            applied[app] = f2
    return sp.expand(expr.xreplace(applied).doit())


def _equal(lhs: sp.Expr, rhs: sp.Expr) -> bool:
    return sp.simplify(sp.expand(lhs - rhs)) == 0


# ------------------------------------------------ the model, equations (1)-(12)
def profits() -> tuple[sp.Expr, sp.Expr]:
    """Equations (3) and (4): ``pi_i = (p - tau) s f_i - c(f1 + f2) f_i``."""
    return A * f1 - c(f1 + f2) * f1, A * f2 - c(f1 + f2) * f2


def welfare() -> sp.Expr:
    """Joint profit under perfectly elastic demand (consumer surplus is zero)."""
    return A * F - c(F) * F


def foc_social() -> sp.Expr:
    """Equation (6), per seat: ``p - tau - [F c'(F) + c(F)]/s = 0``."""
    return as_symbols(sp.diff(welfare(), F) / s)


def foc_follower() -> sp.Expr:
    """Equation (7), per seat: ``p - tau - [f2 c' + c]/s = 0``."""
    _, pi2 = profits()
    return as_symbols(sp.diff(pi2, f2) / s)


def reaction_slope() -> sp.Expr:
    """Equation (8) by the implicit-function theorem on the follower's condition.

    ``df2/df1 = -(c' + f2 c'')/(2 c' + f2 c'')``, which the monograph writes as
    ``-lambda`` with ``1/2 <= lambda < 1``.
    """
    _, pi2 = profits()
    condition = sp.diff(pi2, f2)
    return sp.simplify(-as_symbols(sp.diff(condition, f1)) / as_symbols(sp.diff(condition, f2)))


def lambda_of_x() -> sp.Expr:
    """``lambda`` as a function of ``x = f2 c''/c'``: ``(1 + x)/(2 + x)``."""
    return (1 + x) / (2 + x)


def lambda_bounds() -> dict[str, sp.Expr]:
    """``lambda - 1/2 = x/(2(2 + x)) >= 0`` and ``1 - lambda = 1/(2 + x) > 0``."""
    return {"lambda_minus_half": x / (2 * (2 + x)), "one_minus_lambda": 1 / (2 + x)}


def foc_leader() -> sp.Expr:
    """Equation (9), per seat, with the follower's reaction left as ``slope``.

    ``p - tau - (1/s)[f1 c'(1 + df2/df1) + c] = 0``.
    """
    pi1 = A * f1 - c(f1 + f2_of_f1) * f1
    return as_symbols(sp.diff(pi1, f1) / s)


def leader_follower_ratio() -> sp.Expr:
    """``[here]`` From (7) and (9) at one point: ``f1 = f2/(1 - lambda)``.

    Sharper than the monograph's ``f1 > f2``: because ``lambda >= 1/2``, the
    leader operates at least twice the follower's flights.
    """
    p_from_follower = sp.solve(foc_follower(), p)[0]
    leader_at_that_p = foc_leader().subs(slope, -lam).subs(p, p_from_follower)
    return sp.simplify(sp.solve(leader_at_that_p, f1)[0])


def marginal_congestion_damage() -> sp.Expr:
    """``MCD = (f1 + f2) c'``: the damage one extra flight imposes on all flights."""
    return (f1 + f2) * c1


def toll_leader() -> dict[str, sp.Expr]:
    """Equation (10) in its two forms, per flight of the leader.

    ``T1 = (f2 - f1 df2/df1) c' = (f2 + lambda f1) MCD/(f1 + f2)``.
    """
    return {
        "difference_form": (f2 - f1 * slope) * c1,
        "share_form": (f2 + lam * f1) * marginal_congestion_damage() / (f1 + f2),
    }


def toll_follower() -> sp.Expr:
    """The follower's toll has the Cournot form: ``T2 = f1 c'``."""
    return f1 * c1


def tolls_symmetric() -> dict[str, sp.Expr]:
    """Equation (11): tolls at the symmetric efficient allocation, as shares of ``MCD*``."""
    return {
        "leader": (1 + lam) / 2,
        "follower": sp.Rational(1, 2),
        "cournot": sp.Rational(1, 2),
        "atomistic": sp.Integer(1),
        "monopoly": sp.Integer(0),
        "leader_linear_cost": sp.Rational(3, 4),
    }


def benchmarks() -> dict[str, sp.Expr]:
    """First-order conditions, per seat, of the three reference market structures."""
    return {
        "cournot": p - tau - (f1 * c1 + c0) / s,
        "atomistic": p - tau - c0 / s,
        "monopoly": as_symbols(sp.diff(A * F - c(F) * F, F) / s),
    }


def foc_leader_inelastic() -> sp.Expr:
    """Equation (12): the leader's condition when ``p = d(s F)`` with ``d' < 0``."""
    total = s * (f1 + f2_of_f1)
    pi1 = d(total) * s * f1 - tau * s * f1 - c(f1 + f2_of_f1) * f1
    return as_symbols(sp.diff(pi1, f1) / s)


def foc_social_inelastic() -> sp.Expr:
    """The efficient condition under inelastic demand: ``d - tau - [F c' + c]/s = 0``."""
    surplus = sp.Integral(d(q), (q, 0, s * F)) - tau * s * F - c(F) * F
    return as_symbols(sp.diff(surplus, F) / s)


def inelastic_limits() -> dict[str, sp.Expr]:
    """The two endpoint readings of (12) the monograph discusses ("Pressuposição 2")."""
    foc = foc_leader_inelastic()
    return {
        "slope_minus_one": sp.simplify(foc.subs(slope, -1)),
        "slope_minus_half": sp.simplify(foc.subs(slope, -sp.Rational(1, 2))),
        "market_power_term_at_minus_half": s * f1 * d1 / 2,
        "uninternalised_term_at_minus_half": f1 * c1 / (2 * s),
        "atomistic_toll_per_seat": (f1 + f2) * c1 / s,
    }


def reaction_slope_inelastic() -> sp.Expr:
    """``[here]`` The follower's reaction under ``p = d(s F)``, from its own condition."""
    total = s * (f1 + f2)
    pi2 = d(total) * s * f2 - tau * s * f2 - c(f1 + f2) * f2
    condition = sp.diff(pi2, f2)
    return sp.simplify(-as_symbols(sp.diff(condition, f1)) / as_symbols(sp.diff(condition, f2)))


def inelastic_slope_pieces() -> dict[str, sp.Expr]:
    """``[here]`` ``df2/df1 = -A_/B_``; the bound ``<= -1/2`` holds iff ``c''/s >= s^2 d''``."""
    a_ = (c1 + f2 * c2) / s - s * d1 - s**2 * f2 * d2
    b_ = a_ + c1 / s - s * d1
    return {"A": a_, "B": b_, "slope": -a_ / b_, "condition": c2 / s - s**2 * d2}


def reaction_slope_linear_demand() -> sp.Expr:
    """``[here]`` With ``d'' = 0``: ``-(k + f2 c'')/(2 k + f2 c'')``, ``k = c' - s^2 d' > 0``."""
    k = c1 - s**2 * d1
    return -(k + f2 * c2) / (2 * k + f2 * c2)


def linear_closed_forms() -> dict[str, sp.Expr]:
    """Closed forms under ``c(F) = a + b F`` and perfectly elastic demand, in ``D = (p - tau) s - a``."""
    D = A - a
    reaction = sp.solve((A - (a + b * (f1 + f2)) - f2 * b), f2)[0]
    leader = sp.solve((A - (a + b * (f1 + reaction)) - f1 * b * (1 - sp.Rational(1, 2))), f1)[0]
    follower = reaction.subs(f1, leader)
    social = sp.solve(A - (a + b * F) - F * b, F)[0]
    cournot = sp.solve(A - (a + b * 2 * f1) - f1 * b, f1)[0]
    atomistic = sp.solve(A - (a + b * F), F)[0]
    W = D * F - b * F**2
    W_star = W.subs(F, social)
    return {
        "D": D,
        "F_star": sp.simplify(social),
        "f_cournot": sp.simplify(cournot),
        "f1_stackelberg": sp.simplify(leader),
        "f2_stackelberg": sp.simplify(follower),
        "F_atomistic": sp.simplify(atomistic),
        "loss_share_cournot": sp.simplify((W_star - W.subs(F, 2 * cournot)) / W_star),
        "loss_share_stackelberg": sp.simplify((W_star - W.subs(F, leader + follower)) / W_star),
        "loss_share_atomistic": sp.simplify((W_star - W.subs(F, atomistic)) / W_star),
    }


def inelastic_linear_closed_forms() -> dict[str, sp.Expr]:
    """Closed forms under ``c = a + b F`` and ``d(Q) = d0 - dd Q``, in ``Dp = s d0 - tau s - a``."""
    Dp = s * d0 - tau * s - a
    m = s**2 * dd + b

    def demand(total: sp.Expr) -> sp.Expr:
        return d0 - dd * s * total

    follower_cond = s * (demand(f1 + f2) - tau) - s**2 * f2 * dd - (a + b * (f1 + f2)) - f2 * b
    reaction = sp.solve(follower_cond, f2)[0]
    leader_cond = (
        s * (demand(f1 + reaction) - tau)
        - s**2 * f1 * dd * (1 - sp.Rational(1, 2))
        - (a + b * (f1 + reaction))
        - f1 * b * (1 - sp.Rational(1, 2))
    )
    leader = sp.solve(leader_cond, f1)[0]
    follower = reaction.subs(f1, leader)
    social = sp.solve(s * (demand(F) - tau) - (a + b * F) - F * b, F)[0]
    return {
        "Dp": Dp,
        "m": m,
        "f1_stackelberg": sp.simplify(leader),
        "f2_stackelberg": sp.simplify(follower),
        "F_star": sp.simplify(social),
        "expected_f1": Dp / (2 * m),
        "expected_f2": Dp / (4 * m),
        "expected_F_star": Dp / (s**2 * dd + 2 * b),
    }


# --------------------------------------------------------------- identities
@dataclass(frozen=True)
class Identity:
    """One algebraic statement and the callable that checks it."""

    id: str
    equation: str
    statement: str
    method: str
    check: Callable[[], bool]
    origin: str  # "monograph", "BVD" (Brueckner and Van Dender 2008), or "here"


def _identities() -> tuple[Identity, ...]:
    SYM = "symbolic: simplify(lhs - rhs) == 0"
    SIGN = "symbolic: sign under the declared assumptions"
    half = sp.Rational(1, 2)
    slope_expr = reaction_slope()
    lam_x = lambda_of_x()
    bounds = lambda_bounds()
    foc12 = foc_leader_inelastic()
    limits = inelastic_limits()
    pieces = inelastic_slope_pieces()
    lin = linear_closed_forms()
    inel = inelastic_linear_closed_forms()
    tolls = toll_leader()
    D = lin["D"]
    return (
        Identity(
            "eq6_social_foc",
            "(6)",
            "The efficient condition is p - tau - [F c'(F) + c(F)]/s = 0",
            SYM,
            lambda: _equal(foc_social(), p - tau - (F * c1 + c0) / s),
            "monograph",
        ),
        Identity(
            "eq7_follower_foc",
            "(7)",
            "The follower's condition is p - tau - [f2 c' + c]/s = 0",
            SYM,
            lambda: _equal(foc_follower(), p - tau - (f2 * c1 + c0) / s),
            "monograph",
        ),
        Identity(
            "eq8_reaction_slope",
            "(8)",
            "df2/df1 = -(f2 c'' + c')/(f2 c'' + 2 c')",
            SYM,
            lambda: _equal(slope_expr, -(f2 * c2 + c1) / (f2 * c2 + 2 * c1)),
            "monograph",
        ),
        Identity(
            "eq8_lambda_of_x",
            "(8)",
            "lambda = (1 + x)/(2 + x) with x = f2 c''/c'",
            SYM,
            lambda: _equal((-slope_expr).subs(c2, x * c1 / f2), lam_x),
            "here",
        ),
        Identity(
            "eq8_lambda_minus_half",
            "(8)",
            "lambda - 1/2 = x/(2(2 + x)) >= 0, so lambda >= 1/2",
            SIGN,
            lambda: (
                _equal(lam_x - half, bounds["lambda_minus_half"])
                and bool(bounds["lambda_minus_half"].is_nonnegative)
            ),
            "monograph",
        ),
        Identity(
            "eq8_one_minus_lambda",
            "(8)",
            "1 - lambda = 1/(2 + x) > 0, so lambda < 1",
            SIGN,
            lambda: (
                _equal(1 - lam_x, bounds["one_minus_lambda"])
                and bool(bounds["one_minus_lambda"].is_positive)
            ),
            "monograph",
        ),
        Identity(
            "eq8_lambda_half_when_linear",
            "(8)",
            "lambda = 1/2 exactly when c'' = 0",
            SYM,
            lambda: lam_x.subs(x, 0) == half,
            "monograph",
        ),
        Identity(
            "eq9_leader_foc",
            "(9)",
            "The leader's condition is p - tau - (1/s)[f1 c'(1 + df2/df1) + c] = 0",
            SYM,
            lambda: _equal(foc_leader(), p - tau - (f1 * c1 * (1 + slope) + c0) / s),
            "monograph",
        ),
        Identity(
            "f1_over_f2",
            "(7),(9)",
            "At one point (7) and (9) give f1 = f2/(1 - lambda); with lambda = (1+x)/(2+x), "
            "f1 - 2 f2 = f2 x >= 0",
            SYM,
            lambda: (
                _equal(leader_follower_ratio(), f2 / (1 - lam))
                and _equal((f2 / (1 - lam)).subs(lam, lam_x), f2 * (2 + x))
            ),
            "here",
        ),
        Identity(
            "eq10_gap",
            "(10)",
            "F c' - f1 c'(1 - lambda) = (f2 + lambda f1) c'",
            SYM,
            lambda: _equal((f1 + f2) * c1 - f1 * c1 * (1 - lam), (f2 + lam * f1) * c1),
            "monograph",
        ),
        Identity(
            "eq10_two_forms",
            "(10)",
            "(f2 - f1 df2/df1) c' = (f2 + lambda f1) MCD/(f1 + f2) when df2/df1 = -lambda",
            SYM,
            lambda: _equal(tolls["difference_form"].subs(slope, -lam), tolls["share_form"]),
            "monograph",
        ),
        Identity(
            "eq11_symmetric",
            "(11)",
            "At f1 = f2 = f*: T1* = (1/2)(1 + lambda*) MCD*",
            SYM,
            lambda: _equal(
                tolls["share_form"].subs({f1: f_star, f2: f_star}),
                half * (1 + lam) * (2 * f_star * c1),
            ),
            "BVD",
        ),
        Identity(
            "eq11_linear_3_4",
            "(11)",
            "With c'' = 0 (lambda* = 1/2) the leader's toll is 3/4 of MCD*, halfway between "
            "the Cournot toll (1/2) and the atomistic toll (1)",
            SYM,
            lambda: (half * (1 + lam)).subs(lam, half) == sp.Rational(3, 4),
            "here",
        ),
        Identity(
            "eq11_follower_half",
            "(11)",
            "The follower's toll F c' - f2 c' = f1 c' is 1/2 MCD* at the symmetric optimum",
            SYM,
            lambda: (
                _equal((f1 + f2) * c1 - f2 * c1, toll_follower())
                and _equal(toll_follower().subs(f1, f_star), half * (2 * f_star * c1))
            ),
            "BVD",
        ),
        Identity(
            "monopoly_foc_is_social",
            "benchmark",
            "A monopolist's condition coincides with the efficient one (full internalisation)",
            SYM,
            lambda: _equal(benchmarks()["monopoly"], foc_social()),
            "Brueckner (2002)",
        ),
        Identity(
            "cournot_toll_half_at_symmetry",
            "benchmark",
            "A Cournot duopolist's toll is the rival's flights times c', i.e. 1/2 MCD at symmetry",
            SYM,
            lambda: _equal(
                ((f1 + f2) * c1 - f1 * c1).subs({f1: f_star, f2: f_star}),
                half * (2 * f_star * c1),
            ),
            "Brueckner (2002)",
        ),
        Identity(
            "eq12_leader_foc",
            "(12)",
            "With p = d(sF): d + s f1 d'(1 + df2/df1) - tau - (1/s)[f1 c'(1 + df2/df1) + c] = 0",
            SYM,
            lambda: _equal(
                foc12,
                d0 + s * f1 * d1 * (1 + slope) - tau - (f1 * c1 * (1 + slope) + c0) / s,
            ),
            "monograph",
        ),
        Identity(
            "eq12_social_foc",
            "(12)",
            "The efficient condition under inelastic demand is d - tau - [F c' + c]/s = 0",
            SYM,
            lambda: _equal(foc_social_inelastic(), d0 - tau - (F * c1 + c0) / s),
            "monograph",
        ),
        Identity(
            "eq12_limit_minus_1",
            "(12)",
            "At df2/df1 = -1 the condition collapses to d - tau - c/s = 0",
            SYM,
            lambda: _equal(limits["slope_minus_one"], d0 - tau - c0 / s),
            "monograph",
        ),
        Identity(
            "eq12_limit_minus_half",
            "(12)",
            "At df2/df1 = -1/2: d + s f1 d'/2 - tau - (f1 c'/2 + c)/s = 0",
            SYM,
            lambda: _equal(
                limits["slope_minus_half"],
                d0 + s * f1 * d1 / 2 - tau - (f1 * c1 / 2 + c0) / s,
            ),
            "monograph",
        ),
        Identity(
            "lambda_inelastic_general",
            "(12)",
            "Under p = d(sF), df2/df1 = -A_/B_ with B_ = A_ + c'/s - s d'; and "
            "-df2/df1 - 1/2 = f2 (c''/s - s^2 d'')/(2 B_), so the bound <= -1/2 holds "
            "iff c''/s >= s^2 d''",
            SYM,
            lambda: (
                _equal(reaction_slope_inelastic(), pieces["slope"])
                and _equal(-pieces["slope"] - half, f2 * pieces["condition"] / (2 * pieces["B"]))
            ),
            "here",
        ),
        Identity(
            "lambda_linear_demand",
            "(12)",
            "With d'' = 0: df2/df1 = -(k + f2 c'')/(2k + f2 c''), k = c' - s^2 d' > 0, "
            "so the elastic-case bounds hold",
            SYM,
            lambda: (
                _equal(reaction_slope_inelastic().subs(d2, 0), reaction_slope_linear_demand())
                and bool((c1 - s**2 * d1).is_positive)
            ),
            "here",
        ),
        Identity(
            "linear_F_star",
            "linear",
            "c = a + bF: the efficient total is D/(2b)",
            SYM,
            lambda: _equal(lin["F_star"], D / (2 * b)),
            "here",
        ),
        Identity(
            "linear_cournot",
            "linear",
            "c = a + bF: each Cournot duopolist flies D/(3b)",
            SYM,
            lambda: _equal(lin["f_cournot"], D / (3 * b)),
            "here",
        ),
        Identity(
            "linear_stackelberg",
            "linear",
            "c = a + bF: the leader flies D/(2b) and the follower D/(4b)",
            SYM,
            lambda: (
                _equal(lin["f1_stackelberg"], D / (2 * b))
                and _equal(lin["f2_stackelberg"], D / (4 * b))
            ),
            "here",
        ),
        Identity(
            "linear_atomistic",
            "linear",
            "c = a + bF: price-taking airlines fly D/b in total, twice the efficient total",
            SYM,
            lambda: _equal(lin["F_atomistic"], D / b),
            "here",
        ),
        Identity(
            "linear_welfare_losses",
            "linear",
            "c = a + bF: the welfare loss is 1/9 of W* under Cournot, 1/4 under Stackelberg "
            "and all of it under atomistic behaviour",
            SYM,
            lambda: (
                lin["loss_share_cournot"] == sp.Rational(1, 9)
                and lin["loss_share_stackelberg"] == sp.Rational(1, 4)
                and lin["loss_share_atomistic"] == 1
            ),
            "here",
        ),
        Identity(
            "inelastic_linear_closed_forms",
            "(12) linear",
            "c = a + bF, d = d0 - dd Q: f1 = Dp/(2m), f2 = Dp/(4m), F* = Dp/(s^2 dd + 2b)",
            SYM,
            lambda: (
                _equal(inel["f1_stackelberg"], inel["expected_f1"])
                and _equal(inel["f2_stackelberg"], inel["expected_f2"])
                and _equal(inel["F_star"], inel["expected_F_star"])
            ),
            "here",
        ),
        Identity(
            "T1_equals_T2_at_stackelberg",
            "(10)",
            "At any Stackelberg equilibrium f2 = (1 - lambda) f1, so T1 = T2 = f1 c'",
            SYM,
            lambda: _equal(tolls["share_form"].subs(f2, (1 - lam) * f1), toll_follower()),
            "here",
        ),
    )


IDENTITIES: tuple[Identity, ...] = _identities()


def verify_identities() -> list[dict[str, object]]:
    """Run every identity; ``holds`` is what the checks return, never assumed."""
    return [
        {
            "id": item.id,
            "equation": item.equation,
            "statement": item.statement,
            "method": item.method,
            "origin": item.origin,
            "holds": bool(item.check()),
        }
        for item in IDENTITIES
    ]


# -------------------------------------------------------------- assumptions
@dataclass(frozen=True)
class Assumption:
    id: str
    statement: str
    status: str


ASSUMPTIONS: tuple[Assumption, ...] = (
    Assumption(
        "A1",
        "Demand is perfectly elastic at the total price p in equations (1)-(11); consumer "
        "surplus is zero and welfare is the airlines' joint profit.",
        "assumed",
    ),
    Assumption(
        "A2",
        "Every seat is sold; s is exogenous and identical across the two airlines.",
        "assumed",
    ),
    Assumption(
        "A3",
        "c' > 0 and c'' >= 0 (equation 5). Every bound on lambda is conditional on this.",
        "assumed",
    ),
    Assumption(
        "A4",
        "Airline 1 leads and airline 2 follows by assumption; f1 > f2 is a consequence of who "
        "leads, not of size.",
        "assumed",
    ),
    Assumption(
        "A5",
        "The tolls of (10)-(11) are per-flight constants evaluated at the efficient "
        "allocation; they are not assumed to alter the follower's reaction slope.",
        "assumed",
    ),
    Assumption(
        "A6",
        "'Pressuposição 2' (the leader under inelastic demand sits between the two endpoint "
        "readings of (12)) needs -1 < df2/df1 <= -1/2, which holds iff c''/s >= s^2 d''.",
        "holds iff c''/s >= s^2 d''; verified symbolically for d'' = 0 and numerically for "
        "linear demand",
    ),
    Assumption(
        "A7",
        "'Pressuposição 3' (entry of a low-cost carrier breaks the Stackelberg structure and "
        "the entrant has incentives to internalise its own congestion).",
        "verbal in the monograph; illustrated by this repository's Cournot extension",
    ),
    Assumption(
        "A8",
        "Existence and uniqueness of an interior equilibrium.",
        "verified numerically for the chosen parameters only",
    ),
)
