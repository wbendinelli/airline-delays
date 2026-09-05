"""Every git-tracked text file is scanned for the private research archive.

Deliberately **not** marked ``gabarito``: this must run in CI, in a fresh
clone, with no environment variable set -- it is the check that would have
caught the 30 committed rows of ``data/external/*.csv`` that carried absolute
URLs into the author's private archive for fourteen commits (audit
2026-09-05, finding B-2).

The patterns, the allowlist and the must-reject/must-accept samples live in
``scripts/check_no_private_paths.py``, which the ``no-private-data``
pre-commit hook also runs (with ``--staged``). This module imports that script
rather than restating any of it, so the hook and the test can never drift
apart -- and so this file itself stays free of the strings it hunts for.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_no_private_paths.py"


def _load():
    spec = importlib.util.spec_from_file_location("check_no_private_paths", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


guard = _load()


class TestTrackedContent:
    def test_no_tracked_file_leaks_the_private_archive(self) -> None:
        tracked = guard.tracked_files()
        assert tracked, "git ls-files returned nothing -- is this a git checkout?"
        problems, _ = guard.scan(tracked)
        assert not problems, "\n".join(
            ["private research archive found in git content:", *problems]
        )

    def test_the_reference_tables_are_actually_in_scope(self) -> None:
        # The leak was here. If `data/external/` ever stopped being tracked,
        # the test above would pass vacuously.
        tracked = set(guard.tracked_files())
        for name in ("groups.csv", "events.csv", "README.md"):
            assert f"data/external/{name}" in tracked

    def test_the_allowlist_does_not_rot(self) -> None:
        # `--staged` skips this check (it sees only part of the tree); the
        # full-tree run reports an entry that no longer allows anything.
        assert guard.main([]) == 0


class TestTheGuardItself:
    """A guard that cannot fail is not a guard."""

    @pytest.mark.parametrize("line, tier", guard.MUST_REJECT)
    def test_a_leak_is_rejected_in_an_ordinary_file(self, line: str, tier: int) -> None:
        problems, _ = guard.problems_in("data/external/some_table.csv", line)
        assert problems, f"tier {tier} sample slipped through: {line!r}"

    @pytest.mark.parametrize("line, tier", guard.MUST_REJECT)
    def test_tier_one_is_rejected_even_where_tier_two_is_allowed(
        self, line: str, tier: int
    ) -> None:
        allowed = next(iter(guard.TIER2_ALLOWED))
        problems, _ = guard.problems_in(allowed, line)
        assert bool(problems) is (tier == 1)

    @pytest.mark.parametrize("line", guard.MUST_ACCEPT)
    def test_ordinary_prose_is_not_flagged(self, line: str) -> None:
        problems, _ = guard.problems_in("data/external/some_table.csv", line)
        assert not problems, problems

    def test_the_allowlist_carries_a_reason_for_every_entry(self) -> None:
        assert all(reason.strip() for reason in guard.TIER2_ALLOWED.values())

    def test_no_data_file_is_allowlisted(self) -> None:
        # `data/private/README.md` explains the ignored directory; every other
        # `data/` path must stay out of the allowlist, reference tables above all.
        listed = {name for name in guard.TIER2_ALLOWED if name.startswith("data/")}
        assert listed == {"data/private/README.md"}
