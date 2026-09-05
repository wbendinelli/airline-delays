"""How the headline coefficients move with the one open specification choice.

``dummymonthreg`` builds the 60 region x month dummies and ``gregcontrols`` never
mentions them; the article says "a fixed-effects procedure with seasonality
controls". The grid estimates columns (1) and (2) of Table 3 with and without
the dummies and reports the two coefficients the article is about: ``rthhi``
(the competition-quality channel) and ``maxcthhi`` (congestion
internalisation).

The flight-level outlier threshold (ADR-0008) is *not* an axis here: the
estimation panel arrives aggregated, so its regressands cannot be rebuilt at a
different threshold. That parameter lives in the reconstruction pipeline
(:mod:`airline_delays.definitions.delays`).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from airline_delays.estimation.estimators import fit
from airline_delays.estimation.sample import build_sample
from airline_delays.estimation.specification import ColumnSpec
from airline_delays.estimation.table3 import SPECS as TABLE3_SPECS

#: The coefficients the sensitivity table reports.
FOCUS: tuple[str, ...] = ("rthhi", "maxcthhi")
COLUMNS: tuple[int, ...] = (1, 2)
SEASONALITY_SETTINGS: tuple[bool, ...] = (True, False)


def _cell(sample: pd.DataFrame, spec: ColumnSpec, with_seasonality: bool) -> dict[str, Any]:
    result = fit(sample, spec, with_seasonality=with_seasonality)
    return {
        "column": spec.column,
        "regressand": spec.regressand,
        "with_seasonality": with_seasonality,
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


def run(panel: Path | str | None = None, *, sample: pd.DataFrame | None = None) -> dict[str, Any]:
    """The grid: columns 1 and 2 of Table 3 x with/without seasonality dummies."""
    if sample is None:
        sample = build_sample(panel, filter_regressand="fsc_oddsarr")
    specs = {spec.column: spec for spec in TABLE3_SPECS if spec.column in COLUMNS}
    cells = [
        _cell(sample, specs[column], with_seasonality)
        for column in COLUMNS
        for with_seasonality in SEASONALITY_SETTINGS
    ]
    return {
        "sample": dict(sample.attrs.get("filters", {})),
        "focus": list(FOCUS),
        "axis": "with_seasonality",
        "cells": cells,
        "n_cells": len(cells),
    }
