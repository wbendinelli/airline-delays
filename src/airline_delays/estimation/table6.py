"""Table 6 -- Estimation results, OLS.

`r2-results-v9-_tab5.do` lists `rthhi` and `maxcthhi` as endogenous and then
calls `gregrun, opt(ols)`: the HHIs enter as ordinary regressors and the
instruments are ignored. It is the article's own demonstration that ignoring
endogeneity flips the sign of both concentration coefficients -- the sharpest
single claim in the paper, and the cheapest one to check.

Because no instrument is needed, every column runs on the full filtered sample,
which is why the published N is 19,590 in all six columns rather than 19,419 in
the ODDS ones.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from airline_delays.estimation.common import (
    ENDOG,
    EXOG_FULL,
    EXOG_PARTIAL,
    ColumnSpec,
    Source,
    run_table,
)

SPECS: list[ColumnSpec] = [
    ColumnSpec(1, "fsc_oddsarr", EXOG_PARTIAL, ENDOG, (), "ols"),
    ColumnSpec(2, "fsc_oddsarr", EXOG_FULL, ENDOG, (), "ols"),
    ColumnSpec(3, "fsc_minsarr", EXOG_PARTIAL, ENDOG, (), "ols"),
    ColumnSpec(4, "fsc_minsarr", EXOG_FULL, ENDOG, (), "ols"),
    ColumnSpec(5, "fsc_minsp15arr", EXOG_PARTIAL, ENDOG, (), "ols"),
    ColumnSpec(6, "fsc_minsp15arr", EXOG_FULL, ENDOG, (), "ols"),
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
