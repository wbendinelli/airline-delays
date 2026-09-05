"""The vocabulary that does not appear in this repository's prose (style guide, rule 7)."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FORBIDDEN = [
    r"\bgabarito\b",
    r"\bNECTAR\b",
    r"\bLABTAR\b",
    r"\bproj18\b",
    r"\bvra\.dta\b",
    r"private benchmark",
    r"laboratory base",
    r"base de laborat[óo]rio",
    r"declared[- ]differences?",
    r"not adjusted away",
    r"AIRLINE_DELAYS_PRIVATE_DIR",
    r"data/private\b",
    r"\btaxas\.csv\b",
    r"\breconciliation\.md\b",
    r"\bnota honesta\b",
    r"\btop journal\b",
]
#: `benchmark` is allowed only in the economics sense of the theory chapters.
BENCHMARK_ALLOWED_DIRS = (
    "docs/theory/",
    "reports/theory",
    "reports/theory.typ",
    "src/airline_delays/theory/",
)
EXTENSIONS = {".md", ".typ", ".cff", ".yml", ".yaml", ".toml", ".py", ".json", ".sql", ".txt"}
EXEMPT = {"tests/test_prose_vocabulary.py", "docs/editorial/style-guide.md", "CHANGELOG.md"}


def _tracked_text_files() -> list[Path]:
    names = subprocess.run(
        ["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.split()
    return [
        ROOT / n
        for n in names
        if Path(n).suffix in EXTENSIONS and n not in EXEMPT and not n.startswith("tests/fixtures/")
    ]


def test_the_forbidden_vocabulary_is_gone() -> None:
    hits = []
    pattern = re.compile("|".join(FORBIDDEN), flags=re.IGNORECASE)
    for path in _tracked_text_files():
        for number, line in enumerate(
            path.read_text(encoding="utf-8", errors="replace").splitlines(), 1
        ):
            if pattern.search(line):
                hits.append(f"{path.relative_to(ROOT)}:{number}: {line.strip()[:100]}")
    assert hits == [], "\n".join(hits[:40])


def test_benchmark_only_in_its_economics_sense() -> None:
    hits = []
    for path in _tracked_text_files():
        rel = str(path.relative_to(ROOT))
        if rel.startswith(BENCHMARK_ALLOWED_DIRS) or rel.endswith("published.json"):
            continue
        for number, line in enumerate(
            path.read_text(encoding="utf-8", errors="replace").splitlines(), 1
        ):
            if re.search(r"\bbenchmarks?\b", line, flags=re.IGNORECASE):
                hits.append(f"{rel}:{number}: {line.strip()[:100]}")
    assert hits == [], "\n".join(hits[:40])
