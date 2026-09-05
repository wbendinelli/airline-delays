#!/usr/bin/env python
"""Thin wrapper around `vra.io.fetch` for use outside the CLI.

Downloads the monthly ANAC VRA CSVs for 2000-2013 into ``data/raw/vra/{year}/``
and records url, bytes, sha256, retrieval time and HTTP status in
``data/raw/manifest.json``. Sequential, polite and idempotent.

Usage:
    uv run python scripts/fetch.py [--years 2002 2003] [--force]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from vra.io import YEARS, fetch

ROOT = Path(__file__).resolve().parents[1]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--years", type=int, nargs="*", default=list(YEARS))
    parser.add_argument("--raw-dir", type=Path, default=ROOT / "data" / "raw")
    parser.add_argument(
        "--force", action="store_true", help="re-download even when the sha256 matches"
    )
    args = parser.parse_args(argv)
    for line in fetch(args.raw_dir, years=tuple(args.years), force=args.force):
        print(line, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
