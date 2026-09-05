#!/usr/bin/env python
"""`README.md` and `README.pt-BR.md` quote the same numbers, paths and recipes.

"In sync" means the same facts, not the same sentences: the set of numeric
tokens (after normalising the thousands and decimal separators of the two
languages), the set of backticked paths and `just` recipes, and the number of
H2 sections must be identical.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAIRS = [
    ("README.md", "README.pt-BR.md"),
    ("docs/README.md", "docs/README.pt-BR.md"),
    ("data/README.md", "data/README.pt-BR.md"),
    ("CONTRIBUTING.md", "CONTRIBUTING.pt-BR.md"),
]
FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
CODE_RE = re.compile(r"`([^`\n]+)`")
NUMBER_RE = re.compile(r"(?<![\w.,/-])\d[\d.,]*")
YEAR_RE = re.compile(r"^(19|20)\d\d$")


def _normalise(token: str) -> str:
    token = token.rstrip(".,")
    if re.fullmatch(r"\d{1,3}([.,]\d{3})+", token):  # thousands
        return token.replace(".", "").replace(",", "")
    if re.fullmatch(r"\d+[.,]\d+", token):  # decimal
        return token.replace(",", ".")
    return token


def facts(path: Path) -> dict[str, set[str] | int]:
    text = path.read_text(encoding="utf-8")
    prose = FENCE_RE.sub("", text)
    numbers = {
        _normalise(m.group(0))
        for m in NUMBER_RE.finditer(prose)
        if not YEAR_RE.match(m.group(0)) and m.group(0).strip(".,")
    }
    numbers = {n for n in numbers if not re.fullmatch(r"\d{6}", n)}
    codes = {m.group(1) for m in CODE_RE.finditer(text)}
    paths = {
        c
        for c in codes
        if "/" in c
        or c.endswith((".md", ".json", ".py", ".csv", ".parquet", ".toml", ".cff", ".typ"))
    }
    recipes = set(re.findall(r"\bjust\s+([a-z][a-z0-9-]*)", text))
    h2 = len(re.findall(r"^## ", text, flags=re.MULTILINE))
    return {"numbers": numbers, "paths": paths, "recipes": recipes, "h2": h2}


def main() -> int:
    problems = []
    for left, right in PAIRS:
        a, b = ROOT / left, ROOT / right
        if not a.exists() or not b.exists():
            problems.append(f"{left} / {right}: both pages must exist")
            continue
        fa, fb = facts(a), facts(b)
        if fa["h2"] != fb["h2"]:
            problems.append(f"{left} has {fa['h2']} H2 sections, {right} has {fb['h2']}")
        for key in ("numbers", "paths", "recipes"):
            only_a = sorted(fa[key] - fb[key])
            only_b = sorted(fb[key] - fa[key])
            if only_a:
                problems.append(f"{key} only in {left}: {only_a[:15]}")
            if only_b:
                problems.append(f"{key} only in {right}: {only_b[:15]}")
    for problem in problems:
        print(problem)
    print(f"check_readme_parity: {len(PAIRS)} pair(s), {len(problems)} difference(s)")
    return 1 if problems else 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
