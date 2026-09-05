"""ADR-0014: is the committed panel still what today's code builds?

`data/analysis/*.parquet` and `*.csv.gz` are tracked so a reviewer can run the
public replication without rebuilding. The risk of tracking a generated table
is that it goes stale -- someone edits `schema.py` or `panel.py` (an ADR-0013
rename, say) and forgets to run `just panel` before committing. This module
rebuilds the panel from the *committed* fact table, in memory, and diffs it
against the *committed* panel: a stale commit fails it.

Marked `analysis` (registered in `pyproject.toml`, run by `just check-analysis`
and by a plain `pytest -q` alongside everything else). It skips rather than fails when its inputs are not on
disk: CI's ordinary job has no `data/staged/` and therefore no `data/derived/`
(ADR-0004, `CLAUDE.md`), so the rebuild this test performs cannot run there.
It runs wherever `just fact && just panel` has already been executed, which
is exactly where a stale second edit is possible.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:  # pragma: no cover - typing only
    import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
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
                "check -- run `just fact && just panel` first: missing "
                + ", ".join(str(path.relative_to(ROOT)) for path in missing)
            )
        import pandas as pd

        from airline_delays import panel as panel_mod

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
            "schema.py/panel.py build from the committed fact table -- run `just panel` "
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


@pytest.mark.analysis
class TestTheCommittedReplicationIsFresh:
    """`reports/replication/results.json` is what `airline-delays estimate` produces today.

    The article panel is in git, so this needs no local data layer: it re-estimates
    every table into a temporary directory (about 40 s) and compares every
    coefficient, standard error and statistic with the committed file, to six significant
    digits (an absolute floor of 1e-9 covers coefficients near zero, where the last digits
    differ between BLAS implementations).
    """

    def test_every_estimate_matches_the_committed_results(self, tmp_path: Path) -> None:
        import json
        import math

        from airline_delays.estimation import run as estimation_run

        committed = json.loads(
            (ROOT / "reports" / "replication" / "results.json").read_text(encoding="utf-8")
        )
        fresh = estimation_run.run(outdir=tmp_path, with_sensitivity=False)["results"]
        compared = 0
        for table in ("table2", "table3", "table4", "table5", "table6", "table7"):
            old, new = committed[table]["replicated"], fresh[table]["replicated"]
            if table == "table2":
                for statistic, values in old["univariate"].items():
                    for name, value in values.items():
                        assert new["univariate"][statistic][name] == pytest.approx(
                            value, rel=1e-6, abs=1e-9
                        )
                        compared += 1
                continue
            for column, old_column in old["columns"].items():
                new_column = new["columns"][column]
                for kind in ("b", "se"):
                    for name, value in old_column[kind].items():
                        assert new_column[kind][name] == pytest.approx(value, rel=1e-6, abs=1e-9), (
                            table,
                            column,
                            kind,
                            name,
                        )
                        compared += 1
                for name, value in old_column["stats"].items():
                    if isinstance(value, int | float) and not (
                        isinstance(value, float) and math.isnan(value)
                    ):
                        assert new_column["stats"][name] == pytest.approx(
                            value, rel=1e-6, abs=1e-9
                        ), (
                            table,
                            column,
                            name,
                        )
                        compared += 1
        assert compared > 1000
        assert fresh["meta"]["sample"]["n_after_singleton_cut"] == 20_630


@pytest.mark.analysis
class TestTheCommittedProjectionsAreNotStale:
    """`city_month.parquet` and `airline_city_month.parquet` are what `airline-delays fact` writes."""

    def test_the_two_projections_rebuild_from_the_committed_fact_table(self) -> None:
        import pandas as pd

        from airline_delays import fact as fact_mod

        day_hour_path = DERIVED_DIR / "node_day_hour.parquet"
        if not day_hour_path.exists():
            pytest.skip(f"{day_hour_path} is absent (run `just fact` first)")
        fact = pd.read_parquet(ANALYSIS_DIR / "fact_group_route_month.parquet")
        day_hour = pd.read_parquet(day_hour_path)
        city = fact_mod.slim(fact_mod.city_month(fact, day_hour))
        airline_city = fact_mod.slim(
            fact_mod.add_hub(fact_mod.aggregate(fact, "airline_city_month"))
        )
        for rebuilt, name in ((city, "city_month"), (airline_city, "airline_city_month")):
            committed = pd.read_parquet(ANALYSIS_DIR / f"{name}.parquet")
            assert rebuilt.shape == committed.shape, name
            assert list(rebuilt.columns) == list(committed.columns), name
            assert _checksum(rebuilt) == _checksum(committed), name


@pytest.mark.analysis
class TestOneYearOfTheFactTableRebuilds:
    """One calendar year of the fact table, rebuilt from `data/staged`, equals the committed slice."""

    YEAR = 2012

    def test_the_year_matches_the_committed_fact_table(self, tmp_path: Path) -> None:
        import pandas as pd

        from airline_delays import fact as fact_mod

        staged = ROOT / "data" / "staged"
        if not (staged / f"year={self.YEAR}").exists():
            pytest.skip(f"data/staged/year={self.YEAR} is absent (run `just stage` first)")
        analysis, derived = tmp_path / "analysis", tmp_path / "derived"
        fact_mod.build_fact(
            staged,
            analysis,
            derived,
            years=(self.YEAR,),
            groups_path=EXTERNAL_DIR / "groups.csv",
            verbose=False,
        )
        rebuilt = pd.read_parquet(analysis / "fact_group_route_month.parquet")
        committed = pd.read_parquet(ANALYSIS_DIR / "fact_group_route_month.parquet")
        committed = committed[committed["ym"] // 100 == self.YEAR]
        # Entry and exit flags look at the neighbouring years, which a one-year build
        # does not see; everything else is a function of the year's own flights.
        columns = [c for c in committed.columns if c not in {"is_entry", "is_exit"}]
        keys = list(fact_mod.FACT_UNIQUE_KEY)
        left = rebuilt[columns].sort_values(keys).reset_index(drop=True)
        right = committed[columns].sort_values(keys).reset_index(drop=True)
        assert len(left) == len(right)
        pd.testing.assert_frame_equal(left, right, check_dtype=False, check_categorical=False)
