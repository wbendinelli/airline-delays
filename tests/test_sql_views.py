"""`sql/views.sql`: every view builds over the committed tables; the flight views need `data/staged`."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SQL = ROOT / "sql" / "views.sql"
COMMITTED_VIEWS = (
    "v_fact",
    "v_panel",
    "v_panel_article",
    "v_city",
    "v_airline_city",
    "v_hubs",
    "v_groups",
    "v_cause_codes",
    "v_nodes",
    "v_distances",
)


def _statements() -> list[str]:
    text = SQL.read_text(encoding="utf-8")
    text = re.sub(r"--[^\n]*", "", text)
    return [s.strip() for s in text.split(";") if s.strip()]


def test_the_file_defines_eighteen_views() -> None:
    names = re.findall(r"CREATE OR REPLACE VIEW (\w+)", SQL.read_text(encoding="utf-8"))
    assert len(names) == 18
    assert len(set(names)) == 18


def test_every_view_over_committed_data_builds_and_returns_rows() -> None:
    import duckdb

    staged_present = any((ROOT / "data" / "staged").glob("year=*/*.parquet"))
    con = duckdb.connect()
    con.execute(f"SET file_search_path = '{ROOT}'")
    failed: dict[str, str] = {}
    for statement in _statements():
        match = re.search(r"CREATE OR REPLACE VIEW (\w+)", statement)
        if not match:
            con.execute(statement)
            continue
        name = match.group(1)
        try:
            con.execute(statement)
        except duckdb.Error as exc:  # a flight view without data/staged
            failed[name] = str(exc)
    if staged_present:
        assert failed == {}, failed
    else:
        assert all("staged" in message or "No files" in message for message in failed.values()), (
            failed
        )
    for name in COMMITTED_VIEWS:
        assert name not in failed, failed.get(name)
        rows = con.execute(f"SELECT count(*) FROM {name}").fetchone()[0]
        assert rows > 0, name
