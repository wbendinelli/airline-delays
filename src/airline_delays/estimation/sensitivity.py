"""ADR-0008 -- how the headline coefficients move with the two open choices.

Two axes, and they are not symmetric.

**Outlier threshold.** The laboratory's own scripts trimmed flight-level delays
at 313.25 minutes in one place and at 117.10 (arrivals) / 111.75 (departures) in
another; ADR-0008 makes 313.25 the named default and requires this table. The
threshold is applied *before* aggregation, so varying it means rebuilding the
regressand from flights -- which the source has to offer. A panel that carries
the variants exposes them as suffixed columns (see
:func:`replication.common.regressand_column`); the private benchmark
``proj18.dta`` is delivered already aggregated, under a rule its authors never
documented, so on that source the threshold rows are reported **unavailable**
rather than approximated.

**Seasonality dummies.** ``dummymonthreg`` builds the 60 region x month dummies
and ``gregcontrols`` never mentions them; the ``.ado`` that would settle it was
not delivered. This axis is a pure specification switch and is always available.

The reported coefficients are the two the article is about: ``rthhi`` (the
competition-quality channel) and ``maxcthhi`` (congestion internalisation), in
columns 1 and 2 of Table 3.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from airline_delays.estimation.common import (
    DEFAULT_OUTLIER_THRESHOLD,
    OUTLIER_THRESHOLDS,
    ColumnSpec,
    PublicPanelIncomplete,
    Source,
    build_sample,
    fit,
    regressand_column,
)
from airline_delays.estimation.table3 import SPECS as TABLE3_SPECS

#: The coefficients the sensitivity table reports.
FOCUS: tuple[str, ...] = ("rthhi", "maxcthhi")
COLUMNS: tuple[int, ...] = (1, 2)
SEASONALITY_SETTINGS: tuple[bool, ...] = (True, False)


def _threshold_label(threshold: float | None) -> str:
    if threshold is None:
        return "none"
    return f"{threshold:.2f}"


def _cell(
    sample: pd.DataFrame,
    spec: ColumnSpec,
    threshold: float | None,
    with_seasonality: bool,
) -> dict[str, Any]:
    column_name = regressand_column(spec.regressand, threshold)
    base = {
        "column": spec.column,
        "regressand": spec.regressand,
        "regressand_column": column_name,
        "outlier_threshold": _threshold_label(threshold),
        "with_seasonality": with_seasonality,
        "is_default": threshold == DEFAULT_OUTLIER_THRESHOLD,
    }
    if column_name not in sample.columns:
        return base | {
            "available": False,
            "reason": (
                f"the panel does not carry {column_name!r}: this source cannot rebuild the "
                "regressand at a different flight-level outlier threshold (ADR-0008)"
            ),
        }
    try:
        result = fit(sample, spec, with_seasonality=with_seasonality, outlier_threshold=threshold)
    except PublicPanelIncomplete as exc:
        return base | {"available": False, "reason": str(exc)}
    return base | {
        "available": True,
        "b": {
            name: result.coefficients[name]["b"] for name in FOCUS if name in result.coefficients
        },
        "se": {
            name: result.coefficients[name]["se"] for name in FOCUS if name in result.coefficients
        },
        "stats": {
            key: result.stats.get(key)
            for key in (
                "n_obs",
                "n_params",
                "adj_r2",
                "rmse",
                "j_stat",
                "j_p",
                "kp_lm",
                "weak_kp_f",
            )
        },
    }


def run(
    source: Source | str = Source.PRIVATE,
    *,
    sample: pd.DataFrame | None = None,
) -> dict[str, Any]:
    """The full grid: columns 1 and 2 x three thresholds x with/without seasonality."""
    if sample is None:
        sample = build_sample(source, filter_regressand="fsc_oddsarr")
    specs = {spec.column: spec for spec in TABLE3_SPECS if spec.column in COLUMNS}
    cells = [
        _cell(sample, specs[column], threshold, with_seasonality)
        for column in COLUMNS
        for threshold in OUTLIER_THRESHOLDS
        for with_seasonality in SEASONALITY_SETTINGS
    ]
    available = [cell for cell in cells if cell["available"]]
    return {
        "sample": dict(sample.attrs.get("filters", {})),
        "focus": list(FOCUS),
        "default_outlier_threshold": _threshold_label(DEFAULT_OUTLIER_THRESHOLD),
        "cells": cells,
        "n_cells": len(cells),
        "n_available": len(available),
        "unavailable_thresholds": sorted(
            {cell["outlier_threshold"] for cell in cells if not cell["available"]}
        ),
    }
