"""Compile the Typst reports: `typst compile --root . reports/<name>.typ reports/build/<name>.pdf`."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from airline_delays import paths

#: The three reports, in the order the README lists them.
REPORTS: tuple[str, ...] = ("replication", "prediction", "theory")
BUILD_DIR: Path = paths.REPORTS / "build"


def compile_one(name: str) -> Path:
    """Compile one report; the PDF lands in ``reports/build/``."""
    if shutil.which("typst") is None:
        raise FileNotFoundError(
            "typst is not installed; the reports compile with Typst 0.13 or later "
            "(https://typst.app)"
        )
    source = paths.REPORTS / f"{name}.typ"
    if not source.exists():
        raise FileNotFoundError(f"no such report: {source}")
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    target = BUILD_DIR / f"{name}.pdf"
    subprocess.run(
        ["typst", "compile", "--root", str(paths.REPO_ROOT), str(source), str(target)],
        check=True,
        cwd=paths.REPO_ROOT,
    )
    return target


def compile_all(only: tuple[str, ...] | None = None) -> list[Path]:
    """Compile every report (or the ones named in `only`)."""
    return [compile_one(name) for name in (only or REPORTS)]
