"""Compile the Typst reports: `typst compile --root . reports/<name>.typ reports/pdf/<name>.pdf`.

The PDFs are tracked under ``reports/pdf/`` (DECISIONS.md ADR-0022), so a reader
gets the study without installing Typst; `airline-delays report` regenerates
them. The PDF creation timestamp is the release date of ``CITATION.cff``
(``date-released``, midnight UTC) -- the same date the reports print on their
first page -- so a rerun on an unchanged tree rewrites identical bytes and the
PDFs change only when the prose or a release does.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from airline_delays import paths

#: The three reports, in the order the README lists them.
REPORTS: tuple[str, ...] = ("study", "replication", "prediction")
PDF_DIR: Path = paths.REPORTS / "pdf"
CITATION: Path = paths.REPO_ROOT / "CITATION.cff"
_DATE_RELEASED = re.compile(r"^date-released:\s*'?(\d{4})-(\d{2})-(\d{2})'?\s*$", re.MULTILINE)


def release_date() -> datetime:
    """The ``date-released`` of ``CITATION.cff`` as midnight UTC."""
    match = _DATE_RELEASED.search(CITATION.read_text(encoding="utf-8"))
    if match is None:
        raise ValueError(f"no date-released in {CITATION}")
    year, month, day = (int(part) for part in match.groups())
    return datetime(year, month, day, tzinfo=UTC)


def creation_timestamp() -> int:
    """Unix time stamped into every PDF: the release date, so builds are reproducible."""
    return int(release_date().timestamp())


def compile_one(name: str) -> Path:
    """Compile one report; the PDF lands in ``reports/pdf/``."""
    if shutil.which("typst") is None:
        raise FileNotFoundError(
            "typst is not installed; the reports compile with Typst 0.13 or later "
            "(https://typst.app)"
        )
    source = paths.REPORTS / f"{name}.typ"
    if not source.exists():
        raise FileNotFoundError(f"no such report: {source}")
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    target = PDF_DIR / f"{name}.pdf"
    subprocess.run(
        [
            "typst",
            "compile",
            "--root",
            str(paths.REPO_ROOT),
            "--creation-timestamp",
            str(creation_timestamp()),
            str(source),
            str(target),
        ],
        check=True,
        cwd=paths.REPO_ROOT,
    )
    return target


def compile_all(only: tuple[str, ...] | None = None) -> list[Path]:
    """Compile every report (or the ones named in `only`)."""
    return [compile_one(name) for name in (only or REPORTS)]
