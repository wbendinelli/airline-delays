"""Node map, route key and year-month key.

ADR-0001 fixes the geography: the analysis unit is the *node*, which is a city
airport system, not an airport. Only six airports are grouped, into three
metropolitan nodes; every other airport is its own node and keeps its ICAO
code. Both levels survive downstream, because `origin_icao` and `dest_icao`
travel next to `origin_node` and `dest_node` in the staged table, so
airport-level work never requires re-extraction.

The three metropolitan nodes:

===========  =========================  ==========================
Node         Airports                   City
===========  =========================  ==========================
``MRSP``     SBSP, SBGR, SBKP           São Paulo (with Viracopos)
``MRRJ``     SBGL, SBRJ                 Rio de Janeiro
``MRBH``     SBBH, SBCF                 Belo Horizonte
===========  =========================  ==========================

Viracopos (SBKP) sits inside São Paulo: with it, exact agreement of flight
counts of the article's own panel is exact only with this map
(ADR-0001).
"""

from __future__ import annotations

from datetime import date

METRO_NODES: dict[str, str] = {
    "SBSP": "MRSP",
    "SBGR": "MRSP",
    "SBKP": "MRSP",
    "SBGL": "MRRJ",
    "SBRJ": "MRRJ",
    "SBBH": "MRBH",
    "SBCF": "MRBH",
}
"""The only airports whose node differs from their ICAO code (ADR-0001)."""

METRO_MEMBERS: dict[str, tuple[str, ...]] = {
    "MRSP": ("SBSP", "SBGR", "SBKP"),
    "MRRJ": ("SBGL", "SBRJ"),
    "MRBH": ("SBBH", "SBCF"),
}

CAPITAL_SINGLE_AIRPORTS: tuple[str, ...] = (
    "SBAR",
    "SBBE",
    "SBBR",
    "SBBV",
    "SBCG",
    "SBCT",
    "SBCY",
    "SBEG",
    "SBFL",
    "SBFZ",
    "SBGO",
    "SBJP",
    "SBMO",
    "SBMQ",
    "SBNT",
    "SBPA",
    "SBPJ",
    "SBPV",
    "SBRB",
    "SBRF",
    "SBSL",
    "SBSV",
    "SBTE",
    "SBVT",
)
"""The 24 single-airport state capitals of the replication panel.

Kept for reference and for the replication layer's own filter. Staging does
**not** restrict to these: every airport in the raw file is staged, so that a
national analysis needs no re-extraction.
"""

PANEL_NODES: tuple[str, ...] = tuple(sorted((*CAPITAL_SINGLE_AIRPORTS, *METRO_MEMBERS)))


def node(icao: str | None) -> str | None:
    """Map an airport ICAO code to its node.

    Six airports map to the three metropolitan nodes; every other airport is
    returned unchanged, so no airport is ever dropped.

    >>> node("SBKP"), node("SBGL"), node("SBAR")
    ('MRSP', 'MRRJ', 'SBAR')
    """
    if icao is None:
        return None
    icao = icao.strip().upper()
    if not icao:
        return None
    return METRO_NODES.get(icao, icao)


def route(origin_node: str | None, dest_node: str | None) -> str | None:
    """The directional route key ``origin_node-dest_node``.

    >>> route("MRSP", "SBAR")
    'MRSP-SBAR'
    """
    if not origin_node or not dest_node:
        return None
    return f"{origin_node}-{dest_node}"


def ym(year: int, month: int) -> int:
    """The year-month key as ``YYYYMM``.

    Computed in `int` on purpose: ``int16 * 100`` overflows and produced
    invalid keys in an earlier reconstruction, which matched nothing.

    >>> ym(2012, 3)
    201203
    """
    return int(year) * 100 + int(month)


def ym_of(day: date) -> int:
    """The year-month key of a date."""
    return ym(day.year, day.month)


def is_metro(node_code: str | None) -> bool:
    """True when `node_code` is one of the three metropolitan nodes."""
    return node_code in METRO_MEMBERS


NODE_SQL_CASE = (
    "CASE {col} "
    + " ".join(f"WHEN '{airport}' THEN '{metro}'" for airport, metro in METRO_NODES.items())
    + " ELSE {col} END"
)
"""SQL fragment building the node map inside DuckDB; ``{col}`` is the column."""


def node_sql(column: str) -> str:
    """Render `NODE_SQL_CASE` for `column`."""
    return NODE_SQL_CASE.format(col=column)
