"""ADR-0014: is the committed panel still what today's code builds?

`data/analysis/*.parquet` and `*.csv.gz` are tracked so a reviewer can run the
public replication without rebuilding. The risk of tracking a generated table
is that it goes stale -- someone edits `registry.py` or `panel.py` (an ADR-0013
rename, say) and forgets to run `just panel` before committing. This module
rebuilds the panel from the *committed* fact table, in memory, and diffs it
against the *committed* panel: a stale commit fails it.

Marked `analysis` (registered in `pyproject.toml`, run by `just check-analysis`
and by a plain `pytest -q` alongside everything else -- unlike `gabarito`, it
needs no private data). It skips rather than fails when its inputs are not on
disk: CI's ordinary job has no `data/staged/` and therefore no `data/derived/`
(ADR-0004, `CLAUDE.md`), so the rebuild this test performs cannot run there.
It runs wherever `just features && just panel` has already been executed, which
is exactly where a stale second edit is possible.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:  # pragma: no cover - typing only
    import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

ANALYSIS_DIR = ROOT / "data" / "analysis"
DERIVED_DIR = ROOT / "data" / "derived"
EXTERNAL_DIR = ROOT / "data" / "external"

REQUIRED = (
    ANALYSIS_DIR / "fact_group_route_month.parquet",
    ANALYSIS_DIR / "panel_route_month.parquet",
    DERIVED_DIR / "route_month_context.parquet",
    DERIVED_DIR / "node_day_hour.parquet",
)


def _missing() -> tuple[Path, ...]:
    return tuple(path for path in REQUIRED if not path.exists())


def _checksum(frame: pd.DataFrame) -> int:
    """A single order-sensitive number, stable across an unchanged rebuild."""
    import pandas as pd

    return int(pd.util.hash_pandas_object(frame.reset_index(drop=True), index=False).sum())


@pytest.mark.analysis
class TestTheCommittedPanelIsNotStale:
    """`just check-analysis`: rebuild from the fact table, diff against git."""

    @staticmethod
    @pytest.fixture(scope="class")
    def rebuilt_and_committed() -> tuple[pd.DataFrame, pd.DataFrame]:
        missing = _missing()
        if missing:
            pytest.skip(
                "data/analysis/ or data/derived/ is incomplete for the ADR-0014 staleness "
                "check -- run `just features && just panel` first: missing "
                + ", ".join(str(path.relative_to(ROOT)) for path in missing)
            )
        import pandas as pd

        from vra import panel as panel_mod

        rebuilt, result = panel_mod.build_panel(
            ANALYSIS_DIR, DERIVED_DIR, external_dir=EXTERNAL_DIR, write=False
        )
        assert result is None, "write=False must never touch the committed files"
        committed = pd.read_parquet(ANALYSIS_DIR / "panel_route_month.parquet")
        return rebuilt, committed

    def test_the_shape_matches(
        self, rebuilt_and_committed: tuple[pd.DataFrame, pd.DataFrame]
    ) -> None:
        rebuilt, committed = rebuilt_and_committed
        assert rebuilt.shape == committed.shape, (
            f"panel_route_month.parquet is stale: rebuilding from the committed fact "
            f"table gives {rebuilt.shape}, the committed file is {committed.shape}. "
            "Run `just panel` and commit the result."
        )

    def test_the_columns_match(
        self, rebuilt_and_committed: tuple[pd.DataFrame, pd.DataFrame]
    ) -> None:
        rebuilt, committed = rebuilt_and_committed
        assert list(rebuilt.columns) == list(committed.columns), (
            "panel_route_month.parquet's columns have drifted from what the current "
            "registry.py/panel.py build from the committed fact table -- run `just panel` "
            "and commit the result."
        )

    def test_the_checksum_matches(
        self, rebuilt_and_committed: tuple[pd.DataFrame, pd.DataFrame]
    ) -> None:
        rebuilt, committed = rebuilt_and_committed
        assert _checksum(rebuilt) == _checksum(committed), (
            "panel_route_month.parquet's values have drifted from what the current code "
            "builds from the committed fact table -- run `just panel` and commit the result."
        )
