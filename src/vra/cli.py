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


def main() -> None:
    app()


if __name__ == "__main__":
    main()
