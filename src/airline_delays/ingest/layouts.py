"""The two raw layouts of ANAC's monthly VRA files, declared as data, and the tools that measure a file against them."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RawLayout:
    """A raw CSV layout: how to read the file and where each field sits."""

    name: str
    years: tuple[int, ...]
    separator: str
    encoding: str
    n_columns: int
    columns: tuple[str, ...]
    datetime_format: str
    cause_is_code: bool
    """True when the justification column holds the two-letter IAC 1504 code."""

    quoting: str = "none"
    line_ending: str = "crlf"


LAYOUT_LEGACY = RawLayout(
    name="legacy_12col",
    years=tuple(range(2000, 2010)),
    separator=",",
    encoding="latin-1",
    n_columns=12,
    columns=(
        "ICAO Empresa Aérea",
        "Número Voo",
        "Código Autorização (DI)",
        "Código Tipo Linha",
        "ICAO Aeródromo Origem",
        "ICAO Aeródromoo Destino",  # the typo is in the source file
        "Partida Prevista",
        "Partida Real",
        "Chegada Prevista",
        "Chegada Real",
        "Situação Voo",
        "Código Justificativa",
    ),
    datetime_format="%d/%m/%Y %H:%M",
    cause_is_code=True,
)

LAYOUT_2010 = RawLayout(
    name="wide_20col",
    years=tuple(range(2010, 2014)),
    separator=";",
    encoding="utf-8",
    n_columns=20,
    columns=(
        "Sigla ICAO Empresa Aérea",
        "Empresa Aérea",
        "Número Voo",
        "Código DI",
        "Código Tipo Linha",
        "Modelo Equipamento",
        "Número de Assentos",
        "Sigla ICAO Aeroporto Origem",
        "Descrição Aeroporto Origem",
        "Partida Prevista",
        "Partida Real",
        "Sigla ICAO Aeroporto Destino",
        "Descrição Aeroporto Destino",
        "Chegada Prevista",
        "Chegada Real",
        "Situação Voo",
        "Justificativa",
        "Referência",
        "Situação Partida",
        "Situação Chegada",
    ),
    datetime_format="%d/%m/%Y %H:%M",
    cause_is_code=False,
    line_ending="lf",
)

LAYOUTS: tuple[RawLayout, ...] = (LAYOUT_LEGACY, LAYOUT_2010)


def layout_for(year: int) -> RawLayout:
    """Return the raw layout that applies to `year`."""
    for layout in LAYOUTS:
        if year in layout.years:
            return layout
    raise ValueError(f"no known raw layout for year {year}")


def read_header(path: Path, layout: RawLayout | None = None) -> list[str]:
    """Read the header line of a raw file and split it on its separator."""
    path = Path(path)
    if layout is None:
        year = int(path.parent.name) if path.parent.name.isdigit() else 2002
        layout = layout_for(year)
    with path.open("rb") as handle:
        first = handle.readline()
    return first.decode(layout.encoding).strip("\r\n").split(layout.separator)


def inspect_file(path: Path, sample_lines: int = 5000) -> dict:
    """Measure a raw file instead of assuming: separator, encoding, columns, quirks.

    Returns a dictionary that `docs/notes/staging.md` and the tests consume.
    """
    path = Path(path)
    with path.open("rb") as handle:
        head = handle.read(1 << 20)
    encoding = "utf-8"
    try:
        head.decode("utf-8")
    except UnicodeDecodeError:
        encoding = "latin-1"
    text = head.decode(encoding, errors="replace")
    lines = text.splitlines()[: sample_lines + 1]
    header = lines[0] if lines else ""
    separator = ";" if header.count(";") > header.count(",") else ","
    columns = header.split(separator)
    widths: dict[int, int] = {}
    for line in lines[1:-1]:
        widths[line.count(separator) + 1] = widths.get(line.count(separator) + 1, 0) + 1
    return {
        "file": path.name,
        "encoding": encoding,
        "separator": separator,
        "n_columns": len(columns),
        "columns": columns,
        "line_ending": "crlf" if "\r\n" in text[:4096] else "lf",
        "has_quotes": '"' in text,
        "field_count_histogram": dict(sorted(widths.items())),
        "bytes": path.stat().st_size,
    }
