"""The fetch manifest: one entry per downloaded file with its URL, size, sha256 and retrieval time."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

BASE_URL = "https://siros.anac.gov.br/siros/registros/diversos/vra"

CHUNK_BYTES = 1 << 20


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
