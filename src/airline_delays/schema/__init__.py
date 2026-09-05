"""The column registry and what is generated from it.

No column reaches a public table without a `Column` here; `docs/dictionary.md` and
`datapackage.json` are generated from these entries, never written by hand."""

from __future__ import annotations

from . import metadata, zenodo
from .columns import (
    ARTICLE_PANEL,
    DTYPE_ALIASES,
    FACT,
    ML,
    ML_NAMES,
    STAGED,
    STAGED_NAMES,
    Aggregation,
    Column,
    Layer,
    build_layer,
    describe,
    describe_frame,
    dtype_matches,
    fact_columns,
    get,
    ml_columns,
    to_frame,
    validate_schema,
)
from .datapackage import (
    LICENCES,
    RESOURCE_NOTES,
    RESOURCES,
    SOURCES,
    built_layers,
    package_descriptor,
    resource,
)
from .datapackage import build as build_datapackage
from .datapackage import render as render_datapackage
from .dictionary import (
    LAYER_TITLES,
    dictionary_markdown,
)

__all__ = [
    "ARTICLE_PANEL",
    "DTYPE_ALIASES",
    "FACT",
    "LAYER_TITLES",
    "LICENCES",
    "ML",
    "ML_NAMES",
    "RESOURCES",
    "RESOURCE_NOTES",
    "SOURCES",
    "STAGED",
    "STAGED_NAMES",
    "Aggregation",
    "Column",
    "Layer",
    "build_datapackage",
    "build_layer",
    "built_layers",
    "describe",
    "describe_frame",
    "dictionary_markdown",
    "dtype_matches",
    "fact_columns",
    "get",
    "metadata",
    "ml_columns",
    "package_descriptor",
    "render_datapackage",
    "resource",
    "to_frame",
    "validate_schema",
    "zenodo",
]
