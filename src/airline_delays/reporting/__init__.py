"""Stage 9 -- reporting: the numbers manifest and the compiled reports.

``summary`` reads every committed manifest and report and writes
``reports/summary.json``: the only source of numbers the READMEs quote
(`airline-delays summary`). ``typst`` compiles the three Typst reports under
``reports/`` into the tracked ``reports/pdf/`` (`airline-delays report`).
"""

from __future__ import annotations

from .summary import SUMMARY_PATH, build, check, write
from .typst import REPORTS, compile_all

__all__ = ["REPORTS", "SUMMARY_PATH", "build", "check", "compile_all", "write"]
