"""Table 3 -- Estimation results (2SGMM), the article's baseline.

Six columns from `r2-results-v9-_tab2.do`: three regressands (ODDS, MINS,
MINS > 15) times two specifications (without and with the two LCC dummies).
The endogenous regressors are only ``rthhi`` and ``maxcthhi``; the LCC dummies
are exogenous, which contradicts the article's introduction ("all of the market
structure variables") but is unambiguous in the code, and is what reproduces the
published degrees of freedom.

The instrument list changes between the ODDS block (5 instruments, J with 3 df)
and the MINS block (3 instruments, J with 1 df). The article presents both as
one identification design and never explains the difference. It is not unified
here.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from airline_delays.estimation.common import (
    ENDOG,
    EXOG_FULL,
    EXOG_PARTIAL,
    INSTRUMENTS_MINS,
    INSTRUMENTS_ODDS,
    ColumnSpec,
    Source,
    run_table,
)

SPECS: list[ColumnSpec] = [
    ColumnSpec(1, "fsc_oddsarr", EXOG_PARTIAL, ENDOG, INSTRUMENTS_ODDS, "gmm2s"),
    ColumnSpec(2, "fsc_oddsarr", EXOG_FULL, ENDOG, INSTRUMENTS_ODDS, "gmm2s"),
    ColumnSpec(3, "fsc_minsarr", EXOG_PARTIAL, ENDOG, INSTRUMENTS_MINS, "gmm2s"),
    ColumnSpec(4, "fsc_minsarr", EXOG_FULL, ENDOG, INSTRUMENTS_MINS, "gmm2s"),
    ColumnSpec(5, "fsc_minsp15arr", EXOG_PARTIAL, ENDOG, INSTRUMENTS_MINS, "gmm2s"),
    ColumnSpec(6, "fsc_minsp15arr", EXOG_FULL, ENDOG, INSTRUMENTS_MINS, "gmm2s"),
]


def run(
    source: Source | str = Source.PRIVATE,
    *,
    sample: pd.DataFrame | None = None,
    columns: list[int] | None = None,
    **fit_kwargs: Any,
) -> dict[str, Any]:
    specs = SPECS if columns is None else [s for s in SPECS if s.column in columns]
    return run_table(
        specs, source=source, filter_regressand="fsc_oddsarr", sample=sample, **fit_kwargs
    )
