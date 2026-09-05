"""`datapackage.json` -- a Frictionless Data Package (v2) describing every table this repository
publishes, generated from the registry and the files on disk (`airline-delays datapackage`).
Never edited by hand.

Each resource carries its schema (from the registry), its size and sha256 (from the file; the
size of a parquet file travels under ``x-bytes`` because frictionless cannot measure it), its
row count, its licence and its upstream sources. The two heavy layers that are regenerated rather
than distributed -- the staged flight table and the flight-level modelling table -- are described
under ``x-regenerated`` with the command that rebuilds them, because a ``resources[].path`` is a
promise that the bytes are in the package.
"""

from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path
from typing import Any

from airline_delays import paths
from airline_delays.schema import metadata
from airline_delays.schema.columns import ML, STAGED, Column, describe_frame

PROFILE = "https://datapackage.org/profiles/2.0/datapackage.json"

RESOURCE_NOTES: dict[str, str] = {
    "article_panel": (
        "The estimation panel of Bendinelli, Bettini & Oliveira (2016): one row per directional "
        "city-pair route x month, 2002m1-2013m12, curated from the authors' final base "
        "(December 2015) to the 52 columns the published Tables 2-7 use plus keys and context "
        "(ADR-0020). Canonical file; the csv.gz carries the same values at 32-bit precision."
    ),
    "panel": (
        "The open reconstruction panel: one row per directional route x month over the 27 nodes "
        "of ADR-0001, rebuilt from ANAC's VRA by this repository -- the article's variables under "
        "the article's own names where the VRA can compute them, plus the new feature set. The "
        "csv.gz prints floats with six significant digits."
    ),
    "fact": (
        "The canonical fact table, one row per airline group x route x month over the replication "
        "universe (ADR-0002); every other grain is a projection of it (ADR-0004)."
    ),
    "city": "City-month projection of the fact table: departures and arrivals both counted, with the ADR-0007 congestion proxy.",
    "airline_city": "Airline group x city x month projection of the fact table, with the hub share, score and dummy.",
    "ml": (
        "Flight-level modelling table for delay prediction: one row per scheduled "
        "flight of the replication universe (ADR-0002), pre-departure features only "
        "(ADR-0009), targets null where ADR-0012 leaves no actual timestamp. "
        "Partitioned by year, about 313 MB, rebuilt in about 25 seconds by `just predict-dataset` "
        "and therefore not tracked in git (ADR-0004)."
    ),
    "staged": (
        "The canonical flight table: one row per flight leg of ANAC's VRA, 2000-2013, parsed and "
        "cleaned by `just stage`; about 253 MB in zstd parquet, rebuilt from the raw files and "
        "therefore not tracked in git (ADR-0004)."
    ),
}

#: Registry layer -> the resources built from it: (name, path, primary key).
RESOURCES: dict[str, list[tuple[str, str, list[str]]]] = {
    "fact": [
        (
            "fact_group_route_month",
            "data/analysis/fact_group_route_month.parquet",
            ["ym", "route", "group"],
        )
    ],
    "city": [("city_month", "data/analysis/city_month.parquet", ["ym", "node"])],
    "airline_city": [
        ("airline_city_month", "data/analysis/airline_city_month.parquet", ["ym", "node", "group"])
    ],
    "panel": [
        ("panel_route_month", "data/analysis/panel_route_month.parquet", ["route", "ym"]),
        ("panel_route_month_csv", "data/analysis/panel_route_month.csv.gz", ["route", "ym"]),
    ],
    "article_panel": [
        (
            "article_panel_route_month",
            "data/analysis/article_panel_route_month.parquet",
            ["od", "ym"],
        ),
        (
            "article_panel_route_month_csv",
            "data/analysis/article_panel_route_month.csv.gz",
            ["od", "ym"],
        ),
    ],
}

