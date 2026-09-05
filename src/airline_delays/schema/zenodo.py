""".zenodo.json: what Zenodo reads when a GitHub release is archived. Generated, never hand-edited.

No DOI appears here -- Zenodo assigns it. An invalid file makes Zenodo fall
back silently to inferred metadata, so `tests/test_metadata_consistency.py`
parses the generated file and checks its enumerations.
"""

from __future__ import annotations

import json
from typing import Any

from airline_delays.schema import metadata

UPLOAD_TYPE = "dataset"


def build() -> dict[str, Any]:
    creators = []
    for creator in metadata.CREATORS:
        entry: dict[str, Any] = {"name": creator["name"], "affiliation": creator["affiliation"]}
        if creator.get("orcid"):
            entry["orcid"] = creator["orcid"]
        creators.append(entry)
    return {
        "upload_type": UPLOAD_TYPE,
        "title": metadata.TITLE,
        "description": f"<p>{metadata.DESCRIPTION}</p>",
        "creators": creators,
        "access_right": "open",
        "license": "cc-by-4.0",
        "language": "eng",
        "version": metadata.version(),
        "keywords": list(metadata.KEYWORDS),
        "related_identifiers": [dict(item) for item in metadata.RELATED_IDENTIFIERS],
        "references": [metadata.ARTICLE_CITATION],
        "notes": (
            "Code under MIT (LICENSE); curated data and text under CC BY 4.0 "
            "(LICENSE-CC-BY-4.0.md). VRA-derived tables are attributed to "
            f"'{metadata.ATTRIBUTION_VRA}'. The heavy layers -- the raw ANAC files, the staged "
            "flight table and the flight-level modelling table -- are not in this archive; they "
            "are regenerated from ANAC's public files by the documented commands, with sha256 "
            "provenance in data/raw/manifest.json."
        ),
    }


def render() -> str:
    return json.dumps(build(), indent=2, ensure_ascii=False) + "\n"
