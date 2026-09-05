#!/usr/bin/env python3
"""Markdown that renders on GitHub: math delimiters, tables and fences.

GitHub runs its Markdown parser before MathJax, so a bare ``$...$`` loses its
asterisks, thin spaces (``\\,``) and paired subscripts before the equation is
typeset, and ``$$`` blocks fare no better inside paragraphs. The conventions of
`docs/editorial/style-guide.md` (rule 16) are therefore mechanical:

1. inline math is written as ``$`...`$`` (GitHub's code-span math);
2. display math lives inside a ```math fence, one equation per fence, with
   ``\\tag{n}`` for numbering; ``\\tag`` outside such a fence is an error;
3. a table starts after a blank line (a header row glued to a paragraph is
   rendered as text);
4. every code fence is closed.

Relative link targets are resolved by ``scripts/check_docs_paths.py``. Checked
here: the READMEs, the CONTRIBUTING pages, every ``docs/**/*.md``, the data
guides and ``reports/README.md``. Exit status 1 with ``file:line: message``.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CHECKED_FILES: list[Path] = sorted(
    {
        *ROOT.glob("README*.md"),
        *ROOT.glob("CONTRIBUTING*.md"),
        *ROOT.glob("docs/**/*.md"),
        *ROOT.glob("data/**/README*.md"),
        ROOT / "reports" / "README.md",
    }
)

FENCE_RE = re.compile(r"^\s{0,3}(```+|~~~+)\s*([A-Za-z0-9_+-]*)")
CODE_SPAN_MATH_RE = re.compile(r"\$`[^`\n]+`\$")
CODE_SPAN_RE = re.compile(r"`[^`\n]*`")
TABLE_ROW_RE = re.compile(r"^\s{0,3}\|.*\|\s*$")
TABLE_SEP_RE = re.compile(r"^\s{0,3}\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?\s*$")
CURRENCY_RE = re.compile(r"(?:R|US)\$\s?\d")


def check_file(path: Path) -> list[str]:
    problems: list[str] = []
    rel = path.relative_to(ROOT)
    lines = path.read_text(encoding="utf-8").splitlines()
    fence: str | None = None
    fence_lang = ""
    fence_line = 0
    for number, line in enumerate(lines, 1):
        m = FENCE_RE.match(line)
        if m and (fence is None or line.strip().startswith(fence)):
            if fence is None:
                fence, fence_lang, fence_line = m.group(1)[0] * 3, m.group(2).lower(), number
            elif line.strip() == line.strip()[0] * len(line.strip()):
                fence = None
            continue
        if fence is not None:
            if fence_lang != "math" and "\\tag{" in line:
                problems.append(f"{rel}:{number}: \\tag inside a non-math fence")
            continue
        stripped = CODE_SPAN_MATH_RE.sub("", line)
        stripped = CODE_SPAN_RE.sub("", stripped)
        stripped = CURRENCY_RE.sub("", stripped)
        stripped = stripped.replace("\\$", "")
        if "$" in stripped:
            problems.append(
                f"{rel}:{number}: bare `$` math; write inline math as $`...`$ and display math in a ```math fence"
            )
        if "\\tag{" in stripped:
            problems.append(f"{rel}:{number}: \\tag outside a ```math fence")
        if (
            number >= 2
            and TABLE_ROW_RE.match(line)
            and number < len(lines)
            and TABLE_SEP_RE.match(lines[number])
            and lines[number - 2].strip()
            and not TABLE_ROW_RE.match(lines[number - 2])
        ):
            problems.append(f"{rel}:{number}: table header not preceded by a blank line")
    if fence is not None:
        problems.append(f"{rel}:{fence_line}: code fence never closed")
    return problems


def main() -> int:
    problems: list[str] = []
    for path in CHECKED_FILES:
        problems.extend(check_file(path))
    for problem in problems:
        print(problem)
    print(f"check_markdown_math: {len(CHECKED_FILES)} file(s) checked, {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
