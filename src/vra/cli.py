"""Command line entry point: ``vra fetch | stage | verify | fixture``.

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

from vra.io import YEARS, Manifest, inspect_file, layout_for
from vra.io import fetch as fetch_raw
from vra.stage import stage as stage_years

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="Reconstruct Brazilian airline delay data from ANAC's VRA files.",
)


def repo_root() -> Path:
    """The repository root, resolved from this file's location."""
    return Path(__file__).resolve().parents[2]


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
def verify(
    private_dir: Annotated[
        Path | None,
        typer.Option(envvar="AIRLINE_DELAYS_PRIVATE_DIR", help="Private benchmark directory."),
    ] = None,
    sample: Annotated[
        int, typer.Option(help="Rows in the deterministic column-by-column sample.")
    ] = 200_000,
    out: Annotated[
        Path | None, typer.Option(help="Report path; defaults to reports/reconciliation.md.")
    ] = None,
) -> None:
    """Reconcile the staged data with the acervo's private vra.dta (optional)."""
    if private_dir is None:
        typer.echo("AIRLINE_DELAYS_PRIVATE_DIR is not set; nothing to reconcile.", err=True)
        raise typer.Exit(code=0)
    root = repo_root()
    script = root / "scripts" / "verify_reconcile.py"
    command = [
        sys.executable,
        str(script),
        "--private-dir",
        str(private_dir),
        "--sample",
        str(sample),
        "--out",
        str(out or root / "reports" / "reconciliation.md"),
    ]
    raise typer.Exit(code=subprocess.run(command, check=False).returncode)


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


