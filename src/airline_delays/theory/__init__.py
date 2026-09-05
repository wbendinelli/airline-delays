"""The theory behind the replicated article, derived and checked.

The 2016 article this repository replicates rests on a theory it does not
derive: airlines with market power internalise part of the congestion they
cause, and a Stackelberg leader facing a follower internalises less of it than
a Cournot duopolist. That theory was worked out in the author's 2013
undergraduate monograph (USP/ESALQ), section 4, following Brueckner and Van
Dender (2008, *Journal of Urban Economics* 64, 288-295) and Brueckner (2002,
*American Economic Review* 92, 1357-1375). This package re-derives it
symbolically, checks every identity, solves numeric examples, redraws the five
congestion-economics diagrams of the monograph's section 2, and joins the
model's objects to the published signs of the article's Table 3
(``DECISIONS.md`` ADR-0019).

Layout
------
``model``
    The symbolic model (sympy): equations (1)-(12) of the monograph, the
    reaction slope and its bounds, the tolls, the benchmarks, the inelastic
    demand case; :data:`~theory.model.IDENTITIES` and
    :data:`~theory.model.ASSUMPTIONS`.
``families``
    Concrete primitives for the numeric examples: linear and quadratic
    congestion cost, linear inverse demand.
``equilibrium``
    Numeric solutions -- social optimum, Stackelberg, Cournot, atomistic,
    monopoly, and this repository's low-cost entrant extension.
``figures``
    The five diagrams as hand-written SVG from fixed geometry, plus the
    coordinates of every labelled point.
``bridge``
    Theory object -> article variable -> published sign, joined with
    ``src/airline_delays/estimation/published.json``.
``run``
    Writes ``reports/theory/`` (``model.json``, ``figures.json``, the SVG
    files and ``results.md``). Deterministic and offline: a second run on an
    unchanged tree changes nothing.

Every number the Portuguese chapters under ``docs/theory/`` quote about the
model comes from ``reports/theory/model.json``; every figure from
``reports/theory/figures/``. Nothing here is estimated on data.
"""

from __future__ import annotations

__all__ = ["bridge", "equilibrium", "families", "figures", "model", "run"]
