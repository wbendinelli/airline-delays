"""The article's estimation panel (ADR-0020): registry, files, manifest and invariants.

The panel is committed, so everything here runs in CI without the source base.
The curation itself is exercised end to end on a small synthetic Stata file.
"""

from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from airline_delays.definitions import nodes
from airline_delays.estimation import article_panel as ap
from airline_delays.estimation.loader import REGIONS
from airline_delays.estimation.specification import REQUIRED_COLUMNS
from airline_delays.schema import ARTICLE_PANEL, validate_schema

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def panel() -> pd.DataFrame:
    return pd.read_parquet(ap.PARQUET)


@pytest.fixture(scope="module")
def manifest() -> dict:
    return json.loads(ap.MANIFEST.read_text(encoding="utf-8"))


class TestTheRegistryLayer:
    def test_fifty_two_columns_with_distinct_bilingual_definitions(self) -> None:
        names = [column.name for column in ARTICLE_PANEL]
        assert len(names) == 52
        assert len(set(names)) == 52
        for column in ARTICLE_PANEL:
            assert column.layer == "article_panel"
            assert column.definition_en and column.definition_pt
            assert column.definition_en != column.definition_pt
            assert column.public

    def test_the_layer_covers_the_estimation_contract(self) -> None:
        assert set(REQUIRED_COLUMNS) <= set(ap.COLUMNS)


class TestTheCommittedFiles:
    def test_shape_order_and_schema(self, panel: pd.DataFrame) -> None:
        assert list(panel.columns) == list(ap.COLUMNS)
        assert panel.shape == (24_589, 52)
        validate_schema(panel, ARTICLE_PANEL)

    def test_the_key_is_unique_and_sorted(self, panel: pd.DataFrame) -> None:
        assert not panel.duplicated(["od", "ym"]).any()
        assert panel[["od", "ym"]].equals(panel[["od", "ym"]].sort_values(["od", "ym"]))
        assert panel["od"].nunique() == 209
        assert panel["ym"].between(200201, 201312).all()
        assert panel["ym"].nunique() == 144

    def test_the_invariants_of_the_article_hold(self, panel: pd.DataFrame) -> None:
        assert (panel["od"] == panel["o"] + "-" + panel["d"]).all()
        assert set(panel["o"]).union(panel["d"]) <= set(nodes.PANEL_NODES)
        assert set(panel["o_region"]).union(panel["d_region"]) <= set(REGIONS.values())
        assert (panel["ym"] == panel["year"].astype("int32") * 100 + panel["month"]).all()
        assert (panel["lcc"] == np.maximum(panel["pres_glo"], panel["pres_azu"])).all()
        assert (panel["maxalccfu"] == np.maximum(panel["olccfu"], panel["dlccfu"])).all()
        assert np.allclose(panel["prcanc"], panel["fl_can"] / panel["f"], atol=1e-6)

    def test_the_csv_round_trips_to_the_parquet(self, panel: pd.DataFrame) -> None:
        with gzip.open(ap.CSV, "rt", encoding="utf-8") as handle:
            csv = pd.read_csv(
                handle, dtype={c.name: c.dtype for c in ARTICLE_PANEL if c.dtype == "string"}
            )
        assert list(csv.columns) == list(panel.columns)
        assert len(csv) == len(panel)
        for column in ARTICLE_PANEL:
            if column.dtype == "string":
                assert (csv[column.name].astype("string") == panel[column.name]).all(), column.name
            elif column.dtype.startswith("int"):
                assert (csv[column.name].to_numpy() == panel[column.name].to_numpy()).all(), (
                    column.name
                )
            else:
                expected = panel[column.name].to_numpy(dtype="float32")
                got = csv[column.name].to_numpy(dtype="float32")
                both_null = np.isnan(expected) & np.isnan(got)
                assert np.array_equal(expected[~both_null], got[~both_null]), column.name

    def test_the_manifest_describes_the_files_exactly(
        self, panel: pd.DataFrame, manifest: dict
    ) -> None:
        assert manifest["layer"] == "article_panel"
        assert manifest["rows"] == len(panel) == 24_589
        assert manifest["columns"] == 52
        assert manifest["routes"] == 209
        assert manifest["months"] == 144
        assert manifest["ym_range"] == [200201, 201312]
        for name, expected in manifest["nulls"].items():
            assert int(panel[name].isna().sum()) == expected, name
        assert all(not panel[c].isna().any() for c in panel.columns if c not in manifest["nulls"])
        for filename, entry in manifest["files"].items():
            path = ap.PARQUET.parent / filename
            assert path.stat().st_size == entry["bytes"], filename
            assert hashlib.sha256(path.read_bytes()).hexdigest() == entry["sha256"], filename

    def test_the_manifest_records_provenance_without_a_path(self, manifest: dict) -> None:
        source = manifest["source"]
        assert len(source["sha256"]) == 64
        assert source["stata_header_timestamp"].startswith("2015-12-03")
        assert source["variables_in_source"] == 1_829
        assert source["rows_in_source"] == 24_589
        text = json.dumps(manifest)
        assert "/Users/" not in text and "/Volumes/" not in text
        assert manifest["curation"]["git_commit"] != "UNCOMMITTED"


