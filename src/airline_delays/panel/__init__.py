"""Stage 5 -- panel: the route-month panel of the 27 nodes, the article's columns plus the new
feature set (`airline-delays panel`)."""

from __future__ import annotations

from .build import (
    PanelResult,
    assemble,
    build_panel,
    capacity_note,
)
from .columns import (
    CITY_SIDE_COLUMNS,
    DROPPED_FROM_PANEL,
    NOT_IN_VRA,
    PUBLISHED_SLICE_SUFFIXES,
    SLICE_SUFFIXES,
)

__all__ = [
    "CITY_SIDE_COLUMNS",
    "DROPPED_FROM_PANEL",
    "NOT_IN_VRA",
    "PUBLISHED_SLICE_SUFFIXES",
    "SLICE_SUFFIXES",
    "PanelResult",
    "assemble",
    "build_panel",
    "capacity_note",
]
