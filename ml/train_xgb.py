"""Gradient boosting for the two horizons, with early stopping on the fold's year.

XGBoost with ``tree_method="hist"`` and ``enable_categorical=True``: the
histogram builder is what makes three million rows a two-minute fit on ten
cores, and native categorical support is what lets ``origin_icao`` (about 150
levels) and ``airline`` (about 90) enter as themselves rather than as a
one-hot block wider than the rest of the table put together.

**Early stopping reads the validation year and nothing else.** Every fold has
one: ``y-1`` for the rolling origin, 2011 for the fixed split. The number of
trees is therefore chosen on data the model never fitted and never scores —
which is the only reason a 1,200-tree ceiling is safe to set.

**Both horizons train on every row of the fold.** The H-1 columns are null for
the 20-39% of flights with no linked inbound leg, and XGBoost's default
direction handles a null natively. Restricting the H-1 model to linked flights
would make its test set a different, easier population than D-1's and the
comparison between the two horizons would stop meaning anything;
`ml.evaluate` instead reports the linked subset separately, where the whole
gain of the horizon actually lives.

LightGBM is available as a second learner (``learner="lightgbm"``) and is not
run by default: it is a check that the result is not an artefact of one
implementation, not a second headline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from ml import dataset_flights as ds

if TYPE_CHECKING:  # pragma: no cover - typing only
    import numpy as np
    import pandas as pd

LEARNERS: tuple[str, ...] = ("xgboost", "lightgbm")

HORIZONS: dict[str, tuple[str, ...]] = {
    "D-1": ds.FEATURES_D1,
    "H-1": ds.FEATURES_H1,
}
"""The two horizons of ADR-0009, as feature lists.

``D-1`` is the evening before: schedule, calendar, market structure and closed
historical windows. ``H-1`` adds the three columns of the *inbound* leg's
outcome and nothing else.
"""

HORIZON_LABEL: dict[str, str] = {
    "D-1": "day before (schedule and closed history only)",
    "H-1": "at the gate (adds the inbound leg's realised arrival)",
}

DEFAULT_PARAMS: dict[str, Any] = {
    "tree_method": "hist",
    "enable_categorical": True,
    "max_cat_to_onehot": 4,
    "max_bin": 128,
    "n_estimators": 1200,
    "learning_rate": 0.08,
    "max_depth": 7,
    "min_child_weight": 20.0,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "reg_lambda": 1.0,
    "objective": "binary:logistic",
    "eval_metric": "logloss",
    "random_state": 0,
}
"""Deliberately unremarkable settings.

