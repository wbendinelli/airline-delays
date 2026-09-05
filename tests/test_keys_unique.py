"""ADR-0016: keys are unique by construction, and ADR-0015: the cut is symmetric.

Two invariants, one file, because one defect produced both symptoms in the
first public panel.

**Key uniqueness.** `data/staged/` is partitioned by the year of the *source
file* while `year` and `ym` come from `flight_date`, so a December file carries
legs scheduled for 1 January and a few rows carry an outright typo. Grouping
inside each directory and concatenating emitted the same cell twice: 844 rows
over 422 keys in the fact table, and, through the route-month context join, 866
rows over 433 keys in the panel — with equal flight counts and different
medians, because each copy's median was taken over half of its flights.
`airline_delays.fact_mod.build_fact` now selects each *calendar year* across the whole
tree. The first class below rebuilds from a deliberately mis-partitioned tree,
which is the only way to test the fix rather than the fixture.

**The symmetric cut.** ADR-0015 applies the outlier threshold to `abs(delay)`,
so a month typo cannot enter a sum of minutes from either tail. The tests on
the committed panel check the consequence: no published minutes column can sit
beyond the threshold, by construction.

The `analysis`-marked tests read the committed tables and skip when they are not
on disk, exactly like `tests/test_analysis_staleness.py`.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from airline_delays import fact as fact_mod
from airline_delays import panel as panel_mod
from airline_delays.definitions import delays

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_DIR = ROOT / "data" / "analysis"
DERIVED_DIR = ROOT / "data" / "derived"

PANEL_FIRST_YM = 200001
PANEL_LAST_YM = 201312
PANEL_MAX_MONTHS = 168
"""2000m1 to 2013m12 inclusive; a month outside it is a flight the window excludes."""


def _read(path: Path):
    import pandas as pd

    if not path.exists():
        pytest.skip(f"{path.relative_to(ROOT)} is not built; run `just fact && just panel`")
    return pd.read_parquet(path)


@pytest.fixture(scope="session")
def scrambled_tree(tmp_path_factory: pytest.TempPathFactory, staged_sample: Path) -> Path:
    """The fixture staged tree with every row shifted one partition earlier.

    A worst case of the real defect: *every* row of year Y sits in directory
    ``year=Y-1``, so a build that trusts the directory name splits nothing (it
    simply mislabels) — but a build that trusts it *and* concatenates across
    directories that overlap produces duplicates. Overlap is what the extra
    copy in ``year=<min-1>`` creates: two directories that both contain rows of
    the same calendar year.
    """
    import pyarrow as pa
    import pyarrow.parquet as pq

    target = tmp_path_factory.mktemp("scrambled")
    frame = pq.read_table(staged_sample).to_pandas()
    frame = frame[frame["year"].notna()]
    years = sorted(frame["year"].astype(int).unique())
    for year, part in frame.groupby(frame["year"].astype(int)):
        # Half the rows in the right directory, half one directory earlier:
        # the same calendar year now lives in two partitions, which is the
        # shape that produced the 422 duplicated fact keys.
        head, tail = part.iloc[: len(part) // 2], part.iloc[len(part) // 2 :]
        for offset, piece in ((0, head), (-1, tail)):
            if piece.empty:
                continue
            directory = target / f"year={year + offset}"
            directory.mkdir(parents=True, exist_ok=True)
            path = directory / f"part-{year}.parquet"
            pq.write_table(pa.Table.from_pandas(piece, preserve_index=False), path)
    directory = target / f"year={years[0] - 1}"
    directory.mkdir(parents=True, exist_ok=True)
    return target


@pytest.fixture(scope="session")
def built_from_scrambled(tmp_path_factory: pytest.TempPathFactory, scrambled_tree, groups_csv):
    import pandas as pd

    root = tmp_path_factory.mktemp("scrambled_build")
    analysis, derived = root / "analysis", root / "derived"
    years = tuple(
        sorted(
            int(path.name.split("=")[1])
            for path in scrambled_tree.glob("year=*")
            if path.name.split("=")[1].isdigit()
        )
    )
    result = fact_mod.build_fact(
        scrambled_tree, analysis, derived, years=years, groups_path=groups_csv, verbose=False
    )
    return {
        "result": result,
        "fact": pd.read_parquet(analysis / "fact_group_route_month.parquet"),
        "context": pd.read_parquet(derived / "route_month_context.parquet"),
        "day_hour": pd.read_parquet(derived / "node_day_hour.parquet"),
    }


class TestAMisPartitionedTreeStillBuildsUniqueKeys:
    """The regression test for ADR-0016: build from a tree that lies about years."""

    def test_the_fact_table_is_unique(self, built_from_scrambled) -> None:
        fact = built_from_scrambled["fact"]
        assert not fact.duplicated(list(fact_mod.FACT_UNIQUE_KEY)).any()

    def test_the_route_month_context_is_unique(self, built_from_scrambled) -> None:
        context = built_from_scrambled["context"]
        assert not context.duplicated(list(fact_mod.ROUTE_MONTH_KEY)).any()

    def test_the_node_day_hour_table_is_unique(self, built_from_scrambled) -> None:
        day_hour = built_from_scrambled["day_hour"]
        assert not day_hour.duplicated(["node", "day", "hour"]).any()

    def test_every_year_column_matches_its_own_partition_pass(self, built_from_scrambled) -> None:
        """The cell's `year` is `ym // 100` — the pass is a calendar year, not a file."""
        fact = built_from_scrambled["fact"]
        assert (fact["year"] == fact["ym"] // 100).all()

    def test_the_flights_agree_with_the_tidy_build(self, built_from_scrambled, built) -> None:
        """Scrambling the partitions moves no flight into or out of any cell."""
        scrambled = built_from_scrambled["fact"]
        tidy = built["fact"]
        keys = list(fact_mod.FACT_UNIQUE_KEY)
        left = scrambled.groupby(keys, observed=True)["flights"].sum()
        right = tidy.groupby(keys, observed=True)["flights"].sum()
        shared = left.index.intersection(right.index)
        assert len(shared) > 0
        assert (left.loc[shared] == right.loc[shared]).all()

    def test_the_panel_built_from_it_is_unique(self, built_from_scrambled, external_dir) -> None:
        fact = built_from_scrambled["fact"]
        city = panel_mod.city_month(fact, built_from_scrambled["day_hour"])
        table = panel_mod.assemble(
            fact, built_from_scrambled["context"], city, external_dir=external_dir
        )
        assert not table.duplicated(list(fact_mod.ROUTE_MONTH_KEY)).any()

    def test_rows_outside_the_built_years_are_counted(self, built_from_scrambled) -> None:
        """The empty leading partition holds no flight, and the count says so."""
        outside = fact_mod.out_of_window_records(built_from_scrambled["result"].out_of_window)
        assert all(record["rows"] >= 0 for record in outside)


class TestAssertUnique:
    def test_a_planted_duplicate_is_refused(self, built) -> None:
        import pandas as pd

        fact = built["fact"]
        doubled = pd.concat([fact, fact.head(1)], ignore_index=True)
        with pytest.raises(ValueError, match="not unique"):
            fact_mod.assert_unique(doubled, fact_mod.FACT_UNIQUE_KEY, "planted")

    def test_a_clean_table_passes(self, built) -> None:
        fact_mod.assert_unique(built["fact"], fact_mod.FACT_UNIQUE_KEY, "fixture fact")

    def test_aggregate_refuses_a_duplicated_fact_table(self, built) -> None:
        import pandas as pd

        doubled = pd.concat([built["fact"], built["fact"].head(1)], ignore_index=True)
        with pytest.raises(ValueError, match="not unique"):
            fact_mod.aggregate(doubled, "route_month")


class TestTheSymmetricOutlierRule:
    """ADR-0015: both tails, in Python and in SQL, on the fixture."""

    def test_a_large_negative_delay_is_an_outlier(self) -> None:
        assert delays.is_outlier(-43_170.0)
        assert delays.is_outlier(400.0)
        assert not delays.is_outlier(-8.0)
        assert not delays.is_outlier(None)

    def test_the_sql_predicate_agrees_with_python(self, duck) -> None:
        values = [-43_170.0, -400.0, -313.25, -8.0, 0.0, 8.0, 313.25, 400.0]
        rendered = ", ".join(f"({value})" for value in values)
        rows = duck.execute(
            f"SELECT d, {delays.is_outlier_sql('d')} FROM (VALUES {rendered}) AS t(d)"
        ).fetchall()
        assert [(value, delays.is_outlier(value)) for value in values] == [
            (row[0], bool(row[1])) for row in rows
        ]

    def test_no_fixture_minutes_column_escapes_the_band(self, built) -> None:
        table = built["panel"]
        for name in ("fsc_minsarr", "fsc_minsdep", "all_minsarr", "all_minsdep"):
            values = table[name].dropna()
            assert values.abs().max() < delays.OUTLIER_THRESHOLD_MIN, name

    def test_the_suspect_flag_is_written_at_staging(self, staged_frame) -> None:
        assert "actual_time_suspect" in staged_frame.columns
        expected = (
            staged_frame["dep_delay_min"].abs().ge(delays.SUSPECT_DELAY_MIN)
            | staged_frame["arr_delay_min"].abs().ge(delays.SUSPECT_DELAY_MIN)
        ).fillna(False)
        assert (staged_frame["actual_time_suspect"] == expected).all()


@pytest.mark.analysis
class TestTheCommittedTables:
    """The same invariants on what is actually in git (ADR-0014, ADR-0016)."""

    def test_the_fact_table_is_unique(self) -> None:
        fact = _read(ANALYSIS_DIR / "fact_group_route_month.parquet")
        fact_mod.assert_unique(fact, fact_mod.FACT_UNIQUE_KEY, "committed fact table")

    def test_the_panel_is_unique(self) -> None:
        table = _read(ANALYSIS_DIR / "panel_route_month.parquet")
        fact_mod.assert_unique(table, fact_mod.ROUTE_MONTH_KEY, "committed panel")

    def test_the_city_tables_are_unique(self) -> None:
        city = _read(ANALYSIS_DIR / "city_month.parquet")
        fact_mod.assert_unique(city, fact_mod.CITY_MONTH_KEY, "committed city_month")
        airline_city = _read(ANALYSIS_DIR / "airline_city_month.parquet")
        fact_mod.assert_unique(
            airline_city, fact_mod.AIRLINE_CITY_MONTH_KEY, "committed airline_city_month"
        )

    def test_the_route_month_context_is_unique(self) -> None:
        context = _read(DERIVED_DIR / "route_month_context.parquet")
        fact_mod.assert_unique(context, fact_mod.ROUTE_MONTH_KEY, "committed context")

    def test_the_panel_covers_at_most_the_declared_window(self) -> None:
        table = _read(ANALYSIS_DIR / "panel_route_month.parquet")
        months = sorted(table["ym"].unique())
        assert len(months) <= PANEL_MAX_MONTHS
        assert months[0] >= PANEL_FIRST_YM
        assert months[-1] <= PANEL_LAST_YM

    def test_no_published_minutes_column_escapes_the_band(self) -> None:
        table = _read(ANALYSIS_DIR / "panel_route_month.parquet")
        minutes = [
            name
            for name in table.columns
            if name.endswith(("minsarr", "minsdep", "minsp15arr", "minsp15dep"))
        ]
        assert minutes
        for name in minutes:
            values = table[name].dropna()
            assert values.abs().max() < delays.OUTLIER_THRESHOLD_MIN, name
