"""Table 4 -- Robustness checks (2SGMM), all seven columns on ODDS.

`r2-results-v9-_tab3.do` keeps the regressand and the instrument list fixed and
drops one block of regressors per column. The omission map below is read off
the do-file and matches the published table cell for cell -- including the two
columns that drop one HHI and therefore have a single endogenous regressor (J
with 4 df instead of 3), and column 4, which drops both HHIs *and* switches to
OLS, so it is the only column of the table with no identification statistics
and the larger sample (no lagged instruments to lose).
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from replication.common import (
    ENDOG,
    EXOG_FULL,
    INSTRUMENTS_ODDS,
    ColumnSpec,
    Source,
    run_table,
)

_WITHOUT_UNCONGESTED = tuple(name for name in EXOG_FULL if name != "dailyflncong")
_WITHOUT_FLIGHT_COUNTS = tuple(
    name for name in EXOG_FULL if name not in {"dailyflcong", "dailyflncong"}
)
_WITHOUT_DELAY_CONTROLS = ("cshare", "dailyflcong", "dailyflncong", "lcc", "maxalccfu")

SPECS: list[ColumnSpec] = [
    ColumnSpec(1, "fsc_oddsarr", EXOG_FULL, ENDOG, INSTRUMENTS_ODDS, "gmm2s", "full model"),
    ColumnSpec(
        2, "fsc_oddsarr", EXOG_FULL, ("maxcthhi",), INSTRUMENTS_ODDS, "gmm2s", "drops rthhi"
    ),
    ColumnSpec(
        3, "fsc_oddsarr", EXOG_FULL, ("rthhi",), INSTRUMENTS_ODDS, "gmm2s", "drops maxcthhi"
    ),
    ColumnSpec(4, "fsc_oddsarr", EXOG_FULL, (), (), "ols", "drops both HHIs, OLS"),
    ColumnSpec(
        5,
        "fsc_oddsarr",
        _WITHOUT_DELAY_CONTROLS,
        ENDOG,
        INSTRUMENTS_ODDS,
        "gmm2s",
        "drops weather, incidents, connections and max city delay",
    ),
    ColumnSpec(
        6,
        "fsc_oddsarr",
        _WITHOUT_UNCONGESTED,
        ENDOG,
        INSTRUMENTS_ODDS,
        "gmm2s",
        "drops dailyflncong",
    ),
    ColumnSpec(
        7,
        "fsc_oddsarr",
        _WITHOUT_FLIGHT_COUNTS,
        ENDOG,
        INSTRUMENTS_ODDS,
        "gmm2s",
        "drops both flight counts",
    ),
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
