"""Table 2 -- Descriptive statistics.

`r2-results-v9-_base.do` is a plain ``corr`` plus ``summ`` over 13 variables,
run on the sample the regression tables use: the panel after
``drop if fsc_oddsarr==.`` and the singleton cut. Reproducing it is what proves
that the variables named in the code are the variables printed in the article --
the minima and maxima are distinctive enough to identify each column.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from airline_delays.estimation.common import Source, build_sample
from airline_delays.estimation.published import TABLE2_VARIABLES

STATISTICS: tuple[str, ...] = ("mean", "sd", "min", "max")


def run(
    source: Source | str = Source.PRIVATE, *, sample: pd.DataFrame | None = None
) -> dict[str, Any]:
    """Correlation triangle and univariate statistics of the 13 published variables."""
    if sample is None:
        sample = build_sample(source, filter_regressand="fsc_oddsarr")
    absent = [name for name in TABLE2_VARIABLES if name not in sample.columns]
    # A column that is present but entirely null is not a variable this panel has:
    # reporting a NaN mean would look like a computed number. Say it is empty.
    empty = [
        name
        for name in TABLE2_VARIABLES
        if name in sample.columns and not sample[name].notna().any()
    ]
    present = [name for name in TABLE2_VARIABLES if name in sample.columns and name not in empty]
    block = sample[present].astype(float)
    correlation_matrix = block.corr(method="pearson")
    correlation = {
        row: {
            column: float(correlation_matrix.loc[row, column])
            for column in present[: present.index(row) + 1]
        }
        for row in present
    }
    univariate = {
        "mean": {name: float(block[name].mean()) for name in present},
        "sd": {name: float(block[name].std(ddof=1)) for name in present},
        "min": {name: float(block[name].min()) for name in present},
        "max": {name: float(block[name].max()) for name in present},
    }
    return {
        "sample": dict(sample.attrs.get("filters", {})),
        "variables": present,
        "missing_variables": absent,
        "empty_variables": empty,
        "correlation": correlation,
        "univariate": univariate,
    }
