"""Shared pytest configuration.

Registers the ``gabarito`` marker (tests that read the private benchmark
through ``AIRLINE_DELAYS_PRIVATE_DIR``) and skips those tests automatically
when the variable is unset, so a contributor without the private directory
sees a skip, not a failure or an accidental read of a path that does not
exist. See CLAUDE.md and CONTRIBUTING.md. ``pyproject.toml``'s
``addopts = "-m 'not gabarito'"`` already deselects these tests by default;
this hook is the safety net for the case where someone runs
``pytest -m gabarito`` or overrides ``addopts`` directly.
"""

from __future__ import annotations

import os

import pytest

PRIVATE_DIR_VAR = "AIRLINE_DELAYS_PRIVATE_DIR"


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "gabarito: requires data/private/ via AIRLINE_DELAYS_PRIVATE_DIR -- does not run in CI",
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if os.environ.get(PRIVATE_DIR_VAR):
        return
    skip_gabarito = pytest.mark.skip(
        reason=f"{PRIVATE_DIR_VAR} is unset -- gabarito tests need the private benchmark directory"
    )
    for item in items:
        if "gabarito" in item.keywords:
            item.add_marker(skip_gabarito)


# --------------------------------------------------------------------------- fixtures
#
# The staging fixtures. Everything below runs offline against the files
# committed in ``tests/fixtures``: two raw samples cut byte for byte from the
# real ANAC files (so latin-1, CRLF, ``N/A`` and the free-text 2010 layout are
# all exercised) and one staged parquet. Rebuild them with
# ``uv run vra fixture``.

import sys  # noqa: E402
from pathlib import Path  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    return FIXTURES


@pytest.fixture(scope="session")
def raw_2002() -> Path:
    """A sample of the legacy 12-column layout, bytes untouched."""
    path = FIXTURES / "vra_raw_sample_2002.csv"
    if not path.exists():  # pragma: no cover - fixture missing
        pytest.skip(f"missing fixture {path}; run `uv run vra fixture`")
    return path


@pytest.fixture(scope="session")
def raw_2012() -> Path:
    """A sample of the 20-column layout, bytes untouched."""
    path = FIXTURES / "vra_raw_sample_2012.csv"
    if not path.exists():  # pragma: no cover - fixture missing
        pytest.skip(f"missing fixture {path}; run `uv run vra fixture`")
    return path


@pytest.fixture(scope="session")
def staged_sample() -> Path:
    """Staged rows for three routes in 2004, 2009 and 2012."""
    path = FIXTURES / "vra_sample.parquet"
    if not path.exists():  # pragma: no cover - fixture missing
        pytest.skip(f"missing fixture {path}; run `uv run vra fixture`")
    return path


@pytest.fixture(scope="session")
def staged_table(staged_sample: Path):
    """The staged fixture as a pyarrow Table."""
    import pyarrow.parquet as pq

    return pq.read_table(staged_sample)


@pytest.fixture(scope="session")
def staged_frame(staged_table):
    """The staged fixture as a pandas DataFrame."""
    return staged_table.to_pandas()


@pytest.fixture
def duck():
    """A small DuckDB connection, closed after the test."""
    from vra.stage import connect

    con = connect(memory_limit="2GB", threads=2)
    yield con
    con.close()