The headline of this phase is the evaluation design, not a tuned model, so the
hyperparameters are the ones that would be reached without tuning and are held
fixed across all folds and both horizons. `max_bin=128` halves the histogram
build with no measurable cost on ten million rows; `min_child_weight=20` is the
only concession to the long tail of tiny routes.
"""

EARLY_STOPPING_ROUNDS = 40


@dataclass
class Fitted:
    """A trained model plus everything the report needs to describe it."""

    model: Any
    learner: str
    horizon: str
    target: str
    features: tuple[str, ...]
    n_train: int
    n_valid: int
    base_rate_train: float
    best_iteration: int | None
    seconds: float
    params: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "learner": self.learner,
            "horizon": self.horizon,
            "target": self.target,
            "n_features": len(self.features),
            "n_train": self.n_train,
            "n_valid": self.n_valid,
            "base_rate_train": self.base_rate_train,
            "best_iteration": self.best_iteration,
            "seconds": round(self.seconds, 2),
        }

    def predict(self, frame: pd.DataFrame) -> np.ndarray:
        return predict_proba(self, frame)


def train(
    train_frame: pd.DataFrame,
    valid_frame: pd.DataFrame,
    *,
    horizon: str,
    target: str = "late15_arr",
    learner: str = "xgboost",
    params: dict[str, Any] | None = None,
    n_jobs: int = 8,
) -> Fitted:
    """Fit one model for one horizon, early-stopping on `valid_frame`."""
    import time

    if horizon not in HORIZONS:
        raise KeyError(f"unknown horizon {horizon!r}; expected one of {sorted(HORIZONS)}")
    if learner not in LEARNERS:
        raise KeyError(f"unknown learner {learner!r}; expected one of {LEARNERS}")
    features = HORIZONS[horizon]
    settings = {**DEFAULT_PARAMS, **(params or {}), "n_jobs": n_jobs}
    started = time.time()
    x_train, y_train = train_frame[list(features)], train_frame[target].to_numpy("float32")
    x_valid, y_valid = valid_frame[list(features)], valid_frame[target].to_numpy("float32")
    if learner == "xgboost":
        model, best = _fit_xgboost(x_train, y_train, x_valid, y_valid, settings)
    else:
        model, best = _fit_lightgbm(x_train, y_train, x_valid, y_valid, settings)
    return Fitted(
        model=model,
        learner=learner,
        horizon=horizon,
        target=target,
        features=features,
        n_train=len(train_frame),
        n_valid=len(valid_frame),
        base_rate_train=float(y_train.mean()),
        best_iteration=best,
        seconds=time.time() - started,
        params=settings,
    )


def _fit_xgboost(
    x_train: pd.DataFrame,
    y_train: np.ndarray,
    x_valid: pd.DataFrame,
    y_valid: np.ndarray,
    settings: dict[str, Any],
) -> tuple[Any, int | None]:
    import xgboost as xgb

    model = xgb.XGBClassifier(**settings, early_stopping_rounds=EARLY_STOPPING_ROUNDS, verbosity=0)
    model.fit(x_train, y_train, eval_set=[(x_valid, y_valid)], verbose=False)
    return model, int(getattr(model, "best_iteration", 0) or 0)


def _fit_lightgbm(
    x_train: pd.DataFrame,
    y_train: np.ndarray,
    x_valid: pd.DataFrame,
    y_valid: np.ndarray,
    settings: dict[str, Any],
) -> tuple[Any, int | None]:
    """LightGBM with the same budget; the second implementation, not a second model."""
    import lightgbm as lgb

    mapped = {
        "n_estimators": settings["n_estimators"],
        "learning_rate": settings["learning_rate"],
        "max_depth": settings["max_depth"],
        "min_child_samples": int(settings["min_child_weight"]),
        "subsample": settings["subsample"],
        "subsample_freq": 1,
        "colsample_bytree": settings["colsample_bytree"],
        "reg_lambda": settings["reg_lambda"],
        "max_bin": settings["max_bin"],
        "n_jobs": settings["n_jobs"],
        "random_state": settings["random_state"],
        "verbose": -1,
    }
    model = lgb.LGBMClassifier(**mapped)
    model.fit(
        x_train,
        y_train,
        eval_set=[(x_valid, y_valid)],
        eval_metric="binary_logloss",
        callbacks=[lgb.early_stopping(EARLY_STOPPING_ROUNDS, verbose=False)],
    )
    return model, int(getattr(model, "best_iteration_", 0) or 0)


def predict_proba(fitted: Fitted, frame: pd.DataFrame) -> np.ndarray:
    """Predicted probability of the positive class, for the fitted feature set."""
    import numpy as np

    matrix = frame[list(fitted.features)]
    return np.asarray(fitted.model.predict_proba(matrix)[:, 1], dtype="float64")


def gain_importance(fitted: Fitted) -> dict[str, float]:
    """Total-gain importance per feature, in the model's own units.

    Reported next to permutation importance because the two disagree in a
    readable way: gain rewards a feature used deep in many trees, permutation
    rewards a feature the metric actually depends on.
    """
    if fitted.learner == "xgboost":
        booster = fitted.model.get_booster()
        raw = booster.get_score(importance_type="total_gain")
    else:  # pragma: no cover - optional learner
        raw = dict(
            zip(fitted.features, fitted.model.booster_.feature_importance("gain"), strict=False)
        )
    return {name: float(raw.get(name, 0.0)) for name in fitted.features}


__all__ = [
    "DEFAULT_PARAMS",
    "EARLY_STOPPING_ROUNDS",
    "HORIZONS",
    "HORIZON_LABEL",
    "LEARNERS",
    "Fitted",
    "gain_importance",
    "predict_proba",
    "train",
]
