"""Command line entry point: ``airline-delays <stage>``, one command per pipeline stage.

Each command is a thin shell over the library, so everything it does is also
callable from Python and from a notebook.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Annotated

import typer

from airline_delays import paths, schema
from airline_delays.definitions import carriers, cause_codes
from airline_delays.ingest import YEARS, Manifest, inspect_file, layout_for
from airline_delays.ingest import fetch as fetch_raw
from airline_delays.staging import stage as stage_years

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="Reconstruct Brazilian airline delay data from ANAC's VRA files.",
)


def repo_root() -> Path:
    """The repository root, resolved from this file's location."""
    return paths.REPO_ROOT


def _years(first: int, last: int) -> tuple[int, ...]:
    if first > last:
        raise typer.BadParameter(f"--from {first} is after --to {last}")
    return tuple(range(first, last + 1))


@app.command()
def fetch(
    year_from: Annotated[int, typer.Option("--from", help="First year to download.")] = YEARS[0],
    year_to: Annotated[int, typer.Option("--to", help="Last year to download.")] = YEARS[-1],
    raw_dir: Annotated[Path | None, typer.Option(help="Destination; defaults to data/raw.")] = None,
    force: Annotated[bool, typer.Option(help="Re-download even when the sha256 matches.")] = False,
) -> None:
    """Download the monthly VRA CSVs and record them in data/raw/manifest.json."""
    target = raw_dir or repo_root() / "data" / "raw"
    for line in fetch_raw(target, years=_years(year_from, year_to), force=force):
        typer.echo(line)


@app.command()
def stage(
    year_from: Annotated[int, typer.Option("--from", help="First year to stage.")] = YEARS[0],
    year_to: Annotated[int, typer.Option("--to", help="Last year to stage.")] = YEARS[-1],
    raw_dir: Annotated[Path | None, typer.Option(help="Source; defaults to data/raw.")] = None,
    out_dir: Annotated[
        Path | None, typer.Option(help="Destination; defaults to data/staged.")
    ] = None,
    groups: Annotated[
        Path | None,
        typer.Option(help="Airline groups table; defaults to data/external/groups.csv."),
    ] = None,
) -> None:
    """Parse the raw CSVs into data/staged/year=YYYY/part-0.parquet, one year at a time."""
    root = repo_root()
    groups_path = groups or root / "data" / "external" / "groups.csv"
    results = stage_years(
        raw_dir or root / "data" / "raw",
        out_dir or root / "data" / "staged",
        years=_years(year_from, year_to),
        groups_path=groups_path if groups_path.exists() else None,
        root=root,
    )
    typer.echo(f"staged {sum(r.rows for r in results):,d} rows across {len(results)} years")


@app.command()
def fixture(
    out_dir: Annotated[
        Path | None, typer.Option(help="Destination; defaults to tests/fixtures.")
    ] = None,
    max_rows: Annotated[int, typer.Option(help="Row cap for each raw CSV sample.")] = 3000,
) -> None:
    """Rebuild the test fixtures from the raw and staged data."""
    root = repo_root()
    script = root / "scripts" / "make_fixture.py"
    command = [
        sys.executable,
        str(script),
        "--out-dir",
        str(out_dir or root / "tests" / "fixtures"),
        "--max-rows",
        str(max_rows),
    ]
    raise typer.Exit(code=subprocess.run(command, check=False).returncode)


@app.command()
def layouts(
    raw_dir: Annotated[Path | None, typer.Option(help="Source; defaults to data/raw.")] = None,
    as_json: Annotated[bool, typer.Option("--json", help="Emit the measurements as JSON.")] = False,
) -> None:
    """Measure the raw layout of the first file of every downloaded year."""
    target = (raw_dir or repo_root() / "data" / "raw") / "vra"
    out = []
    for year_dir in sorted(target.glob("[0-9][0-9][0-9][0-9]")):
        files = sorted(year_dir.glob("*.csv"))
        if not files:
            continue
        year = int(year_dir.name)
        measured = inspect_file(files[0])
        measured["year"] = year
        measured["declared_layout"] = layout_for(year).name
        out.append(measured)
    if as_json:
        typer.echo(json.dumps(out, indent=2, ensure_ascii=False))
        return
    for item in out:
        typer.echo(
            f"{item['year']}  {item['declared_layout']:<12}  {item['n_columns']:>2} cols  "
            f"sep={item['separator']!r}  {item['encoding']}  {item['line_ending']}  "
            f"quotes={item['has_quotes']}  {item['bytes'] / 1e6:.1f} MB"
        )