@app.command()
def refs(
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
    from vra import codes, groups

    problems = []
    try:
        groups.GroupTable.load(target / "groups.csv")
    except ValueError as exc:
        problems.append(f"groups.csv: {exc}")
    declared = codes.sets_from_file(target / "cause_codes.csv")
    for name, expected in codes.ARTICLE_SETS.items():
        if declared.get(name, ()) != tuple(sorted(expected)):
            problems.append(
                f"cause_codes.csv: article set {name} is {declared.get(name)}, "
                f"ADR-0005 declares {tuple(sorted(expected))}"
            )
    for name, expected_codes in codes.CATEGORIES.items():
        found = codes.categories_from_file(target / "cause_codes.csv").get(name, ())
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


@app.command()
def features(
    staged_dir: Annotated[
        Path | None, typer.Option(help="Source; defaults to data/staged.")
    ] = None,
    out_dir: Annotated[
        Path | None, typer.Option(help="Destination; defaults to data/analysis.")
    ] = None,
    year_from: Annotated[int | None, typer.Option("--from", help="First year.")] = None,
    year_to: Annotated[int | None, typer.Option("--to", help="Last year.")] = None,
    legacy_missing_actual_as_zero: Annotated[
        bool,
        typer.Option(help="ADR-0012: count a realised flight with no actual time as on schedule."),
    ] = True,
) -> None:
    """Build the group x route x month fact table and its city projections."""
    from vra import features as features_mod
    from vra import panel as panel_mod

    root = repo_root()
    analysis = out_dir or root / "data" / "analysis"
    result = features_mod.build_fact(
        staged_dir or root / "data" / "staged",
        analysis,
        root / "data" / "derived",
        years=_years(year_from, year_to) if year_from and year_to else None,
        groups_path=root / "data" / "external" / "groups.csv",
        legacy_missing_actual_as_zero=legacy_missing_actual_as_zero,
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
    outside = features_mod.out_of_window_records(result.out_of_window)
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
    city = panel_mod.city_month(
        fact,
        pd.read_parquet(root / "data" / "derived" / "node_day_hour.parquet"),
        legacy_missing_actual_as_zero=legacy_missing_actual_as_zero,
    )
    airline_city = features_mod.add_hub(
        features_mod.aggregate(
            fact,
            "airline_city_month",
            legacy_missing_actual_as_zero=legacy_missing_actual_as_zero,
        )
    )
    features_mod.write_table(features_mod.slim(city), analysis / "city_month.parquet")
    features_mod.write_table(
        features_mod.slim(airline_city), analysis / "airline_city_month.parquet"
    )
    typer.echo(f"city_month: {len(city):,d} rows; airline_city_month: {len(airline_city):,d} rows")
    typer.echo(panel_mod.capacity_note(root / "data" / "external"))


@app.command()
def panel(
    analysis_dir: Annotated[
        Path | None, typer.Option(help="Fact table location; defaults to data/analysis.")
    ] = None,
    legacy_missing_actual_as_zero: Annotated[
        bool, typer.Option(help="ADR-0012 convention; True reproduces the benchmark.")
    ] = True,
    panel_nodes_only: Annotated[
        bool, typer.Option(help="Restrict to the 27 nodes of ADR-0001.")
    ] = True,
) -> None:
    """Build the public route-month panel from the fact table."""
    from vra import panel as panel_mod

    root = repo_root()
    _, result = panel_mod.build_panel(
        analysis_dir or root / "data" / "analysis",
        root / "data" / "derived",
        external_dir=root / "data" / "external",
        legacy_missing_actual_as_zero=legacy_missing_actual_as_zero,
        panel_nodes_only=panel_nodes_only,
    )
    assert result is not None
    typer.echo(
        f"panel: {result.rows:,d} route-months x {result.columns} columns in "
        f"{result.seconds:.1f}s -> {result.parquet.name} "
        f"({result.parquet.stat().st_size / 1e6:.1f} MB) and "
        f"{result.csv.name} ({result.csv.stat().st_size / 1e6:.1f} MB)"
    )


RESOURCE_NOTES: dict[str, str] = {
    "ml": (
        "Flight-level modelling table for delay prediction: one row per scheduled "
        "flight of the replication universe (ADR-0002), pre-departure features only "
        "(ADR-0009), targets null where ADR-0012 leaves no actual timestamp. "
        "Partitioned by year, about 313 MB, rebuilt in 33 seconds by `just ml-dataset` and "
        "therefore not tracked in git (ADR-0004)."
    ),
}


def _built_layers(root: Path) -> dict[str, list]:
    """Registry entries for every table that currently exists on disk."""
    import pandas as pd

    from vra import registry

    analysis = root / "data" / "analysis"
    layers: dict[str, list] = {"staged": list(registry.STAGED)}
    for layer, filename in (
        ("fact", "fact_group_route_month.parquet"),
        ("city", "city_month.parquet"),
        ("airline_city", "airline_city_month.parquet"),
        ("panel", "panel_route_month.parquet"),
    ):
        path = analysis / filename
        if path.exists():
            frame = pd.read_parquet(path)
            layers[layer] = registry.describe_frame(frame, layer)
    # The flight-level modelling table is 313 MB and never enters git (ADR-0004),
    # so its entry is the registry's declared list rather than a built file --
    # a reader of the dictionary must be able to see the columns of a table they
    # will rebuild, not only of the tables that ship.
    layers["ml"] = list(registry.ML)
    return layers


@app.command()
def dictionary(
    out: Annotated[
        Path | None, typer.Option(help="Destination; defaults to docs/dictionary.md.")
    ] = None,
) -> None:
    """Generate docs/dictionary.md from the registry. Never edit it by hand."""
    from vra import registry

    root = repo_root()
    layers = _built_layers(root)
    target = out or root / "docs" / "dictionary.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(registry.dictionary_markdown(layers), encoding="utf-8")
    total = sum(len(columns) for columns in layers.values())
    typer.echo(f"dictionary: {total} columns across {len(layers)} layers -> {target}")


@app.command()
def datapackage(
    out: Annotated[
        Path | None, typer.Option(help="Destination; defaults to datapackage.json.")
    ] = None,
) -> None:
    """Generate datapackage.json (Frictionless v2) from the registry."""
    from vra import registry

    root = repo_root()
    layers = _built_layers(root)
    paths = {
        "fact": (
            "fact_group_route_month",
            "data/analysis/fact_group_route_month.parquet",
            ["ym", "route", "group"],
        ),
        "city": ("city_month", "data/analysis/city_month.parquet", ["ym", "node"]),
        "airline_city": (
            "airline_city_month",
            "data/analysis/airline_city_month.parquet",
            ["ym", "node", "group"],
        ),
        "panel": ("panel_route_month", "data/analysis/panel_route_month.parquet", ["route", "ym"]),
        "ml": ("flights_features", "data/derived/ml/year=*/part-0.parquet", []),
    }
    resources = [
        registry.resource(name, path, layers[layer], key, description=RESOURCE_NOTES.get(layer))
        for layer, (name, path, key) in paths.items()
        if layer in layers
    ]
    target = out or root / "datapackage.json"
    target.write_text(
        json.dumps(registry.datapackage(resources), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    typer.echo(f"datapackage: {len(resources)} resources -> {target}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
