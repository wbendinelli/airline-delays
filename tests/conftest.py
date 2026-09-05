"""Shared pytest configuration and the offline fixtures.

Everything runs against the files committed in ``tests/fixtures`` and the
tables committed in ``data/analysis``; no test needs a network connection or
a directory outside the repository. Tests marked ``analysis`` additionally
rebuild committed tables from ``data/staged``/``data/derived`` and skip when
those layers are absent (``pyproject.toml``).
"""

from __future__ import annotations

# --------------------------------------------------------------------------- fixtures
#
# The staging fixtures. Everything below runs offline against the files
# committed in ``tests/fixtures``: two raw samples cut byte for byte from the
# real ANAC files (so latin-1, CRLF, ``N/A`` and the free-text 2010 layout are
# all exercised) and one staged parquet. Rebuild them with
# ``uv run airline-delays fixture``.
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    return FIXTURES


@pytest.fixture(scope="session")
def raw_2002() -> Path:
    """A sample of the legacy 12-column layout, bytes untouched."""
    path = FIXTURES / "vra_raw_sample_2002.csv"
    if not path.exists():  # pragma: no cover - fixture missing
        pytest.skip(f"missing fixture {path}; run `uv run airline-delays fixture`")
    return path


@pytest.fixture(scope="session")
def raw_2012() -> Path:
    """A sample of the 20-column layout, bytes untouched."""
    path = FIXTURES / "vra_raw_sample_2012.csv"
    if not path.exists():  # pragma: no cover - fixture missing
        pytest.skip(f"missing fixture {path}; run `uv run airline-delays fixture`")
    return path


@pytest.fixture(scope="session")
def staged_sample() -> Path:
    """Staged rows for three routes in 2004, 2009 and 2012."""
    path = FIXTURES / "vra_sample.parquet"
    if not path.exists():  # pragma: no cover - fixture missing
        pytest.skip(f"missing fixture {path}; run `uv run airline-delays fixture`")
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
    from airline_delays.staging import connect

    con = connect(memory_limit="2GB", threads=2)
    yield con
    con.close()


# --------------------------------------------------------------------------- layers
#
# The feature, panel and registry tests all need the same thing: a small staged
# tree partitioned by year, and the tables built from it. Building them once per
# session keeps the suite well under a minute, and building them from the
# committed fixture keeps it offline.


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return ROOT


@pytest.fixture(scope="session")
def groups_csv() -> Path:
    return ROOT / "data" / "external" / "groups.csv"


@pytest.fixture(scope="session")
def external_dir() -> Path:
    return ROOT / "data" / "external"


@pytest.fixture(scope="session")
def staged_tree(tmp_path_factory: pytest.TempPathFactory, staged_sample: Path) -> Path:
    """The fixture parquet re-partitioned as ``year=YYYY/part-0.parquet``.

    `airline_delays.fact_mod.build_fact` reads one year at a time, so the fixture has to
    look like `data/staged/` even though it is a single file on disk.
    """
    import pyarrow as pa
    import pyarrow.parquet as pq

    target = tmp_path_factory.mktemp("staged")
    frame = pq.read_table(staged_sample).to_pandas()
    frame = frame[frame["year"].notna()]
    for year, part in frame.groupby(frame["year"].astype(int)):
        directory = target / f"year={year}"
        directory.mkdir(parents=True, exist_ok=True)
        pq.write_table(
            pa.Table.from_pandas(part, preserve_index=False), directory / "part-0.parquet"
        )
    return target


@pytest.fixture(scope="session")
def built(tmp_path_factory: pytest.TempPathFactory, staged_tree: Path, groups_csv: Path):
    """Every table of the analysis layer, built once from the fixture."""
    import pandas as pd

    from airline_delays import fact as fact_mod
    from airline_delays import panel

    root = tmp_path_factory.mktemp("built")
    analysis, derived = root / "analysis", root / "derived"
    result = fact_mod.build_fact(
        staged_tree, analysis, derived, groups_path=groups_csv, verbose=False
    )
    fact = pd.read_parquet(analysis / "fact_group_route_month.parquet")
    context = pd.read_parquet(derived / "route_month_context.parquet")
    day_hour = pd.read_parquet(derived / "node_day_hour.parquet")
    city = fact_mod.city_month(fact, day_hour)
    airline_city = fact_mod.add_hub(fact_mod.aggregate(fact, "airline_city_month"))
    table = panel.assemble(fact, context, city, external_dir=ROOT / "data" / "external")
    return {
        "result": result,
        "analysis": analysis,
        "derived": derived,
        "fact": fact,
        "context": context,
        "day_hour": day_hour,
        "city": city,
        "airline_city": airline_city,
        "panel": table,
    }