@app.command()
def manifest(raw_dir: Path = typer.Option(None, help="Source; defaults to data/raw.")) -> None:
    """Summarise data/raw/manifest.json."""
    target = raw_dir or repo_root() / "data" / "raw"
    loaded = Manifest.load(target / "manifest.json")
    by_year: dict[int, list[int]] = {}
    for entry in loaded.entries.values():
        by_year.setdefault(entry.year, []).append(entry.bytes)
    for year in sorted(by_year):
        sizes = by_year[year]
        typer.echo(f"{year}: {len(sizes)} files, {sum(sizes) / 1e6:8.1f} MB")
    typer.echo(
        f"total: {len(loaded.entries)} files, "
        f"{sum(e.bytes for e in loaded.entries.values()) / 1e6:.1f} MB"
    )


@app.command(name="reference")
def reference(
    external_dir: Annotated[
        Path | None, typer.Option(help="Reference tables; defaults to data/external.")
    ] = None,
) -> None:
    """Validate data/external: provenance on every row, and the ADR sets they encode."""
    root = repo_root()
    target = external_dir or root / "data" / "external"
    problems: list[str] = []
    for path in sorted(target.glob("*.csv")):
        problems += _check_provenance(path)
    problems += _check_reference_tables(target)
    for line in _reference_summary(target):
        typer.echo(line)
    if problems:
        for problem in problems:
            typer.echo(f"FAIL {problem}", err=True)
        raise typer.Exit(code=1)
    typer.echo("refs: every row carries source, url and confidence; ADR sets agree")


def _check_provenance(path: Path) -> list[str]:
    """Every row of every reference table must carry its own source, url and grade."""
    import pandas as pd

    frame = pd.read_csv(path, dtype=str, keep_default_na=False)
    problems = []
    for column in ("source", "url", "confidence"):
        if column not in frame.columns:
            problems.append(f"{path.name}: no `{column}` column")
            continue
        blank = int((frame[column].fillna("").str.strip() == "").sum())
        # `url` is allowed to be blank when `source` is a computation rather than
        # a document -- observances.csv computes Easter and cites the algorithm.
        if blank and column != "url":
            problems.append(f"{path.name}: {blank} rows without `{column}`")
    return problems


def _check_reference_tables(target: Path) -> list[str]:
    """The CSVs must agree with the ADR constants the code compiles in."""

    problems = []
    try:
        carriers.GroupTable.load(target / "groups.csv")
    except ValueError as exc:
        problems.append(f"groups.csv: {exc}")
    declared = cause_codes.sets_from_file(target / "cause_codes.csv")
    for name, expected in cause_codes.ARTICLE_SETS.items():
        if declared.get(name, ()) != tuple(sorted(expected)):
            problems.append(
                f"cause_codes.csv: article set {name} is {declared.get(name)}, "
                f"ADR-0005 declares {tuple(sorted(expected))}"
            )
    for name, expected_codes in cause_codes.CATEGORIES.items():
        found = cause_codes.categories_from_file(target / "cause_codes.csv").get(name, ())
        if found != tuple(sorted(expected_codes)):
            problems.append(
                f"cause_codes.csv: category {name} is {found}, ADR-0005 declares {tuple(sorted(expected_codes))}"
            )
    return problems


def _reference_summary(target: Path) -> list[str]:
    import pandas as pd

    out = []
    for path in sorted(target.glob("*.csv")):
        frame = pd.read_csv(path, dtype=str, keep_default_na=False)
        grades = ""
        if "confidence" in frame.columns:
            counts = frame["confidence"].value_counts().to_dict()
            grades = "  " + " ".join(f"{grade}={count}" for grade, count in sorted(counts.items()))
        out.append(f"{path.name:<20} {len(frame):>6,d} rows{grades}")
    return out


