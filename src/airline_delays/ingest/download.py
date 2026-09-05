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

import re
import time
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - typing only
    import requests
from airline_delays.ingest.manifest import (
    BASE_URL,
    CHUNK_BYTES,
    Manifest,
    ManifestEntry,
    sha256_file,
)

YEARS = tuple(range(2000, 2014))

USER_AGENT = "airline-delays/0.1 (research; https://github.com/wbendinelli/airline-delays)"

REQUEST_DELAY_S = 0.5

"""Politeness delay between two requests to the same host."""

MAX_RETRIES = 4

RETRY_BACKOFF_S = 3.0

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
