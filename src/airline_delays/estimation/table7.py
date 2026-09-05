"""Table 7 -- Estimation results, departures.

`r2-results-v9-_tab6.do` is Table 3 with the three departure regressands
(`fsc_oddsdep`, `fsc_minsdep`, `fsc_minsp15dep`) in place of the arrival ones.
The sample filter moves with them: the do-file drops on `fsc_oddsdep`, not on
`fsc_oddsarr`, which is why the published N is 19,408/19,579 here against
19,419/19,590 in Table 3.
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

FILTER_REGRESSAND = "fsc_oddsdep"

SPECS: list[ColumnSpec] = [
    ColumnSpec(1, "fsc_oddsdep", EXOG_PARTIAL, ENDOG, INSTRUMENTS_ODDS, "gmm2s"),
    ColumnSpec(2, "fsc_oddsdep", EXOG_FULL, ENDOG, INSTRUMENTS_ODDS, "gmm2s"),
    ColumnSpec(3, "fsc_minsdep", EXOG_PARTIAL, ENDOG, INSTRUMENTS_MINS, "gmm2s"),
    ColumnSpec(4, "fsc_minsdep", EXOG_FULL, ENDOG, INSTRUMENTS_MINS, "gmm2s"),
    ColumnSpec(5, "fsc_minsp15dep", EXOG_PARTIAL, ENDOG, INSTRUMENTS_MINS, "gmm2s"),
    ColumnSpec(6, "fsc_minsp15dep", EXOG_FULL, ENDOG, INSTRUMENTS_MINS, "gmm2s"),
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
        specs, source=source, filter_regressand=FILTER_REGRESSAND, sample=sample, **fit_kwargs
    )