@app.command(name="fact")
def fact(
    staged_dir: Annotated[
        Path | None, typer.Option(help="Source; defaults to data/staged.")
    ] = None,
    out_dir: Annotated[
        Path | None, typer.Option(help="Destination; defaults to data/analysis.")
    ] = None,
    year_from: Annotated[int | None, typer.Option("--from", help="First year.")] = None,
    year_to: Annotated[int | None, typer.Option("--to", help="Last year.")] = None,
    empty_actual_means_on_time: Annotated[
        bool,
        typer.Option(help="ADR-0012: count a realised flight with no actual time as on schedule."),
    ] = True,
) -> None:
    """Build the group x route x month fact table and its city projections."""
    from airline_delays import fact as fact_mod
    from airline_delays import panel as panel_mod

    root = repo_root()
    analysis = out_dir or root / "data" / "analysis"
    result = fact_mod.build_fact(
        staged_dir or root / "data" / "staged",
        analysis,
        root / "data" / "derived",
        years=_years(year_from, year_to) if year_from and year_to else None,
        groups_path=root / "data" / "external" / "groups.csv",
        empty_actual_means_on_time=empty_actual_means_on_time,
    )
    typer.echo(
        f"fact: {result.fact_rows:,d} cells over {len(result.years)} years in {result.seconds:.1f}s"
    )
    typer.echo("realised flights with no actual time, per year (ADR-0012):")
    for row in result.missing_actual_by_year.to_dict("records"):
        share = row["sh_arr_missing"]
        typer.echo(
            f"  {row['year']}: {row['arr_missing_actual']:>8,d} of {row['realized']:>8,d}"
            f"  ({share:.1%})"
            if share is not None
            else f"  {row['year']}: n/a"
        )
    outside = fact_mod.out_of_window_records(result.out_of_window)
    if outside:
        typer.echo("staged rows dated outside the built years (ADR-0016, not in any table):")
        for row in outside:
            label = "no flight_date" if row["year"] is None else str(row["year"])
            typer.echo(
                f"  {label:>14}: {row['rows']:>6,d} rows, "
                f"{row['universe_rows']:>5,d} in the replication universe"
            )
    import pandas as pd

    fact = pd.read_parquet(analysis / "fact_group_route_month.parquet")
    city = fact_mod.city_month(
        fact,
        pd.read_parquet(root / "data" / "derived" / "node_day_hour.parquet"),
        empty_actual_means_on_time=empty_actual_means_on_time,
    )
    airline_city = fact_mod.add_hub(
        fact_mod.aggregate(
            fact,
            "airline_city_month",
            empty_actual_means_on_time=empty_actual_means_on_time,
        )
    )
    fact_mod.write_table(fact_mod.slim(city), analysis / "city_month.parquet")
    fact_mod.write_table(fact_mod.slim(airline_city), analysis / "airline_city_month.parquet")
    typer.echo(f"city_month: {len(city):,d} rows; airline_city_month: {len(airline_city):,d} rows")
    typer.echo(panel_mod.capacity_note(root / "data" / "external"))


@app.command()
def panel(
    analysis_dir: Annotated[
        Path | None, typer.Option(help="Fact table location; defaults to data/analysis.")
    ] = None,
    empty_actual_means_on_time: Annotated[
        bool, typer.Option(help="ADR-0012 convention; True reproduces the benchmark.")
    ] = True,
    panel_nodes_only: Annotated[
        bool, typer.Option(help="Restrict to the 27 nodes of ADR-0001.")
    ] = True,
) -> None:
    """Build the public route-month panel from the fact table."""
    from airline_delays import panel as panel_mod

    root = repo_root()
    _, result = panel_mod.build_panel(
        analysis_dir or root / "data" / "analysis",
        root / "data" / "derived",
        external_dir=root / "data" / "external",
        empty_actual_means_on_time=empty_actual_means_on_time,
        panel_nodes_only=panel_nodes_only,
    )
    assert result is not None
    typer.echo(
        f"panel: {result.rows:,d} route-months x {result.columns} columns in "
        f"{result.seconds:.1f}s -> {result.parquet.name} "
        f"({result.parquet.stat().st_size / 1e6:.1f} MB) and "
        f"{result.csv.name} ({result.csv.stat().st_size / 1e6:.1f} MB)"
    )


@app.command()
def dictionary(
    out: Annotated[
        Path | None, typer.Option(help="Destination; defaults to docs/dictionary.md.")
    ] = None,
    check: Annotated[
        bool,
        typer.Option(
            "--check", help="Compare the committed file with a rebuild; exit 1 on a difference."
        ),
    ] = False,
) -> None:
    """Generate docs/dictionary.md from the schema. Never edit it by hand."""

    root = repo_root()
    layers = schema.built_layers(root)
    target = out or root / "docs" / "dictionary.md"
    rendered = schema.dictionary_markdown(layers)
    if check:
        if target.exists() and target.read_text(encoding="utf-8") == rendered:
            typer.echo(f"dictionary: {target} is in step with the registry")
            return
        typer.echo(f"dictionary: {target} is stale; run `airline-delays dictionary`", err=True)
        raise typer.Exit(code=1)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(rendered, encoding="utf-8")
    total = sum(len(columns) for columns in layers.values())
    typer.echo(f"dictionary: {total} columns across {len(layers)} layers -> {target}")


@app.command()
def datapackage(
    out: Annotated[
        Path | None, typer.Option(help="Destination; defaults to datapackage.json.")
    ] = None,
    check: Annotated[
        bool,
        typer.Option(
            "--check", help="Compare the committed file with a rebuild; exit 1 on a difference."
        ),
    ] = False,
) -> None:
    """Generate datapackage.json (Frictionless v2) from the schema."""

    root = repo_root()
    target = out or root / "datapackage.json"
    rendered = schema.render_datapackage(root)
    if check:
        if target.exists() and target.read_text(encoding="utf-8") == rendered:
            typer.echo(f"datapackage: {target} is in step with the registry and the tables")
            return
        typer.echo(f"datapackage: {target} is stale; run `airline-delays datapackage`", err=True)
        raise typer.Exit(code=1)
    target.write_text(rendered, encoding="utf-8")
    n_resources = len(json.loads(rendered)["resources"])
    typer.echo(f"datapackage: {n_resources} resources -> {target}")


