"""`scripts/monograph_airports.py` counts the 2013 airport list, and does not invent it.

The table under test is ``data/external/monograph_airports.csv``: 38 rows
transcribed verbatim from the Lista de Siglas of the author's 2013
undergraduate monograph, with a flag for the 37 that also appear in its Tables
3 and 4. Everything the script prints is a count over that table joined to
``data/external/nodes.csv``; the assertions below pin the counts so a silent
edit to either CSV fails here instead of in prose.
"""

from __future__ import annotations

import csv
import importlib.util
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "monograph_airports.py"
TABLE = ROOT / "data" / "external" / "monograph_airports.csv"


def _load():
    spec = importlib.util.spec_from_file_location("monograph_airports", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


script = _load()


def _table() -> list[dict[str, str]]:
    with TABLE.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class TestTheCounts:
    def test_the_three_airport_counts(self) -> None:
        summary = script.summarise()
        assert summary["listed"] == 38
        assert summary["in_tables_3_4"] == 37
        # Declared, never reconciled: the prose of section 5.2 says 36.
        assert summary["stated_in_text"] == 36
        assert summary["not_in_tables_3_4"] == ["SBPS"]

    def test_the_join_against_the_adr_0001_map(self) -> None:
        summary = script.summarise()
        assert summary["mapped"] == 31
        assert summary["nodes_covered"] == 27
        assert summary["nodes_total"] == 27
        assert summary["unmapped"] == [
            "SBJF",
            "SBJV",
            "SBLO",
            "SBPS",
            "SBRP",
            "SBSJ",
            "SBUL",
        ]


class TestTheTable:
    def test_every_row_is_grade_a(self) -> None:
        rows = _table()
        assert len(rows) == 38
        assert {row["confidence"] for row in rows} == {"A"}
        assert all(row["source"].strip() for row in rows)

    def test_the_four_annotated_codes_carry_a_note(self) -> None:
        notes = {row["icao"]: row["note"] for row in _table()}
        for icao in ("SBKP", "SBPJ", "SBNT", "SBPS"):
            assert notes[icao].strip(), icao

    def test_only_those_four_are_annotated(self) -> None:
        annotated = {row["icao"] for row in _table() if row["note"].strip()}
        assert annotated == {"SBKP", "SBPJ", "SBNT", "SBPS"}


class TestTheOutput:
    def test_it_prints_exactly_three_lines(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(SCRIPT)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert completed.returncode == 0, completed.stdout + completed.stderr
        printed = completed.stdout.splitlines()
        assert len(printed) == 3
        assert printed == script.lines()
        assert printed[0].startswith("monograph (2013): 38 airports")
        assert "(absent: SBPS)" in printed[0]
        assert "31 of 38 present -> 27 nodes (all 27 nodes covered)" in printed[1]
        assert printed[2] == "absent from the map (7): SBJF SBJV SBLO SBPS SBRP SBSJ SBUL"
