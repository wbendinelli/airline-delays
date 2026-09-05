"""The benchmark comparison — skipped unless `AIRLINE_DELAYS_PRIVATE_DIR` is set.

Two kinds of test live here, and only the second reads the private directory.

The first kind exercises `replication/gabarito/compare.py` on synthetic frames,
so the guard that stops a benchmark value from reaching disk is tested in CI,
where the benchmark does not exist. The second kind, marked `gabarito`, runs the
real comparison and asserts that no column has regressed against the rates
measured when this pipeline was built. Those floors are a regression guard, not
a target: `EXPECTED` in `compare.py` still carries the 2019-vintage rates the
earlier reconstruction reported, and the gap between the two is the finding
recorded in `docs/declared-differences.md`.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
for candidate in (ROOT, ROOT / "src"):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from replication.gabarito import compare  # noqa: E402

MEASURED_FLOOR: dict[str, float] = {
    "f": 0.95,
    "fl_can": 0.94,
    "fl_odel": 0.87,
    "fscb_prdelarr": 0.64,
    "prwheather": 0.91,
    "princident": 0.95,
    "pr_connc": 0.94,
    "olccfu": 1.00,
    "dlccfu": 1.00,
    "maxalccfu": 1.00,
}
"""Stable-vintage rates measured when this pipeline was built, rounded down.

A regression floor: if a later change drops one of these, something broke. It is
deliberately *not* the same as `compare.EXPECTED`, which holds what the earlier
reconstruction measured against the 2019 vintage of the raw files.
"""


# ------------------------------------------------------------------ offline tests


class TestTheGuardsRunWithoutTheBenchmark:
    def test_a_missing_variable_is_a_clear_exit_not_a_traceback(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv(compare.PRIVATE_DIR_VAR, raising=False)
        with pytest.raises(SystemExit, match=compare.PRIVATE_DIR_VAR):
            compare.private_dir()

    def test_the_private_path_is_never_written_in_the_source(self) -> None:
        # The path lives in the shell, not in the repository (SECURITY.md).
        text = Path(compare.__file__).read_text(encoding="utf-8")
        assert "pesquisa-acervo" not in text
        assert "_recebidos" not in text

    def test_only_agreement_statistics_may_be_written(self) -> None:
        rates = pd.DataFrame(
            {
                "column": ["f"],
                "benchmark_column": ["f"],
                "definition": ["x"],
                "tolerance": [0.5],
                "n": [10],
                "rate": [1.0],
                "median_abs_diff": [0.0],
                "p90_abs_diff": [0.0],
                "n_stable_vintage": [5],
                "rate_stable_vintage": [1.0],
                "expected_rate": [0.975],
                "note": [""],
            }
        )
        compare.assert_no_values(rates)
        with pytest.raises(ValueError, match="not agreement statistics"):
            compare.assert_no_values(rates.assign(benchmark_value=[42.0]))

    def test_agreement_counts_only_comparable_rows(self) -> None:
        public = pd.Series([1.0, 2.0, None, 4.0])
        benchmark = pd.Series([1.0, 3.0, 3.0, None])
        measured = compare.agreement(public, benchmark, tolerance=0.5)
        assert measured["n"] == 2, "a row missing on either side is not a disagreement"
        assert measured["rate"] == 0.5
        assert measured["median_abs_diff"] == pytest.approx(0.5)

    def test_an_empty_overlap_reports_nothing_rather_than_dividing_by_zero(self) -> None:
        measured = compare.agreement(pd.Series([None]), pd.Series([None]), tolerance=0.5)
        assert measured == {
            "n": 0,
            "rate": None,
            "median_abs_diff": None,
            "p90_abs_diff": None,
            "n_stable_vintage": 0,
            "rate_stable_vintage": None,
        }

    def test_the_stable_vintage_split_reads_the_public_reconciliation_table(self) -> None:
        months = compare.stable_vintage_months()
        if months is None:
            pytest.skip("reports/reconciliation_by_month.csv not built yet")
        assert len(months) >= 60
        assert all(200001 <= month <= 201312 for month in months)

    def test_the_generated_block_is_replaced_in_place(self, tmp_path: Path) -> None:
        path = tmp_path / "declared-differences.md"
        path.write_text(
            f"# Head\n\nprose\n\n{compare.MARKER_START}\nold\n{compare.MARKER_END}\n\ntail\n",
            encoding="utf-8",
        )
        compare.update_declared_differences(
            path, f"{compare.MARKER_START}\nnew\n{compare.MARKER_END}"
        )
        text = path.read_text(encoding="utf-8")
        assert "prose" in text and "tail" in text and "new" in text
        assert "old" not in text
        assert text.count(compare.MARKER_START) == 1


# ------------------------------------------------------------------ gabarito tests


@pytest.fixture(scope="module")
def rates() -> pd.DataFrame:
    """The real comparison, run once for the whole module."""
    panel_path = ROOT / "data" / "analysis" / "panel_route_month.parquet"
    if not panel_path.exists():
        pytest.skip("the panel is not built; run `just features && just panel`")
    benchmark = compare.load_benchmark(
        compare.find_benchmark(compare.private_dir()),
        sorted({check.benchmark for check in compare.CHECKS}),
    )
    return compare.compare(compare.load_panel(panel_path), benchmark)


@pytest.mark.gabarito
class TestAgainstThePrivateBenchmark:
    def test_the_keys_line_up(self, rates: pd.DataFrame) -> None:
        assert int(rates.loc[rates["column"] == "ndays", "n"].iloc[0]) > 20_000
        assert float(rates.loc[rates["column"] == "ndays", "rate"].iloc[0]) == 1.0

    @pytest.mark.parametrize("column", sorted(MEASURED_FLOOR))
    def test_no_column_regressed_against_its_measured_rate(
        self, rates: pd.DataFrame, column: str
    ) -> None:
        row = rates[rates["column"] == column]
        assert len(row) == 1, column
        measured = row["rate_stable_vintage"].iloc[0]
        assert measured is not None
        assert measured >= MEASURED_FLOOR[column] - 1e-9, (
            f"{column}: {measured:.3f} below the floor {MEASURED_FLOOR[column]:.3f}"
        )

    def test_the_article_fsc_set_reproduces_better_than_the_fsc_class(
        self, rates: pd.DataFrame
    ) -> None:
        # The declared difference of ADR-0003 in one number: the benchmark's FSC
        # set excludes Avianca Brasil, which this repository classes as FSC.
        by_column = rates.set_index("column")["rate_stable_vintage"]
        assert by_column["fscb_prdelarr"] > by_column["fsc_prdelarr"]

    def test_taxas_is_written_without_a_single_benchmark_value(
        self, rates: pd.DataFrame, tmp_path: Path
    ) -> None:
        path = compare.write_rates(rates, tmp_path / "taxas.csv")
        written = pd.read_csv(path)
        assert set(written.columns) == set(rates.columns)
        assert len(written) == len(rates)


@pytest.mark.gabarito
def test_the_private_directory_is_readable_when_declared() -> None:
    assert os.environ.get(compare.PRIVATE_DIR_VAR)
    assert compare.find_benchmark(compare.private_dir()).exists()
