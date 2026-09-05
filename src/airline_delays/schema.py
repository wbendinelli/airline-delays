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
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:  # pragma: no cover - typing only
    import pandas as pd

Aggregation = Literal["sum", "mean", "recompute", "none"]
Layer = Literal["staged", "fact", "city", "airline_city", "panel", "derived", "ml"]


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
_DERIVED = "derived in airline_delays.staging"

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
    Column(
        name="actual_time_suspect",
        dtype="bool",
        unit="flag",
        definition_en="ADR-0015: the departure or arrival delay is a whole calendar day or more in absolute value (|delay| >= 1440 minutes), which in the raw files is a month typo rather than an operation. False when no actual time exists, because an absence is not a suspect timestamp.",
        definition_pt="ADR-0015: o atraso de partida ou de chegada é de um dia civil ou mais em valor absoluto (|atraso| >= 1440 minutos), que nos arquivos brutos é erro de digitação de mês e não operação. Falso quando não há horário real, porque ausência não é horário suspeito.",
        source=_DERIVED,
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
    # `category` and `dictionary<...>` are how a *string* column arrives once it
    # has been dictionary-encoded -- which is what the flight-level table does to
    # every label, because ten million repetitions of "MRSP-MRRJ" as Python
    # objects is a gigabyte and as codes is ten megabytes. Same logical type.
    "string": ("string", "large_string", "varchar", "object", "category", "dictionary"),
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


# =========================================================================== layers
#
# Everything below describes the tables built on top of the staged flights: the
# fact table (`airline_delays.fact`), its city projections and the public route-month
# panel (`airline_delays.panel`). The entries are *generated* from one description
# resolver rather than typed out one by one, because most of them are genuinely
# parametric — "flights whose scheduled departure hour is 07" differs from its
# 23 siblings only in the number, and a hand-typed copy of each is a copy that
# drifts. `tests/test_registry.py` closes the loop the other way: it builds the
# real tables from the fixture and fails if any column has no entry, or any
# entry no column. A generated definition that is wrong is a bug; a definition
# that is missing cannot happen.

_SIDES: dict[str, tuple[str, str]] = {
    "dep": ("departure", "partida"),
    "arr": ("arrival", "chegada"),
}
_CUTS: dict[str, tuple[str, str]] = {
    "gt0": ("more than 0 minutes late", "com mais de 0 minutos de atraso"),
    "gt15": ("more than 15 minutes late", "com mais de 15 minutos de atraso"),
    "gt30": ("more than 30 minutes late", "com mais de 30 minutos de atraso"),
    "gt60": ("more than 60 minutes late", "com mais de 60 minutos de atraso"),
    "1530": ("between 15 and 30 minutes late", "com atraso entre 15 e 30 minutos"),
}
_CATEGORY_PT: dict[str, str] = {
    "weather": "meteorologia",
    "airport_restricted": "aeroporto interditado ou com restrição",
    "rotation": "rotação de aeronave",
    "technical": "técnica (pane, avaria, defeito)",
    "operational": "operacional e tráfego aéreo",
    "authorised": "autorizada",
    "other": "outras",
}
_CLASS_PT: dict[str, str] = {
    "fsc": "das empresas de serviço completo (FSC)",
    "lcc": "das empresas de baixo custo (LCC)",
    "regional": "das regionais",
    "other": "das demais empresas",
}
_SLICES: dict[str, tuple[str, str]] = {
    "fsc": (
        "the article's FSC group set (TAM, Varig, Transbrasil, Vasp), which excludes Avianca Brasil",
        "o conjunto FSC do artigo (TAM, Varig, Transbrasil, Vasp), que exclui a Avianca Brasil",
    ),
    "lccclass": (
        "carriers of class LCC, Webjet included",
        "empresas de classe LCC, Webjet incluída",
    ),
    "fscc": ("carriers of class FSC (ADR-0003)", "empresas de classe FSC (ADR-0003)"),
    "lccfu": (
        "the Gol and Azul groups, the article's LCC set",
        "os grupos Gol e Azul, o conjunto LCC do artigo",
    ),
}

_ANALYSIS = "derived in airline_delays.fact from data/staged"
_PANEL_SRC = "derived in airline_delays.panel from the fact table"
_EXTERNAL = "data/external"


@dataclass(frozen=True)
class _Doc:
    dtype: str
    unit: str
    en: str
    pt: str
    aggregation: Aggregation


_KEY_DOCS: dict[str, _Doc] = {
    "ym": _Doc("int32", "YYYYMM", "Year-month key.", "Chave ano-mês.", "none"),
    "year": _Doc("int16", "year", "Calendar year.", "Ano civil.", "none"),
    "month": _Doc("int8", "month", "Calendar month, 1-12.", "Mês civil, 1-12.", "none"),
    "route": _Doc(
        "string",
        "node pair",
        "Directional route, origin_node-dest_node (ADR-0001).",
        "Rota direcional, origin_node-dest_node (ADR-0001).",
        "none",
    ),
    "origin_node": _Doc(
        "string", "node code", "Origin node (ADR-0001).", "Nó de origem (ADR-0001).", "none"
    ),
    "dest_node": _Doc(
        "string", "node code", "Destination node (ADR-0001).", "Nó de destino (ADR-0001).", "none"
    ),
    "node": _Doc(
        "string",
        "node code",
        "City node the row describes (ADR-0001).",
        "Nó de cidade descrito pela linha (ADR-0001).",
        "none",
    ),
    "group": _Doc(
        "string",
        "group code",
        "Airline economic group at this month (ADR-0003); an unlabelled airline keeps its own ICAO code.",
        "Grupo econômico da empresa neste mês (ADR-0003); empresa sem rótulo mantém o próprio ICAO.",
        "none",
    ),
    "class": _Doc(
        "string",
        "class",
        "Business-model class: FSC, LCC, regional or other (ADR-0011).",
        "Classe de modelo de negócio: FSC, LCC, regional ou other (ADR-0011).",
        "none",
    ),
}


def _measure_doc(name: str) -> _Doc:
    """Definition, unit and aggregation rule of one measure, by name.

    Deliberately a long, flat if-chain: each branch is one column family and
    reads as its own sentence. Raises for an unknown name, so a column added to
    `features.py` without a definition here fails loudly instead of shipping
    undocumented.
    """
    if name in _KEY_DOCS:
        return _KEY_DOCS[name]
    if name.startswith("sched_dep_h"):
        hour = name[-2:]
        return _Doc(
            "int32",
            "flights",
            f"Flights of the cell whose scheduled departure falls in hour {hour} local time.",
            f"Voos da célula com partida prevista na hora {hour}, horário local.",
            "sum",
        )
    for category in (
        "weather",
        "airport_restricted",
        "rotation",
        "technical",
        "operational",
        "authorised",
        "other",
    ):
        if name == f"cause_{category}":
            return _Doc(
                "int32",
                "flights",
                f"Flights whose IAC 1504 justification code falls in the ADR-0005 category '{category}'.",
                f"Voos cujo código de justificativa da IAC 1504 pertence à categoria ADR-0005 '{category}' ({_CATEGORY_PT[category]}).",
                "sum",
            )
        if name == f"sh_cause_{category}":
            return _Doc(
                "float32",
                "share",
                f"cause_{category} divided by the flights of the cell.",
                f"cause_{category} dividido pelos voos da célula.",
                "recompute",
            )
    for set_name, set_codes in _ARTICLE_SETS_FOR_DOCS.items():
        if name == set_name:
            joined = ", ".join(set_codes)
            return _Doc(
                "float32",
                "share",
                f"Flights coded {joined} divided by the flights (or movements) of the cell — the article's '{set_name}'.",
                f"Voos com código {joined} divididos pelos voos (ou movimentos) da célula — o '{set_name}' do artigo.",
                "recompute",
            )
    for klass, klass_pt in _CLASS_PT.items():
        if name == f"sh_flights_{klass}":
            return _Doc(
                "float32",
                "share",
                f"Share of the cell's flights flown by carriers of class {klass.upper()} (ADR-0011).",
                f"Participação dos voos da célula operados por empresas {klass_pt} (ADR-0011).",
                "recompute",
            )
        if name == f"sh_movements_{klass}":
            return _Doc(
                "float32",
                "share",
                f"Share of the node's movements flown by carriers of class {klass.upper()} (ADR-0011).",
                f"Participação dos movimentos do nó operados por empresas {klass_pt} (ADR-0011).",
                "recompute",
            )
    if name == "cause_none":
        return _Doc(
            "int32",
            "flights",
            "Flights with no justification code: no occurrence was reported.",
            "Voos sem código de justificativa: nenhuma ocorrência foi reportada.",
            "sum",
        )
    if name == "sh_cause_none":
        return _Doc(
            "float32",
            "share",
            "cause_none divided by the flights of the cell.",
            "cause_none dividido pelos voos da célula.",
            "recompute",
        )
    if name.startswith("cause_set_"):
        set_name = name[len("cause_set_") :]
        codes = ", ".join(_ARTICLE_SETS_FOR_DOCS[set_name])
        return _Doc(
            "int32",
            "flights",
            f"Flights whose justification code is in the article's '{set_name}' set ({codes}).",
            f"Voos cujo código de justificativa está no conjunto '{set_name}' do artigo ({codes}).",
            "sum",
        )
    if name in ("cancel_technical", "cancel_weather", "cancel_authorised"):
        codes = ", ".join(_CANCEL_CODES_FOR_DOCS[name])
        return _Doc(
            "int32",
            "flights",
            f"Cancelled flights with code {codes}.",
            f"Voos cancelados com código {codes}.",
            "sum",
        )
    if name.startswith("sh_cancel_"):
        stem = name[len("sh_") :]
        return _Doc(
            "float32",
            "share",
            f"{stem} divided by the cancelled flights of the cell.",
            f"{stem} dividido pelos voos cancelados da célula.",
            "recompute",
        )
    doc = _side_doc(name)
    if doc is not None:
        return doc
    if name in _PLAIN_DOCS:
        return _PLAIN_DOCS[name]
    raise KeyError(f"no registry definition for measure {name!r}; add one in airline_delays.schema")


def _side_doc(name: str) -> _Doc | None:
    """Definitions of the two symmetric departure/arrival families."""
    for side, (side_en, side_pt) in _SIDES.items():
        if name == f"{side}_delay_obs":
            return _Doc(
                "int32",
                "flights",
                f"Realised flights with an observed signed {side_en} delay, both timestamps present.",
                f"Voos realizados com atraso de {side_pt} observado e com sinal, os dois horários presentes.",
                "sum",
            )
        if name == f"{side}_missing_actual":
            return _Doc(
                "int32",
                "flights",
                f"Realised flights with a scheduled {side_en} but no actual one — the rows the 2019 vintage read as on time (ADR-0012).",
                f"Voos realizados com {side_pt} prevista e sem {side_pt} real — as linhas que a safra de 2019 leu como pontuais (ADR-0012).",
                "sum",
            )
        if name == f"{side}_early":
            return _Doc(
                "int32",
                "flights",
                f"Realised flights that {side_en[:-1]}ed early, signed delay below zero (ADR-0008).",
                f"Voos realizados com {side_pt} antecipada, atraso com sinal abaixo de zero (ADR-0008).",
                "sum",
            )
        if name == f"{side}_outliers":
            return _Doc(
                "int32",
                "flights",
                f"Realised flights whose {side_en} delay reaches the outlier threshold of 313.25 minutes (ADR-0008); excluded from every sum of minutes.",
                f"Voos realizados cujo atraso de {side_pt} atinge o limiar de outlier de 313,25 minutos (ADR-0008); excluídos de toda soma de minutos.",
                "sum",
            )
        if name == f"{side}_delay_denominator":
            return _Doc(
                "float32",
                "flights",
                f"Flights the {side_en}-delay proportions of this row were divided by, under the convention in force (ADR-0012).",
                f"Voos que serviram de denominador às proporções de atraso de {side_pt} desta linha, sob a convenção vigente (ADR-0012).",
                "recompute",
            )
        if name == f"{side}_delay_mean_min":
            return _Doc(
                "float32",
                "minute",
                f"Mean signed {side_en} delay over the denominator, outliers removed; early flights count negative (ADR-0008).",
                f"Atraso médio de {side_pt} com sinal sobre o denominador, sem outliers; antecipações contam negativo (ADR-0008).",
                "recompute",
            )
        if name == f"{side}_delay_mean_pos_min":
            return _Doc(
                "float32",
                "minute",
                f"Mean {side_en} delay truncated at zero, the private vintage's convention (ADR-0008).",
                f"Atraso médio de {side_pt} truncado em zero, a convenção da safra privada (ADR-0008).",
                "recompute",
            )
        if name == f"{side}_delay_median_min":
            return _Doc(
                "float32",
                "minute",
                f"Median {side_en} delay, recomputed from the flights of this cell (ADR-0004).",
                f"Mediana do atraso de {side_pt}, recalculada dos voos da célula (ADR-0004).",
                "recompute",
            )
        if name == f"{side}_delay_p90_min":
            return _Doc(
                "float32",
                "minute",
                f"90th percentile of the {side_en} delay, recomputed from the flights.",
                f"Percentil 90 do atraso de {side_pt}, recalculado dos voos.",
                "recompute",
            )
        if name == f"sum_{side}_delay_min":
            return _Doc(
                "float64",
                "minute",
                f"Sum of the signed {side_en} delays, outliers removed, early flights negative (ADR-0008).",
                f"Soma dos atrasos de {side_pt} com sinal, sem outliers, antecipações negativas (ADR-0008).",
                "sum",
            )
        if name == f"sum_{side}_delay_pos_min":
            return _Doc(
                "float64",
                "minute",
                f"Sum of the {side_en} delays truncated at zero, outliers removed.",
                f"Soma dos atrasos de {side_pt} truncados em zero, sem outliers.",
                "sum",
            )
        if name == f"sum_{side}_delay_p15_min":
            return _Doc(
                "float64",
                "minute",
                f"Sum of the {side_en} delays counting only what exceeds 15 minutes, zero otherwise.",
                f"Soma dos atrasos de {side_pt} contando só o que passa de 15 minutos, zero caso contrário.",
                "sum",
            )
        for cut, (cut_en, cut_pt) in _CUTS.items():
            if name == f"{side}_delayed_{cut}":
                return _Doc(
                    "int32",
                    "flights",
                    f"Realised flights whose {side_en} was {cut_en}.",
                    f"Voos realizados cuja {side_pt} foi {cut_pt}.",
                    "sum",
                )
            if name == f"sh_{side}_{cut}":
                return _Doc(
                    "float32",
                    "share",
                    f"{side}_delayed_{cut} divided by the {side_en}-delay denominator.",
                    f"{side}_delayed_{cut} dividido pelo denominador de atraso de {side_pt}.",
                    "recompute",
                )
        if name == f"sh_{side}_early":
            return _Doc(
                "float32",
                "share",
                f"{side}_early divided by the {side_en}-delay denominator.",
                f"{side}_early dividido pelo denominador de atraso de {side_pt}.",
                "recompute",
            )
        if name == f"{side}_flights":
            return _Doc(
                "int32",
                "flights",
                f"Flights of the universe scheduled to {side_en[:-1]}e at this node.",
                f"Voos do universo com {side_pt} prevista neste nó.",
                "sum",
            )
        if name == f"{side}_realized":
            return _Doc(
                "int32",
                "flights",
                f"Realised flights scheduled to {side_en[:-1]}e at this node.",
                f"Voos realizados com {side_pt} prevista neste nó.",
                "sum",
            )
        if name == f"{side}_cancelled":
            return _Doc(
                "int32",
                "flights",
                f"Cancelled flights scheduled to {side_en[:-1]}e at this node.",
                f"Voos cancelados com {side_pt} prevista neste nó.",
                "sum",
            )
    if name == "sh_arr_1530":
        return _Doc(
            "float32",
            "share",
            "arr_delayed_1530 divided by the arrival-delay denominator.",
            "arr_delayed_1530 dividido pelo denominador de atraso de chegada.",
            "recompute",
        )
    return None


_ARTICLE_SETS_FOR_DOCS: dict[str, tuple[str, ...]] = {
    "prwheather": (
        "AI",
        "AJ",
        "AM",
        "AR",
        "RI",
        "RM",
        "WA",
        "WO",
        "WR",
        "WT",
        "XI",
        "XJ",
        "XM",
        "XO",
        "XS",
        "XT",
    ),
    "princident": ("DF", "DG", "HB", "MA", "TD"),
    "pr_connc": ("RA",),
}
_CANCEL_CODES_FOR_DOCS: dict[str, tuple[str, ...]] = {
    "cancel_technical": ("XN",),
    "cancel_weather": ("XO", "XT", "XS", "XI", "XJ", "XM"),
    "cancel_authorised": ("XA", "XB"),
}

_PLAIN_DOCS: dict[str, _Doc] = {
    "flights": _Doc(
        "int32",
        "flights",
        "Flights of the replication universe scheduled in the cell: realised plus cancelled (ADR-0002). This is the article's `f`.",
        "Voos do universo de replicação programados na célula: realizados mais cancelados (ADR-0002). É o `f` do artigo.",
        "sum",
    ),
    "realized": _Doc(
        "int32",
        "flights",
        "Flights of the cell that operated.",
        "Voos da célula que operaram.",
        "sum",
    ),
    "cancelled": _Doc(
        "int32",
        "flights",
        "Flights of the cell published as cancelled.",
        "Voos da célula publicados como cancelados.",
        "sum",
    ),
    "n_flight_numbers": _Doc(
        "int32",
        "count",
        "Distinct flight numbers in the cell; not additive, because two groups can reuse a number.",
        "Números de voo distintos na célula; não é aditivo, porque dois grupos podem repetir um número.",
        "recompute",
    ),
    "recovery_obs": _Doc(
        "int32",
        "flights",
        "Realised flights with both delays observed, the base of the recovery measures.",
        "Voos realizados com os dois atrasos observados, base das medidas de recuperação.",
        "sum",
    ),
    "sum_recovery_min": _Doc(
        "float64",
        "minute",
        "Sum of arrival delay minus departure delay; negative means time was made up in the air.",
        "Soma do atraso de chegada menos o de partida; negativo significa recuperação em voo.",
        "sum",
    ),
    "recovered_gt15": _Doc(
        "int32",
        "flights",
        "Flights that left more than 15 minutes late and still arrived within 15.",
        "Voos que partiram com mais de 15 minutos de atraso e ainda assim chegaram dentro de 15.",
        "sum",
    ),
    "sched_block_obs": _Doc(
        "int32",
        "flights",
        "Flights with a scheduled block time.",
        "Voos com tempo de bloco previsto.",
        "sum",
    ),
    "sum_sched_block_min": _Doc(
        "float64",
        "minute",
        "Sum of the scheduled block times.",
        "Soma dos tempos de bloco previstos.",
        "sum",
    ),
    "sum_sched_block_sq": _Doc(
        "float64",
        "minute^2",
        "Sum of the squared scheduled block times, so the standard deviation is exact at any grain.",
        "Soma dos quadrados dos tempos de bloco previstos, para que o desvio-padrão seja exato em qualquer grão.",
        "sum",
    ),
    "actual_block_obs": _Doc(
        "int32",
        "flights",
        "Flights with an actual block time.",
        "Voos com tempo de bloco realizado.",
        "sum",
    ),
    "sum_actual_block_min": _Doc(
        "float64",
        "minute",
        "Sum of the actual block times.",
        "Soma dos tempos de bloco realizados.",
        "sum",
    ),
    "padding_obs": _Doc(
        "int32",
        "flights",
        "Realised flights with both block times, the base of the padding measure.",
        "Voos realizados com os dois tempos de bloco, base da medida de folga.",
        "sum",
    ),
    "sum_padding_min": _Doc(
        "float64",
        "minute",
        "Sum of scheduled minus actual block time: positive means the schedule held slack.",
        "Soma do bloco previsto menos o realizado: positivo significa folga na programação.",
        "sum",
    ),
    "weekend_flights": _Doc(
        "int32",
        "flights",
        "Flights of the cell on a Saturday or Sunday.",
        "Voos da célula em sábado ou domingo.",
        "sum",
    ),
    "night_flights": _Doc(
        "int32",
        "flights",
        "Flights scheduled to depart between 22:00 and 05:59.",
        "Voos com partida prevista entre 22h e 5h59.",
        "sum",
    ),
    "is_entry": _Doc(
        "int8",
        "flag",
        "The group operated this route this month and not in the previous calendar month.",
        "O grupo operou esta rota neste mês e não no mês civil anterior.",
        "sum",
    ),
    "is_exit": _Doc(
        "int8",
        "flag",
        "The group operated this route this month and not in the next calendar month.",
        "O grupo operou esta rota neste mês e não no mês civil seguinte.",
        "sum",
    ),
    "sched_block_mean_min": _Doc(
        "float32",
        "minute",
        "Mean scheduled block time of the cell.",
        "Tempo de bloco previsto médio da célula.",
        "recompute",
    ),
    "sched_block_sd_min": _Doc(
        "float32",
        "minute",
        "Sample standard deviation of the scheduled block time, from the two sums.",
        "Desvio-padrão amostral do tempo de bloco previsto, calculado das duas somas.",
        "recompute",
    ),
    "padding_mean_min": _Doc(
        "float32",
        "minute",
        "Mean scheduled slack: scheduled minus actual block time.",
        "Folga média: bloco previsto menos realizado.",
        "recompute",
    ),
    "recovery_mean_min": _Doc(
        "float32",
        "minute",
        "Mean in-flight recovery: arrival delay minus departure delay.",
        "Recuperação média em voo: atraso de chegada menos o de partida.",
        "recompute",
    ),
    "sh_recovered": _Doc(
        "float32",
        "share",
        "recovered_gt15 divided by recovery_obs.",
        "recovered_gt15 dividido por recovery_obs.",
        "recompute",
    ),
    "sh_night": _Doc(
        "float32",
        "share",
        "night_flights divided by the flights of the cell.",
        "night_flights dividido pelos voos da célula.",
        "recompute",
    ),
    "sh_weekend": _Doc(
        "float32",
        "share",
        "weekend_flights divided by the flights of the cell.",
        "weekend_flights dividido pelos voos da célula.",
        "recompute",
    ),
    "sh_cancel": _Doc(
        "float32",
        "share",
        "Cancelled flights divided by the flights of the cell.",
        "Voos cancelados divididos pelos voos da célula.",
        "recompute",
    ),
    "peak_hour_share": _Doc(
        "float32",
        "share",
        "Share of the cell's flights in its busiest scheduled departure hour.",
        "Participação dos voos da célula na hora de partida programada mais carregada.",
        "recompute",
    ),
    "hhi_hours": _Doc(
        "float32",
        "index 0-1",
        "Herfindahl index of the scheduled departure hours: how concentrated the timetable is in the day.",
        "Índice de Herfindahl das horas de partida programadas: quão concentrada é a malha no dia.",
        "recompute",
    ),
    "n_groups": _Doc(
        "int32",
        "count",
        "Airline groups with at least one flight in the cell.",
        "Grupos de empresas com ao menos um voo na célula.",
        "recompute",
    ),
    "hhi_flights": _Doc(
        "float32",
        "index 0-1",
        "Herfindahl index over the groups' shares of flights; not the article's passenger-based `rthhi` (ADR-0004).",
        "Índice de Herfindahl sobre as participações dos grupos em voos; não é o `rthhi` do artigo, que usa passageiros (ADR-0004).",
        "recompute",
    ),
    "sh_leader": _Doc(
        "float32",
        "share",
        "Flight share of the largest group in the cell.",
        "Participação em voos do maior grupo da célula.",
        "recompute",
    ),
    "n_entries": _Doc(
        "int32",
        "count",
        "Groups operating the route this month that did not operate it in the previous calendar month.",
        "Grupos operando a rota neste mês que não a operavam no mês civil anterior.",
        "sum",
    ),
    "n_exits": _Doc(
        "int32",
        "count",
        "Groups operating the route this month that do not operate it in the next calendar month.",
        "Grupos operando a rota neste mês que não a operam no mês civil seguinte.",
        "sum",
    ),
    "entry_lcc": _Doc(
        "int8",
        "flag",
        "Gol or Azul entered this route this month.",
        "Gol ou Azul entrou nesta rota neste mês.",
        "recompute",
    ),
    "movements": _Doc(
        "int32",
        "movements",
        "Scheduled movements at the node: departures plus arrivals of the universe.",
        "Movimentos programados no nó: partidas mais chegadas do universo.",
        "sum",
    ),
    "movements_realized": _Doc(
        "int32", "movements", "Movements that operated.", "Movimentos que operaram.", "sum"
    ),
    "movements_cancelled": _Doc(
        "int32", "movements", "Movements cancelled.", "Movimentos cancelados.", "sum"
    ),
    "mov_hour_max": _Doc(
        "float32",
        "movements",
        "Busiest single day-hour of the month at this node.",
        "Maior número de movimentos numa dia-hora do mês neste nó.",
        "recompute",
    ),
    "mov_hour_mean": _Doc(
        "float32",
        "movements",
        "Mean movements over the day-hours that had any movement.",
        "Média de movimentos nas dia-horas com algum movimento.",
        "recompute",
    ),
    "congested_hours": _Doc(
        "int32",
        "count",
        "Day-hours of the month at or above the node's own p90 for the year (ADR-0007).",
        "Dia-horas do mês em ou acima do p90 do próprio nó no ano (ADR-0007).",
        "recompute",
    ),
    "congested_movements": _Doc(
        "int32",
        "movements",
        "Movements inside those congested day-hours.",
        "Movimentos dentro dessas dia-horas congestionadas.",
        "recompute",
    ),
    "sh_movements_congested": _Doc(
        "float32",
        "share",
        "Share of the node's monthly movements in congested day-hours; the ADR-0007 proxy for the article's `prcongested`.",
        "Participação dos movimentos do mês do nó em dia-horas congestionadas; o proxy do ADR-0007 para o `prcongested` do artigo.",
        "recompute",
    ),
    "lccfu_present": _Doc(
        "int8",
        "flag",
        "Gol or Azul operated at least one route touching this node this month.",
        "Gol ou Azul operou ao menos uma rota que toca este nó neste mês.",
        "recompute",
    ),
    "n_hub_groups": _Doc(
        "int32",
        "count",
        "Groups for which this node is a hub this month (share, ratio and volume floors of airline_delays.definitions.hubs).",
        "Grupos para os quais este nó é hub neste mês (participação, razão e pisos de volume de airline_delays.definitions.hubs).",
        "recompute",
    ),
    "hub_max_score": _Doc(
        "float32",
        "ratio",
        "Largest hub score at the node: the highest ratio of a group's city share to its system share.",
        "Maior escore de hub no nó: a maior razão entre a participação do grupo na cidade e sua participação no sistema.",
        "recompute",
    ),
    "city_share": _Doc(
        "float32",
        "share",
        "The group's share of this node's movements in the month.",
        "Participação do grupo nos movimentos deste nó no mês.",
        "recompute",
    ),
    "hub_score": _Doc(
        "float32",
        "ratio",
        "The group's city share divided by its share of all movements in the same month.",
        "Participação do grupo na cidade dividida por sua participação em todos os movimentos do mesmo mês.",
        "recompute",
    ),
    "is_hub": _Doc(
        "int8",
        "flag",
        "The node is a hub for this group: share at least 0.20, ratio at least 2, above both volume floors.",
        "O nó é hub deste grupo: participação de ao menos 0,20, razão de ao menos 2, acima dos dois pisos de volume.",
        "recompute",
    ),
    "n_rows_all": _Doc(
        "int32",
        "rows",
        "Every staged row of the route-month, any DI, line type or status — the universe is a filter, not a fact about the world.",
        "Todas as linhas staged da rota-mês, qualquer DI, tipo de linha ou situação — o universo é um filtro, não um fato sobre o mundo.",
        "sum",
    ),
    "n_extra": _Doc(
        "int32",
        "flights",
        "Extra flights, DI 1 and 2, outside the replication universe.",
        "Voos extras, DI 1 e 2, fora do universo de replicação.",
        "sum",
    ),
    "n_return": _Doc("int32", "flights", "Return flights, DI 3.", "Voos de retorno, DI 3.", "sum"),
    "n_intl_leg": _Doc(
        "int32",
        "flights",
        "Domestic legs of international lines, line type I.",
        "Trechos domésticos de linhas internacionais, tipo de linha I.",
        "sum",
    ),
    "n_cargo": _Doc(
        "int32",
        "flights",
        "Cargo flights, line types C and G.",
        "Voos cargueiros, tipos de linha C e G.",
        "sum",
    ),
    "n_postal": _Doc(
        "int32",
        "flights",
        "Postal network flights, line type L.",
        "Voos da rede postal, tipo de linha L.",
        "sum",
    ),
    "n_off_universe": _Doc(
        "int32",
        "rows",
        "Rows of the route-month outside the replication universe.",
        "Linhas da rota-mês fora do universo de replicação.",
        "sum",
    ),
    "sh_extra": _Doc(
        "float32",
        "share",
        "n_extra divided by n_rows_all.",
        "n_extra dividido por n_rows_all.",
        "recompute",
    ),
}


_ARTICLE_DOCS: dict[str, _Doc] = {
    "f": _Doc(
        "int32",
        "flights",
        "Article `f`: flights scheduled on the route-month, realised plus cancelled (ADR-0002).",
        "`f` do artigo: voos programados na rota-mês, realizados mais cancelados (ADR-0002).",
        "sum",
    ),
    "fl_real": _Doc(
        "int32",
        "flights",
        "Flights of the route-month that operated.",
        "Voos da rota-mês que operaram.",
        "sum",
    ),
    "fl_can": _Doc(
        "int32",
        "flights",
        "Article `fl_can`: flights of the route-month that did not operate.",
        "`fl_can` do artigo: voos da rota-mês que não operaram.",
        "sum",
    ),
    "fl_odel": _Doc(
        "int32",
        "flights",
        "Article `fl_odel`: realised flights that departed more than 0 minutes late — the article's cut is 0, not 15.",
        "`fl_odel` do artigo: voos realizados que partiram com mais de 0 minuto de atraso — o corte do artigo é 0, não 15.",
        "sum",
    ),
    "fl_ddel": _Doc(
        "int32",
        "flights",
        "Article `fl_ddel`: realised flights that arrived more than 0 minutes late. Reproduces at 59.8% under the same rule that gives 92.4% for departures; the asymmetry is declared, not resolved (ADR-0002).",
        "`fl_ddel` do artigo: voos realizados que chegaram com mais de 0 minuto de atraso. Reproduz 59,8% sob a mesma regra que dá 92,4% nas partidas; a assimetria está declarada, não resolvida (ADR-0002).",
        "sum",
    ),
    "ndays": _Doc("int16", "days", "Days in the calendar month.", "Dias do mês civil.", "none"),
    "dailyfl": _Doc(
        "float32",
        "flights/day",
        "Article `dailyfl`: f divided by the days in the month.",
        "`dailyfl` do artigo: f dividido pelos dias do mês.",
        "recompute",
    ),
    "dailyfl00": _Doc(
        "float32",
        "hundred flights/day",
        "Article `dailyfl00`: dailyfl divided by 100.",
        "`dailyfl00` do artigo: dailyfl dividido por 100.",
        "recompute",
    ),
    "prcanc": _Doc(
        "float32",
        "share",
        "Article `prcanc`: fl_can divided by f.",
        "`prcanc` do artigo: fl_can dividido por f.",
        "recompute",
    ),
    "all_prdelarr": _Doc(
        "float32",
        "share",
        "All carriers: realised flights arriving more than 15 minutes late, over the arrival denominator.",
        "Todas as empresas: voos realizados chegando com mais de 15 minutos de atraso, sobre o denominador de chegada.",
        "recompute",
    ),
    "all_prdeldep": _Doc(
        "float32",
        "share",
        "All carriers: realised flights departing more than 15 minutes late.",
        "Todas as empresas: voos realizados partindo com mais de 15 minutos de atraso.",
        "recompute",
    ),
    "all_minsarr": _Doc(
        "float32",
        "minute/flight",
        "Article `all_minsarr`: sum of every carrier's signed arrival delay divided by the realised flights of the route-month.",
        "`all_minsarr` do artigo: soma dos atrasos de chegada com sinal de todas as empresas dividida pelos voos realizados da rota-mês.",
        "recompute",
    ),
    "all_minsdep": _Doc(
        "float32",
        "minute/flight",
        "The departure counterpart of all_minsarr.",
        "A contrapartida de partida de all_minsarr.",
        "recompute",
    ),
    "pres_glo": _Doc(
        "int8",
        "flag",
        "The Gol group operated the route this month (VRA operations). The article's `pres_glo` is read from ticket sales.",
        "O grupo Gol operou a rota neste mês (operação no VRA). O `pres_glo` do artigo é lido da venda de bilhetes.",
        "recompute",
    ),
    "pres_azu": _Doc(
        "int8",
        "flag",
        "The Azul group operated the route this month.",
        "O grupo Azul operou a rota neste mês.",
        "recompute",
    ),
    "pres_tam": _Doc(
        "int8",
        "flag",
        "The TAM group operated the route this month.",
        "O grupo TAM operou a rota neste mês.",
        "recompute",
    ),
    "lcc": _Doc(
        "int8",
        "flag",
        "Article `lcc`: Gol or Azul present on the route. Here from VRA operations; the article reads it from the tariff base (ticket sales).",
        "`lcc` do artigo: Gol ou Azul presente na rota. Aqui por operação no VRA; o artigo lê da base tarifária (venda de bilhetes).",
        "recompute",
    ),
    "olccfu": _Doc(
        "int8",
        "flag",
        "Article `olccfu`: Gol or Azul operated some route touching the origin city this month.",
        "`olccfu` do artigo: Gol ou Azul operou alguma rota que toca a cidade de origem neste mês.",
        "recompute",
    ),
    "dlccfu": _Doc(
        "int8",
        "flag",
        "Article `dlccfu`: the same at the destination city.",
        "`dlccfu` do artigo: o mesmo na cidade de destino.",
        "recompute",
    ),
    "maxalccfu": _Doc(
        "int8",
        "flag",
        "Article `maxalccfu`: the larger of olccfu and dlccfu.",
        "`maxalccfu` do artigo: o maior entre olccfu e dlccfu.",
        "recompute",
    ),
    "prwheather": _Doc(
        "float32",
        "share",
        "Article `prwheather` (the misspelling is the article's): flights coded AI, AJ, AM, AR, RI, RM, WA, WO, WR, WT, XI, XJ, XM, XO, XS, XT divided by f. Not only weather — its dominant code is AR, restricted airport (ADR-0005). Reproduces at 98.5%.",
        "`prwheather` do artigo (o erro de grafia é do artigo): voos com código AI, AJ, AM, AR, RI, RM, WA, WO, WR, WT, XI, XJ, XM, XO, XS, XT divididos por f. Não é só clima — seu código dominante é AR, aeroporto com restrições (ADR-0005). Reproduz 98,5%.",
        "recompute",
    ),
    "princident": _Doc(
        "float32",
        "share",
        "Article `princident`: flights coded DF, DG, HB, MA, TD divided by f. Reproduces at 99.1%.",
        "`princident` do artigo: voos com código DF, DG, HB, MA, TD divididos por f. Reproduz 99,1%.",
        "recompute",
    ),
    "pr_connc": _Doc(
        "float32",
        "share",
        "Article `pr_connc`: flights coded RA divided by f. RA is aircraft rotation, not passengers held for a connection as the article's label says (declared difference). Reproduces at 99.2%.",
        "`pr_connc` do artigo: voos com código RA divididos por f. RA é conexão de aeronave, não espera de passageiros como diz o rótulo do artigo (diferença declarada). Reproduz 99,2%.",
        "recompute",
    ),
    "rthhi": _Doc(
        "float32",
        "index 0-1",
        "Article `rthhi`: route concentration over paid passengers. Null throughout: the VRA has no traffic and ANAC's statistical data are not collected (ADR-0004). See rthhi_flights.",
        "`rthhi` do artigo: concentração da rota sobre passageiros pagos. Nulo em toda a base: o VRA não tem tráfego e os dados estatísticos da ANAC não foram coletados (ADR-0004). Ver rthhi_flights.",
        "recompute",
    ),
    "maxcthhi": _Doc(
        "float32",
        "index 0-1",
        "Article `maxcthhi`: the larger endpoint-city passenger HHI. Null for the same reason as rthhi.",
        "`maxcthhi` do artigo: o maior HHI de passageiros entre as cidades-extremo. Nulo pelo mesmo motivo de rthhi.",
        "recompute",
    ),
    "gmchhi": _Doc(
        "float32",
        "index 0-1",
        "Article `gmchhi`: geometric mean of the two endpoint-city passenger HHIs. Null for the same reason.",
        "`gmchhi` do artigo: média geométrica dos dois HHIs de passageiros das cidades-extremo. Nulo pelo mesmo motivo.",
        "recompute",
    ),
    "prcongested": _Doc(
        "float32",
        "share",
        "Article `prcongested`: share of flights in a clock hour above the airport's declared capacity. Null: capacity.csv holds one airport, and one row is not a panel (ADR-0007). The p90 proxy is o_/d_sh_movements_congested.",
        "`prcongested` do artigo: participação dos voos em hora cheia acima da capacidade declarada do aeroporto. Nulo: capacity.csv tem um aeroporto, e uma linha não é um painel (ADR-0007). O proxy p90 é o_/d_sh_movements_congested.",
        "recompute",
    ),
    "rthhi_flights": _Doc(
        "float32",
        "index 0-1",
        "Route concentration over flights, the VRA-computable counterpart of rthhi.",
        "Concentração da rota sobre voos, a contrapartida calculável no VRA de rthhi.",
        "recompute",
    ),
    "maxcthhi_flights": _Doc(
        "float32",
        "index 0-1",
        "The larger of the two endpoint cities' flight HHIs.",
        "O maior entre os HHIs de voos das duas cidades-extremo.",
        "recompute",
    ),
    "gmchhi_flights": _Doc(
        "float32",
        "index 0-1",
        "Geometric mean of the two endpoint cities' flight HHIs.",
        "Média geométrica dos HHIs de voos das duas cidades-extremo.",
        "recompute",
    ),
    "maxcongested": _Doc(
        "float32",
        "share",
        "The larger of the two endpoint cities' congestion proxies (ADR-0007).",
        "O maior entre os proxies de congestionamento das duas cidades-extremo (ADR-0007).",
        "recompute",
    ),
    "maxprdel_proxy": _Doc(
        "float32",
        "share",
        "Proxy for the article's `maxprdel`: the larger of the two endpoint cities' arrival-delay rates. The article's own definition was not recovered (over 40 candidates tested) and is not claimed here.",
        "Proxy para o `maxprdel` do artigo: a maior das taxas de atraso de chegada das duas cidades-extremo. A definição do artigo não foi recuperada (mais de 40 candidatas testadas) e não é reivindicada aqui.",
        "recompute",
    ),
    "distance_km": _Doc(
        "float32",
        "kilometre",
        "Great-circle distance between the two nodes, from data/external/distances_km.csv.",
        "Distância great-circle entre os dois nós, de data/external/distances_km.csv.",
        "none",
    ),
    "legacy_missing_actual_as_zero": _Doc(
        "int8",
        "flag",
        "The ADR-0012 convention this table was built under: 1 means a realised flight with no actual time counted as on schedule, the article's own convention.",
        "A convenção do ADR-0012 sob a qual esta tabela foi construída: 1 significa que um voo realizado sem horário real contou como pontual, a convenção do próprio artigo.",
        "none",
    ),
}

_SLICE_SUFFIX_DOCS: dict[str, tuple[str, str, str, str, Aggregation]] = {
    "f": (
        "int32",
        "flights",
        "Flights of {en} on the route-month, realised plus cancelled.",
        "Voos {pt} na rota-mês, realizados mais cancelados.",
        "sum",
    ),
    "n": (
        "int32",
        "flights",
        "Realised flights of {en} on the route-month.",
        "Voos realizados {pt} na rota-mês.",
        "sum",
    ),
    "prdelarr": (
        "float32",
        "share",
        "Flights of {en} arriving more than 15 minutes late, over their arrival denominator. The article's ODDS is built on this.",
        "Voos {pt} chegando com mais de 15 minutos de atraso, sobre o denominador de chegada. O ODDS do artigo é construído sobre isto.",
        "recompute",
    ),
    "prdelarr1530": (
        "float32",
        "share",
        "Flights of {en} arriving between 15 and 30 minutes late.",
        "Voos {pt} chegando com atraso entre 15 e 30 minutos.",
        "recompute",
    ),
    "prdelarr30m": (
        "float32",
        "share",
        "Flights of {en} arriving more than 30 minutes late.",
        "Voos {pt} chegando com mais de 30 minutos de atraso.",
        "recompute",
    ),
    "prdeldep": (
        "float32",
        "share",
        "Flights of {en} departing more than 15 minutes late.",
        "Voos {pt} partindo com mais de 15 minutos de atraso.",
        "recompute",
    ),
    "oddsarr": (
        "float32",
        "log-odds",
        "Log-odds of the arrival proportion of {en}; null at 0 and 1.",
        "Log-odds da proporção de chegada {pt}; nulo em 0 e 1.",
        "recompute",
    ),
    "oddsdep": (
        "float32",
        "log-odds",
        "Log-odds of the departure proportion of {en}.",
        "Log-odds da proporção de partida {pt}.",
        "recompute",
    ),
    "minsarr": (
        "float32",
        "minute/flight",
        "Sum of the signed arrival delays of {en} divided by the realised flights of ALL carriers on the route-month. The denominator is the article's, and it dilutes the mean by the other carriers' share (declared difference).",
        "Soma dos atrasos de chegada com sinal {pt} dividida pelos voos realizados de TODAS as empresas na rota-mês. O denominador é o do artigo, e dilui a média pela participação das outras empresas (diferença declarada).",
        "recompute",
    ),
    "minsdep": (
        "float32",
        "minute/flight",
        "The departure counterpart of minsarr for {en}.",
        "A contrapartida de partida de minsarr {pt}.",
        "recompute",
    ),
    "minsp15arr": (
        "float32",
        "minute/flight",
        "Sum of the arrival delays of {en} counting only what exceeds 15 minutes, over the same denominator.",
        "Soma dos atrasos de chegada {pt} contando só o que passa de 15 minutos, sobre o mesmo denominador.",
        "recompute",
    ),
    "minsp15dep": (
        "float32",
        "minute/flight",
        "The departure counterpart of minsp15arr for {en}.",
        "A contrapartida de partida de minsp15arr {pt}.",
        "recompute",
    ),
    "minsarr_trunc": (
        "float32",
        "minute/flight",
        "minsarr with early arrivals truncated at zero, the private vintage's convention (ADR-0008); published next to the signed one, not instead of it.",
        "minsarr com chegadas antecipadas truncadas em zero, a convenção da safra privada (ADR-0008); publicado ao lado da versão com sinal, não no lugar dela.",
        "recompute",
    ),
    "minsdep_trunc": (
        "float32",
        "minute/flight",
        "The departure counterpart of minsarr_trunc.",
        "A contrapartida de partida de minsarr_trunc.",
        "recompute",
    ),
}


def _column(name: str, doc: _Doc, layer: Layer, source: str, public: bool = True) -> Column:
    return Column(
        name=name,
        dtype=doc.dtype,
        unit=doc.unit,
        definition_en=doc.en,
        definition_pt=doc.pt,
        source=source,
        layer=layer,
        aggregation=doc.aggregation,
        public=public,
    )


def _panel_doc(name: str) -> _Doc:
    """Definition of one panel column: article, slice, city side, or shared measure."""
    if name in _ARTICLE_DOCS:
        return _ARTICLE_DOCS[name]
    for stem, (slice_en, slice_pt) in _SLICES.items():
        if name.startswith(f"{stem}_"):
            suffix = name[len(stem) + 1 :]
            if suffix in _SLICE_SUFFIX_DOCS:
                dtype, unit, en, pt, aggregation = _SLICE_SUFFIX_DOCS[suffix]
                return _Doc(
                    dtype, unit, en.format(en=slice_en), pt.format(pt=slice_pt), aggregation
                )
            try:
                base = _measure_doc(suffix)
            except KeyError:
                # Not a slice at all: `lccfu_present` shares a prefix with the
                # `lccfu_` slice and is a city-level presence dummy of its own.
                break
            return _Doc(
                base.dtype,
                base.unit,
                f"{base.en} Restricted to {slice_en}.",
                f"{base.pt} Restrito a {slice_pt}.",
                base.aggregation,
            )
    for prefix, (side_en, side_pt) in (
        ("o_", ("origin", "origem")),
        ("d_", ("destination", "destino")),
    ):
        if name.startswith(prefix):
            base = _panel_doc(name[len(prefix) :])
            return _Doc(
                base.dtype,
                base.unit,
                f"{base.en} Measured at the {side_en} city of the route.",
                f"{base.pt} Medido na cidade de {side_pt} da rota.",
                "recompute",
            )
    return _measure_doc(name)


def _resolver(layer: Layer):
    """The definition resolver of one layer."""
    if layer == "ml":
        return _ml_doc
    if layer in {"panel", "city", "airline_city"}:
        return _panel_doc
    return _measure_doc


def build_layer(names: list[str], layer: Layer, source: str) -> list[Column]:
    """Registry entries for one table, in the table's own column order."""
    resolver = _panel_doc if layer == "panel" else _resolver(layer)
    return [_column(name, resolver(name), layer, source) for name in names]


def fact_columns() -> list[Column]:
    """Registry entries for `data/analysis/fact_group_route_month.parquet`."""

    from airline_delays import fact

    names = [*fact.FACT_KEYS, *fact.fact_measures(), "is_entry", "is_exit"]
    return build_layer(names, "fact", _ANALYSIS)


FACT: list[Column] = fact_columns()

_ML_SRC = "derived in airline_delays.prediction.dataset from data/staged and the fact table"

ML_NAMES: tuple[str, ...] = (
    "flight_date",
    "year",
    "ym",
    "flight_number",
    "route",
    "month",
    "dow",
    "is_weekend",
    "is_holiday",
    "is_observance",
    "is_holiday_window",
    "is_high_season",
    "sched_dep_hour",
    "sched_arr_hour",
    "sched_block_min",
    "leg_index",
    "origin_icao",
    "dest_icao",
    "origin_node",
    "dest_node",
    "route_kind",
    "distance_km",
    "origin_metro",
    "dest_metro",
    "origin_slot_coordinated",
    "dest_slot_coordinated",
    "origin_movements_hour",
    "dest_movements_hour",
    "origin_movements_day",
    "dest_movements_day",
    "origin_p90_hour",
    "dest_p90_hour",
    "airline",
    "group",
    "class",
    "airline_route_share_l1",
    "airline_origin_share_l1",
    "months_on_route",
    "is_new_on_route",
    "route_late15_l1",
    "route_obs_l1",
    "route_late15_l12",
    "group_late15_l1",
    "flight_no_late15_l3",
    "flight_no_obs_l3",
    "origin_late15_l1",
    "dest_late15_l1",
    "origin_weather_l1",
    "dest_weather_l1",
    "prev_leg",
    "prev_turnaround_min",
    "prev_arr_delay_min",
    "prev_late15",
    "prev_cancelled",
    "is_realized",
    "has_arr_actual",
    "has_dep_actual",
    "actual_time_suspect",
    "on_time_no_bav",
    "prev_arr_known_h1",
    "late15_arr",
    "late30_arr",
    "arr_delay_min",
    "late15_dep",
    "cancelled",
)
"""Column order of `data/derived/ml/year=YYYY/part-0.parquet`.

Kept here rather than imported from `airline_delays.prediction.dataset` so that `airline_delays.schema`
never depends on the modelling package that depends on it;
`tests/test_leakage.py` asserts the two lists are identical, in order, which
is the same closed loop `tests/test_registry.py` runs for the fact table.
"""

_ML_DOCS: dict[str, _Doc] = {
    "flight_date": _Doc(
        "date32",
        "date",
        "Scheduled departure date. Rows without a scheduled departure are not in this table.",
        "Data da partida prevista. Linhas sem partida prevista não entram nesta tabela.",
        "none",
    ),
    "year": _Doc(
        "int16",
        "year",
        "Calendar year of the scheduled departure.",
        "Ano civil da partida prevista.",
        "none",
    ),
    "ym": _Doc(
        "int32",
        "YYYYMM",
        "Year-month key of the scheduled departure; the key every closed lag window is joined on.",
        "Chave ano-mês da partida prevista; é a chave de junção de toda janela defasada fechada.",
        "none",
    ),
    "flight_number": _Doc(
        "int32",
        "count",
        "Flight number, carried as an identifier; the model sees its lagged delay rate, not the number itself.",
        "Número do voo, mantido como identificador; o modelo vê a taxa de atraso defasada dele, não o número.",
        "none",
    ),
    "route": _Doc(
        "string",
        "node pair",
        "Directional route key origin_node-dest_node; the unit the rolling-origin subsample is drawn on.",
        "Chave direcional da rota origin_node-dest_node; é a unidade em que a subamostra da origem rolante é sorteada.",
        "none",
    ),
    "month": _Doc(
        "int8",
        "month",
        "Calendar month of the scheduled departure, 1-12.",
        "Mês civil da partida prevista, 1-12.",
        "none",
    ),
    "dow": _Doc(
        "int8",
        "day",
        "Day of week of the scheduled departure, 0 = Monday.",
        "Dia da semana da partida prevista, 0 = segunda-feira.",
        "none",
    ),
    "is_weekend": _Doc(
        "int8",
        "flag",
        "1 when the scheduled departure falls on a Saturday or Sunday.",
        "1 quando a partida prevista cai em sábado ou domingo.",
        "sum",
    ),
    "is_holiday": _Doc(
        "int8",
        "flag",
        "1 when the date is a national holiday by federal law (data/external/holidays.csv).",
        "1 quando a data é feriado nacional por lei federal (data/external/holidays.csv).",
        "sum",
    ),
    "is_observance": _Doc(
        "int8",
        "flag",
        "1 on Carnival Monday/Tuesday, Good Friday or Corpus Christi (data/external/observances.csv): days that move schedules without being holidays by law.",
        "1 na segunda e terça de Carnaval, Sexta-Feira Santa ou Corpus Christi (data/external/observances.csv): dias que mexem na malha sem serem feriados por lei.",
        "sum",
    ),
    "is_holiday_window": _Doc(
        "int8",
        "flag",
        "1 on a holiday or observance and on the day before and after it.",
        "1 no feriado ou ponto facultativo e também na véspera e no dia seguinte.",
        "sum",
    ),
    "is_high_season": _Doc(
        "int8",
        "flag",
        "1 in January, July and December, the Brazilian school-holiday months. A declared convention, not a measurement.",
        "1 em janeiro, julho e dezembro, meses de férias escolares no Brasil. Convenção declarada, não medida.",
        "sum",
    ),
    "sched_dep_hour": _Doc(
        "int8",
        "hour",
        "Hour of the scheduled departure, 0-23, computed from sched_dep alone -- unlike the staged dep_hour, which falls back to the actual departure.",
        "Hora da partida prevista, 0-23, calculada só a partir de sched_dep -- ao contrário de dep_hour da camada staged, que recorre à partida real.",
        "none",
    ),
    "sched_arr_hour": _Doc(
        "int8",
        "hour",
        "Hour of the scheduled arrival, 0-23, computed from sched_arr alone.",
        "Hora da chegada prevista, 0-23, calculada só a partir de sched_arr.",
        "none",
    ),
    "sched_block_min": _Doc(
        "int16",
        "minutes",
        "Scheduled block time: minutes between the scheduled departure and the scheduled arrival.",
        "Tempo de bloco previsto: minutos entre a partida prevista e a chegada prevista.",
        "mean",
    ),
    "leg_index": _Doc(
        "int8",
        "count",
        "Position of this leg in the day's chain for the same airline and flight number, 1 for the first.",
        "Posição desta etapa na cadeia do dia da mesma empresa e número de voo, 1 para a primeira.",
        "mean",
    ),
    "origin_icao": _Doc(
        "string",
        "ICAO code",
        "ICAO code of the origin aerodrome.",
        "Código ICAO do aeródromo de origem.",
        "none",
    ),
    "dest_icao": _Doc(
        "string",
        "ICAO code",
        "ICAO code of the destination aerodrome.",
        "Código ICAO do aeródromo de destino.",
        "none",
    ),
    "origin_node": _Doc(
        "string",
        "node code",
        "Origin node (ADR-0001).",
        "Nó de origem (ADR-0001).",
        "none",
    ),
    "dest_node": _Doc(
        "string",
        "node code",
        "Destination node (ADR-0001).",
        "Nó de destino (ADR-0001).",
        "none",
    ),
    "route_kind": _Doc(
        "string",
        "category",
        "shuttle (MRSP-MRRJ either way), metro (both ends metropolitan nodes), capital (both ends in nodes.csv), mixed (one end), other.",
        "shuttle (MRSP-MRRJ nos dois sentidos), metro (as duas pontas em nós metropolitanos), capital (as duas pontas em nodes.csv), mixed (uma ponta), other.",
        "none",
    ),
    "distance_km": _Doc(
        "float32",
        "km",
        "Great-circle distance between the two nodes (data/external/distances_km.csv); null off the 27-node network.",
        "Distância ortodrômica entre os dois nós (data/external/distances_km.csv); nula fora da rede de 27 nós.",
        "mean",
    ),
    "origin_metro": _Doc(
        "int8",
        "flag",
        "1 when the origin airport belongs to one of the three metropolitan nodes (ADR-0001).",
        "1 quando o aeroporto de origem pertence a um dos três nós metropolitanos (ADR-0001).",
        "sum",
    ),
    "dest_metro": _Doc(
        "int8",
        "flag",
        "1 when the destination airport belongs to one of the three metropolitan nodes.",
        "1 quando o aeroporto de destino pertence a um dos três nós metropolitanos.",
        "sum",
    ),
    "origin_slot_coordinated": _Doc(
        "int8",
        "flag",
        "1 when the origin airport was slot-coordinated at this month (data/external/slots.csv: SBGR from 2009-01, SBRJ from 2009-03). Congonhas is absent because no act or date was found for it.",
        "1 quando o aeroporto de origem era coordenado por slots neste mês (data/external/slots.csv: SBGR desde 2009-01, SBRJ desde 2009-03). Congonhas não está na tabela porque nenhum ato ou data foi localizado.",
        "sum",
    ),
    "dest_slot_coordinated": _Doc(
        "int8",
        "flag",
        "1 when the destination airport was slot-coordinated at this month.",
        "1 quando o aeroporto de destino era coordenado por slots neste mês.",
        "sum",
    ),
    "origin_movements_hour": _Doc(
        "int16",
        "movements",
        "Movements scheduled at the origin airport in the flight's own scheduled departure hour, counted over every staged row of the year -- extras, international and cargo included, because they occupy the same runway.",
        "Movimentos previstos no aeroporto de origem na hora prevista de partida do próprio voo, contados sobre todas as linhas staged do ano -- extras, internacionais e cargueiros incluídos, porque ocupam a mesma pista.",
        "recompute",
    ),
    "dest_movements_hour": _Doc(
        "int16",
        "movements",
        "Movements scheduled at the destination airport in the flight's scheduled arrival hour, on the same rule.",
        "Movimentos previstos no aeroporto de destino na hora prevista de chegada, pela mesma regra.",
        "recompute",
    ),
    "origin_movements_day": _Doc(
        "int16",
        "movements",
        "Movements scheduled at the origin airport on the whole day.",
        "Movimentos previstos no aeroporto de origem no dia inteiro.",
        "recompute",
    ),
    "dest_movements_day": _Doc(
        "int16",
        "movements",
        "Movements scheduled at the destination airport on the arrival day.",
        "Movimentos previstos no aeroporto de destino no dia da chegada.",
        "recompute",
    ),
    "origin_p90_hour": _Doc(
        "float32",
        "flag",
        "1 when origin_movements_hour reaches the airport's p90 of scheduled movements per day-hour in the PREVIOUS calendar year (ADR-0007 proxy with the window closed, ADR-0009); null in the first year of a build, which has no previous year.",
        "1 quando origin_movements_hour atinge o p90 de movimentos previstos por dia-hora do próprio aeroporto no ano civil ANTERIOR (proxy da ADR-0007 com a janela fechada, ADR-0009); nulo no primeiro ano da construção, que não tem ano anterior.",
        "recompute",
    ),
    "dest_p90_hour": _Doc(
        "float32",
        "flag",
        "The same busy-hour flag at the destination airport.",
        "A mesma marca de hora cheia no aeroporto de destino.",
        "recompute",
    ),
    "airline": _Doc(
        "string",
        "ICAO designator",
        "Three-letter ICAO designator of the operating airline.",
        "Designador ICAO de três letras da empresa operadora.",
        "none",
    ),
    "group": _Doc(
        "string",
        "group code",
        "Airline economic group at this month (ADR-0003); an unlabelled airline keeps its own ICAO code.",
        "Grupo econômico da empresa neste mês (ADR-0003); empresa sem rótulo mantém o próprio ICAO.",
        "none",
    ),
    "class": _Doc(
        "string",
        "class",
        "Business-model class: FSC, LCC, regional or other (ADR-0011).",
        "Classe de modelo de negócio: FSC, LCC, regional ou other (ADR-0011).",
        "none",
    ),
    "airline_route_share_l1": _Doc(
        "float32",
        "share",
        "The group's share of the route's flights in the PREVIOUS month, from the fact table.",
        "Participação do grupo nos voos da rota no mês ANTERIOR, a partir da tabela de fatos.",
        "recompute",
    ),
    "airline_origin_share_l1": _Doc(
        "float32",
        "share",
        "The group's share of the departures from the origin node in the previous month.",
        "Participação do grupo nas partidas do nó de origem no mês anterior.",
        "recompute",
    ),
    "months_on_route": _Doc(
        "float32",
        "months",
        "Months the group had been continuously on the route as of the previous month, counted from the fact table's is_entry (a gap in the calendar restarts the count). Null when the group was not on the route last month.",
        "Meses que o grupo estava continuamente na rota até o mês anterior, contados a partir do is_entry da tabela de fatos (uma lacuna no calendário reinicia a contagem). Nulo quando o grupo não estava na rota no mês anterior.",
        "recompute",
    ),
    "is_new_on_route": _Doc(
        "int8",
        "flag",
        "1 when months_on_route is null: the group did not fly this route in the previous month.",
        "1 quando months_on_route é nulo: o grupo não voou esta rota no mês anterior.",
        "sum",
    ),
    "route_late15_l1": _Doc(
        "float32",
        "share",
        "Share of the route's observed arrivals more than 15 minutes late in the PREVIOUS month. Denominator arr_delay_obs, so legacy_missing_actual_as_zero = False (ADR-0012).",
        "Proporção das chegadas observadas da rota com mais de 15 minutos de atraso no mês ANTERIOR. Denominador arr_delay_obs, ou seja legacy_missing_actual_as_zero = False (ADR-0012).",
        "recompute",
    ),
    "route_obs_l1": _Doc(
        "int32",
        "flights",
        "Arrivals with an actual timestamp on the route in the previous month: the support behind route_late15_l1, so a rate over three flights is distinguishable from one over three hundred.",
        "Chegadas com horário real na rota no mês anterior: o suporte de route_late15_l1, para distinguir uma taxa sobre três voos de uma sobre trezentos.",
        "recompute",
    ),
    "route_late15_l12": _Doc(
        "float32",
        "share",
        "The same rate twelve months before, which carries the seasonality the one-month lag cannot.",
        "A mesma taxa doze meses antes, que carrega a sazonalidade que a defasagem de um mês não carrega.",
        "recompute",
    ),
    "group_late15_l1": _Doc(
        "float32",
        "share",
        "Share of the airline group's observed arrivals more than 15 minutes late in the previous month, over its whole network.",
        "Proporção das chegadas observadas do grupo com mais de 15 minutos de atraso no mês anterior, em toda a sua malha.",
        "recompute",
    ),
    "flight_no_late15_l3": _Doc(
        "float32",
        "share",
        "Share of arrivals more than 15 minutes late for this airline and flight number over the three previous months (t-3, t-2, t-1).",
        "Proporção de chegadas com mais de 15 minutos de atraso desta empresa e número de voo nos três meses anteriores (t-3, t-2, t-1).",
        "recompute",
    ),
    "flight_no_obs_l3": _Doc(
        "int32",
        "flights",
        "Observations behind flight_no_late15_l3.",
        "Observações por trás de flight_no_late15_l3.",
        "recompute",
    ),
    "origin_late15_l1": _Doc(
        "float32",
        "share",
        "Share of departures from the origin node more than 15 minutes late in the previous month.",
        "Proporção das partidas do nó de origem com mais de 15 minutos de atraso no mês anterior.",
        "recompute",
    ),
    "dest_late15_l1": _Doc(
        "float32",
        "share",
        "Share of arrivals at the destination node more than 15 minutes late in the previous month.",
        "Proporção das chegadas no nó de destino com mais de 15 minutos de atraso no mês anterior.",
        "recompute",
    ),
    "origin_weather_l1": _Doc(
        "float32",
        "share",
        "Share of departures from the origin node carrying a weather justification code (ADR-0005 category 'weather') in the previous month: the closed-window stand-in for a METAR the VRA does not have.",
        "Proporção das partidas do nó de origem com código de justificativa de clima (categoria 'weather' da ADR-0005) no mês anterior: o substituto de janela fechada para um METAR que o VRA não tem.",
        "recompute",
    ),
    "dest_weather_l1": _Doc(
        "float32",
        "share",
        "The same weather-code share among arrivals at the destination node.",
        "A mesma proporção de códigos de clima entre as chegadas no nó de destino.",
        "recompute",
    ),
    "prev_leg": _Doc(
        "int8",
        "flag",
        "1 when a previous leg of the same airline and flight number, on the same day, is scheduled to arrive at this flight's origin airport before it departs.",
        "1 quando existe etapa anterior da mesma empresa e número de voo, no mesmo dia, prevista para chegar ao aeroporto de origem deste voo antes da sua partida.",
        "sum",
    ),
    "prev_turnaround_min": _Doc(
        "float32",
        "minutes",
        "Scheduled turnaround: minutes between the inbound leg's scheduled arrival and this flight's scheduled departure. Null without a linked leg.",
        "Folga programada: minutos entre a chegada prevista da etapa anterior e a partida prevista deste voo. Nulo sem etapa ligada.",
        "mean",
    ),
    "prev_arr_delay_min": _Doc(
        "float32",
        "minutes",
        "H-1 only. Signed arrival delay of the inbound leg, in minutes. Known at the gate, never the day before.",
        "Só no horizonte H-1. Atraso de chegada com sinal da etapa anterior, em minutos. Conhecido no portão, nunca na véspera.",
        "mean",
    ),
    "prev_late15": _Doc(
        "float32",
        "flag",
        "H-1 only. 1 when the inbound leg arrived more than 15 minutes late.",
        "Só no horizonte H-1. 1 quando a etapa anterior chegou com mais de 15 minutos de atraso.",
        "sum",
    ),
    "prev_cancelled": _Doc(
        "float32",
        "flag",
        "H-1 only. 1 when the inbound leg was cancelled.",
        "Só no horizonte H-1. 1 quando a etapa anterior foi cancelada.",
        "sum",
    ),
    "is_realized": _Doc(
        "bool",
        "flag",
        "Whether the flight operated. A diagnostic, never a feature: it is known only after the fact.",
        "Se o voo operou. Diagnóstico, nunca variável explicativa: só se sabe depois do fato.",
        "sum",
    ),
    "has_arr_actual": _Doc(
        "bool",
        "flag",
        "Whether an actual arrival timestamp exists. Diagnostic: it is what decides whether the arrival targets exist (ADR-0012).",
        "Se existe horário real de chegada. Diagnóstico: é o que decide se os alvos de chegada existem (ADR-0012).",
        "sum",
    ),
    "has_dep_actual": _Doc(
        "bool",
        "flag",
        "Whether an actual departure timestamp exists.",
        "Se existe horário real de partida.",
        "sum",
    ),
    "actual_time_suspect": _Doc(
        "bool",
        "flag",
        "ADR-0015: an actual timestamp a whole day or more away from the schedule (|delay| >= 1440 minutes), which in the raw files is a month typo, not an operation. Excluded from every delay target, counted per year; kept as a row, because the flight was still scheduled and still occupied its slot.",
        "ADR-0015: horário real a um dia ou mais do previsto (|atraso| >= 1440 minutos), que nos arquivos brutos é erro de digitação de mês, não operação. Excluído de todo alvo de atraso, contado por ano; mantido como linha, porque o voo foi programado e ocupou o slot.",
        "sum",
    ),
    "on_time_no_bav": _Doc(
        "bool",
        "flag",
        "ADR-0017 reading B: a realised flight of a pre-2010 year, operated by a carrier whose groups.csv class is FSC, LCC or regional, with an empty actual departure or arrival time. IAC 1504 issues the Boletim de Alteracao de Voo only when there is an alteration, so the empty field is the absence of a reported alteration and the delay is read as 0. Never a feature: it is a fact about the outcome.",
        "ADR-0017 leitura B: voo realizado de ano anterior a 2010, operado por empresa cuja classe em groups.csv e FSC, LCC ou regional, com horario real de partida ou chegada vazio. A IAC 1504 so emite o Boletim de Alteracao de Voo quando ha alteracao, entao o campo vazio e a ausencia de alteracao reportada e o atraso e lido como 0. Nunca e feature: e um fato sobre o desfecho.",
        "sum",
    ),
    "prev_arr_known_h1": _Doc(
        "float32",
        "flag",
        "Diagnostic: 1 when the inbound leg's ACTUAL arrival happened at least 60 minutes before this flight's scheduled departure, so prev_arr_delay_min would really be known at H-1. Reported per year rather than used to null the feature, because ADR-0009 defines the horizon.",
        "Diagnóstico: 1 quando a chegada REAL da etapa anterior ocorreu ao menos 60 minutos antes da partida prevista deste voo, de modo que prev_arr_delay_min seria mesmo conhecido em H-1. Reportado por ano em vez de usado para anular a variável, porque a ADR-0009 define o horizonte.",
        "recompute",
    ),
    "late15_arr": _Doc(
        "float32",
        "flag",
        "TARGET. 1 when the arrival delay exceeds 15 minutes. Null on a cancelled flight, on a realised flight with no actual arrival time (ADR-0012) and on a flight whose timestamps are suspect (ADR-0015), never zero.",
        "ALVO. 1 quando o atraso de chegada passa de 15 minutos. Nulo em voo cancelado, em voo realizado sem horário real de chegada (ADR-0012) e em voo com horário suspeito (ADR-0015), nunca zero.",
        "sum",
    ),
    "late30_arr": _Doc(
        "float32",
        "flag",
        "TARGET. 1 when the arrival delay exceeds 30 minutes, ANAC's own second band.",
        "ALVO. 1 quando o atraso de chegada passa de 30 minutos, a segunda faixa da própria ANAC.",
        "sum",
    ),
    "arr_delay_min": _Doc(
        "float32",
        "minutes",
        "TARGET, regression. Signed arrival delay in minutes, actual minus scheduled, early arrivals negative (ADR-0008). Suspect timestamps are already out (ADR-0015); the symmetric outlier threshold of ADR-0015 is not applied here, because trimming a regression target is the consumer's decision.",
        "ALVO de regressão. Atraso de chegada com sinal, real menos previsto, chegada adiantada negativa (ADR-0008). Horários suspeitos já saíram (ADR-0015); o corte simétrico de outlier da ADR-0015 não é aplicado aqui, porque aparar um alvo de regressão é decisão de quem consome.",
        "mean",
    ),
    "late15_dep": _Doc(
        "float32",
        "flag",
        "TARGET. 1 when the departure delay exceeds 15 minutes.",
        "ALVO. 1 quando o atraso de partida passa de 15 minutos.",
        "sum",
    ),
    "cancelled": _Doc(
        "int8",
        "flag",
        "TARGET. 1 when the flight was cancelled. Defined on every row, because the table is the SCHEDULED universe, not the realised one -- this is the only target with no ADR-0012 exclusion.",
        "ALVO. 1 quando o voo foi cancelado. Definido em todas as linhas, porque a tabela é o universo PROGRAMADO e não o realizado -- é o único alvo sem exclusão da ADR-0012.",
        "sum",
    ),
}


def _ml_doc(name: str) -> _Doc:
    """Definition of one column of the flight-level modelling table."""
    try:
        return _ML_DOCS[name]
    except KeyError as exc:
        raise KeyError(
            f"{name!r} is not a registered ml column; add it to registry._ML_DOCS"
        ) from exc


def ml_columns() -> list[Column]:
    """Registry entries for the flight-level modelling table, in column order."""
    return [_column(name, _ml_doc(name), "ml", _ML_SRC) for name in ML_NAMES]


ML: list[Column] = ml_columns()


_BY_NAME_ALL: dict[str, Column] = {column.name: column for column in (*STAGED, *FACT, *ML)}


def describe(name: str, layer: Layer = "panel") -> Column:
    """The registry entry a table column would get, resolved by name and layer."""
    source = {"staged": _DERIVED, "fact": _ANALYSIS, "ml": _ML_SRC}.get(layer, _PANEL_SRC)
    if layer == "staged":
        return get(name)
    return _column(name, _resolver(layer)(name), layer, source)


def describe_frame(frame: Any, layer: Layer, source: str | None = None) -> list[Column]:
    """Registry entries for every column of a built table, in its own order.

    This is how the panel, the city tables and the dictionary stay in step with
    the code that builds them: the names come from the table, the definitions
    from this module, and `tests/test_registry.py` fails if any name has none.
    """
    names, _ = _schema_of(frame)
    chosen = source or {"fact": _ANALYSIS, "staged": _DERIVED, "ml": _ML_SRC}.get(layer, _PANEL_SRC)
    return [_column(name, _resolver(layer)(name), layer, chosen) for name in names]


# ------------------------------------------------------------------ generated docs

LAYER_TITLES: dict[str, str] = {
    "staged": "Staged flights (`data/staged/year=YYYY/part-0.parquet`)",
    "fact": "Fact table, group x route x month (`data/analysis/fact_group_route_month.parquet`)",
    "city": "City-month (`data/analysis/city_month.parquet`)",
    "airline_city": "Airline x city x month (`data/analysis/airline_city_month.parquet`)",
    "panel": "Route-month panel (`data/analysis/panel_route_month.parquet`)",
    "ml": "Flight-level modelling table (`data/derived/ml/year=YYYY/part-0.parquet`)",
}


def dictionary_markdown(layers: dict[str, list[Column]]) -> str:
    """The data dictionary, generated. Never hand-edited (rule 5 of the brief)."""
    lines = [
        "# Data dictionary",
        "",
        "Generated from `src/airline_delays/schema.py` by `airline-delays dictionary`. Do not edit by",
        "hand: the registry is the source of truth, and this file is a rendering of it.",
        "Definitions are given in English and Portuguese; `aggregation` says what happens",
        "to the column when rows are rolled up to a coarser grain (`sum` adds, `recompute`",
        "must be rebuilt from the flights, `none` is a key or label).",
        "",
    ]
    for layer, columns in layers.items():
        if not columns:
            continue
        lines += [
            f"## {LAYER_TITLES.get(layer, layer)}",
            "",
            f"{len(columns)} columns.",
            "",
            "| column | type | unit | aggregation | definition (en) | definição (pt) |",
            "|---|---|---|---|---|---|",
        ]
        for column in columns:
            lines.append(
                f"| `{column.name}` | {column.dtype} | {column.unit} | {column.aggregation} | "
                f"{_escape(column.definition_en)} | {_escape(column.definition_pt)} |"
            )
        lines.append("")
    return "\n".join(lines)


def _escape(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


_FRICTIONLESS_TYPES: dict[str, tuple[str, str | None]] = {
    "date32": ("date", None),
    "int8": ("integer", None),
    "int16": ("integer", None),
    "int32": ("integer", None),
    "int64": ("integer", None),
    "float32": ("number", None),
    "float64": ("number", None),
    "string": ("string", None),
    "bool": ("boolean", None),
    "timestamp[s]": ("datetime", None),
}

LICENCES: dict[str, dict[str, str]] = {
    "data": {
        "name": "CC-BY-4.0",
        "title": "Creative Commons Attribution 4.0",
        "path": "https://creativecommons.org/licenses/by/4.0/",
    },
    "code": {
        "name": "MIT",
        "title": "MIT License",
        "path": "https://opensource.org/licenses/MIT",
    },
}

SOURCES: list[dict[str, str]] = [
    {
        "title": "ANAC, Voo Regular Ativo (VRA), via dados.gov.br",
        "path": "https://dados.gov.br/dados/conjuntos-dados/dadosabertos-areas-de-atuacao-voos-e-operacoes-aereas-voo-regular-ativo-vra",
    },
    {
        "title": "ANAC, IAC 1504 (justification codes, DI codes, line types)",
        "path": "https://pergamum.anac.gov.br/pergamum/vinculos/IAC1504.pdf",
    },
    {
        "title": "OurAirports (airport coordinates behind the node map)",
        "path": "https://davidmegginson.github.io/ourairports-data/airports.csv",
    },
]


def datapackage(resources: list[dict[str, Any]], doi: str | None = None) -> dict:
    """A Frictionless v2 datapackage descriptor, generated from the registry.

    ``id`` is **omitted** until a DOI exists. Frictionless makes the field
    optional, and a placeholder there is worse than nothing: harvesters read the
    descriptor as machine-readable metadata and would resolve
    ``10.5281/zenodo.PENDING`` as a real, dead identifier (audit 2026-09-05,
    M-5). The custom ``pending_doi`` flag says the omission is deliberate and
    where the deposit stands; pass ``doi=`` once Zenodo has minted one and both
    fields flip together.
    """
    identity: dict[str, Any] = (
        {"id": f"https://doi.org/{doi}"}
        if doi
        else {
            "pending_doi": True,
            "pending_doi_note": (
                "No DOI has been minted yet; `id` is omitted rather than filled with a "
                "placeholder that would resolve to nothing. The Zenodo deposit is "
                "tracked in ROADMAP.md, 'Open items'."
            ),
        }
    )
    document: dict[str, Any] = {
        "profile": "data-package",
        "name": "airline-delays",
        **identity,
        "title": "Brazilian airline delays, reconstructed from ANAC's VRA (2000-2013)",
        "description": (
            "Route-month panel and group x route x month fact table reconstructed from "
            "ANAC's Voo Regular Ativo flight-leg records, with the columns of "
            "Bendinelli, Bettini & Oliveira (2016) reproduced under declared definitions."
        ),
        "homepage": "https://github.com/wbendinelli/airline-delays",
        "version": "0.1.0",
        "licenses": [LICENCES["data"]],
        "sources": SOURCES,
        "contributors": [
            {"title": "William Eduardo Bendinelli", "role": "author"},
        ],
        "resources": resources,
    }
    return document


def resource(
    name: str,
    path: str,
    columns: list[Column],
    primary_key: list[str],
    description: str | None = None,
) -> dict:
    """One Frictionless resource whose schema is the registry's own entries.

    `primary_key` may be empty: the flight-level table has no key that is unique
    in the source data (the raw VRA repeats rows), and declaring one that is not
    would be a claim, not a schema.
    """
    fields = []
    for column in columns:
        field_type, field_format = _FRICTIONLESS_TYPES.get(column.dtype, ("any", None))
        field: dict[str, Any] = {
            "name": column.name,
            "type": field_type,
            "title": column.unit,
            "description": column.definition_en,
        }
        if field_format:
            field["format"] = field_format
        field["x-definition-pt"] = column.definition_pt
        field["x-aggregation"] = column.aggregation
        field["x-source"] = column.source
        fields.append(field)
    schema: dict[str, Any] = {"fields": fields}
    if primary_key:
        schema["primaryKey"] = primary_key
    out = {
        "name": name,
        "path": path,
        "format": Path(path).suffix.lstrip("."),
        "mediatype": "application/vnd.apache.parquet" if path.endswith(".parquet") else "text/csv",
        "schema": schema,
    }
    if description:
        out["description"] = description
    return out