def _passthrough(module_main, ctx: typer.Context) -> None:
    """Hand the raw arguments to a stage's own ``main``; the stage owns its options."""
    raise typer.Exit(code=module_main(list(ctx.args)))


@app.command(name="zenodo-json")
def zenodo_json(
    out: Annotated[Path | None, typer.Option(help="Destination; defaults to .zenodo.json.")] = None,
    check: Annotated[
        bool,
        typer.Option(
            "--check", help="Compare the committed file with a rebuild; exit 1 on a difference."
        ),
    ] = False,
) -> None:
    """Generate .zenodo.json from the publication metadata. Never edit it by hand."""
    root = repo_root()
    target = out or root / ".zenodo.json"
    rendered = schema.zenodo.render()
    if check:
        if target.exists() and target.read_text(encoding="utf-8") == rendered:
            typer.echo(f"zenodo-json: {target} is in step with the metadata")
            return
        typer.echo(f"zenodo-json: {target} is stale; run `airline-delays zenodo-json`", err=True)
        raise typer.Exit(code=1)
    target.write_text(rendered, encoding="utf-8")
    typer.echo(f"zenodo-json -> {target}")


@app.command(name="article-panel")
def article_panel(
    source: Annotated[
        Path,
        typer.Option(help="The authors' final estimation base (Stata). Read once; never recorded."),
    ],
    out_dir: Annotated[
        Path | None, typer.Option(help="Destination; defaults to data/analysis.")
    ] = None,
) -> None:
    """Curate the article's estimation panel into data/analysis/ (ADR-0020). Owner's machine only."""
    from airline_delays.estimation import article_panel as article_panel_mod

    result = article_panel_mod.build(source, out_dir)
    typer.echo(
        f"article panel: {result.rows:,d} route-months x {result.columns} columns, "
        f"{result.routes} routes, {result.months} months -> {result.parquet.name} "
        f"({result.parquet.stat().st_size / 1e6:.1f} MB), {result.csv.name} "
        f"({result.csv.stat().st_size / 1e6:.1f} MB), {result.manifest.name} in {result.seconds:.1f}s"
    )


@app.command(
    name="estimate", context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
)
def estimate(ctx: typer.Context) -> None:
    """Tables 2-7 of Bendinelli, Bettini & Oliveira (2016) -> reports/replication/."""
    from airline_delays.estimation import run as estimation_run

    _passthrough(estimation_run.main, ctx)


@app.command(name="predict-dataset")
def predict_dataset() -> None:
    """The flight-level modelling table -> data/derived/ml/ (one DuckDB scan per year)."""
    from airline_delays.prediction.dataset import build_dataset

    build_dataset()


@app.command(
    name="predict", context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
)
def predict(ctx: typer.Context) -> None:
    """Rolling-origin delay prediction -> reports/prediction/ (about 39 minutes)."""
    from airline_delays.prediction import run as prediction_run

    _passthrough(prediction_run.main, ctx)


@app.command(
    name="theory", context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
)
def theory(ctx: typer.Context) -> None:
    """The congestion model derived and checked, eleven figures -> reports/theory/ (about 1 s)."""
    from airline_delays.theory import run as theory_run

    _passthrough(theory_run.main, ctx)


@app.command()
def summary(
    out: Annotated[
        Path | None, typer.Option(help="Destination; defaults to reports/summary.json.")
    ] = None,
    check: Annotated[
        bool,
        typer.Option(
            "--check", help="Compare the committed file with a rebuild; exit 1 on a difference."
        ),
    ] = False,
) -> None:
    """reports/summary.json: every headline number the READMEs quote, read from the artefacts."""
    from airline_delays import reporting

    target = out or reporting.SUMMARY_PATH
    if check:
        problems = reporting.check(target)
        if problems:
            for problem in problems:
                typer.echo(f"summary: {problem}", err=True)
            raise typer.Exit(code=1)
        typer.echo(f"summary: {target} is fresh")
        return
    reporting.write(target)
    typer.echo(f"summary -> {target}")


@app.command()
def report(
    only: Annotated[
        list[str] | None,
        typer.Option(help="Compile only these reports (replication, prediction, theory)."),
    ] = None,
) -> None:
    """Compile the Typst reports into reports/build/ (needs typst on the PATH)."""
    from airline_delays import reporting

    for pdf in reporting.compile_all(tuple(only) if only else None):
        typer.echo(f"report -> {pdf}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
