"""Stage 1 -- ingest: discover and download the raw ANAC VRA monthly files (`airline-delays fetch`).

`layouts` declares the two raw layouts (2000-2009 and 2010-2013), `manifest` records
what was downloaded and `download` talks to ANAC's server."""

from __future__ import annotations

from .download import (
    MAX_RETRIES,
    REQUEST_DELAY_S,
    RETRY_BACKOFF_S,
    USER_AGENT,
    YEARS,
    RemoteFile,
    expected_names,
    fetch,
    list_year,
)
from .layouts import (
    LAYOUT_2010,
    LAYOUT_LEGACY,
    LAYOUTS,
    RawLayout,
    inspect_file,
    layout_for,
    read_header,
)
from .manifest import (
    BASE_URL,
    CHUNK_BYTES,
    Manifest,
    ManifestEntry,
    sha256_file,
)

__all__ = [
    "BASE_URL",
    "CHUNK_BYTES",
    "LAYOUTS",
    "LAYOUT_2010",
    "LAYOUT_LEGACY",
    "MAX_RETRIES",
    "REQUEST_DELAY_S",
    "RETRY_BACKOFF_S",
    "USER_AGENT",
    "YEARS",
    "Manifest",
    "ManifestEntry",
    "RawLayout",
    "RemoteFile",
    "expected_names",
    "fetch",
    "inspect_file",
    "layout_for",
    "list_year",
    "read_header",
    "sha256_file",
]
