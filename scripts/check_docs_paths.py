#!/usr/bin/env python3
"""Check that every path and command mentioned in the reader-facing docs is real.

Scope is deliberately narrow: ``README.md`` and ``docs/tutorial/*.md`` are the
two places a reader follows literally, step by step, so a stale path or a
renamed target there is the most expensive kind of error -- it strands
someone mid-exercise. This script scans both for three things and fails on
any miss:

1. Backticked or fenced-code filesystem paths (``src/vra/registry.py``,
   ``data/analysis/taxas.csv``, brace groups like ``src/vra/{groups,codes}.py``).
2. ``just <target>`` invocations, checked against the recipe names actually
   defined in ``justfile``.
3. ``uv run vra <subcommand>`` invocations, checked against the commands the
   ``vra`` CLI actually registers; ``uv run python -m <module>`` and
   ``uv run python scripts/<name>.py`` invocations, checked against the file
   the module or script resolves to.

Markdown link targets (``[text](path)``) are also checked, resolved relative
to the file that contains them -- a link written in ``docs/tutorial/06-x.md``
as ``../dictionary.md`` is checked against ``docs/dictionary.md``, not
``dictionary.md`` at the repository root.

Paths under ``data/raw/``, ``data/staged/``, ``data/derived/`` and
``data/private/`` are pipeline *output*: git-ignored (see ``.gitignore`` and
``CLAUDE.md`` rule 4), so a fresh clone or CI checkout never has them beyond
the tracked ``README.md`` (and, for ``data/raw/``, ``manifest.json``). This
script does not require the generated content under those directories to
exist -- only that the directory name itself is one of the four real ones,
which still catches a typo like ``data/stage/`` or a renamed layer.

Usage: ``uv run python scripts/check_docs_paths.py`` from the repository
root (also wired into CI, see ``.github/workflows/ci.yml``).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CHECKED_FILES = [ROOT / "README.md", *sorted((ROOT / "docs" / "tutorial").glob("*.md"))]

# Top-level names that make a slash-containing backtick span worth treating as
# a repository path, rather than prose that happens to contain a slash (line
# types "N/R/E", fractions "302/306", date ranges, and so on).
KNOWN_TOP = {
    "src",
    "scripts",
    "tests",
    "data",
    "docs",
    "reports",
    "replication",
    "ml",
    "sql",
    ".github",
}
# Root files with no slash: checked only on an exact match, so "README.md" is
# a path candidate but "N/A" or "ROADMAP" (no extension, prose) are not.
ROOT_FILES = {
    "README.md",
    "CLAUDE.md",
    "AGENTS.md",
    "CONTRIBUTING.md",
    "ROADMAP.md",
    "DECISIONS.md",
    "CHANGELOG.md",
    "SECURITY.md",
    "LICENSE",
    "LICENSE-CC-BY-4.0.md",
    "CITATION.cff",
    "pyproject.toml",
    "justfile",
    "ruff.toml",
    ".pre-commit-config.yaml",
    ".editorconfig",
    ".gitattributes",
    ".gitignore",
    "uv.lock",
    ".python-version",
    "datapackage.json",
    ".sapians-repo.yml",
}
# Pipeline output: git-ignored beyond these tracked anchors (see .gitignore).
GENERATED_PREFIXES = ("data/raw/", "data/staged/", "data/derived/", "data/private/")
GENERATED_ANCHORS = {
    "data/raw/README.md",
    "data/raw/manifest.json",
    "data/staged/README.md",
    "data/derived/README.md",
    "data/private/README.md",
}

FENCE_RE = re.compile(r"```[a-zA-Z0-9_-]*\n(.*?)```", re.DOTALL)
INLINE_CODE_RE = re.compile(r"`([^`\n]+)`")
LINK_RE = re.compile(r"\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
JUST_RE = re.compile(r"\bjust\s+([a-zA-Z][a-zA-Z0-9_-]*)")
VRA_RE = re.compile(r"\buv run vra\s+([a-zA-Z][a-zA-Z0-9_-]*)")
MODULE_RE = re.compile(r"\buv run python -m\s+([a-zA-Z0-9_.]+)")
SCRIPT_RE = re.compile(r"\buv run python\s+(scripts/[a-zA-Z0-9_./-]+\.py)")
JUSTFILE_RECIPE_RE = re.compile(
    r"^([a-zA-Z_][a-zA-Z0-9_-]*)(?:\s+[a-zA-Z_][\w]*(?:=\"[^\"]*\")?)*\s*:"
)


class Problem:
    def __init__(self, file: Path, line: int, kind: str, token: str, detail: str) -> None:
        self.file = file
        self.line = line
        self.kind = kind
        self.token = token
        self.detail = detail

    def __str__(self) -> str:
        rel = self.file.relative_to(ROOT)
        return f"{rel}:{self.line}: [{self.kind}] `{self.token}` -- {self.detail}"


def justfile_recipes() -> set[str]:
    text = (ROOT / "justfile").read_text(encoding="utf-8")
    recipes = set()
    for line in text.splitlines():
        if not line or line[0] in " \t#":
            continue
        m = JUSTFILE_RECIPE_RE.match(line)
        if m:
            recipes.add(m.group(1))
    return recipes


def vra_subcommands() -> set[str]:
    import typer

    from vra.cli import app

    return set(typer.main.get_command(app).commands.keys())


def is_path_candidate(token: str) -> bool:
    if "://" in token or token.startswith("mailto:"):
        return False
    if token in ROOT_FILES:
        return True
    if "/" not in token:
        return False
    head = token.split("/", 1)[0]
    return head in KNOWN_TOP


def expand_braces(token: str) -> list[str]:
    """``src/vra/{groups,codes}.py`` -> two literal paths. One brace group only."""
    m = re.search(r"\{([^{}]+)\}", token)
    if not m:
        return [token]
    options = m.group(1).split(",")
    return [token[: m.start()] + opt.strip() + token[m.end() :] for opt in options]


def strip_anchor(token: str) -> str:
    return token.split("#", 1)[0] if not token.startswith("#") else token


def path_exists_repo_relative(token: str) -> bool:
    token = strip_anchor(token).strip()
    if not token:
        return True
    for prefix in GENERATED_PREFIXES:
        if token.startswith(prefix):
            return (
                token in GENERATED_ANCHORS or True
            )  # directory name itself is real by construction
    if any(ch in token for ch in "*?["):
        return bool(list(ROOT.glob(token)))
    return (ROOT / token).exists()


def check_paths(file: Path, text: str, problems: list[Problem]) -> int:
    checked = 0
    lines = text.splitlines()
    line_starts = []
    pos = 0
    for line in lines:
        line_starts.append(pos)
        pos += len(line) + 1

    def line_of(offset: int) -> int:
        lo, hi = 0, len(line_starts) - 1
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if line_starts[mid] <= offset:
                lo = mid
            else:
                hi = mid - 1
        return lo + 1

    # 1. Inline backtick spans and fenced-code-block lines: root-relative paths.
    candidates: list[tuple[int, str]] = []
    for m in INLINE_CODE_RE.finditer(text):
        candidates.append((m.start(), m.group(1)))
    for m in FENCE_RE.finditer(text):
        cursor = m.start(1)
        for raw_line in m.group(1).splitlines():
            for tok in re.split(r"[\s`'\"(),;]+", raw_line):
                if tok:
                    candidates.append((cursor, tok))
            cursor += len(raw_line) + 1

    for offset, token in candidates:
        token = token.strip().rstrip(".,;:")
        if not token or not is_path_candidate(token):
            continue
        # The sanctioned placeholder for a number that lands with a later
        # phase (see CLAUDE.md / the phase-6 brief): a path named on the same
        # line as a `<!-- PREDICTION: ... -->` marker is a forward reference,
        # not a claim that the file exists yet.
        source_line = lines[line_of(offset) - 1] if 0 < line_of(offset) <= len(lines) else ""
        if "PREDICTION:" in source_line:
            continue
        checked += 1
        for expanded in expand_braces(token):
            if not path_exists_repo_relative(expanded):
                problems.append(
                    Problem(
                        file, line_of(offset), "path", expanded, "does not exist in the repository"
                    )
                )

    # 2. Markdown links: resolved relative to the file's own directory first,
    #    then as a repository-root path if that also fails and looks eligible.
    for m in LINK_RE.finditer(text):
        target = m.group(1).strip()
        if not target or target.startswith(("#", "mailto:")) or "://" in target:
            continue
        link_line = lines[line_of(m.start()) - 1] if 0 < line_of(m.start()) <= len(lines) else ""
        if "PREDICTION:" in link_line:
            continue
        checked += 1
        target_clean = strip_anchor(target)
        if not target_clean:
            continue
        resolved_local = (file.parent / target_clean).resolve()
        ok = False
        for prefix in GENERATED_PREFIXES:
            try:
                rel = resolved_local.relative_to(ROOT).as_posix()
            except ValueError:
                rel = None
            if rel and rel.startswith(prefix):
                ok = True
                break
        if not ok and resolved_local.exists():
            ok = True
        if not ok and is_path_candidate(target_clean) and path_exists_repo_relative(target_clean):
            ok = True
        if not ok:
            problems.append(Problem(file, line_of(m.start()), "link", target, "target not found"))

    return checked


def check_commands(
    file: Path, text: str, recipes: set[str], subcommands: set[str], problems: list[Problem]
) -> int:
    checked = 0
    lines = text.splitlines()
    line_starts = []
    pos = 0
    for line in lines:
        line_starts.append(pos)
        pos += len(line) + 1

    def line_of(offset: int) -> int:
        lo, hi = 0, len(line_starts) - 1
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if line_starts[mid] <= offset:
                lo = mid
            else:
                hi = mid - 1
        return lo + 1

    for m in JUST_RE.finditer(text):
        checked += 1
        target = m.group(1)
        if target not in recipes:
            problems.append(
                Problem(
                    file,
                    line_of(m.start()),
                    "just",
                    target,
                    f"no such recipe in justfile (have: {', '.join(sorted(recipes))})",
                )
            )

    for m in VRA_RE.finditer(text):
        checked += 1
        sub = m.group(1)
        if sub not in subcommands:
            problems.append(
                Problem(
                    file,
                    line_of(m.start()),
                    "vra",
                    sub,
                    f"no such `vra` subcommand (have: {', '.join(sorted(subcommands))})",
                )
            )

    for m in MODULE_RE.finditer(text):
        checked += 1
        module = m.group(1)
        as_path = ROOT / Path(module.replace(".", "/") + ".py")
        as_pkg = ROOT / Path(module.replace(".", "/")) / "__init__.py"
        if not as_path.exists() and not as_pkg.exists():
            problems.append(
                Problem(
                    file,
                    line_of(m.start()),
                    "module",
                    module,
                    "resolves to no file under the repository",
                )
            )

    for m in SCRIPT_RE.finditer(text):
        checked += 1
        script = m.group(1)
        if not (ROOT / script).exists():
            problems.append(Problem(file, line_of(m.start()), "script", script, "does not exist"))

    return checked


def main() -> int:
    recipes = justfile_recipes()
    try:
        subcommands = vra_subcommands()
    except Exception as exc:  # noqa: BLE001 -- CLI introspection can fail in many ways; degrade, don't crash
        print(
            f"warning: could not introspect the `vra` CLI ({exc}); skipping `uv run vra` checks",
            file=sys.stderr,
        )
        subcommands = set()

    problems: list[Problem] = []
    n_paths = n_cmds = 0
    for file in CHECKED_FILES:
        if not file.exists():
            problems.append(
                Problem(
                    file, 0, "missing-file", str(file), "listed for checking but does not exist"
                )
            )
            continue
        text = file.read_text(encoding="utf-8")
        n_paths += check_paths(file, text, problems)
        n_cmds += check_commands(file, text, recipes, subcommands, problems)

    print(
        f"check_docs_paths: {len(CHECKED_FILES)} file(s), {n_paths} path candidate(s), {n_cmds} command(s) checked"
    )
    if problems:
        print(f"\n{len(problems)} problem(s):\n")
        for p in problems:
            print(f"  {p}")
        return 1
    print("all paths and commands resolved")
    return 0


if __name__ == "__main__":
    sys.exit(main())
