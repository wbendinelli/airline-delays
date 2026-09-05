"""Every number in the entry pages is a value of reports/summary.json (style guide, rule 4)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_every_number_in_the_entry_pages_is_printed_by_the_summary() -> None:
    module = _load("check_prose_numbers")
    accepted, allowed = module.accepted_values(), module.allowlist()
    problems = [
        problem
        for name in module.ENTRY_PAGES
        if (ROOT / name).exists()
        for problem in module.check_file(ROOT / name, accepted, allowed)
    ]
    assert problems == [], "\n".join(problems[:40])


def test_the_two_readmes_quote_the_same_facts() -> None:
    module = _load("check_readme_parity")
    problems = []
    for left, right in module.PAIRS:
        a, b = ROOT / left, ROOT / right
        if not (a.exists() and b.exists()):
            problems.append(f"{left} / {right}: both pages must exist")
            continue
        fa, fb = module.facts(a), module.facts(b)
        if fa["h2"] != fb["h2"]:
            problems.append(f"{left}: {fa['h2']} H2 vs {right}: {fb['h2']}")
        for key in ("numbers", "paths", "recipes"):
            if fa[key] != fb[key]:
                problems.append(
                    f"{key}: only in {left} {sorted(fa[key] - fb[key])[:10]}; only in {right} {sorted(fb[key] - fa[key])[:10]}"
                )
    assert problems == [], "\n".join(problems)
