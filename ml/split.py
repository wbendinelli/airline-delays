"""Temporal splits: rolling origin (headline) and the fixed split (illustrative).

ADR-0009 fixes both. **Rolling origin** trains on everything up to ``y-2``,
early-stops on ``y-1`` and tests on ``y``, for every ``y`` from 2006 to 2013;
it is the headline because a single split cannot show what 2007 (43.6% of
arrivals late) and 2013 (15.7%) do to a model trained on the other. The **fixed
split** — train 2002-2010, validate 2011, test 2012-2013 — is reported next to
it because it is the design the literature uses, not because it is the better
answer.

Two rules are enforced here rather than trusted to the caller:

*The validation year is never in the training set.* Early stopping reads it, so
a model that had also trained on it would stop late and score its own memory.

*Subsampling, when it happens at all, is by whole route.* A random sample of
rows would put the São Paulo-Rio shuttle of March 2009 in training and the same
route's April 2009 in test, and the row-level dependence between flights of one
route in adjacent months is exactly the dependence a temporal split exists to
respect. `route_bucket` hashes the *route string* (blake2b over the ~2,000
distinct values, not over ten million rows), so the same routes are in or out in
every fold and every year: the sample is a sample of the market, not of time.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from ml import dataset_flights as ds

if TYPE_CHECKING:  # pragma: no cover - typing only
    import numpy as np
    import pandas as pd

ROLLING_TEST_YEARS: tuple[int, ...] = tuple(range(2006, 2014))
"""Test years of the rolling-origin evaluation (ADR-0009)."""

FIRST_TRAIN_YEAR = 2002
"""First year that can enter a training set.

2000 and 2001 stay out of training on purpose: they have no ``t-12`` lag for
their own first year and, more importantly, the fixed split of ADR-0009 starts
in 2002, so both designs see the same history.
"""

FIXED_TRAIN_YEARS: tuple[int, ...] = tuple(range(2002, 2011))
FIXED_VALID_YEAR = 2011
FIXED_TEST_YEARS: tuple[int, ...] = (2012, 2013)

HASH_BUCKETS = 1000
"""Granularity of the route hash: a sampling rate is a share of these buckets."""


@dataclass(frozen=True)
class Fold:
    """One train / validate / test partition of the years."""

    name: str
    kind: str
    train_years: tuple[int, ...]
    valid_year: int
    test_years: tuple[int, ...]

    @property
    def years(self) -> tuple[int, ...]:
        return tuple(sorted({*self.train_years, self.valid_year, *self.test_years}))

    def as_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "kind": self.kind,
            "train_years": list(self.train_years),
            "valid_year": self.valid_year,
            "test_years": list(self.test_years),
        }

    def check(self) -> None:
        """Fail on the two mistakes that would make the split meaningless."""
        if self.valid_year in self.train_years:
            raise ValueError(f"{self.name}: the validation year is inside the training years")
        overlap = set(self.test_years) & (set(self.train_years) | {self.valid_year})
        if overlap:
            raise ValueError(f"{self.name}: test years {sorted(overlap)} are also fitted on")
        latest_fitted = max([*self.train_years, self.valid_year])
        if min(self.test_years) <= latest_fitted:
            raise ValueError(
                f"{self.name}: test year {min(self.test_years)} is not after the "
                f"last fitted year {latest_fitted}"
            )


def rolling_origin(
    test_years: tuple[int, ...] = ROLLING_TEST_YEARS,
    first_train_year: int = FIRST_TRAIN_YEAR,
) -> tuple[Fold, ...]:
    """One fold per test year: train ``<= y-2``, validate ``y-1``, test ``y``."""
    folds = []
    for year in test_years:
        train = tuple(range(first_train_year, year - 1))
        if not train:
            raise ValueError(f"test year {year} leaves no training years after {first_train_year}")
        fold = Fold(
            name=f"rolling_{year}",
            kind="rolling",
            train_years=train,
            valid_year=year - 1,
            test_years=(year,),
        )
        fold.check()
        folds.append(fold)
    return tuple(folds)


def fixed_split() -> Fold:
    """The illustrative split of ADR-0009: 2002-2010 / 2011 / 2012-2013."""
    fold = Fold(
        name="fixed",
        kind="fixed",
        train_years=FIXED_TRAIN_YEARS,
        valid_year=FIXED_VALID_YEAR,
        test_years=FIXED_TEST_YEARS,
    )
    fold.check()
    return fold


# ------------------------------------------------------------------- sampling


def route_bucket(routes: pd.Series, buckets: int = HASH_BUCKETS) -> np.ndarray:
    """A stable bucket in ``[0, buckets)`` for each route string.

    Hashed with blake2b over the distinct route values, so the answer does not
    depend on the pandas version, the row order or the years being read — the
    same route is in the same bucket in 2002 and in 2013.
    """
    import numpy as np
    import pandas as pd

    values = pd.Index(pd.Series(routes).astype("string").fillna(""))
    distinct = values.unique()
    table = {
        value: int.from_bytes(hashlib.blake2b(str(value).encode(), digest_size=8).digest(), "big")
        % buckets
        for value in distinct
    }
    return np.asarray(values.map(table), dtype="int32")


def subsample_mask(frame: pd.DataFrame, rate: float, key: str = "route") -> np.ndarray:
    """Keep whole routes covering roughly `rate` of the buckets.

    `rate >= 1` keeps everything and does no hashing at all, so the default path
    costs nothing.
    """
    import numpy as np

    if rate >= 1.0:
        return np.ones(len(frame), dtype=bool)
    if rate <= 0.0:
        raise ValueError(f"sampling rate must be positive, got {rate}")
    return route_bucket(frame[key]) < round(rate * HASH_BUCKETS)


# ---------------------------------------------------------------------- loading


def load_years(
    years: tuple[int, ...],
    target: str,
    features: tuple[str, ...],
    *,
    dataset_dir: Path = ds.DATASET_DIR,
    extra: tuple[str, ...] = (),
    sample_rate: float = 1.0,
    require_target: bool = True,
) -> pd.DataFrame:
    """Read the years a fold needs, one partition at a time, already filtered.

    Filtering inside the loop is what keeps the peak in memory to one year:
    2002-2011 is 6.9 M scheduled flights but only 2.9 M of them have an arrival
    target under ADR-0012, and the 4 M that do not never need to exist as a
    frame at all.
    """
    import pandas as pd

    columns = list(dict.fromkeys([*ds.KEY_COLUMNS, *features, target, *extra]))
    parts: list[pd.DataFrame] = []
    for year in years:
        part = ds.read_dataset(dataset_dir, years=(year,), columns=columns)
        if require_target:
            part = part[part[target].notna()]
        if sample_rate < 1.0:
            part = part[subsample_mask(part, sample_rate)]
        parts.append(part.reset_index(drop=True))
    if not parts:
        raise ValueError("no years requested")
    return pd.concat(ds.align_categories(parts), ignore_index=True)


__all__ = [
    "FIRST_TRAIN_YEAR",
    "FIXED_TEST_YEARS",
    "FIXED_TRAIN_YEARS",
    "FIXED_VALID_YEAR",
    "HASH_BUCKETS",
    "ROLLING_TEST_YEARS",
    "Fold",
    "fixed_split",
    "load_years",
    "rolling_origin",
    "route_bucket",
    "subsample_mask",
]
