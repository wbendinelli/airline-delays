"""No tracked text file carries a path into somebody's machine.

Manifests and reports record repository-relative paths, file names and hashes;
an absolute path (`/Users/...`, `/Volumes/...`, `file:///...`) in a committed
file is a defect, whatever it points at.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATTERN = re.compile(r"(/Users/|/Volumes/|file:///|C:\\\\Users\\\\)")
EXTENSIONS = {
    ".md",
    ".typ",
    ".cff",
    ".yml",
    ".yaml",
    ".toml",
    ".py",
    ".json",
    ".sql",
    ".txt",
    ".csv",
}
EXEMPT = {"tests/test_no_local_paths.py", "tests/test_article_panel.py"}


def test_no_absolute_local_path_in_tracked_files() -> None:
    names = subprocess.run(
        ["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.split()
    hits = []
    for name in names:
        if Path(name).suffix not in EXTENSIONS or name in EXEMPT:
            continue
        text = (ROOT / name).read_text(encoding="utf-8", errors="replace")
        for number, line in enumerate(text.splitlines(), 1):
            if PATTERN.search(line):
                hits.append(f"{name}:{number}: {line.strip()[:100]}")
    assert hits == [], "\n".join(hits[:30])