#: The curated reference tables: stem -> (description, candidate primary key, upstream source title).
EXTERNAL_TABLES: dict[str, tuple[str, list[str], str]] = {
    "airports_br": (
        (
            "Every OurAirports record with iso_country == BR: the universe every Brazilian ICAO code "
            "in the VRA resolves against."
        ),
        ["icao"],
        "OurAirports (public domain)",
    ),
    "nodes": (
        "The airport -> panel-node crosswalk of ADR-0001: one row per constituent airport of the 27 nodes.",
        ["icao"],
        "OurAirports coordinates; ADR-0001",
    ),
    "distances_km": (
        "Great-circle distance for every ordered pair of the 27 nodes, computed from nodes.csv.",
        ["origin_node", "dest_node"],
        "computed from nodes.csv (haversine, R = 6371.0088 km)",
    ),
    "groups": (
        (
            "The dated airline -> economic group and class map of ADR-0003 and ADR-0011, one row "
            "per carrier and period, each with its source."
        ),
        [],
        "CADE and ANAC acts, press of record",
    ),
    "cause_codes": (
        "IAC 1504 Annex 2 justification codes with the article's sets and the ADR-0005 taxonomy.",
        ["code"],
        "ANAC, IAC 1504",
    ),
    "di_codes": ("IAC 1504 flight-type (DI) codes.", ["code"], "ANAC, IAC 1504"),
    "line_types": ("IAC 1504 line-nature codes.", ["code"], "ANAC, IAC 1504"),
    "holidays": (
        "National holidays 2000-2013 that exist by federal law.",
        ["date", "name"],
        "Diário Oficial da União",
    ),
    "observances": (
        "Carnival, Good Friday and Corpus Christi 2000-2013, computed from Easter Sunday.",
        ["date", "name"],
        "computed (Meeus-Jones-Butcher)",
    ),
    "events": (
        "Dated market events: mergers, entries, exits, the 2006-2007 crisis, the 2008-2009 window.",
        [],
        "CADE and ANAC acts, press of record",
    ),
    "capacity": (
        "Declared hourly capacity where located (ADR-0007): one row, Congonhas after July 2007.",
        [],
        "press retrospectives (confidence B)",
    ),
    "slots": (
        "Slot-coordination starts where located: Guarulhos and Santos Dumont.",
        [],
        "ANAC acts",
    ),
    "monograph_airports": (
        "The 38 airports listed in the author's 2013 undergraduate monograph, spellings as printed.",
        ["icao"],
        "Bendinelli (2013), undergraduate monograph, USP",
    ),
}

MANIFESTS: tuple[tuple[str, str, str], ...] = (
    (
        "manifest_raw",
        "data/raw/manifest.json",
        "The fetch manifest: URL, size, sha256 and retrieval time of each of the 168 monthly ANAC files.",
    ),
    (
        "manifest_fact",
        "data/analysis/manifest.json",
        "Provenance of the fact table: commit, tool versions, threshold, convention, per-year accounting.",
    ),
    (
        "manifest_panel",
        "data/analysis/panel_manifest.json",
        "Provenance of the reconstruction panel: commit, tool versions, shape and byte sizes.",
    ),
    (
        "manifest_article_panel",
        "data/analysis/article_panel_manifest.json",
        "Provenance of the article panel: source sha256 and header timestamp, shape, nulls, file hashes.",
    ),
)

_FRICTIONLESS_TYPES: dict[str, str] = {
    "date32": "date",
    "int8": "integer",
    "int16": "integer",
    "int32": "integer",
    "int64": "integer",
    "float32": "number",
    "float64": "number",
    "string": "string",
    "bool": "boolean",
    "timestamp[s]": "datetime",
}

#: Kept for callers that imported the old names.
LICENCES = metadata.LICENSES
SOURCES = [dict(source) for source in metadata.SOURCES]

_REGIONS = ["Centro-Oeste", "Nordeste", "Norte", "Sudeste", "Sul"]
_BOUNDED_UNITS = {"share", "flag", "index 0-1", "index 0-1 (flights)", "share of flights"}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return "sha256:" + digest.hexdigest()


def _rows(path: Path) -> int | None:
    if path.suffix == ".parquet":
        import pyarrow.parquet as pq

        return int(pq.read_metadata(path).num_rows)
    if path.name.endswith(".csv.gz"):
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            return sum(1 for _ in handle) - 1
    if path.suffix == ".csv":
        with path.open(encoding="utf-8") as handle:
            return sum(1 for _ in handle) - 1
    return None


def _null_counts(relpath: str) -> dict[str, int]:
    """Per-column null counts from the parquet footer (no data read); {} for other formats."""
    if not relpath.endswith(".parquet"):
        return {}
    import pyarrow.parquet as pq

    metadata_ = pq.ParquetFile(paths.REPO_ROOT / relpath).metadata
    counts: dict[str, int] = {}
    for group in range(metadata_.num_row_groups):
        row_group = metadata_.row_group(group)
        for index in range(row_group.num_columns):
            chunk = row_group.column(index)
            name = chunk.path_in_schema
            nulls = chunk.statistics.null_count if chunk.statistics is not None else 0
            counts[name] = counts.get(name, 0) + int(nulls or 0)
    return counts


