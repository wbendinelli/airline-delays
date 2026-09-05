"""`datapackage.json` (Frictionless Data Package), generated from the registry and the tables on disk
(`airline-delays datapackage`). Never edited by hand."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from airline_delays.schema.columns import ML, STAGED, Column, describe_frame

RESOURCE_NOTES: dict[str, str] = {
    "article_panel": (
        "The estimation panel of Bendinelli, Bettini & Oliveira (2016): one row per directional "
        "city-pair route x month, 2002m1-2013m12, curated from the authors' final base "
        "(December 2015) to the 52 columns the published Tables 2-7 use plus keys and context "
        "(ADR-0020). Canonical file; the csv.gz carries the same values at 32-bit precision."
    ),
    "ml": (
        "Flight-level modelling table for delay prediction: one row per scheduled "
        "flight of the replication universe (ADR-0002), pre-departure features only "
        "(ADR-0009), targets null where ADR-0012 leaves no actual timestamp. "
        "Partitioned by year, about 313 MB, rebuilt in 33 seconds by `just predict-dataset` and "
        "therefore not tracked in git (ADR-0004)."
    ),
}

RESOURCES: dict[str, tuple[str, str, list[str]]] = {
    "fact": (
        "fact_group_route_month",
        "data/analysis/fact_group_route_month.parquet",
        ["ym", "route", "group"],
    ),
    "city": ("city_month", "data/analysis/city_month.parquet", ["ym", "node"]),
    "airline_city": (
        "airline_city_month",
        "data/analysis/airline_city_month.parquet",
        ["ym", "node", "group"],
    ),
    "panel": ("panel_route_month", "data/analysis/panel_route_month.parquet", ["route", "ym"]),
    "article_panel": (
        "article_panel_route_month",
        "data/analysis/article_panel_route_month.parquet",
        ["od", "ym"],
    ),
    "ml": ("flights_features", "data/derived/ml/year=*/part-0.parquet", []),
}


def built_layers(root: Path) -> dict[str, list[Column]]:
    """Registry entries for every table that currently exists on disk."""
    import pandas as pd

    analysis = root / "data" / "analysis"
    layers: dict[str, list] = {"staged": list(STAGED)}
    for layer, filename in (
        ("fact", "fact_group_route_month.parquet"),
        ("city", "city_month.parquet"),
        ("airline_city", "airline_city_month.parquet"),
        ("panel", "panel_route_month.parquet"),
        ("article_panel", "article_panel_route_month.parquet"),
    ):
        path = analysis / filename
        if path.exists():
            frame = pd.read_parquet(path)
            layers[layer] = describe_frame(frame, layer)
    # The flight-level modelling table is 313 MB and never enters git (ADR-0004),
    # so its entry is the registry's declared list rather than a built file --
    # a reader of the dictionary must be able to see the columns of a table they
    # will rebuild, not only of the tables that ship.
    layers["ml"] = list(ML)
    return layers


def build(root: Path, *, doi: str | None = None) -> dict:
    """The descriptor for every resource whose table exists under `root`."""
    layers = built_layers(root)
    resources = [
        resource(name, path, layers[layer], key, description=RESOURCE_NOTES.get(layer))
        for layer, (name, path, key) in RESOURCES.items()
        if layer in layers
    ]
    return datapackage(resources, doi=doi)


_FRICTIONLESS_TYPES: dict[str, tuple[str, str | None]] = {
    "date32": ("date", None),
    "int8": ("integer", None),
    "int16": ("integer", None),
    "int32": ("integer", None),
    "int64": ("integer", None),
    "float32": ("number", None),
    "float64": ("number", None),
    "string": ("string", None),
    "bool": ("boolean", None),
    "timestamp[s]": ("datetime", None),
}

LICENCES: dict[str, dict[str, str]] = {
    "data": {
        "name": "CC-BY-4.0",
        "title": "Creative Commons Attribution 4.0",
        "path": "https://creativecommons.org/licenses/by/4.0/",
    },
    "code": {
        "name": "MIT",
        "title": "MIT License",
        "path": "https://opensource.org/licenses/MIT",
    },
}

SOURCES: list[dict[str, str]] = [
    {
        "title": "ANAC, Voo Regular Ativo (VRA), via dados.gov.br",
        "path": "https://dados.gov.br/dados/conjuntos-dados/dadosabertos-areas-de-atuacao-voos-e-operacoes-aereas-voo-regular-ativo-vra",
    },
    {
        "title": "ANAC, IAC 1504 (justification codes, DI codes, line types)",
        "path": "https://pergamum.anac.gov.br/pergamum/vinculos/IAC1504.pdf",
    },
    {
        "title": "OurAirports (airport coordinates behind the node map)",
        "path": "https://davidmegginson.github.io/ourairports-data/airports.csv",
    },
]


def datapackage(resources: list[dict[str, Any]], doi: str | None = None) -> dict:
    """A Frictionless v2 datapackage descriptor, generated from the registry.

    ``id`` is **omitted** until a DOI exists. Frictionless makes the field
    optional, and a placeholder there is worse than nothing: harvesters read the
    descriptor as machine-readable metadata and would resolve
    ``10.5281/zenodo.PENDING`` as a real, dead identifier (audit 2026-09-05,
    M-5). The custom ``pending_doi`` flag says the omission is deliberate and
    where the deposit stands; pass ``doi=`` once Zenodo has minted one and both
    fields flip together.
    """
    identity: dict[str, Any] = (
        {"id": f"https://doi.org/{doi}"}
        if doi
        else {
            "pending_doi": True,
            "pending_doi_note": (
                "No DOI has been minted yet; `id` is omitted rather than filled with a "
                "placeholder that would resolve to nothing. The Zenodo deposit is "
                "tracked in ROADMAP.md, 'Open items'."
            ),
        }
    )
    document: dict[str, Any] = {
        "profile": "data-package",
        "name": "airline-delays",
        **identity,
        "title": "Brazilian airline delays, reconstructed from ANAC's VRA (2000-2013)",
        "description": (
            "Route-month panel and group x route x month fact table reconstructed from "
            "ANAC's Voo Regular Ativo flight-leg records, with the columns of "
            "Bendinelli, Bettini & Oliveira (2016) reproduced under declared definitions."
        ),
        "homepage": "https://github.com/wbendinelli/airline-delays",
        "version": "0.1.0",
        "licenses": [LICENCES["data"]],
        "sources": SOURCES,
        "contributors": [
            {"title": "William Eduardo Bendinelli", "role": "author"},
        ],
        "resources": resources,
    }
    return document


def resource(
    name: str,
    path: str,
    columns: list[Column],
    primary_key: list[str],
    description: str | None = None,
) -> dict:
    """One Frictionless resource whose schema is the registry's own entries.

    `primary_key` may be empty: the flight-level table has no key that is unique
    in the source data (the raw VRA repeats rows), and declaring one that is not
    would be a claim, not a schema.
    """
    fields = []
    for column in columns:
        field_type, field_format = _FRICTIONLESS_TYPES.get(column.dtype, ("any", None))
        field: dict[str, Any] = {
            "name": column.name,
            "type": field_type,
            "title": column.unit,
            "description": column.definition_en,
        }
        if field_format:
            field["format"] = field_format
        field["x-definition-pt"] = column.definition_pt
        field["x-aggregation"] = column.aggregation
        field["x-source"] = column.source
        fields.append(field)
    schema: dict[str, Any] = {"fields": fields}
    if primary_key:
        schema["primaryKey"] = primary_key
    out = {
        "name": name,
        "path": path,
        "format": Path(path).suffix.lstrip("."),
        "mediatype": "application/vnd.apache.parquet" if path.endswith(".parquet") else "text/csv",
        "schema": schema,
    }
    if description:
        out["description"] = description
    return out
