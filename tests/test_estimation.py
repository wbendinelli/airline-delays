"""The estimation stage: one panel, one code path, fail fast on anything it lacks.

Tables 2-7 run on the article's estimation panel
(``data/analysis/article_panel_route_month.parquet``, ADR-0020) or on any
route-month panel that carries the estimation contract. Four things are checked:

1. a missing panel fails with a message that names the file and the command
   that builds it, not with a ``KeyError`` deep inside pandas;
2. a panel that lacks contract columns is refused, naming every missing column;
3. Table 2 and Table 3 column 1 run end to end on a synthetic panel built to the
   contract -- sample filters, route and time dummies, seasonality dummies,
   collinearity pruning, 2SGMM with the HAC kernel, Hansen J, Kleibergen-Paap;
4. on the committed article panel the do-files' filters give the sample the
   published tables were estimated on, and Table 2 computes all 13 variables.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from airline_delays.estimation import loader, specification, table2, table3
from airline_delays.estimation.loader import (
    ARTICLE_PANEL_PATH,
    ArticlePanelNotBuilt,
    PanelIncomplete,
)
from airline_delays.estimation.sample import build_sample
from airline_delays.estimation.specification import REQUIRED_COLUMNS


@pytest.fixture(autouse=True)
def _clear_panel_cache() -> None:
    """The loader caches by path; tests move the path around."""
    loader._PANEL_CACHE.clear()


def make_panel(n_routes: int = 40, n_months: int = 36, *, seed: int = 20260905) -> pd.DataFrame:
    """A synthetic route-month panel that satisfies :data:`REQUIRED_COLUMNS`.

    Not realistic data -- realistic *shape*: a panel of directed city pairs over
    consecutive months inside the article's 2002-2013 window, with a first stage
    strong enough that the IV columns identify.
    """
    rng = np.random.default_rng(seed)
    regions = ["Nordeste", "Norte", "Centro-Oeste", "Sudeste", "Sul"]
    months = [201001 + 100 * (i // 12) + (i % 12) for i in range(n_months)]
    routes = [f"CT{i:02d}-CT{(i + 7) % n_routes:02d}" for i in range(n_routes)]
    frame = pd.DataFrame(
        [
            {
                "od": route,
                "ym": ym,
                "o_region": regions[index % len(regions)],
                "d_region": regions[(index + 2) % len(regions)],
            }
            for index, route in enumerate(routes)
            for ym in months
        ]
    )
    n = len(frame)
    instruments = {name: rng.uniform(0.2, 0.9, n) for name in specification.ALL_INSTRUMENTS}
    for name, values in instruments.items():
        frame[name] = values
    common_shock = rng.normal(size=n)
    frame["rthhi"] = np.clip(
        0.45
        + 0.30 * (instruments["h2_rthhi"] - 0.55)
        + 0.25 * (instruments["h1_maxcthhi"] - 0.55)
        + 0.05 * common_shock
        + 0.03 * rng.normal(size=n),
        0.2,
        1.0,
    )
    frame["maxcthhi"] = np.clip(
        0.40
        + 0.30 * (instruments["h3_maxcthhi"] - 0.55)
        + 0.20 * (instruments["h2_maxcthhi"] - 0.55)
        + 0.04 * common_shock
        + 0.02 * rng.normal(size=n),
        0.2,
        1.0,
    )
    frame["dailyflcong"] = rng.gamma(1.5, 1.2, n)
    frame["dailyflncong"] = rng.gamma(2.0, 3.0, n)
    frame["prwheather"] = rng.beta(2, 8, n)
    frame["princident"] = rng.beta(1, 80, n)
    frame["pr_connc"] = rng.beta(1, 40, n)
    frame["maxprdel"] = rng.beta(5, 15, n)
    frame["cshare"] = (rng.uniform(size=n) < 0.2).astype(float)
    frame["lcc"] = (rng.uniform(size=n) < 0.9).astype(float)
    frame["maxalccfu"] = (rng.uniform(size=n) < 0.99).astype(float)
    signal = (
        0.004 * frame["dailyflcong"]
        + 0.004 * frame["dailyflncong"]
        + 4.5 * frame["prwheather"]
        + 6.0 * frame["princident"]
        + 2.4 * frame["pr_connc"]
        + 1.5 * frame["maxprdel"]
        + 0.8 * frame["rthhi"]
        - 1.4 * frame["maxcthhi"]
    )
    noise = 0.4 * common_shock + 0.4 * rng.normal(size=n)
    frame["fsc_oddsarr"] = signal - 2.0 + noise
    frame["fsc_minsarr"] = 8.0 * signal + 4.0 * noise
    frame["fsc_minsp15arr"] = np.clip(frame["fsc_minsarr"], 0.0, None)
    frame["fsc_oddsdep"] = frame["fsc_oddsarr"] + 0.05 * rng.normal(size=n)
    frame["fsc_minsdep"] = frame["fsc_minsarr"] + 0.5 * rng.normal(size=n)
    frame["fsc_minsp15dep"] = np.clip(frame["fsc_minsdep"], 0.0, None)
    return frame[list(REQUIRED_COLUMNS)]


@pytest.fixture
def synthetic_panel(tmp_path: Path) -> Path:
    path = tmp_path / "panel.parquet"
    make_panel().to_parquet(path, index=False)
    return path


# --------------------------------------------------------------- the contract
def test_a_missing_panel_names_the_file_and_the_command(tmp_path: Path) -> None:
    with pytest.raises(ArticlePanelNotBuilt) as excinfo:
        loader.load_panel(tmp_path / "nowhere.parquet")
    message = str(excinfo.value)
    assert "nowhere.parquet" in message
    assert "airline-delays article-panel" in message


def test_an_incomplete_panel_is_refused_naming_every_missing_column(tmp_path: Path) -> None:
    path = tmp_path / "panel.parquet"
    make_panel(n_routes=8, n_months=8).drop(
        columns=["rthhi", "h2_rthhi", "fsc_minsdep"]
    ).to_parquet(path, index=False)
    with pytest.raises(PanelIncomplete) as excinfo:
        loader.load_panel(path)
    message = str(excinfo.value)
    for name in ("rthhi", "h2_rthhi", "fsc_minsdep"):
        assert name in message
    assert "REQUIRED_COLUMNS" in message


def test_required_columns_are_unique_and_cover_the_specification() -> None:
    assert len(REQUIRED_COLUMNS) == len(set(REQUIRED_COLUMNS))
    for block in (
        specification.EXOG_FULL,
        specification.ENDOG,
        specification.ARRIVAL_REGRESSANDS,
        specification.DEPARTURE_REGRESSANDS,
    ):
        assert set(block) <= set(REQUIRED_COLUMNS)
    assert set(specification.INSTRUMENTS_ODDS) | set(specification.INSTRUMENTS_MINS) <= set(
        REQUIRED_COLUMNS
    )


# ------------------------------------------------------------ the whole path
def test_sample_filters_and_dummies_on_a_synthetic_panel(synthetic_panel: Path) -> None:
    sample = build_sample(synthetic_panel)
    filters = sample.attrs["filters"]
    assert filters["n_after_singleton_cut"] == len(sample)
    assert filters["routes"] == sample["od"].nunique()
    assert filters["window"] == [loader.FIRST_YM, loader.LAST_YM]
    # The dummies are rebuilt, not read: 144 time columns and 60 seasonality ones.
    assert all(name in sample.columns for name in loader.TIME_DUMMIES)
    assert all(name in sample.columns for name in loader.SEASONALITY)
    # Every row sits in exactly one month, and touches one or two regions.
    assert sample[list(loader.TIME_DUMMIES)].to_numpy().sum(axis=1).max() == 1
    assert set(np.unique(sample[list(loader.SEASONALITY)].to_numpy().sum(axis=1))) <= {1.0, 2.0}


def test_table2_runs_on_a_synthetic_panel(synthetic_panel: Path) -> None:
    result = table2.run(synthetic_panel)
    assert result["missing_variables"] == []
    assert set(result["univariate"]) == {"mean", "sd", "min", "max"}
    for name in result["variables"]:
        assert result["univariate"]["min"][name] <= result["univariate"]["max"][name]
        assert result["correlation"][name][name] == pytest.approx(1.0)


def test_table3_column_1_runs_on_a_synthetic_panel(synthetic_panel: Path) -> None:
    result = table3.run(synthetic_panel, columns=[1])["columns"]["1"]
    assert result["estimator"] == "gmm2s"
    assert result["regressand"] == "fsc_oddsarr"
    assert set(result["b"]) == set(specification.EXOG_PARTIAL) | set(specification.ENDOG)
    assert all(np.isfinite(value) for value in result["b"].values())
    assert all(value > 0 for value in result["se"].values())
    stats = result["stats"]
    # 5 excluded instruments, 2 endogenous regressors: J has 3 df, rk has 4.
    assert stats["j_df"] == 3
    assert stats["kp_df"] == 4
    assert stats["n_obs"] == 40 * 36
    assert 0.0 < stats["adj_r2"] < 1.0
    assert np.isfinite(stats["kp_lm"]) and stats["kp_lm"] > 0
    assert stats["f_stat"] is None  # not the same quantity as ivreg2's; left empty


# ------------------------------------------------------- the article's panel
class TestTheArticlePanel:
    """The committed panel, through the do-files' filters."""

    @pytest.fixture(scope="class")
    def arrival_sample(self) -> pd.DataFrame:
        loader._PANEL_CACHE.clear()
        return build_sample(ARTICLE_PANEL_PATH, filter_regressand="fsc_oddsarr")

    def test_the_filters_give_the_published_estimation_sample(self, arrival_sample) -> None:
        filters = arrival_sample.attrs["filters"]
        assert filters["n_raw"] == 24_589
        assert filters["routes_raw"] == 209
        assert filters["n_outside_window"] == 0
        assert filters["n_after_missing_regressand"] == 20_655
        assert filters["n_after_singleton_cut"] == 20_630
        assert filters["routes"] == 190
        assert filters["months"] == 144

    def test_table_2_computes_all_thirteen_variables(self, arrival_sample) -> None:
        result = table2.run(ARTICLE_PANEL_PATH, sample=arrival_sample)
        assert len(result["variables"]) == 13
        assert result["missing_variables"] == []
        assert result["empty_variables"] == []

    def test_the_departure_filter_gives_table_7_its_own_sample(self) -> None:
        loader._PANEL_CACHE.clear()
        departures = build_sample(ARTICLE_PANEL_PATH, filter_regressand="fsc_oddsdep")
        assert departures.attrs["filters"]["n_after_singleton_cut"] == 20_627
