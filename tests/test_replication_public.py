"""The public path of the replication: no private data, no manual editing to enable it.

The tables have to run on ``data/analysis/panel_route_month.parquet`` whatever
state that panel is in, and the ways it can fall short have to be *reported*
rather than papered over. Five things are checked:

1. asking for the public panel while the file is absent fails with a message
   that names the path and says what to do, not with a ``KeyError`` deep inside
   pandas;
2. a panel that exists but lacks model variables still loads, records exactly
   what it lacks, and refuses the columns that need them, naming them;
3. a panel that spells the route key ``route`` instead of ``od`` is accepted --
   a synonym is not a substitution, and a proxy for a model variable is;
4. Table 2 and Table 3 column 1 run end to end on a synthetic panel built to the
   contract -- sample filters, route and time dummies, seasonality dummies,
   collinearity pruning, 2SGMM with the HAC kernel, Hansen J, Kleibergen-Paap;
5. if a real public panel is present (the fixture one, or the one under
   ``data/analysis/``), the sample filters and Table 2 run on it, and Table 3
   either runs or names what the panel still owes.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from replication import common, table2, table3  # noqa: E402
from replication.common import (  # noqa: E402
    PANEL_PATH_VAR,
    REQUIRED_COLUMNS,
    PublicPanelIncomplete,
    PublicPanelNotBuilt,
    Source,
    build_sample,
)

FIXTURE_PANEL = ROOT / "tests" / "fixtures" / "panel_route_month_sample.parquet"


@pytest.fixture(autouse=True)
def _clear_panel_cache() -> None:
    """The loader caches by (source, path); tests move the path around."""
    common._PANEL_CACHE.clear()


def make_public_panel(
    n_routes: int = 40, n_months: int = 36, *, seed: int = 20260905
) -> pd.DataFrame:
    """A synthetic route-month panel that satisfies :data:`REQUIRED_COLUMNS`.

    Not realistic data -- realistic *shape*: an unbalanced-capable panel of
    directed city pairs over consecutive months inside the article's 2002-2013
    window, with a first stage strong enough that the IV columns identify.
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

    instruments = {name: rng.uniform(0.2, 0.9, n) for name in common.ALL_INSTRUMENTS}
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
def public_panel(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "panel_route_month.parquet"
    make_public_panel().to_parquet(path, index=False)
    monkeypatch.setenv(PANEL_PATH_VAR, str(path))
    return path


# --------------------------------------------------------------- the contract
def test_public_panel_reports_that_it_is_not_built_yet(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(PANEL_PATH_VAR, raising=False)
    if common.public_panel_path().exists():
        pytest.skip("the public panel exists on this machine; nothing to report as missing")
    with pytest.raises(PublicPanelNotBuilt) as excinfo:
        common.load_panel(Source.PUBLIC)
    message = str(excinfo.value)
    assert "not built yet" in message
    assert str(common.PUBLIC_PANEL_PATH) in message
    assert "just panel" in message


def test_incomplete_public_panel_records_every_missing_column(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A panel missing model variables still loads; what it lacks is recorded, not guessed."""
    path = tmp_path / "panel_route_month.parquet"
    make_public_panel(n_routes=8, n_months=8).drop(
        columns=["rthhi", "h2_rthhi", "fsc_minsdep"]
    ).to_parquet(path, index=False)
    monkeypatch.setenv(PANEL_PATH_VAR, str(path))
    panel = common.load_panel(Source.PUBLIC)
    assert set(panel.attrs["missing_contract_columns"]) == {"rthhi", "h2_rthhi", "fsc_minsdep"}
    # ...and a column that needs one of them refuses, naming it.
    with pytest.raises(PublicPanelIncomplete) as excinfo:
        table3.run(Source.PUBLIC, columns=[1])
    assert "rthhi" in str(excinfo.value)


def test_public_panel_without_a_route_key_cannot_be_read_at_all(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "panel_route_month.parquet"
    make_public_panel(n_routes=8, n_months=8).drop(columns=["od"]).to_parquet(path, index=False)
    monkeypatch.setenv(PANEL_PATH_VAR, str(path))
    with pytest.raises(PublicPanelIncomplete) as excinfo:
        common.load_panel(Source.PUBLIC)
    assert "REQUIRED_COLUMNS" in str(excinfo.value)


def test_a_panel_that_spells_the_route_key_route_is_accepted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`route` is a synonym for `od`; a proxy for a model variable never is."""
    path = tmp_path / "panel_route_month.parquet"
    make_public_panel(n_routes=10, n_months=12).rename(columns={"od": "route"}).to_parquet(
        path, index=False
    )
    monkeypatch.setenv(PANEL_PATH_VAR, str(path))
    assert "od" in common.load_panel(Source.PUBLIC).columns


def test_required_columns_are_unique_and_cover_the_specification() -> None:
    assert len(REQUIRED_COLUMNS) == len(set(REQUIRED_COLUMNS))
    for block in (common.EXOG_FULL, common.ENDOG, common.ARRIVAL_REGRESSANDS):
        assert set(block) <= set(REQUIRED_COLUMNS)
    assert set(common.INSTRUMENTS_ODDS) | set(common.INSTRUMENTS_MINS) <= set(REQUIRED_COLUMNS)


# ------------------------------------------------------- the whole public path
def test_sample_filters_run_on_the_public_panel(public_panel: Path) -> None:
    sample = build_sample(Source.PUBLIC)
    filters = sample.attrs["filters"]
    assert filters["source"] == "public"
    assert filters["n_after_singleton_cut"] == len(sample)
    assert filters["routes"] == sample["od"].nunique()
    # The dummies are rebuilt, not read: 144 time columns and 60 seasonality ones.
    assert all(name in sample.columns for name in common.TIME_DUMMIES)
    assert all(name in sample.columns for name in common.SEASONALITY)
    # Every row sits in exactly one month, and touches one or two regions.
    assert sample[list(common.TIME_DUMMIES)].to_numpy().sum(axis=1).max() == 1
    assert set(np.unique(sample[list(common.SEASONALITY)].to_numpy().sum(axis=1))) <= {1.0, 2.0}


def test_table2_runs_on_the_public_panel(public_panel: Path) -> None:
    result = table2.run(Source.PUBLIC)
    assert result["missing_variables"] == []
    assert set(result["univariate"]) == {"mean", "sd", "min", "max"}
    for name in result["variables"]:
        assert result["univariate"]["min"][name] <= result["univariate"]["max"][name]
        assert result["correlation"][name][name] == pytest.approx(1.0)


def test_table3_column_1_runs_on_the_public_panel(public_panel: Path) -> None:
    result = table3.run(Source.PUBLIC, columns=[1])["columns"]["1"]
    assert result["estimator"] == "gmm2s"
    assert result["regressand"] == "fsc_oddsarr"
    assert set(result["b"]) == set(common.EXOG_PARTIAL) | set(common.ENDOG)
    assert all(np.isfinite(value) for value in result["b"].values())
    assert all(value > 0 for value in result["se"].values())
    stats = result["stats"]
    # 5 excluded instruments, 2 endogenous regressors: J has 3 df, rk has 4.
    assert stats["j_df"] == 3
    assert stats["kp_df"] == 4
    assert stats["n_obs"] == 40 * 36
    assert 0.0 < stats["adj_r2"] < 1.0
    assert np.isfinite(stats["kp_lm"]) and stats["kp_lm"] > 0
    assert stats["f_stat"] is None  # declared difference, never guessed


def test_the_public_path_needs_no_private_directory(
    public_panel: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv(common.PRIVATE_DIR_VAR, raising=False)
    assert table3.run(Source.PUBLIC, columns=[1])["columns"]["1"]["stats"]["n_obs"] > 0


# ------------------------------------------------- and on a real panel, if any
def _real_panel() -> Path | None:
    for candidate in (FIXTURE_PANEL, common.PUBLIC_PANEL_PATH):
        if candidate.exists():
            return candidate
    return None


def test_sample_and_table2_run_on_the_real_public_panel_when_it_exists(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Whatever the real panel carries today has to load, filter and describe cleanly."""
    panel = _real_panel()
    if panel is None:
        pytest.skip(
            "no public panel yet: neither tests/fixtures/panel_route_month_sample.parquet "
            f"nor {common.PUBLIC_PANEL_PATH} exists"
        )
    monkeypatch.setenv(PANEL_PATH_VAR, str(panel))
    sample = build_sample(Source.PUBLIC)
    filters = sample.attrs["filters"]
    assert len(sample) > 0
    # The article's panel is 2002m1-2013m12; anything wider is cut, not absorbed.
    assert filters["window"] == [common.FIRST_YM, common.LAST_YM]
    assert sample["ym"].between(common.FIRST_YM, common.LAST_YM).all()
    descriptives = table2.run(Source.PUBLIC, sample=sample)
    assert descriptives["variables"], "the panel carries none of the 13 published variables"
    for name in descriptives["variables"]:
        assert descriptives["correlation"][name][name] == pytest.approx(1.0)
    # Columns present but entirely null are named, not reported as NaN statistics.
    assert set(descriptives["empty_variables"]).isdisjoint(descriptives["variables"])


def test_table3_on_the_real_public_panel_either_runs_or_says_what_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The IV columns need variables the VRA alone cannot yield (codeshare, the
    Hausman instruments, the seat-weighted HHIs). Until the panel carries them,
    the correct behaviour is a message naming them -- never a near-equivalent
    column quietly standing in for the published one."""
    panel = _real_panel()
    if panel is None:
        pytest.skip("no public panel yet")
    monkeypatch.setenv(PANEL_PATH_VAR, str(panel))
    sample = build_sample(Source.PUBLIC)
    try:
        column = table3.run(Source.PUBLIC, sample=sample, columns=[1])["columns"]["1"]
    except PublicPanelIncomplete as exc:
        missing = sample.attrs["filters"]["missing_contract_columns"]
        assert missing, "an incomplete-panel error must come with the list of what is missing"
        assert any(name in str(exc) for name in missing)
        return
    assert column["stats"]["n_obs"] > 0
    assert np.isfinite(column["stats"]["kp_lm"])