class TestTheCuration:
    def test_build_curates_a_synthetic_stata_file_end_to_end(self, tmp_path: Path) -> None:
        rng = np.random.default_rng(7)
        n = 30
        frame = pd.DataFrame(
            {name: rng.uniform(0.05, 0.95, n).astype("float32") for name in ap.COLUMNS}
        )
        o = ["SBBR"] * 15 + ["MRSP"] * 15
        d = ["MRSP"] * 15 + ["SBBR"] * 15
        frame["o"], frame["d"] = o, d
        frame["od"] = [f"{a}-{b}" for a, b in zip(o, d, strict=True)]
        frame["o_uf"], frame["d_uf"] = ["DF"] * 15 + ["SP"] * 15, ["SP"] * 15 + ["DF"] * 15
        frame["o_region"] = ["Centro-Oeste"] * 15 + ["Sudeste"] * 15
        frame["d_region"] = ["Sudeste"] * 15 + ["Centro-Oeste"] * 15
        months = [(2005, m) for m in range(1, 13)] + [(2006, m) for m in range(1, 4)]  # 15 months
        year = np.array([y for y, _ in months] * 2)
        month = np.array([m for _, m in months] * 2)
        frame["year"], frame["month"] = year.astype("int16"), month.astype("int8")
        frame["ym"] = (year * 100 + month).astype("float64")
        frame["km"] = np.int16(870)
        frame["ndays"] = np.int8(30)
        for name in ("f", "fl_can", "fl_odel", "fl_ddel"):
            frame[name] = rng.integers(10, 400, n).astype("float64")
        frame["prcanc"] = (frame["fl_can"] / frame["f"]).astype("float32")
        for name in ("pres_glo", "pres_azu", "pres_tam", "pres_web", "olccfu", "dlccfu", "cshare"):
            frame[name] = rng.integers(0, 2, n).astype("float32")
        frame["lcc"] = np.maximum(frame["pres_glo"], frame["pres_azu"])
        frame["maxalccfu"] = np.maximum(frame["olccfu"], frame["dlccfu"])
        frame["junk_1"] = rng.normal(size=n)
        frame["fe_k_1"] = 1.0
        frame = frame.sample(frac=1.0, random_state=1).reset_index(drop=True)  # unsorted on purpose
        source = tmp_path / "base.dta"
        frame.to_stata(source, write_index=False)

        result = ap.build(source, tmp_path / "out")
        out = pd.read_parquet(result.parquet)
        assert list(out.columns) == list(ap.COLUMNS)
        assert len(out) == n and result.rows == n and result.routes == 2
        assert (
            out["ym"].dtype == "int32" and out["f"].dtype == "int32" and out["lcc"].dtype == "int8"
        )
        assert out[["od", "ym"]].equals(out[["od", "ym"]].sort_values(["od", "ym"]))
        manifest = json.loads(result.manifest.read_text(encoding="utf-8"))
        assert manifest["rows"] == n and manifest["columns"] == 52
        assert str(tmp_path) not in json.dumps(manifest)
        assert "base.dta" not in json.dumps(manifest)

    def test_a_lossy_cast_stops_the_curation(self) -> None:
        frame = pd.DataFrame({name: [0.5, 0.25] for name in ap.COLUMNS})
        frame["f"] = [1.5, 2.0]  # not an integer count
        with pytest.raises(ValueError, match="not lossless"):
            ap.curate(frame)
