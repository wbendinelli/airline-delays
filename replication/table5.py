"""Table 5 -- Estimation results, LIML.

`r2-results-v9-_tab4.do` is Table 3 with `gregest liml bw(5) rob`: same sample,
same regressors, same instruments, limited-information maximum likelihood
instead of two-step GMM. The article uses it to show the baseline does not
depend on the GMM weighting, and the published numbers bear that out -- the
coefficients move in the third decimal.

`linearmodels.iv.IVLIML` exposes Sargan, not Hansen's J, so the J statistic
here comes from `common.hansen_j`, which evaluates the HAC optimal weight
matrix at the LIML residuals -- what `ivreg2` prints for any robust estimator.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from replication.common import (
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
    ColumnSpec(1, "fsc_oddsarr", EXOG_PARTIAL, ENDOG, INSTRUMENTS_ODDS, "liml"),
    ColumnSpec(2, "fsc_oddsarr", EXOG_FULL, ENDOG, INSTRUMENTS_ODDS, "liml"),
    ColumnSpec(3, "fsc_minsarr", EXOG_PARTIAL, ENDOG, INSTRUMENTS_MINS, "liml"),
    ColumnSpec(4, "fsc_minsarr", EXOG_FULL, ENDOG, INSTRUMENTS_MINS, "liml"),
    ColumnSpec(5, "fsc_minsp15arr", EXOG_PARTIAL, ENDOG, INSTRUMENTS_MINS, "liml"),
    ColumnSpec(6, "fsc_minsp15arr", EXOG_FULL, ENDOG, INSTRUMENTS_MINS, "liml"),
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
