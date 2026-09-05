"""Stage 2 -- staging: parse and clean the raw CSVs into the canonical flight table
(`airline-delays stage`; `data/staged/year=YYYY/part-0.parquet`)."""

from __future__ import annotations

from .build import (
    DEFAULT_MEMORY_LIMIT,
    DEFAULT_THREADS,
    YearResult,
    _register_helpers,
    connect,
    git_commit,
    read_staged,
    stage,
    stage_year,
    tool_versions,
    write_manifest,
)
from .clean import (
    AMBIGUOUS_CAUSE_TEXTS,
    CAUSE_TEXT_TO_CODE,
    DI_LETTERS,
    IAC1504_CODES,
    LINE_TYPE_NULLS,
    NORMALISE_TEXT_SQL,
    STATUS_MAP,
    cause_code_from_text,
    normalise_text,
    normalise_text_sql,
)
from .select import (
    build_select,
    positions_for,
)

__all__ = [
    "AMBIGUOUS_CAUSE_TEXTS",
    "CAUSE_TEXT_TO_CODE",
    "DEFAULT_MEMORY_LIMIT",
    "DEFAULT_THREADS",
    "DI_LETTERS",
    "IAC1504_CODES",
    "LINE_TYPE_NULLS",
    "NORMALISE_TEXT_SQL",
    "STATUS_MAP",
    "YearResult",
    "_register_helpers",
    "build_select",
    "cause_code_from_text",
    "connect",
    "git_commit",
    "normalise_text",
    "normalise_text_sql",
    "positions_for",
    "read_staged",
    "stage",
    "stage_year",
    "tool_versions",
    "write_manifest",
]
