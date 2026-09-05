"""The command line: one command per stage, in pipeline order, and the docs checker sees them."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from airline_delays.cli import app

ROOT = Path(__file__).resolve().parents[1]
PIPELINE_ORDER = [
    "fetch",
    "stage",
    "reference",
    "fact",
    "panel",
    "dictionary",
    "datapackage",
    "article-panel",
    "estimate",
    "predict-dataset",
    "predict",
    "theory",
]


def _commands() -> list[str]:
    import typer.main

    return list(typer.main.get_command(app).commands)


def test_help_exits_cleanly() -> None:
    result = CliRunner().invoke(app, ["--help"])
    assert result.exit_code == 0, result.output
    for name in PIPELINE_ORDER:
        assert name in result.output


def test_commands_follow_the_pipeline_order() -> None:
    names = _commands()
    positions = [names.index(name) for name in PIPELINE_ORDER]
    assert positions == sorted(positions), names


@pytest.mark.parametrize("name", PIPELINE_ORDER)
def test_every_command_has_help(name: str) -> None:
    result = CliRunner().invoke(app, [name, "--help"])
    assert result.exit_code == 0, result.output


def test_the_docs_checker_sees_the_same_commands() -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "check_docs_paths", ROOT / "scripts" / "check_docs_paths.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    assert module.cli_subcommands() == set(_commands())
    # The top-level directories the checker treats as paths must exist -- a stale
    # entry would silently stop checking a whole subtree.
    assert module.KNOWN_TOP <= {p.name for p in ROOT.iterdir() if p.is_dir()}
    recipes = module.justfile_recipes() if hasattr(module, "justfile_recipes") else None
    if recipes is not None:
        assert {"fetch", "stage", "fact", "panel", "estimate", "predict", "theory", "demo"} <= set(
            recipes
        )
