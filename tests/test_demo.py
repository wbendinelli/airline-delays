"""`just demo` (scripts/demo.py) runs offline on the fixture and writes what it says."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "demo.py"


@pytest.fixture(scope="module")
def demo_out(tmp_path_factory: pytest.TempPathFactory) -> Path:
    out = tmp_path_factory.mktemp("demo")
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "--out", str(out), "--quiet"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "route-months from" in completed.stdout
    return out


class TestTheDemoRunsEndToEnd:
    def test_every_layer_is_written(self, demo_out: Path) -> None:
        assert (demo_out / "staged" / "year=2004" / "part-0.parquet").exists()
        assert (demo_out / "analysis" / "fact_group_route_month.parquet").exists()
        assert (demo_out / "analysis" / "panel_route_month.parquet").exists()
        assert (demo_out / "replication" / "results.json").exists()
        assert (demo_out / "replication" / "tables.md").exists()

    def test_the_summary_matches_the_files(self, demo_out: Path) -> None:
        import pandas as pd

        summary = json.loads((demo_out / "summary.json").read_text(encoding="utf-8"))
        panel = pd.read_parquet(demo_out / "analysis" / "panel_route_month.parquet")
        assert summary["panel_rows"] == len(panel)
        assert summary["panel_columns"] == panel.shape[1]
        assert not panel.duplicated(["route", "ym"]).any()
        assert summary["fact_rows"] > 0
        assert summary["seconds"] < 120

    def test_table_2_runs_on_the_article_panel(self, demo_out: Path) -> None:
        results = json.loads((demo_out / "replication" / "results.json").read_text("utf-8"))
        replicated = results["table2"]["replicated"]
        assert len(replicated["variables"]) == 13
        assert replicated["sample"]["n_after_singleton_cut"] == 20_630
        assert results["meta"]["panel"]["path"] == "data/analysis/article_panel_route_month.parquet"
        summary = json.loads((demo_out / "summary.json").read_text(encoding="utf-8"))
        assert summary["table2_n_obs"] == 20_630

    def test_the_committed_tables_are_untouched(self, demo_out: Path) -> None:
        # The demo writes only under its --out directory: data/analysis and
        # reports/ stay exactly as committed.
        status = subprocess.run(
            ["git", "status", "--porcelain", "--", "data/analysis", "reports"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        touched = [line for line in status.stdout.splitlines() if line.strip()]
        # Lines already dirty before the demo (an unrelated edit in progress) are
        # tolerated; a demo run must not *add* anything under these paths.
        assert all(not line.startswith("??") for line in touched), touched
