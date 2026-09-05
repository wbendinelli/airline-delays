#!/usr/bin/env python
"""Every number in the entry pages is a value of `reports/summary.json`.

Numeric tokens are read from the prose of the entry pages (fenced code and
inline code are skipped, as are URLs); each must equal, in one of the accepted
renderings, a numeric leaf of `reports/summary.json` -- or sit on a line that
marks an outside document ("(article, Table 1)", "documento externo"), or be
listed in `docs/editorial/number-allowlist.txt` with a reason. Years, DOIs,
versions, ADR, table, module and footnote numbers are not measurements and are
skipped.

Usage::

    uv run python scripts/check_prose_numbers.py            # the entry pages
    uv run python scripts/check_prose_numbers.py README.md  # one file
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "reports" / "summary.json"
ALLOWLIST = ROOT / "docs" / "editorial" / "number-allowlist.txt"
ENTRY_PAGES = [
    "README.md",
    "README.pt-BR.md",
    "docs/README.md",
    "docs/README.pt-BR.md",
    "data/README.md",
    "data/README.pt-BR.md",
    "CONTRIBUTING.md",
    "CONTRIBUTING.pt-BR.md",
]

FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
INLINE_CODE_RE = re.compile(r"`[^`\n]*`")
URL_RE = re.compile(r"https?://\S+|doi\.org/\S+|10\.\d{4,}/\S+")
BADGE_RE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
NUMBER_RE = re.compile(r"(?<![\w.,/-])[+-]?\d[\d.,]*(?:%|)")
OUTSIDE_RE = re.compile(
    r"\(article,|\(artigo,|documento externo|outside document|Table 1\b|Tabela 1\b|monografia",
    re.IGNORECASE,
)
SKIP_RE = re.compile(
    r"^(19\d\d|20\d\d|200\d\d\d|201\d\d\d|\d{4}-\d{2}(-\d{2})?|[0-3]?\d\.[01]?\d\.\d{2,4}|0\.\d+\.\d+|\d+\.\d+\.\d+)$"
)


def _renderings(value: float, *, share_like: bool = False) -> set[str]:
    """The strings a prose token may take for one numeric leaf (signs are compared apart).

    Integers render plain and with thousands separators in both languages; floats
    with 0-4 decimals in both languages; a share-like leaf (0-1, under a key that
    names a share, rate or percentage) also as a percentage.
    """
    out: set[str] = set()
    if isinstance(value, bool):
        return out
    value = abs(value)
    if isinstance(value, int):
        text = f"{value:,}"
        out.update({str(value), text, text.replace(",", "."), str(value) + "%", text + "%"})
        return out
    for digits in range(5):
        text = f"{value:,.{digits}f}"
        pt = text.replace(",", "@").replace(".", ",").replace("@", ".")
        out.update({text, pt, text + "%", pt + "%"})
    if share_like and 0 <= value <= 1:
        for digits in range(3):
            pct = f"{100 * value:.{digits}f}"
            out.update({pct, pct.replace(".", ","), pct + "%", pct.replace(".", ",") + "%"})
    return out


SHARE_KEYS = ("share", "rate", "pct", "excess", "linked")


def _leaves(node, path: str = "") -> list[tuple[str, float | int]]:
    if isinstance(node, dict):
        return [leaf for key, value in node.items() for leaf in _leaves(value, f"{path}.{key}")]
    if isinstance(node, list):
        return [leaf for value in node for leaf in _leaves(value, path)]
    if isinstance(node, int | float) and not isinstance(node, bool):
        return [(path, node)]
    return []


def accepted_values() -> set[str]:
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    summary.pop("meta", None)
    accepted: set[str] = set()
    for path, leaf in _leaves(summary):
        share_like = any(key in path.lower() for key in SHARE_KEYS)
        accepted |= _renderings(leaf, share_like=share_like)
    return accepted


def allowlist() -> set[str]:
    if not ALLOWLIST.exists():
        return set()
    entries = set()
    for line in ALLOWLIST.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            entries.add(line.split()[0])
    return entries


def prose_lines(text: str) -> list[tuple[int, str]]:
    """The prose of a Markdown file, with code, URLs, badges and comments blanked."""
    text = FENCE_RE.sub(lambda m: "\n" * m.group(0).count("\n"), text)
    text = HTML_COMMENT_RE.sub(lambda m: "\n" * m.group(0).count("\n"), text)
    lines = []
    for number, line in enumerate(text.splitlines(), start=1):
        line = BADGE_RE.sub(" ", line)
        line = INLINE_CODE_RE.sub(" ", line)
        line = URL_RE.sub(" ", line)
        lines.append((number, line))
    return lines


def check_file(path: Path, accepted: set[str], allowed: set[str]) -> list[str]:
    problems = []
    for number, line in prose_lines(path.read_text(encoding="utf-8")):
        if OUTSIDE_RE.search(line):
            continue
        for match in NUMBER_RE.finditer(line):
            token = match.group(0).strip("+-").rstrip(".,")
            if not token or SKIP_RE.match(token):
                continue
            before = line[: match.start()]
            if re.search(
                r"(ADR-|Table |Tabela |Tables |Tabelas |M|§|col\.? |column |coluna |\(|Section |Seção |Python |Typst |v)$",
                before,
            ):
                continue
            if (
                re.search(r"^\s*(-\d|x\b|×)", line[match.end() :])
                and token.isdigit()
                and len(token) <= 2
            ):
                continue
            if token in accepted or token in allowed:
                continue
            problems.append(
                f"{path.relative_to(ROOT)}:{number}: {token!r} is not a value of reports/summary.json"
            )
    return problems


def main(argv: list[str] | None = None) -> int:
    files = [ROOT / arg for arg in (argv or sys.argv[1:])] or [
        ROOT / name for name in ENTRY_PAGES if (ROOT / name).exists()
    ]
    accepted = accepted_values()
    allowed = allowlist()
    problems = [problem for path in files for problem in check_file(path, accepted, allowed)]
    for problem in problems:
        print(problem)
    print(f"check_prose_numbers: {len(files)} file(s), {len(problems)} unexplained number(s)")
    return 1 if problems else 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
