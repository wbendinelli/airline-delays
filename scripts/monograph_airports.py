#!/usr/bin/env python3
"""Count the airports of the author's 2013 undergraduate monograph against ADR-0001.

The source is Bendinelli (2013), *Efeitos da entrada de uma empresa aérea de
baixo custo na internalização das externalidades do congestionamento*
(undergraduate monograph, USP). The document is not redistributed here; what
is redistributed is one derived table,
``data/external/monograph_airports.csv``, transcribed verbatim from its "Lista
de Siglas" and annotated with whether each airport also appears in its Tables 3
and 4.

Three counts disagree in the document itself, and this script prints all three
rather than reconciling them: 38 airports in the Lista de Siglas, 37 in Tables 3
and 4, and "36 aeroportos" stated in the prose of section 5.2. The disagreement
is the finding — see ``docs/notes/monografia-2013.md`` section 2.

The join against ``data/external/nodes.csv`` says how much of the 2013 airport
set survives into this repository's 27-node panel (ADR-0001).

Usage: ``uv run python scripts/monograph_airports.py`` from the repository root.
"""

from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AIRPORTS = ROOT / "data" / "external" / "monograph_airports.csv"
NODES = ROOT / "data" / "external" / "nodes.csv"

# Section 5.2 of the monograph says "selecionaram-se 36 aeroportos"; the Lista
# de Siglas and Tables 3-4 give 38 and 37. Declared, never reconciled, so this
# is the one number here that is read from prose rather than counted from a row.
STATED_IN_TEXT = 36


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def summarise() -> dict:
    """Counts and code lists behind the three lines `main` prints."""
    airports = _rows(AIRPORTS)
    nodes = _rows(NODES)

    listed = [row["icao"] for row in airports]
    in_tables = [row["icao"] for row in airports if row["in_tables_3_4"] == "True"]
    not_in_tables = sorted(set(listed) - set(in_tables))

    node_of = {row["icao"]: row["node"] for row in nodes}
    mapped = sorted(icao for icao in listed if icao in node_of)
    unmapped = sorted(icao for icao in listed if icao not in node_of)
    covered = {node_of[icao] for icao in mapped}
    all_nodes = set(node_of.values())

    return {
        "listed": len(listed),
        "in_tables_3_4": len(in_tables),
        "not_in_tables_3_4": not_in_tables,
        "stated_in_text": STATED_IN_TEXT,
        "mapped": len(mapped),
        "unmapped": unmapped,
        "nodes_covered": len(covered),
        "nodes_total": len(all_nodes),
    }


def lines() -> list[str]:
    """The three lines, in the order `main` prints them."""
    summary = summarise()
    absent = " ".join(summary["not_in_tables_3_4"])
    coverage = (
        f"all {summary['nodes_total']} nodes covered"
        if summary["nodes_covered"] == summary["nodes_total"]
        else f"{summary['nodes_covered']} of {summary['nodes_total']} nodes covered"
    )
    unmapped = summary["unmapped"]
    return [
        (
            f"monograph (2013): {summary['listed']} airports in the Lista de Siglas; "
            f"{summary['in_tables_3_4']} in Tables 3-4 (absent: {absent}); "
            f"the text of section 5.2 says {summary['stated_in_text']}"
        ),
        (
            f"ADR-0001 map (data/external/nodes.csv): {summary['mapped']} of "
            f"{summary['listed']} present -> {summary['nodes_covered']} nodes ({coverage})"
        ),
        f"absent from the map ({len(unmapped)}): {' '.join(unmapped)}",
    ]


def main() -> int:
    for line in lines():
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
