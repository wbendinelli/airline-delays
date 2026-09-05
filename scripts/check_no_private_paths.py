#!/usr/bin/env python3
"""Fail if the private research archive leaks into git *content*, not just paths.

The ``no-private-data`` pre-commit hook has always matched staged *path
names*, and ``tests/test_gabarito.py`` asserted on the contents of one module.
Neither looks inside an arbitrary tracked file, so 30 rows of
``data/external/*.csv`` shipped absolute
``file:///Users/…/pesquisa-acervo/…/_analises/…`` URLs and two private base
names for fourteen commits (audit 2026-09-05, finding B-2). This script closes
that gap and is the single source of truth for both callers:

* ``--staged`` -- the ``no-private-data`` pre-commit hook, over the staged
  blobs (so the check runs on what is about to enter git, not on the worktree).
* no flag -- ``tests/test_no_private_paths.py``, over every git-tracked text
  file.

Two tiers, because the two classes of string are not the same problem:

**Tier 1 -- the archive's own layout, forbidden everywhere.** An absolute path
into the author's machine, or any segment of the private archive's directory
tree. These say where the archive lives and how it is organised; nothing in a
public repository ever needs them, so the only exemptions are this file's own
pattern list and the audit report that reported the leak.

**Tier 2 -- the benchmark's file names.** ``proj18.dta``, the LABTAR/NECTAR
bases and ``vra.dta`` are named on purpose in the places that *declare* them
as the omission (``README.md``, ``SECURITY.md``, ``CLAUDE.md``, the data
availability statement) and in the code that reads them through
``AIRLINE_DELAYS_PRIVATE_DIR``. Naming a file that is not redistributed is
transparency, not a leak -- but only where a human decided so. Tier 2 is
therefore allowlisted per file: a mention in any *other* file, and in
particular anywhere under ``data/``, fails. Adding one means editing
``TIER2_ALLOWED`` in this file, which is exactly the review gate that was
missing.

The allowlist is also checked for rot: an entry that no longer matches
anything is an error, so it cannot quietly outlive the mention it covers.

Usage::

    uv run python scripts/check_no_private_paths.py            # all tracked files
    uv run python scripts/check_no_private_paths.py --staged   # pre-commit
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Tier 1: the private archive's location and layout. Never legitimate.
TIER1 = (
    r"pesquisa-acervo",
    r"_recebidos",
    r"_analises/",
    r"file:///Users/",
    r"/Users/[A-Za-z0-9._-]+/Documents",
)

# Tier 2: the private benchmark's own file names, legitimate only where the
# repository declares them as the omission or reads them through the
# environment variable.
TIER2 = (
    r"proj18",
    r"labtar",
    r"nectarbase",
    r"\.dta\b",
)

# Files that may name the private benchmark, and why. Anything not listed here
# fails on a tier-2 match; `data/**` is never listed.
TIER2_ALLOWED = {
    "CLAUDE.md": "hard rule: these files never enter git",
    "CONTRIBUTING.md": "same rule, for outside contributors",
    "README.md": "declares the benchmark as the one non-public input",
    "SECURITY.md": "states how the benchmark is reached and never stored",
    "CHANGELOG.md": "history of the reconciliation work",
    "data/private/README.md": "explains what the ignored directory is for",
    "docs/data-availability.md": "source 12 of the availability statement",
    "docs/declared-differences.md": "names the vintage a difference is against",
    "docs/notes/features.md": "research-evidence note on the reconciliation",
    "docs/notes/monografia-2013.md": "names the 2013 do-file and its laboratory base as outside documents, never redistributed",
    "docs/notes/references.md": "research-evidence note on the reference tables",
    "docs/notes/staging.md": "research-evidence note on the staging comparison",
    "docs/tutorial/06-dados-fonte-ao-painel.md": "teaches the reconciliation",
    "docs/tutorial/08-o-que-reproduz.md": "teaches what does not reproduce",
    "docs/tutorial/09-da-dissertacao-ao-artigo.md": "dates the final base",
    "docs/tutorial/12-consentimento-licencas-publicacao.md": "teaches this guard",
    "replication/common.py": "resolves the benchmark under the private dir",
    "replication/gabarito/compare.py": "reads the benchmark",
    "replication/sensitivity.py": "documents the benchmark's aggregation",
    "reports/README.md": "lists which report needs the private input",
    "reports/reconciliation.md": "the reconciliation report itself",
    "scripts/README.md": "lists which script needs the private input",
    "scripts/verify_reconcile.py": "reads the 2019 vintage",
    "src/vra/cli.py": "docstring of the optional reconcile command",
    ".pre-commit-config.yaml": "the hook's own pattern list",
    "scripts/check_no_private_paths.py": "this file's own pattern list",
    "docs/audit/2026-09-05-pre-publication.md": "the audit that found the leak",
}

# Files exempt from tier 1 as well: the pattern lists themselves and the audit
# report that documented the leak.
TIER1_ALLOWED = {
    "scripts/check_no_private_paths.py",
    "tests/test_gabarito.py",
    "docs/audit/2026-09-05-pre-publication.md",
}

_TIER1_RE = re.compile("|".join(TIER1), re.IGNORECASE)
_TIER2_RE = re.compile("|".join(TIER2), re.IGNORECASE)

# Lines that MUST be rejected, kept here rather than in the test so the test
# module itself stays free of the strings it hunts for. Each is (line, tier).
MUST_REJECT = (
    ("url,file:///Users/someone/Documents/pesquisa-acervo/a/_analises/b.py", 1),
    ("cf. /Users/someone/Documents/archive/note.md", 1),
    ("the deliverables live under _recebidos/", 1),
    ("read from proj18.dta", 2),
    ("nectarbase_delays_v005.dta", 2),
    ("the LABTAR base", 2),
)

# Lines that must NOT be rejected: ordinary prose that merely looks close.
MUST_ACCEPT = (
    "the reference tables cite the author's research notes (private, not redistributed)",
    "data/analysis/taxas.csv holds the agreement rates",
    "docs/notes/references.md documents every row's provenance",
)


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout


def tracked_files() -> list[str]:
    """Every file git tracks, as repository-relative POSIX paths."""
    return [line for line in _git("ls-files", "-z").split("\0") if line]


def staged_files() -> list[str]:
    """Files added, copied or modified in the index."""
    out = _git("diff", "--cached", "--name-only", "-z", "--diff-filter=ACM")
    return [line for line in out.split("\0") if line]


def _read(name: str, *, staged: bool) -> str | None:
    """The file's text, from the index when staged, else from the worktree.

    Returns ``None`` for anything that is not decodable text -- parquet, gzip
    and the like carry no prose to leak.
    """
    try:
        if staged:
            raw = subprocess.run(
                ["git", "show", f":{name}"], cwd=ROOT, capture_output=True, check=True
            ).stdout
        else:
            raw = (ROOT / name).read_bytes()
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return None
    if b"\0" in raw[:8192]:
        return None
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return None


def problems_in(name: str, text: str) -> tuple[list[str], bool]:
    """Scan one file's text. Returns (problems, whether tier 2 matched at all)."""
    problems: list[str] = []
    matched_tier2 = False
    for number, line in enumerate(text.splitlines(), start=1):
        hit = _TIER1_RE.search(line)
        if hit and name not in TIER1_ALLOWED:
            problems.append(
                f"{name}:{number}: `{hit.group(0)}` -- the private archive's "
                "path or layout must never appear in git content"
            )
        hit = _TIER2_RE.search(line)
        if hit:
            matched_tier2 = True
            if name not in TIER2_ALLOWED:
                problems.append(
                    f"{name}:{number}: `{hit.group(0)}` -- the private benchmark's "
                    "file names are allowed only where the repository declares "
                    "them; add the file to TIER2_ALLOWED in "
                    "scripts/check_no_private_paths.py if that is deliberate"
                )
    return problems, matched_tier2


def scan(names: list[str], *, staged: bool = False) -> tuple[list[str], set[str]]:
    """Return (problems, files that matched tier 2) for the given files."""
    problems: list[str] = []
    matched_tier2: set[str] = set()
    for name in sorted(names):
        text = _read(name, staged=staged)
        if text is None:
            continue
        found, matched = problems_in(name, text)
        problems += found
        if matched:
            matched_tier2.add(name)
    return problems, matched_tier2


def main(argv: list[str]) -> int:
    staged = "--staged" in argv
    names = staged_files() if staged else tracked_files()
    problems, matched = scan(names, staged=staged)
    if not staged:
        tracked = set(names)
        stale = sorted(
            name
            for name in TIER2_ALLOWED
            if name in tracked and name not in matched  # allowlisted, nothing to allow
        )
        problems += [
            f"{name}: allowlisted in TIER2_ALLOWED but no longer names the "
            "private benchmark -- drop the entry"
            for name in stale
        ]
    if problems:
        print("no-private-data: private research archive found in git content:")
        for problem in problems:
            print(f"  {problem}")
        return 1
    print(f"no-private-data: {len(names)} file(s) checked, no private path in content")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
