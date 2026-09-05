"""Discovery, download and layout description of the raw ANAC VRA monthly files.

The raw files live on an IIS directory listing at
``https://siros.anac.gov.br/siros/registros/diversos/vra/{year}/``. The listing
is the authority on which files exist: file names follow two known patterns
(``VRA_{year}{month}.csv`` with an unpadded month up to 2009 and
``VRA_{year}_{MM}.csv`` from 2010), but the fetcher never guesses — it parses
the listing and falls back to the patterns only when the listing is
unreachable.

Two raw layouts exist in 2000-2013 and this module names them:

``LAYOUT_LEGACY`` (2000-2009)
    12 columns, comma separated, latin-1, CRLF line endings, no quoting.
    ``Código Justificativa`` carries the two-letter IAC 1504 code directly, or
    the literal ``N/A`` when the flight had no occurrence.

``LAYOUT_2010`` (2010-2013)
    20 columns, semicolon separated, UTF-8, LF line endings, no quoting. Column
    order differs
    from the legacy layout: the origin airport and its description come before
    the departure timestamps, and the destination airport and its description
    come before the arrival timestamps. ``Justificativa`` carries the free
    text of the IAC 1504 justification, not the code, so `stage` maps the text
    back to the code.

Everything downloaded is recorded in ``data/raw/manifest.json`` with url,
file, bytes, sha256, retrieved_at and http_status, which makes `fetch`
idempotent: a file whose sha256 already matches the manifest is skipped.
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - typing only
    import requests

BASE_URL = "https://siros.anac.gov.br/siros/registros/diversos/vra"
YEARS = tuple(range(2000, 2014))

USER_AGENT = "airline-delays/0.1 (research; https://github.com/wbendinelli/airline-delays)"
REQUEST_DELAY_S = 0.5
"""Politeness delay between two requests to the same host."""

MAX_RETRIES = 4
RETRY_BACKOFF_S = 3.0
CHUNK_BYTES = 1 << 20


# --------------------------------------------------------------------------- layouts


@dataclass(frozen=True)
class RawLayout:
    """A raw CSV layout: how to read the file and where each field sits."""

    name: str
    years: tuple[int, ...]
    separator: str
    encoding: str
    n_columns: int
    columns: tuple[str, ...]
    datetime_format: str
    cause_is_code: bool
    """True when the justification column holds the two-letter IAC 1504 code."""

    quoting: str = "none"
    line_ending: str = "crlf"


LAYOUT_LEGACY = RawLayout(
    name="legacy_12col",
    years=tuple(range(2000, 2010)),
    separator=",",
    encoding="latin-1",
    n_columns=12,
    columns=(
        "ICAO Empresa Aérea",
        "Número Voo",
        "Código Autorização (DI)",
        "Código Tipo Linha",
        "ICAO Aeródromo Origem",
        "ICAO Aeródromoo Destino",  # the typo is in the source file
        "Partida Prevista",
        "Partida Real",
        "Chegada Prevista",
        "Chegada Real",
        "Situação Voo",
        "Código Justificativa",
    ),
    datetime_format="%d/%m/%Y %H:%M",
    cause_is_code=True,
)

LAYOUT_2010 = RawLayout(
    name="wide_20col",
    years=tuple(range(2010, 2014)),
    separator=";",
    encoding="utf-8",
    n_columns=20,
    columns=(
        "Sigla ICAO Empresa Aérea",
        "Empresa Aérea",
        "Número Voo",
        "Código DI",
        "Código Tipo Linha",
        "Modelo Equipamento",
        "Número de Assentos",
        "Sigla ICAO Aeroporto Origem",
        "Descrição Aeroporto Origem",
        "Partida Prevista",
        "Partida Real",
        "Sigla ICAO Aeroporto Destino",
        "Descrição Aeroporto Destino",
        "Chegada Prevista",
        "Chegada Real",
        "Situação Voo",
        "Justificativa",
        "Referência",
        "Situação Partida",
        "Situação Chegada",
    ),
    datetime_format="%d/%m/%Y %H:%M",
    cause_is_code=False,
    line_ending="lf",
)

LAYOUTS: tuple[RawLayout, ...] = (LAYOUT_LEGACY, LAYOUT_2010)


def layout_for(year: int) -> RawLayout:
    """Return the raw layout that applies to `year`."""
    for layout in LAYOUTS:
        if year in layout.years:
            return layout
    raise ValueError(f"no known raw layout for year {year}")


# --------------------------------------------------------------------------- discovery

_HREF_RE = re.compile(r'HREF="(/siros/registros/diversos/vra/\d{4}/[^"]+\.csv)"', re.IGNORECASE)
_MONTH_RE = re.compile(r"VRA_(\d{4})_?(\d{1,2})\.csv$", re.IGNORECASE)


@dataclass(frozen=True)
class RemoteFile:
    """One monthly CSV on the ANAC server."""

    year: int
    month: int
    name: str
    url: str


def expected_names(year: int) -> list[str]:
    """The file names the two known patterns predict for `year`.

    Used only as a fallback when the directory listing cannot be read.
    """
    if year >= 2010:
        return [f"VRA_{year}_{m:02d}.csv" for m in range(1, 13)]
    return [f"VRA_{year}{m}.csv" for m in range(1, 13)]


def list_year(year: int, session: requests.Session | None = None) -> list[RemoteFile]:
    """List the monthly files of `year` by parsing the server's directory index.

    Falls back to `expected_names` when the index cannot be fetched. Any file
    name that does not match the two known month patterns is still returned,
    with month 0, so that an unknown pattern is downloaded and reported rather
    than silently dropped.
    """
    import requests

    session = session or _session()
    url = f"{BASE_URL}/{year}/"
    names: list[str]
    try:
        response = session.get(url, timeout=60)
        response.raise_for_status()
        names = sorted({Path(href).name for href in _HREF_RE.findall(response.text)})
    except requests.RequestException:
        names = expected_names(year)
    out: list[RemoteFile] = []
    for name in names:
        match = _MONTH_RE.search(name)
        month = int(match.group(2)) if match and int(match.group(1)) == year else 0
        out.append(RemoteFile(year=year, month=month, name=name, url=f"{BASE_URL}/{year}/{name}"))
    return sorted(out, key=lambda f: (f.month, f.name))


# --------------------------------------------------------------------------- manifest


@dataclass
class ManifestEntry:
    url: str
    file: str
    bytes: int
    sha256: str
    retrieved_at: str
    http_status: int
    year: int = 0
    month: int = 0

    def as_dict(self) -> dict:
        return {
            "url": self.url,
            "file": self.file,
            "bytes": self.bytes,
            "sha256": self.sha256,
            "retrieved_at": self.retrieved_at,
            "http_status": self.http_status,
            "year": self.year,
            "month": self.month,
        }


@dataclass
class Manifest:
    """The `data/raw/manifest.json` document, keyed by repository-relative path."""

    path: Path
    entries: dict[str, ManifestEntry] = field(default_factory=dict)
    source: str = BASE_URL

    @classmethod
    def load(cls, path: Path) -> Manifest:
        manifest = cls(path=path)
        if path.exists():
            raw = json.loads(path.read_text(encoding="utf-8"))
            for item in raw.get("files", []):
                entry = ManifestEntry(
                    url=item["url"],
                    file=item["file"],
                    bytes=item["bytes"],
                    sha256=item["sha256"],
                    retrieved_at=item["retrieved_at"],
                    http_status=item["http_status"],
                    year=item.get("year", 0),
                    month=item.get("month", 0),
                )
                manifest.entries[entry.file] = entry
        return manifest

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        files = [self.entries[key].as_dict() for key in sorted(self.entries)]
        document = {
            "dataset": "ANAC Voo Regular Ativo (VRA)",
            "source": self.source,
            "attribution": "ANAC, Voo Regular Ativo (VRA), via dados.gov.br",
            "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
            "n_files": len(files),
            "total_bytes": sum(item["bytes"] for item in files),
            "files": files,
        }
        self.path.write_text(
            json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )


def sha256_file(path: Path, chunk: int = CHUNK_BYTES) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(chunk):
            digest.update(block)
    return digest.hexdigest()


# --------------------------------------------------------------------------- fetch


def _session() -> requests.Session:
    import requests

    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    return session


def _download(url: str, target: Path, session: requests.Session) -> tuple[int, int]:
    """Download `url` to `target` atomically. Returns (http_status, bytes)."""
    import requests

    tmp = target.with_suffix(target.suffix + ".part")
    last: Exception | None = None
    for attempt in range(MAX_RETRIES):
        try:
            with session.get(url, stream=True, timeout=(30, 300)) as response:
                status = response.status_code
                response.raise_for_status()
                target.parent.mkdir(parents=True, exist_ok=True)
                written = 0
                with tmp.open("wb") as handle:
                    for block in response.iter_content(chunk_size=CHUNK_BYTES):
                        handle.write(block)
                        written += len(block)
            tmp.replace(target)
            return status, written
        except requests.RequestException as exc:
            last = exc
            tmp.unlink(missing_ok=True)
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_BACKOFF_S * (attempt + 1))
    raise RuntimeError(f"failed to download {url} after {MAX_RETRIES} attempts") from last


def fetch(
    raw_dir: Path,
    years: tuple[int, ...] = YEARS,
    manifest_path: Path | None = None,
    force: bool = False,
    delay_s: float = REQUEST_DELAY_S,
) -> Iterator[str]:
    """Download every monthly CSV of `years` into ``raw_dir/vra/{year}/``.

    Sequential and polite by design. Yields one progress line per file so a CLI
    can print it. Idempotent: a file already on disk whose sha256 matches the
    manifest is skipped unless `force`.
    """
    raw_dir = Path(raw_dir)
    manifest_path = manifest_path or raw_dir / "manifest.json"
    manifest = Manifest.load(manifest_path)
    session = _session()
    for year in years:
        remote_files = list_year(year, session=session)
        yield f"{year}: {len(remote_files)} files listed"
        for remote in remote_files:
            target = raw_dir / "vra" / str(year) / remote.name
            # Manifest keys are repository-relative on purpose: the file must be
            # identifiable from a clone, not from this machine's absolute paths.
            key = f"data/raw/vra/{year}/{remote.name}"
            known = manifest.entries.get(key)
            if (
                not force
                and known
                and target.exists()
                and target.stat().st_size == known.bytes
                and sha256_file(target) == known.sha256
            ):
                yield f"  skip {remote.name} ({known.bytes:,} B, sha256 matches)"
                continue
            status, written = _download(remote.url, target, session)
            manifest.entries[key] = ManifestEntry(
                url=remote.url,
                file=key,
                bytes=written,
                sha256=sha256_file(target),
                retrieved_at=datetime.now(UTC).isoformat(timespec="seconds"),
                http_status=status,
                year=year,
                month=remote.month,
            )
            manifest.save()
            yield f"  got  {remote.name} ({written:,} B, HTTP {status})"
            time.sleep(delay_s)
    manifest.save()
    yield f"manifest: {len(manifest.entries)} files, {sum(e.bytes for e in manifest.entries.values()):,} bytes"


# --------------------------------------------------------------------------- inspection


def read_header(path: Path, layout: RawLayout | None = None) -> list[str]:
    """Read the header line of a raw file and split it on its separator."""
    path = Path(path)
    if layout is None:
        year = int(path.parent.name) if path.parent.name.isdigit() else 2002
        layout = layout_for(year)
    with path.open("rb") as handle:
        first = handle.readline()
    return first.decode(layout.encoding).strip("\r\n").split(layout.separator)


def inspect_file(path: Path, sample_lines: int = 5000) -> dict:
    """Measure a raw file instead of assuming: separator, encoding, columns, quirks.

    Returns a dictionary that `docs/notes/staging.md` and the tests consume.
    """
    path = Path(path)
    with path.open("rb") as handle:
        head = handle.read(1 << 20)
    encoding = "utf-8"
    try:
        head.decode("utf-8")
    except UnicodeDecodeError:
        encoding = "latin-1"
    text = head.decode(encoding, errors="replace")
    lines = text.splitlines()[: sample_lines + 1]
    header = lines[0] if lines else ""
    separator = ";" if header.count(";") > header.count(",") else ","
    columns = header.split(separator)
    widths: dict[int, int] = {}
    for line in lines[1:-1]:
        widths[line.count(separator) + 1] = widths.get(line.count(separator) + 1, 0) + 1
    return {
        "file": path.name,
        "encoding": encoding,
        "separator": separator,
        "n_columns": len(columns),
        "columns": columns,
        "line_ending": "crlf" if "\r\n" in text[:4096] else "lf",
        "has_quotes": '"' in text,
        "field_count_histogram": dict(sorted(widths.items())),
        "bytes": path.stat().st_size,
    }
