"""Metrics, calibration, the two naive baselines and permutation importance.

Four numbers per model, and they answer different questions. **AUC** is
ranking: can the model put the late flight above the punctual one, whatever the
base rate. **PR-AUC** is the same ranking read on the positive class only, and
it is the number that moves when the base rate does — comparing PR-AUC between
2007 (94% of the *observed* arrivals late) and 2013 (16%) without also reading
the base rate is meaningless, so both are always reported together.
**Brier** is squared error on the probability itself: it punishes a model that
ranks well and is confidently wrong about the level, which is exactly what a
model trained on 2000-2009 does when scored on 2010-2013 (ADR-0012 changes the
sample, not the world). The **calibration table** is Brier read bin by bin.

Two naive baselines, both from ADR-0009 and both already columns of the
dataset: the route's late rate in the previous month, and the airline group's.
They are not strawmen — a route's own recent prevalence is what an operations
desk would guess — and they are the reason the model's AUC has to be read as a
gain over about 0.60, not over 0.50.

`permutation_importance` measures the drop in AUC when one column is shuffled.
It is reported instead of gain alone because gain rewards a feature that gets
*used*, and permutation rewards a feature the metric actually needs; where the
two disagree, the disagreement is the finding.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ml import train_xgb as tx

if TYPE_CHECKING:  # pragma: no cover - typing only
    import numpy as np
    import pandas as pd

    from ml.train_xgb import Fitted

CALIBRATION_BINS = 10
"""Equal-width bins of the predicted probability, over [0, 1]."""

BASELINES: dict[str, str] = {
    "route_prevalence_l1": "route_late15_l1",
    "group_prevalence_l1": "group_late15_l1",
}
"""The naive references of ADR-0009, as the dataset columns that carry them."""

PERMUTATION_REPEATS = 3
PERMUTATION_SAMPLE = 250_000
"""Rows drawn for permutation importance.

A full test year is a million rows and 49 features times 3 repeats is 147 extra
scoring passes; a quarter of a million rows puts the standard error of an AUC
difference around 0.0005, far below anything the report reads.
"""


def binary_metrics(y_true: np.ndarray, y_prob: np.ndarray) -> dict[str, Any]:
    """AUC, PR-AUC, Brier, base rate and n, with nulls dropped in one place.

    A degenerate fold (one class only) returns ``None`` for AUC and PR-AUC
    rather than raising: the fold is still worth reporting, and a missing number
    that says why is better than a fold that vanishes from the table.
    """
    import numpy as np
    from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score

    y_true = np.asarray(y_true, dtype="float64")
    y_prob = np.asarray(y_prob, dtype="float64")
    keep = np.isfinite(y_true) & np.isfinite(y_prob)
    y_true, y_prob = y_true[keep], y_prob[keep]
    out: dict[str, Any] = {
        "n": int(y_true.size),
        "base_rate": float(y_true.mean()) if y_true.size else None,
        "auc": None,
        "pr_auc": None,
        "brier": None,
    }
    if y_true.size and 0 < y_true.sum() < y_true.size:
        out["auc"] = float(roc_auc_score(y_true, y_prob))
        out["pr_auc"] = float(average_precision_score(y_true, y_prob))
    if y_true.size:
        out["brier"] = float(brier_score_loss(y_true, np.clip(y_prob, 0.0, 1.0)))
    return out


def calibration_table(
    y_true: np.ndarray, y_prob: np.ndarray, bins: int = CALIBRATION_BINS
) -> list[dict[str, Any]]:
    """Observed frequency against mean predicted probability, bin by bin."""
    import numpy as np

    y_true = np.asarray(y_true, dtype="float64")
    y_prob = np.asarray(y_prob, dtype="float64")
    keep = np.isfinite(y_true) & np.isfinite(y_prob)
    y_true, y_prob = y_true[keep], np.clip(y_prob[keep], 0.0, 1.0)
    edges = np.linspace(0.0, 1.0, bins + 1)
    index = np.clip(np.digitize(y_prob, edges[1:-1], right=False), 0, bins - 1)
    rows: list[dict[str, Any]] = []
    for slot in range(bins):
        mask = index == slot
        count = int(mask.sum())
        if count == 0:
            continue
        rows.append(
            {
                "bin_low": float(edges[slot]),
                "bin_high": float(edges[slot + 1]),
                "n": count,
                "share": count / y_true.size,
                "mean_predicted": float(y_prob[mask].mean()),
                "observed": float(y_true[mask].mean()),
            }
        )
    return rows


def naive_predictions(
    frame: pd.DataFrame, fallback: float, baselines: dict[str, str] = BASELINES
) -> dict[str, np.ndarray]:
    """The baseline probability vectors for a test frame.

    Where the previous month has no observation the baseline falls back to the
    **training** years' base rate, which is the only number a naive forecaster
    would have had; filling with the test year's own rate would hand the
    baseline a look at the answer.
    """
    import numpy as np

    out: dict[str, np.ndarray] = {}
    for name, column in baselines.items():
        values = frame[column].to_numpy(dtype="float64", copy=True)
        values[~np.isfinite(values)] = fallback
        out[name] = np.clip(values, 0.0, 1.0)
    return out


def permutation_importance(
    fitted: Fitted,
    frame: pd.DataFrame,
    target: str,
    *,
    n_repeats: int = PERMUTATION_REPEATS,
    sample: int = PERMUTATION_SAMPLE,
    seed: int = 0,
) -> list[dict[str, Any]]:
    """Drop in test AUC when one feature is shuffled, averaged over repeats."""
    import numpy as np

    rng = np.random.default_rng(seed)
    if len(frame) > sample:
        frame = frame.iloc[rng.choice(len(frame), size=sample, replace=False)]
    frame = frame.reset_index(drop=True).copy()
    y_true = frame[target].to_numpy(dtype="float64")
    base = binary_metrics(y_true, tx.predict_proba(fitted, frame))["auc"]
    gains = tx.gain_importance(fitted)
    rows: list[dict[str, Any]] = []
    for name in fitted.features:
        original = frame[name].copy()
        drops = []
        for _ in range(n_repeats):
            # `.iloc[perm].set_axis(...)` rather than a numpy round trip: writing a
            # numpy object array back into a `category` column silently turns it
            # into `object`, and XGBoost then refuses the whole frame.
            frame[name] = original.iloc[rng.permutation(len(frame))].set_axis(frame.index)
            shuffled = binary_metrics(y_true, tx.predict_proba(fitted, frame))["auc"]
            drops.append((base or 0.0) - (shuffled or 0.0))
        frame[name] = original
        rows.append(
            {
                "feature": name,
                "auc_drop": float(np.mean(drops)),
                "auc_drop_sd": float(np.std(drops)),
                "total_gain": gains.get(name, 0.0),
            }
        )
    rows.sort(key=lambda row: row["auc_drop"], reverse=True)
    return rows


def evaluate_predictions(
    y_true: np.ndarray,
    predictions: dict[str, np.ndarray],
    *,
    calibrate: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Metrics for several prediction vectors over the same rows."""
    out: dict[str, Any] = {}
    for name, y_prob in predictions.items():
        entry = binary_metrics(y_true, y_prob)
        if name in calibrate:
            entry["calibration"] = calibration_table(y_true, y_prob)
        out[name] = entry
    return out


__all__ = [
    "BASELINES",
    "CALIBRATION_BINS",
    "PERMUTATION_REPEATS",
    "PERMUTATION_SAMPLE",
    "binary_metrics",
    "calibration_table",
    "evaluate_predictions",
    "naive_predictions",
    "permutation_importance",
]
