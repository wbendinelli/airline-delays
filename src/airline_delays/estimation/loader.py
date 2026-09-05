"""Loading the estimation panel and rebuilding its dummies.

One source, one code path: the article's estimation panel,
``data/analysis/article_panel_route_month.parquet`` (ADR-0020), curated from the
authors' final base by :mod:`airline_delays.estimation.article_panel`. Another
route-month panel can be passed by path, provided it carries every column of
:data:`~airline_delays.estimation.specification.REQUIRED_COLUMNS`; a panel that
lacks one is refused by :class:`PanelIncomplete`, which names the columns. A
column that measures something *near* a published variable is not a
substitute, so no alias or proxy is ever mapped in.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from airline_delays import paths
from airline_delays.estimation.specification import REQUIRED_COLUMNS

ARTICLE_PANEL_PATH: Path = paths.ANALYSIS / "article_panel_route_month.parquet"
ARTICLE_PANEL_MANIFEST: Path = paths.ANALYSIS / "article_panel_manifest.json"


class ArticlePanelNotBuilt(FileNotFoundError):
    """The estimation panel is not on disk."""


class PanelIncomplete(ValueError):
    """The panel exists but does not carry every column the tables need."""


#: Region codes of the `sz_*` dummies -> the region names carried by the panel.
REGIONS: dict[str, str] = {
    "ne": "Nordeste",
    "no": "Norte",
    "co": "Centro-Oeste",
    "se": "Sudeste",
    "su": "Sul",
}
SEASONALITY: tuple[str, ...] = tuple(
    f"sz_{code}_m_{month}" for code in REGIONS for month in range(1, 13)
)
FIRST_YM = 200201
LAST_YM = 201312
N_PERIODS = 144
TIME_DUMMIES: tuple[str, ...] = tuple(f"t_{i}" for i in range(1, N_PERIODS + 1))

_PANEL_CACHE: dict[str, pd.DataFrame] = {}


def resolve_panel(panel: Path | str | None = None) -> Path:
    """The panel file to estimate on: the committed article panel unless a path is given."""
    return Path(panel).expanduser() if panel is not None else ARTICLE_PANEL_PATH


def read_panel(path: Path) -> pd.DataFrame:
    """The contract columns of a route-month panel, before any dummy or filter."""
    if not path.exists():
        raise ArticlePanelNotBuilt(
            f"the estimation panel is not on disk: {path} does not exist. The article's "
            "panel is committed as data/analysis/article_panel_route_month.parquet; rebuild it "
            "with `airline-delays article-panel --source <the authors' base>`, or pass "
            "another route-month panel with `--panel`."
        )
    frame = pd.read_parquet(path)
    missing = [name for name in REQUIRED_COLUMNS if name not in frame.columns]
    if missing:
        raise PanelIncomplete(
            f"{path} does not carry every column of the estimation contract; missing: "
            f"{missing}. The contract is airline_delays.estimation.specification."
            "REQUIRED_COLUMNS, the article's own variable names. A near-equivalent column is "
            "not a substitute."
        )
    frame = frame.loc[:, list(REQUIRED_COLUMNS)].copy()
    frame["ym"] = frame["ym"].astype(int)
    frame.attrs["panel_path"] = str(path)
    return frame


def load_panel(panel: Path | str | None = None) -> pd.DataFrame:
    """The raw route-month panel, before any sample filter, with the dummies attached."""
    path = resolve_panel(panel)
    key = str(path.resolve())
    if key in _PANEL_CACHE:
        return _PANEL_CACHE[key]
    frame = read_panel(path)
    attrs = dict(frame.attrs)
    frame = frame.replace([np.inf, -np.inf], np.nan)
    frame = add_dummies(frame)
    frame.attrs.update(attrs)
    _PANEL_CACHE[key] = frame
    return frame


def add_dummies(frame: pd.DataFrame) -> pd.DataFrame:
    """Attach ``t_1..t_144`` and the 60 ``sz_*`` region x month dummies.

    Both are rebuilt from ``ym``, ``o_region`` and ``d_region`` rather than
    shipped with the panel. Verified against the 60 stored ``sz_*`` columns and
    the 144 stored ``t_*`` columns of the authors' base: exact agreement on all
    24,589 rows.
    """
    frame = frame.copy()
    year, month = np.divmod(frame["ym"].to_numpy(dtype=np.int64), 100)
    period = (year - FIRST_YM // 100) * 12 + month
    frame["_period"] = period
    time_block = {
        name: (period == index).astype(np.float64)
        for index, name in enumerate(TIME_DUMMIES, start=1)
    }
    origin = frame["o_region"].to_numpy()
    destination = frame["d_region"].to_numpy()
    season_block = {
        f"sz_{code}_m_{m}": (((origin == name) | (destination == name)) & (month == m)).astype(
            np.float64
        )
        for code, name in REGIONS.items()
        for m in range(1, 13)
    }
    return pd.concat([frame, pd.DataFrame(time_block | season_block, index=frame.index)], axis=1)
