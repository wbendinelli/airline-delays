"""The article's estimation panel, curated once from the authors' final base (ADR-0020).

Tables 2-7 of Bendinelli, Bettini & Oliveira (2016) were estimated on a route x
month panel the authors closed in December 2015 (a Stata file of 24,589 rows and
1,829 variables). This module reads that file **once**, on the author's machine,
keeps the columns the published tables use plus keys and context, and writes
them to ``data/analysis/article_panel_route_month.parquet`` (canonical) and
``.csv.gz`` (the same values at 32-bit precision) with a manifest. The output is
committed; CI never runs the curation.

What ships, and what does not
-----------------------------
The 52 columns of :data:`COLUMNS` -- the registry layer ``article_panel`` in
:mod:`airline_delays.schema.columns` -- are an explicit allowlist: keys and
geography, the flight counts every share is built on, the six regressands, the
nine exogenous regressors, the two concentration terms and the two the
reconstruction cannot compute, the seven instruments, and the components of the
two low-cost dummies. Not shipped: the 1,052 generated dummies (route and time
fixed effects and the 60 region x month seasonality dummies, rebuilt exactly by
:mod:`airline_delays.estimation.loader`), every column derived from a source
that is not open (weather cessions, airport-operator reports, tariff microdata
prices and revenues), and the base's own bookkeeping.

Curation is not transformation: values are never rounded, imputed or clipped.
Dtypes are tightened only where the cast is proven lossless on every non-null
value, and the invariants of the panel -- unique ``(od, ym)``, ``od == o-d``,
the composite low-cost dummies -- are asserted, not assumed.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

from airline_delays import paths
from airline_delays.definitions import nodes as nodes_mod
from airline_delays.estimation.loader import REGIONS
from airline_delays.estimation.specification import REQUIRED_COLUMNS
from airline_delays.fact.build import write_table
from airline_delays.schema.columns import ARTICLE_PANEL
from airline_delays.staging import git_commit, tool_versions

NAME = "article_panel_route_month"
PARQUET: Path = paths.ANALYSIS / f"{NAME}.parquet"
CSV: Path = paths.ANALYSIS / f"{NAME}.csv.gz"
MANIFEST: Path = paths.ANALYSIS / "article_panel_manifest.json"
KEY: tuple[str, ...] = ("od", "ym")

#: The 52 published columns, in the registry's order.
COLUMNS: tuple[str, ...] = tuple(column.name for column in ARTICLE_PANEL)
#: Target dtype per column, from the registry.
DTYPES: dict[str, str] = {column.name: column.dtype for column in ARTICLE_PANEL}

SOURCE_DESCRIPTION = (
    "the authors' final estimation base for Bendinelli, Bettini & Oliveira (2016): "
    "a Stata file of 24,589 route-months x 1,829 variables, header timestamp 3 Dec 2015"
)

_STRING = "string"


@dataclass(frozen=True)
class ArticlePanelResult:
    rows: int
    columns: int
    routes: int
    months: int
    parquet: Path
    csv: Path
    manifest: Path
    seconds: float


def read_source(source: Path) -> pd.DataFrame:
    """The 52 columns of the authors' base, read with the same reader the estimation used."""
    frame = pd.read_stata(source, columns=list(COLUMNS), convert_categoricals=False)
    return frame.loc[:, list(COLUMNS)]


def _lossless(values: pd.Series, dtype: str) -> bool:
    """True when casting every non-null value to `dtype` and back changes nothing."""
    present = values.dropna()
    if present.empty:
        return True
    if dtype == _STRING:
        return True
    cast = present.astype(dtype)
    return bool(np.array_equal(present.to_numpy(), cast.to_numpy().astype(present.dtype)))


