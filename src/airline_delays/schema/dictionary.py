"""`docs/dictionary.md`, generated from the registry (`airline-delays dictionary`). Never edited by hand."""

from __future__ import annotations

from airline_delays.schema.columns import Column

LAYER_TITLES: dict[str, str] = {
    "staged": "Staged flights (`data/staged/year=YYYY/part-0.parquet`)",
    "fact": "Fact table, group x route x month (`data/analysis/fact_group_route_month.parquet`)",
    "city": "City-month (`data/analysis/city_month.parquet`)",
    "airline_city": "Airline x city x month (`data/analysis/airline_city_month.parquet`)",
    "panel": "Reconstruction panel, route x month (`data/analysis/panel_route_month.parquet`)",
    "article_panel": "The article's estimation panel, route x month (`data/analysis/article_panel_route_month.parquet`)",
    "ml": "Flight-level modelling table (`data/derived/ml/year=YYYY/part-0.parquet`)",
}


def dictionary_markdown(layers: dict[str, list[Column]]) -> str:
    """The data dictionary, generated. Never hand-edited (rule 5 of the brief)."""
    lines = [
        "# Data dictionary",
        "",
        "Generated from `src/airline_delays/schema/columns.py` by `airline-delays dictionary`. Do not edit by",
        "hand: the registry is the source of truth, and this file is a rendering of it.",
        "Definitions are given in English and Portuguese; `aggregation` says what happens",
        "to the column when rows are rolled up to a coarser grain (`sum` adds, `recompute`",
        "must be rebuilt from the flights, `none` is a key or label).",
        "",
    ]
    for layer, columns in layers.items():
        if not columns:
            continue
        lines += [
            f"## {LAYER_TITLES.get(layer, layer)}",
            "",
            f"{len(columns)} columns.",
            "",
            "| column | type | unit | aggregation | definition (en) | definição (pt) |",
            "|---|---|---|---|---|---|",
        ]
        for column in columns:
            lines.append(
                f"| `{column.name}` | {column.dtype} | {column.unit} | {column.aggregation} | "
                f"{_escape(column.definition_en)} | {_escape(column.definition_pt)} |"
            )
        lines.append("")
    return "\n".join(lines)


def _escape(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")
