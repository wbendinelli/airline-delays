"""The specification of Tables 2-7, fixed once and reused by every table.

Everything the published do-files set at the top and never change: the
regressor and instrument lists, the regressands, the column contract of the
estimation panel, the order and labels the article prints coefficients in, and
the HAC settings.

Estimation choices, and why
---------------------------
* **Bandwidth 4, Bartlett.** ``linearmodels`` weights lag *j* by
  ``1 - j/(bandwidth+1)``; Stata's ``ivreg2 ..., bw(5)`` weights it by
  ``1 - j/5`` for ``j = 0..4``. **4 here is 5 there.** The article's own choice
  is ``T^(1/3)`` with ``T = 144``, i.e. 5.24 -> 5.
* **``debiased=True``.** ``ivreg2`` without ``small`` divides by N; with
  ``small`` it divides by N-K and prints an F statistic. The published tables
  print an F statistic, so ``small`` was on.
* **Seasonality dummies on.** ``dummymonthreg`` builds the 60 region x month
  dummies; the article says "a fixed-effects procedure with seasonality
  controls", and including them puts the coefficients measurably closer to the
  published ones. The switch stays exposed (``with_seasonality``) and
  :mod:`airline_delays.estimation.sensitivity` reports both settings.
* **Dummies enter explicitly.** The do-files use neither ``partial()`` nor
  ``xtivreg2``, so the surviving route dummies and ``t_2..t_144`` are columns
  of the design matrix, with one route dummy omitted against the constant and
  exact collinearity removed by a rank-revealing QR.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Estimator = Literal["gmm2s", "liml", "ols"]

# ------------------------------------------------------------------ the model
EXOG_PARTIAL: tuple[str, ...] = (
    "maxprdel",
    "prwheather",
    "princident",
    "pr_connc",
    "cshare",
    "dailyflcong",
    "dailyflncong",
)
LCC_TERMS: tuple[str, ...] = ("lcc", "maxalccfu")
EXOG_FULL: tuple[str, ...] = EXOG_PARTIAL + LCC_TERMS
ENDOG: tuple[str, ...] = ("rthhi", "maxcthhi")

#: `gregins` for the ODDS/ODDSD blocks (5 excluded instruments, J with 3 df).
INSTRUMENTS_ODDS: tuple[str, ...] = (
    "h3_maxcthhi",
    "lnh1_maxcthhi",
    "l1h1_maxcthhi",
    "l1h2_maxcthhi",
    "h2_rthhi",
)
#: `gregins` for the MINS/MINSD blocks (3 excluded instruments, J with 1 df).
#: The two lists differ, the article does not say why, and they are not unified
#: here -- see `docs/notes/replication.md`.
INSTRUMENTS_MINS: tuple[str, ...] = ("h1_maxcthhi", "h2_maxcthhi", "h3_maxcthhi")

ARRIVAL_REGRESSANDS: tuple[str, ...] = ("fsc_oddsarr", "fsc_minsarr", "fsc_minsp15arr")
DEPARTURE_REGRESSANDS: tuple[str, ...] = ("fsc_oddsdep", "fsc_minsdep", "fsc_minsp15dep")

KEY_COLUMNS: tuple[str, ...] = ("od", "ym", "o_region", "d_region")
ALL_INSTRUMENTS: tuple[str, ...] = tuple(sorted(set(INSTRUMENTS_ODDS + INSTRUMENTS_MINS)))

#: The column contract of the estimation panel: the article's own variable
#: names, because this module is a port of a Stata specification and those
#: names are what identify each regressor in the published tables.
REQUIRED_COLUMNS: tuple[str, ...] = (
    KEY_COLUMNS + ARRIVAL_REGRESSANDS + DEPARTURE_REGRESSANDS + EXOG_FULL + ENDOG + ALL_INSTRUMENTS
)

#: The order the article lists coefficients in, and the labels it prints.
COEF_ORDER: tuple[str, ...] = (
    "dailyflcong",
    "dailyflncong",
    "prwheather",
    "princident",
    "pr_connc",
    "maxprdel",
    "cshare",
    "rthhi",
    "maxcthhi",
    "lcc",
    "maxalccfu",
)
COEF_LABEL: dict[str, str] = {
    "dailyflcong": "Nr flights in congested hours",
    "dailyflncong": "Nr flights in uncongested hours",
    "prwheather": "Prop flights with bad weather",
    "princident": "Prop flights with incidents",
    "pr_connc": "Prop flights held for late connections",
    "maxprdel": "Max prop city delayed flights",
    "cshare": "Codeshare agreement",
    "rthhi": "HHI city-pair",
    "maxcthhi": "HHI max endpoint cities",
    "lcc": "LCC presence city-pair",
    "maxalccfu": "LCC presence max endpoint cities",
}

# ------------------------------------------------------------- HAC / estimator
HAC_BANDWIDTH = 4
DEBIASED = True
WITH_SEASONALITY = True
SINGLETON_CUTOFF = 5


@dataclass(frozen=True)
class ColumnSpec:
    """One column of one published table."""

    column: int
    regressand: str
    exog: tuple[str, ...]
    endog: tuple[str, ...] = ()
    instruments: tuple[str, ...] = ()
    estimator: Estimator = "gmm2s"
    note: str = ""

    @property
    def is_iv(self) -> bool:
        return self.estimator != "ols" and bool(self.endog)
