"""Theory object -> article variable -> published sign, joined with ``replication/published.json``.

The monograph's model has a handful of objects -- flight volumes and the
congestion cost, market power, the follower's reaction, the leader's toll,
the low-cost entrant -- and the 2016 article has eleven regressors. Which
object each regressor stands for, and what sign the theory expects, is a
judgment recorded once here (:data:`ROWS`); the published coefficients, signs
and stars are read from ``replication/published.json`` (written by
``replication/published.py`` out of the article's text) and joined, never
typed. ``docs/theory/03-do-modelo-ao-artigo.md`` quotes the result out of
``reports/theory/model.json``.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from replication.published import load as load_published

TABLES = ("table3", "table6")


@dataclass(frozen=True)
class BridgeRow:
    variable: str
    theory_object: str
    theory_object_pt: str
    expected_sign: str | None
    rationale: str


ROWS: tuple[BridgeRow, ...] = (
    BridgeRow(
        "dailyflcong",
        "flight volumes in the congested (peak) period: f1 + f2 with c' > 0",
        "volumes de voo no pico: f1 + f2, com c' > 0",
        "+",
        "more flights in congested hours raise c(F) and delays",
    ),
    BridgeRow(
        "dailyflncong",
        "flight volumes off peak: the period where the model puts no congestion",
        "volumes fora do pico: o período sem congestionamento no modelo",
        "+",
        "the model predicts nothing here; the article finds the same positive sign as on peak",
    ),
    BridgeRow(
        "prwheather",
        "non-strategic delay: weather and airport restrictions",
        "atraso não estratégico: clima e restrições de aeroporto",
        "+",
        "a control outside the game",
    ),
    BridgeRow(
        "princident",
        "non-strategic delay: incidents",
        "atraso não estratégico: incidentes",
        "+",
        "a control outside the game",
    ),
    BridgeRow(
        "pr_connc",
        "non-strategic delay: aircraft rotation (code RA)",
        "atraso não estratégico: rotação de aeronave (código RA)",
        "+",
        "a control outside the game",
    ),
    BridgeRow(
        "maxprdel",
        "the airport's congestion state: delays of all carriers at the busier endpoint",
        "o estado de congestionamento do aeroporto: atrasos de todas as empresas na ponta mais movimentada",
        "+",
        "c(F) is a function of everybody's traffic",
    ),
    BridgeRow(
        "cshare",
        "cooperation outside the model",
        "cooperação fora do modelo",
        None,
        "no prediction",
    ),
    BridgeRow(
        "rthhi",
        "market power on the route: d' < 0 in equation (12)",
        "poder de mercado na rota: d' < 0 na equação (12)",
        None,
        "ambiguous: the monograph's Table 1 expected '-, +'; the 2016 article reads it as the competition-quality channel",
    ),
    BridgeRow(
        "maxcthhi",
        "internalisation at the airport: the dominant carrier's own share of MCD, Proposition 1",
        "internalização no aeroporto: a parcela própria do dano marginal da dominante, Proposição 1",
        "-",
        "a carrier that faces its own congestion restrains flights; the toll it needs is smaller",
    ),
    BridgeRow(
        "lcc",
        "a low-cost carrier on the route: 'Pressuposição 3'",
        "uma LCC na rota: 'Pressuposição 3'",
        "-",
        "the monograph's Table 1 expects both LCC dummies to reduce delays",
    ),
    BridgeRow(
        "maxalccfu",
        "a low-cost carrier at either endpoint city: the non-price spillover",
        "uma LCC em uma das cidades-extremo: o spillover não-preço",
        "-",
        "same expectation, at the city rather than the route",
    ),
)


def _sign(value: float | None) -> str | None:
    if value is None:
        return None
    return "+" if value > 0 else "-" if value < 0 else "0"


def bridge(
    published: dict[str, Any] | None = None, tables: tuple[str, ...] = TABLES
) -> dict[str, Any]:
    """The join, per table: expected sign, published b/se/stars/sign per column, agreement."""
    published = load_published() if published is None else published
    out: dict[str, Any] = {"rows": [asdict(row) for row in ROWS], "tables": {}}
    for table in tables:
        columns = published[table]["columns"]
        per_variable: dict[str, Any] = {}
        for row in ROWS:
            cells: dict[str, Any] = {}
            signs: list[str | None] = []
            for column, content in columns.items():
                b = content.get("b", {}).get(row.variable)
                sign = _sign(b)
                signs.append(sign)
                cells[column] = {
                    "b": b,
                    "se": content.get("se", {}).get(row.variable),
                    "stars": content.get("stars", {}).get(row.variable),
                    "sign": sign,
                    "agrees": None
                    if row.expected_sign is None or sign is None
                    else sign == row.expected_sign,
                }
            per_variable[row.variable] = {
                "expected_sign": row.expected_sign,
                "columns": cells,
                "pattern": {
                    "positive": sum(sg == "+" for sg in signs),
                    "negative": sum(sg == "-" for sg in signs),
                    "absent": sum(sg is None for sg in signs),
                },
            }
        out["tables"][table] = {
            "caption": published[table].get("caption"),
            "variables": per_variable,
        }
    return out
