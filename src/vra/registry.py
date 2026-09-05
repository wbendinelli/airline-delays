"""The column registry: the single source of truth for every published column.

Rule 5 of the build brief: every column that reaches a public table has an
entry here, and the data dictionary, ``datapackage.json`` and the schema tests
are generated from the registry rather than hand-written. This module holds the
staged flight layer; later layers append their own lists and reuse `Column`.

`aggregation` says what happens to a column when rows are rolled up to a
coarser grain:

``sum``
    Additive across rows (counts, minutes).
``mean``
    Averaged, weighted by the row count of the finer grain.
``recompute``
    Must be recomputed from the flights at the target grain — proportions,
    order statistics and concentration indices. Never averaged.
``none``
    A key or a label; not aggregated at all.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:  # pragma: no cover - typing only
    import pandas as pd

Aggregation = Literal["sum", "mean", "recompute", "none"]
Layer = Literal["staged", "derived", "panel", "ml"]


@dataclass(frozen=True)
class Column:
    """One column of one layer, with everything needed to document and test it."""

    name: str
    dtype: str
    unit: str
    definition_en: str
    definition_pt: str
    source: str
    layer: Layer
    aggregation: Aggregation
    public: bool

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


_RAW_LEGACY = "ANAC VRA raw CSV 2000-2009 (12 columns, comma, latin-1)"
_RAW_2010 = "ANAC VRA raw CSV 2010-2013 (20 columns, semicolon, UTF-8)"
_RAW_BOTH = "ANAC VRA raw CSV (both layouts)"
_DERIVED = "derived in vra.stage"

STAGED: list[Column] = [
    Column(
        name="flight_date",
        dtype="date32",
        unit="date",
        definition_en="Calendar date of the scheduled departure; falls back to the actual departure date when the schedule is missing.",
        definition_pt="Data civil da partida prevista; usa a partida real quando a prevista está ausente.",
        source=_DERIVED,
        layer="staged",
        aggregation="none",
        public=True,
    ),
    Column(
        name="year",
        dtype="int16",
        unit="year",
        definition_en="Calendar year of flight_date.",
        definition_pt="Ano civil de flight_date.",
        source=_DERIVED,
        layer="staged",
        aggregation="none",
        public=True,
    ),
    Column(
        name="month",
        dtype="int8",
        unit="month",
        definition_en="Calendar month of flight_date, 1-12.",
        definition_pt="Mês civil de flight_date, 1-12.",
        source=_DERIVED,
        layer="staged",
        aggregation="none",
        public=True,
    ),
    Column(
        name="ym",
        dtype="int32",
        unit="YYYYMM",
        definition_en="Year-month key as YYYYMM, computed in 32-bit arithmetic.",
        definition_pt="Chave ano-mês no formato AAAAMM, calculada em aritmética de 32 bits.",
        source=_DERIVED,
        layer="staged",
        aggregation="none",
        public=True,
    ),
    Column(
        name="airline",
        dtype="string",
        unit="ICAO designator",
        definition_en="Three-letter ICAO designator of the operating airline.",
        definition_pt="Designador ICAO de três letras da empresa operadora.",
        source=_RAW_BOTH,
        layer="staged",
        aggregation="none",
        public=True,
    ),
    Column(
        name="flight_number",
        dtype="int32",
        unit="count",
        definition_en="Flight number as an integer; leading zeros of the 2010-2013 layout are dropped.",
        definition_pt="Número do voo como inteiro; zeros à esquerda do layout 2010-2013 são removidos.",
        source=_RAW_BOTH,
        layer="staged",
        aggregation="none",
        public=True,
    ),
    Column(
        name="line_type",
        dtype="string",
        unit="code",
        definition_en="IAC 1504 line type: I international, N national, R regional, E special, L, H, C, G.",
        definition_pt="Tipo de linha da IAC 1504: I internacional, N nacional, R regional, E especial, L, H, C, G.",
        source=_RAW_BOTH,
        layer="staged",
        aggregation="none",
        public=True,
    ),
    Column(
        name="di",
        dtype="int8",
        unit="code",
        definition_en="IAC 1504 authorisation code (DI), 0-9; the letters A and B are mapped to 10 and 11.",
        definition_pt="Código de autorização (DI) da IAC 1504, 0-9; as letras A e B viram 10 e 11.",
        source=_RAW_BOTH,
        layer="staged",
        aggregation="none",
        public=True,
    ),
    Column(
        name="origin_icao",
        dtype="string",
        unit="ICAO code",
        definition_en="ICAO code of the origin aerodrome, as published.",
        definition_pt="Código ICAO do aeródromo de origem, como publicado.",
        source=_RAW_BOTH,
        layer="staged",
        aggregation="none",
        public=True,
    ),
    Column(
        name="dest_icao",
        dtype="string",
        unit="ICAO code",
        definition_en="ICAO code of the destination aerodrome, as published.",
        definition_pt="Código ICAO do aeródromo de destino, como publicado.",
        source=_RAW_BOTH,
        layer="staged",
        aggregation="none",
        public=True,
    ),
    Column(
        name="origin_node",
        dtype="string",
        unit="node code",
        definition_en="Origin node (ADR-0001): MRSP for SBSP/SBGR/SBKP, MRRJ for SBGL/SBRJ, MRBH for SBBH/SBCF; every other airport keeps its ICAO code.",
        definition_pt="Nó de origem (ADR-0001): MRSP para SBSP/SBGR/SBKP, MRRJ para SBGL/SBRJ, MRBH para SBBH/SBCF; os demais aeroportos mantêm o próprio ICAO.",
        source=_DERIVED,
        layer="staged",
        aggregation="none",
        public=True,
    ),
    Column(
        name="dest_node",
        dtype="string",
        unit="node code",
        definition_en="Destination node, under the same rule as origin_node.",
        definition_pt="Nó de destino, pela mesma regra de origin_node.",
        source=_DERIVED,
        layer="staged",
        aggregation="none",
        public=True,
    ),
    Column(
        name="route",
        dtype="string",
        unit="node pair",
        definition_en="Directional route key, origin_node-dest_node.",
        definition_pt="Chave direcional da rota, origin_node-dest_node.",
        source=_DERIVED,
        layer="staged",
        aggregation="none",
        public=True,
    ),
    Column(
        name="status",
        dtype="string",
        unit="category",
        definition_en="Normalised flight status: realized, cancelled or other.",
        definition_pt="Situação do voo normalizada: realized, cancelled ou other.",
        source=_RAW_BOTH,
        layer="staged",
        aggregation="none",
        public=True,
    ),
    Column(
        name="cause_code",
        dtype="string",
        unit="code",
        definition_en="Two-letter IAC 1504 justification code; null when absent or N/A. For 2010-2013 the raw file carries the free text, which is mapped back to the code.",
        definition_pt="Código de justificativa de duas letras da IAC 1504; nulo quando ausente ou N/A. Em 2010-2013 o arquivo bruto traz o texto, que é remapeado para o código.",
        source=_RAW_BOTH,
        layer="staged",
        aggregation="none",
        public=True,
    ),
    Column(
        name="sched_dep",
        dtype="timestamp[s]",
        unit="local time (Brasília)",
        definition_en="Scheduled departure timestamp as published, in Brasília local time.",
        definition_pt="Partida prevista como publicada, no horário de Brasília.",
        source=_RAW_BOTH,
        layer="staged",
        aggregation="none",
        public=True,
    ),
    Column(
        name="actual_dep",
        dtype="timestamp[s]",
        unit="local time (Brasília)",
        definition_en="Actual departure timestamp; null when the flight did not depart.",
        definition_pt="Partida real; nula quando o voo não partiu.",
        source=_RAW_BOTH,
        layer="staged",
        aggregation="none",
        public=True,
    ),
    Column(
        name="sched_arr",
        dtype="timestamp[s]",
        unit="local time (Brasília)",
        definition_en="Scheduled arrival timestamp as published.",
        definition_pt="Chegada prevista como publicada.",
        source=_RAW_BOTH,
        layer="staged",
        aggregation="none",
        public=True,
    ),
    Column(
        name="actual_arr",
        dtype="timestamp[s]",
        unit="local time (Brasília)",
        definition_en="Actual arrival timestamp; null when the flight did not arrive.",
        definition_pt="Chegada real; nula quando o voo não chegou.",
        source=_RAW_BOTH,
        layer="staged",
        aggregation="none",
        public=True,
    ),
    Column(
        name="dep_delay_min",
        dtype="float32",
        unit="minute",
        definition_en="Signed departure delay, actual_dep minus sched_dep; negative when early, null when either timestamp is missing (ADR-0008).",
        definition_pt="Atraso de partida com sinal, actual_dep menos sched_dep; negativo quando antecipado, nulo quando falta um dos horários (ADR-0008).",
        source=_DERIVED,
        layer="staged",
        aggregation="mean",
        public=True,
    ),
    Column(
        name="arr_delay_min",
        dtype="float32",
        unit="minute",
        definition_en="Signed arrival delay, actual_arr minus sched_arr; early arrivals stay negative (ADR-0008).",
        definition_pt="Atraso de chegada com sinal, actual_arr menos sched_arr; chegadas antecipadas permanecem negativas (ADR-0008).",
        source=_DERIVED,
        layer="staged",
        aggregation="mean",
        public=True,
    ),
    Column(
        name="sched_block_min",
        dtype="int16",
        unit="minute",
        definition_en="Scheduled block time, sched_arr minus sched_dep.",
        definition_pt="Tempo de bloco previsto, sched_arr menos sched_dep.",
        source=_DERIVED,
        layer="staged",
        aggregation="mean",
        public=True,
    ),
    Column(
        name="actual_block_min",
        dtype="int16",
        unit="minute",
        definition_en="Actual block time, actual_arr minus actual_dep; null for flights that did not both depart and arrive.",
        definition_pt="Tempo de bloco realizado, actual_arr menos actual_dep; nulo para voos que não partiram e chegaram.",
        source=_DERIVED,
        layer="staged",
        aggregation="mean",
        public=True,
    ),
    Column(
        name="dep_hour",
        dtype="int8",
        unit="hour",
        definition_en="Hour of the scheduled departure, 0-23.",
        definition_pt="Hora da partida prevista, 0-23.",
        source=_DERIVED,
        layer="staged",
        aggregation="none",
        public=True,
    ),
    Column(
        name="arr_hour",
        dtype="int8",
        unit="hour",
        definition_en="Hour of the scheduled arrival, 0-23.",
        definition_pt="Hora da chegada prevista, 0-23.",
        source=_DERIVED,
        layer="staged",
        aggregation="none",
        public=True,
    ),
    Column(
        name="dow",
        dtype="int8",
        unit="weekday",
        definition_en="Day of week of flight_date, 0 Monday to 6 Sunday.",
        definition_pt="Dia da semana de flight_date, 0 segunda a 6 domingo.",
        source=_DERIVED,
        layer="staged",
        aggregation="none",
        public=True,
    ),
    Column(
        name="group",
        dtype="string",
        unit="group code",
        definition_en="Airline economic group at the flight date, from data/external/groups.csv (ADR-0003); null when the table is absent at staging time.",
        definition_pt="Grupo econômico da empresa na data do voo, de data/external/groups.csv (ADR-0003); nulo quando a tabela não existe na hora do staging.",
        source="data/external/groups.csv",
        layer="staged",
        aggregation="none",
        public=True,
    ),
    Column(
        name="class",
        dtype="string",
        unit="class",
        definition_en="Business-model class of the group at the flight date: FSC, LCC or regional (ADR-0003).",
        definition_pt="Classe de modelo de negócio do grupo na data do voo: FSC, LCC ou regional (ADR-0003).",
        source="data/external/groups.csv",
        layer="staged",
        aggregation="none",
        public=True,
    ),
    Column(
        name="universe_repl",
        dtype="bool",
        unit="flag",
        definition_en="Replication universe (ADR-0002): line_type in N, R, E and di equal to 0; realised and cancelled flights both included.",
        definition_pt="Universo de replicação (ADR-0002): line_type em N, R, E e di igual a 0; realizados e cancelados incluídos.",
        source=_DERIVED,
        layer="staged",
        aggregation="sum",
        public=True,
    ),
    Column(
        name="universe_ml",
        dtype="bool",
        unit="flag",
        definition_en="Prediction universe (ADR-0002): universe_repl restricted to realised flights.",
        definition_pt="Universo de previsão (ADR-0002): universe_repl restrito aos voos realizados.",
        source=_DERIVED,
        layer="staged",
        aggregation="sum",
        public=True,
    ),
    Column(
        name="is_realized",
        dtype="bool",
        unit="flag",
        definition_en="True when the published status is REALIZADO.",
        definition_pt="Verdadeiro quando a situação publicada é REALIZADO.",
        source=_RAW_BOTH,
        layer="staged",
        aggregation="sum",
        public=True,
    ),
]

STAGED_NAMES: tuple[str, ...] = tuple(column.name for column in STAGED)

_BY_NAME: dict[str, Column] = {column.name: column for column in STAGED}


def get(name: str) -> Column:
    """Look a staged column up by name."""
    try:
        return _BY_NAME[name]
    except KeyError as exc:  # pragma: no cover - defensive
        raise KeyError(f"{name!r} is not a registered staged column") from exc


def to_frame(columns: list[Column] | None = None) -> pd.DataFrame:
    """The registry as a data frame, one row per column, in declaration order."""
    import pandas as pd

    return pd.DataFrame([column.as_dict() for column in (columns or STAGED)])


DTYPE_ALIASES: dict[str, tuple[str, ...]] = {
    "date32": ("date32[day]", "date32", "date"),
    "int8": ("int8", "int08", "tinyint"),
    "int16": ("int16", "smallint"),
    "int32": ("int32", "integer", "int"),
    "int64": ("int64", "bigint"),
    "float32": ("float", "float32", "real"),
    "float64": ("double", "float64"),
    "string": ("string", "large_string", "varchar", "object"),
    "bool": ("bool", "boolean"),
    "timestamp[s]": (
        "timestamp[s]",
        "timestamp[us]",
        "timestamp",
        "datetime64[s]",
        "datetime64[us]",
        "datetime64[ns]",
    ),
}


def _normalise(dtype: str) -> str:
    return str(dtype).strip().lower()


def dtype_matches(declared: str, actual: str) -> bool:
    """True when an observed physical dtype is compatible with the declared one."""
    actual_n = _normalise(actual)
    aliases = DTYPE_ALIASES.get(declared, (declared,))
    return any(actual_n == alias or actual_n.startswith(alias) for alias in aliases)


def validate_schema(
    table: Any, columns: list[Column] | None = None, *, strict_dtypes: bool = True
) -> None:
    """Check that `table` carries exactly the registered columns, in order.

    `table` may be a pandas DataFrame, a pyarrow Table or anything exposing a
    ``columns``/``column_names`` sequence and a way to read dtypes. Raises
    ``ValueError`` listing every problem found, so one run reports them all.
    """
    columns = columns or STAGED
    expected = [column.name for column in columns]
    names, dtypes = _schema_of(table)
    problems: list[str] = []
    missing = [name for name in expected if name not in names]
    extra = [name for name in names if name not in expected]
    if missing:
        problems.append(f"missing columns: {missing}")
    if extra:
        problems.append(f"unregistered columns: {extra}")
    if not missing and not extra and names != expected:
        problems.append(f"column order differs: expected {expected}, got {names}")
    if strict_dtypes:
        for column in columns:
            if column.name in dtypes and not dtype_matches(column.dtype, dtypes[column.name]):
                problems.append(
                    f"{column.name}: registry declares {column.dtype}, table has {dtypes[column.name]}"
                )
    if problems:
        raise ValueError("schema does not match the registry:\n  " + "\n  ".join(problems))


def _schema_of(table: Any) -> tuple[list[str], dict[str, str]]:
    """Names and dtypes of a pandas DataFrame or a pyarrow Table."""
    if hasattr(table, "column_names") and hasattr(table, "schema"):  # pyarrow.Table
        names = list(table.column_names)
        return names, {name: str(table.schema.field(name).type) for name in names}
    if hasattr(table, "dtypes") and hasattr(table, "columns"):  # pandas.DataFrame
        names = [str(name) for name in table.columns]
        return names, {name: str(table.dtypes[name]) for name in names}
    names = [str(name) for name in getattr(table, "columns", [])]
    return names, {}