def _field(column: Column, primary_key: list[str], nullable: bool = True) -> dict[str, Any]:
    field: dict[str, Any] = {
        "name": column.name,
        "type": _FRICTIONLESS_TYPES.get(column.dtype, "any"),
        "title": column.unit,
        "description": column.definition_en,
        "x-definition-pt": column.definition_pt,
        "x-aggregation": column.aggregation,
        "x-source": column.source,
    }
    constraints: dict[str, Any] = {}
    if column.name in primary_key:
        constraints["required"] = True
    if column.name in ("o_region", "d_region"):
        constraints["enum"] = list(_REGIONS)
    elif column.unit in _BOUNDED_UNITS and field["type"] in {"number", "integer"} and not nullable:
        # Declared only where every cell satisfies it: a bounded share with missing
        # cells would fail a validator that reads a null as a number.
        constraints["minimum"] = 0
        constraints["maximum"] = 1
    if constraints:
        field["constraints"] = constraints
    return field


def _file_block(relpath: str) -> dict[str, Any]:
    path = paths.REPO_ROOT / relpath
    if not path.exists():
        raise FileNotFoundError(
            f"{relpath} is not on disk; build it before generating datapackage.json "
            "(`just fact && just panel`, or `airline-delays article-panel`)"
        )
    # frictionless verifies `bytes` and cannot measure a parquet file's, so parquet
    # sizes travel under `x-bytes`; the sha256 is checked by tests/test_datapackage.py.
    size_key = "x-bytes" if relpath.endswith(".parquet") else "bytes"
    block: dict[str, Any] = {size_key: path.stat().st_size, "hash": _sha256(path)}
    rows = _rows(path)
    if rows is not None:
        block["x-rows"] = rows
    return block


def _format(relpath: str) -> dict[str, Any]:
    if relpath.endswith(".parquet"):
        return {"format": "parquet", "mediatype": "application/vnd.apache.parquet"}
    if relpath.endswith(".csv.gz"):
        return {
            "format": "csv",
            "mediatype": "text/csv",
            "encoding": "utf-8",
            "x-compression": "gz",
        }
    if relpath.endswith(".csv"):
        return {"format": "csv", "mediatype": "text/csv", "encoding": "utf-8"}
    return {"format": "json", "mediatype": "application/json", "encoding": "utf-8"}