def curate(frame: pd.DataFrame) -> pd.DataFrame:
    """Tighten dtypes, normalise keys, assert the panel's invariants. Nothing else."""
    out = frame.copy()
    for name in COLUMNS:
        dtype = DTYPES[name]
        if dtype == _STRING:
            out[name] = out[name].astype("string").str.strip()
            continue
        if not _lossless(out[name], dtype):
            raise ValueError(f"{name}: casting to {dtype} is not lossless; the curation stops")
        if out[name].isna().any() and dtype.startswith("int"):
            raise ValueError(f"{name}: has nulls and cannot be an integer column")
        out[name] = out[name].astype(dtype)
    for name in ("od", "o", "d", "o_uf", "d_uf"):
        out[name] = out[name].str.upper()

    duplicated = out.duplicated(list(KEY)).sum()
    if duplicated:
        raise ValueError(f"{duplicated} duplicated (od, ym) keys in the source")
    if not (out["ym"] == out["year"].astype("int32") * 100 + out["month"].astype("int32")).all():
        raise ValueError("ym != year*100 + month on some rows")
    if not (out["od"] == out["o"] + "-" + out["d"]).all():
        raise ValueError("od != o-d on some rows")
    unknown = set(out["o"]).union(out["d"]) - set(nodes_mod.PANEL_NODES)
    if unknown:
        raise ValueError(f"node codes outside ADR-0001's 27 nodes: {sorted(unknown)}")
    regions = set(out["o_region"]).union(out["d_region"]) - set(REGIONS.values())
    if regions:
        raise ValueError(f"unknown regions: {sorted(regions)}")
    if not (out["lcc"] == np.maximum(out["pres_glo"], out["pres_azu"])).all():
        raise ValueError("lcc != max(pres_glo, pres_azu) on some rows")
    if not (out["maxalccfu"] == np.maximum(out["olccfu"], out["dlccfu"])).all():
        raise ValueError("maxalccfu != max(olccfu, dlccfu) on some rows")
    missing_contract = [name for name in REQUIRED_COLUMNS if name not in out.columns]
    if missing_contract:
        raise ValueError(f"estimation contract not covered: {missing_contract}")
    return out.sort_values(list(KEY), ignore_index=True)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _source_metadata(source: Path) -> dict[str, object]:
    """Provenance of the source file without its path: description, sha256, header timestamp."""
    metadata: dict[str, object] = {"description": SOURCE_DESCRIPTION, "sha256": _sha256(source)}
    try:
        import pyreadstat

        _, meta = pyreadstat.read_dta(str(source), metadataonly=True)
        created = getattr(meta, "creation_time", None)
        metadata["stata_header_timestamp"] = created.isoformat() if created else None
        metadata["rows_in_source"] = int(getattr(meta, "number_rows", 0) or 0) or None
        metadata["variables_in_source"] = int(getattr(meta, "number_columns", 0) or 0) or None
    except (ImportError, OSError, ValueError):  # pragma: no cover - header read is best effort
        metadata["stata_header_timestamp"] = None
    return metadata


def _csv_text(frame: pd.DataFrame) -> pd.DataFrame:
    """Floats printed with nine significant digits (exact for float32), missing values empty."""
    out = frame.copy()
    for name in out.columns:
        if str(out[name].dtype).startswith("float"):
            values = out[name]
            out[name] = values.map(lambda v: "" if pd.isna(v) else f"{v:.9g}").astype("string")
    return out


def write(
    frame: pd.DataFrame, out_dir: Path, *, source_metadata: dict[str, object]
) -> ArticlePanelResult:
    """Parquet (zstd 9), csv.gz (deterministic, 9 significant digits) and the manifest."""
    started = time.time()
    out_dir.mkdir(parents=True, exist_ok=True)
    parquet = write_table(frame, out_dir / PARQUET.name)
    csv = out_dir / CSV.name
    with gzip.GzipFile(filename="", mode="wb", fileobj=csv.open("wb"), mtime=0) as handle:
        _csv_text(frame).to_csv(handle, index=False)
    manifest = out_dir / MANIFEST.name
    nulls = {name: int(frame[name].isna().sum()) for name in COLUMNS if frame[name].isna().any()}
    payload = {
        "layer": "article_panel",
        "grain": (
            "one row per directional city-pair route x month, 2002m1-2013m12: the estimation "
            "panel of Bendinelli, Bettini & Oliveira (2016)"
        ),
        "source": {
            **source_metadata,
            "columns_kept": len(COLUMNS),
            "columns_excluded": {
                "generated_dummies": "route and time fixed effects and the 60 region x month "
                "seasonality dummies, rebuilt by airline_delays.estimation.loader",
                "outside_the_contract": "every other variable of the source, among them all "
                "columns from non-open sources",
            },
        },
        "curation": {
            "module": "airline_delays.estimation.article_panel",
            "command": "airline-delays article-panel --source <the authors' base>",
            "git_commit": git_commit(paths.REPO_ROOT, short=True),
            "tool_versions": tool_versions(),
        },
        "rows": len(frame),
        "columns": int(frame.shape[1]),
        "routes": int(frame["od"].nunique()),
        "months": int(frame["ym"].nunique()),
        "ym_range": [int(frame["ym"].min()), int(frame["ym"].max())],
        "nulls": nulls,
        "files": {
            parquet.name: {"bytes": parquet.stat().st_size, "sha256": _sha256(parquet)},
            csv.name: {"bytes": csv.stat().st_size, "sha256": _sha256(csv)},
        },
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
    }
    manifest.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return ArticlePanelResult(
        rows=len(frame),
        columns=frame.shape[1],
        routes=payload["routes"],
        months=payload["months"],
        parquet=parquet,
        csv=csv,
        manifest=manifest,
        seconds=round(time.time() - started, 2),
    )


def build(source: Path, out_dir: Path | None = None) -> ArticlePanelResult:
    """Read the authors' base, curate it, write the three files. The path is not recorded."""
    source = Path(source).expanduser()
    if not source.exists():
        raise FileNotFoundError(f"source base not found: {source}")
    frame = curate(read_source(source))
    return write(frame, out_dir or paths.ANALYSIS, source_metadata=_source_metadata(source))
