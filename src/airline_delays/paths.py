"""Repository paths, resolved once from this file's location.

The only place in the package that walks up the tree: every stage imports
these constants instead of counting `parents[N]` itself.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT: Path = Path(__file__).resolve().parents[2]
DATA: Path = REPO_ROOT / "data"
RAW: Path = DATA / "raw"
STAGED: Path = DATA / "staged"
DERIVED: Path = DATA / "derived"
ANALYSIS: Path = DATA / "analysis"
EXTERNAL: Path = DATA / "external"
REPORTS: Path = REPO_ROOT / "reports"
REPLICATION_REPORTS: Path = REPORTS / "replication"
PREDICTION_REPORTS: Path = REPORTS / "prediction"
THEORY_REPORTS: Path = REPORTS / "theory"
DOCS: Path = REPO_ROOT / "docs"
FIXTURES: Path = REPO_ROOT / "tests" / "fixtures"