def resource(
    name: str,
    path: str,
    columns: list[Column],
    primary_key: list[str],
    description: str | None = None,
    *,
    sources: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """One tabular resource whose schema is the registry's own entries, plus size, hash and rows."""
    nulls = _null_counts(path if path.endswith(".parquet") else path.replace(".csv.gz", ".parquet"))
    schema: dict[str, Any] = {
        "fields": [
            _field(column, primary_key, nullable=nulls.get(column.name, 1) > 0)
            for column in columns
        ],
        "missingValues": [""],
    }
    if primary_key:
        schema["primaryKey"] = primary_key
    out: dict[str, Any] = {"name": name, "type": "table", "path": path, **_format(path)}
    if description:
        out["description"] = description
    out.update(_file_block(path))
    out["licenses"] = [metadata.LICENSES["data"]]
    out["sources"] = sources or [
        {"title": metadata.ATTRIBUTION_VRA, "path": metadata.VRA_CATALOGUE_URL}
    ]
    out["schema"] = schema
    return out


def external_resource(stem: str) -> dict[str, Any]:
    """A curated reference table: fields inferred from the CSV, key declared only if it holds."""
    import pandas as pd

    description, candidate_key, upstream = EXTERNAL_TABLES[stem]
    relpath = f"data/external/{stem}.csv"
    frame = pd.read_csv(paths.REPO_ROOT / relpath)
    fields = []
    for column in frame.columns:
        kind = str(frame[column].dtype)
        ftype = (
            "integer"
            if kind.startswith("int")
            else "number"
            if kind.startswith("float")
            else "boolean"
            if kind == "bool"
            else "string"
        )
        fields.append({"name": column, "type": ftype})
    schema: dict[str, Any] = {"fields": fields, "missingValues": [""]}
    if (
        candidate_key
        and not frame[candidate_key].isna().any().any()
        and not frame.duplicated(candidate_key).any()
    ):
        schema["primaryKey"] = candidate_key
    out: dict[str, Any] = {
        "name": f"external_{stem}",
        "type": "table",
        "path": relpath,
        **_format(relpath),
        "description": description
        + " Every row cites its source, url, retrieval date and a confidence grade (data/external/README.md).",
    }
    out.update(_file_block(relpath))
    grades = frame["confidence"].value_counts().to_dict() if "confidence" in frame.columns else {}
    out["x-confidence-grades"] = {str(k): int(v) for k, v in sorted(grades.items())}
    out["licenses"] = [metadata.LICENSES["data"]]
    out["sources"] = [{"title": upstream}]
    out["x-documentation"] = "data/external/README.md"
    out["schema"] = schema
    return out


def manifest_resource(name: str, relpath: str, description: str) -> dict[str, Any]:
    out: dict[str, Any] = {
        "name": name,
        "path": relpath,
        **_format(relpath),
        "description": description,
    }
    out.update(_file_block(relpath))
    out["licenses"] = [metadata.LICENSES["data"]]
    out["x-role"] = "provenance"
    return out


def regenerated() -> list[dict[str, Any]]:
    """The layers a reader rebuilds rather than downloads, with the command that does it."""
    return [
        {
            "name": "staged_flights",
            "x-path-pattern": "data/staged/year=*/part-0.parquet",
            "format": "parquet",
            "description": RESOURCE_NOTES["staged"],
            "x-command": "just fetch && just stage",
            "x-approx-bytes": 253_000_000,
            "x-manifest": "data/staged/manifest.json",
            "schema": {"fields": [_field(column, []) for column in STAGED]},
        },
        {
            "name": "flights_features",
            "x-path-pattern": "data/derived/ml/year=*/part-0.parquet",
            "format": "parquet",
            "description": RESOURCE_NOTES["ml"],
            "x-command": "just predict-dataset",
            "x-approx-bytes": 316_000_000,
            "x-manifest": "data/derived/ml/manifest.json",
            "schema": {"fields": [_field(column, []) for column in ML]},
        },
    ]


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


def _created() -> str:
    stamps = []
    for relpath in (
        "data/analysis/manifest.json",
        "data/analysis/panel_manifest.json",
        "data/analysis/article_panel_manifest.json",
    ):
        path = paths.REPO_ROOT / relpath
        if path.exists():
            stamps.append(json.loads(path.read_text(encoding="utf-8")).get("generated_at", ""))
    return max(stamps) if stamps else ""


def package_descriptor(resources: list[dict[str, Any]], doi: str | None = None) -> dict[str, Any]:
    """The package-level descriptor around `resources`.

    ``id`` is **omitted** until a DOI exists: a placeholder there would be a dead
    identifier harvesters resolve. ``x-pending-doi`` says the omission is
    deliberate; pass ``doi=`` (or set `metadata.DOI`) and both flip together.
    """
    doi = doi or metadata.DOI
    identity: dict[str, Any] = (
        {"id": f"https://doi.org/{doi}"}
        if doi
        else {
            "x-pending-doi": True,
            "x-pending-doi-note": (
                "No DOI has been minted yet; `id` is omitted rather than filled with a "
                "placeholder. The Zenodo deposit is the next milestone in ROADMAP.md."
            ),
        }
    )
    contributors = []
    for creator in metadata.CREATORS:
        entry: dict[str, Any] = {
            "title": f"{creator['given_names']} {creator['family_names']}",
            "givenName": creator["given_names"],
            "familyName": creator["family_names"],
            "organization": creator["affiliation"],
            "roles": ["creator", "maintainer", "publisher"],
        }
        if creator.get("orcid"):
            entry["path"] = f"https://orcid.org/{creator['orcid']}"
        contributors.append(entry)
    return {
        "$schema": PROFILE,
        "name": "airline-delays",
        **identity,
        "title": metadata.TITLE,
        "description": metadata.DESCRIPTION,
        "homepage": metadata.HOMEPAGE,
        "version": metadata.version(),
        "created": _created(),
        "keywords": list(metadata.KEYWORDS),
        "licenses": [metadata.LICENSES["data"]],
        "contributors": contributors,
        "sources": [dict(source) for source in metadata.SOURCES],
        "resources": resources,
        "x-code-license": metadata.LICENSES["code"],
        "x-attribution": metadata.ATTRIBUTION_VRA,
        "x-regenerated": regenerated(),
    }


def build(root: Path = paths.REPO_ROOT, *, doi: str | None = None) -> dict[str, Any]:
    """The descriptor for every resource whose table exists under `root`."""
    layers = built_layers(root)
    resources: list[dict[str, Any]] = []
    for layer, entries in RESOURCES.items():
        if layer not in layers:
            continue
        sources = (
            [
                {"title": metadata.ATTRIBUTION_VRA, "path": metadata.VRA_CATALOGUE_URL},
                {"title": metadata.SOURCES[2]["title"], "path": metadata.SOURCES[2]["path"]},
                {"title": metadata.SOURCES[-1]["title"], "path": metadata.SOURCES[-1]["path"]},
            ]
            if layer == "article_panel"
            else None
        )
        for name, path, key in entries:
            resources.append(
                resource(
                    name,
                    path,
                    layers[layer],
                    key,
                    description=RESOURCE_NOTES.get(layer),
                    sources=sources,
                )
            )
    resources += [external_resource(stem) for stem in EXTERNAL_TABLES]
    resources += [
        manifest_resource(name, relpath, description) for name, relpath, description in MANIFESTS
    ]
    return package_descriptor(resources, doi=doi)


def render(root: Path = paths.REPO_ROOT, *, doi: str | None = None) -> str:
    return json.dumps(build(root, doi=doi), indent=2, ensure_ascii=False) + "\n"
