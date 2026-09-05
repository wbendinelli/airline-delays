"""Parse the raw monthly CSVs into the canonical staged flight table.

One row per flight leg, one parquet part per year, zstd level 9, tight types.
DuckDB streams each year straight from CSV to parquet, so peak memory stays
bounded and no more than one year is ever in flight — the machine has 16 GB and
the full series is about 1.2 GB of CSV.

Reading the raw files positionally, not by header name, is deliberate. The two
layouts disagree on separator, encoding, column count *and column order*: in
2010-2013 the destination airport sits between the departure and the arrival
timestamps, so a name-blind positional read of the wrong layout would silently
swap fields. `vra.io.layout_for` picks the layout and this module maps
positions to meanings.

Cleaning decisions, all counted and reported in ``docs/notes/staging.md``:

* ``DI``: digits become integers; the letters ``A`` and ``B`` become 10 and 11;
  anything else (the stray ``O``) becomes null.
* ``Código Tipo Linha``: ``NA`` and ``N/I`` become null; other values are kept
  uppercase even when they are outside the IAC 1504 list.
* ``Código Justificativa``: ``N/A`` and anything that is not two letters become
  null.
* 2010-2013 carry the justification as free text; `CAUSE_TEXT_TO_CODE` maps it
  back to the IAC 1504 code. The one genuinely ambiguous text, ``AUTORIZADO``,
  is resolved by status: ``XB`` for a cancelled flight, ``OA`` otherwise.
* ``flight_date`` is the date of the scheduled departure, falling back to the
  actual departure when the schedule is missing (frequent for DI 7 and DI 9).
* Timestamps that do not parse become null; the delay built on them is null
  too, never zero.
"""

from __future__ import annotations

import json
import platform
import re
import subprocess
import sys
import unicodedata
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from vra import delays as delays_mod
from vra import keys as keys_mod
from vra import universe as universe_mod
from vra.io import LAYOUT_2010, LAYOUT_LEGACY, RawLayout, layout_for, sha256_file

DEFAULT_MEMORY_LIMIT = "8GB"
DEFAULT_THREADS = 8

STATUS_MAP: dict[str, str] = {
    "REALIZADO": universe_mod.STATUS_REALIZED,
    "CANCELADO": universe_mod.STATUS_CANCELLED,
}
"""Raw `Situação Voo` to normalised status; everything else becomes ``other``."""

DI_LETTERS: dict[str, int] = {"A": 10, "B": 11}
"""ADR-free convention from the brief: the two letter DI codes become 10 and 11."""

LINE_TYPE_NULLS: tuple[str, ...] = ("NA", "N/A", "N/I", "NI", "")
"""Raw line-type values that mean "not informed"."""


# --------------------------------------------------------------------- cause codes

IAC1504_CODES: dict[str, str] = {
    # A - flight delays
    "AA": "ATRASO AEROPORTO DE ALTERNATIVA - ORDEM TECNICA",
    "AF": "FACILIDADES DO AEROPORTO - RESTRICOES DE APOIO",
    "AG": "MIGRACAO/ALFANDEGA/SAUDE",
    "AI": "AEROPORTO DE ORIGEM INTERDITADO",
    "AJ": "AEROPORTO DE DESTINO INTERDITADO",
    "AM": "ATRASO AEROPORTO DE ALTERNATIVA - CONDICOES METEOROLOGICAS",
    "AS": "SEGURANCA/PAX/CARGA/ALARME",
    "AR": "AEROPORTO COM RESTRICOES OPERACIONAIS",
    "AT": "LIBERACAO SERV. TRAFEGO AEREO/ANTECIPACAO",
    "DF": "AVARIA DURANTE OPERACOES EM VOO",
    "DG": "AVARIA DURANTE OPERACOES EM SOLO",
    "FP": "PLANO DE VOO - APROVACAO",
    "GF": "ABASTECIMENTO/DESTANQUEIO",
    "MA": "FALHA EQUIPO AUTOMOTIVO E DE ATENDIMENTO DE PAX",
    "MX": "ATRASOS NAO ESPECIFICOS - OUTROS",
    "OA": "AUTORIZADO",
    "RA": "CONEXAO DE AERONAVE",
    "RI": "CONEXAO AERONAVE/VOLTA - VOO DE IDA NAO PENALIZADO AEROPORTO INTERDITADO",
    "RM": "CONEXAO AERONAVE/VOLTA - VOO DE IDA NAO PENALIZADO CONDICOES METEOROLOGICAS",
    "TC": "TROCA DE AERONAVE",
    "TD": "DEFEITOS DA AERONAVE",
    "WA": "ALTERNATIVA ABAIXO DOS LIMITES",
    "WI": "DEGELO E REMOCAO DE NEVE E/OU LAMA EM AERONAVE",
    "WR": "ATRASO DEVIDO RETORNO - CONDICOES METEOROLOGICAS",
    "WO": "AEROPORTO ORIGEM ABAIXO DOS LIMITES",
    "WP": "ATRASO DEVIDO RETORNO - ORDEM TECNICA",
    "WT": "AEROPORTO DESTINO ABAIXO DOS LIMITES",
    "WS": "REMOCAO GELO/AGUA/LAMA/AREIA-EM AEROPORTO",
    # B - cancellations
    "XA": "PROGRAMADO - FERIADO NACIONAL",
    "XB": "AUTORIZADO",
    "XI": "DEVIDO AEROPORTO DE ORIGEM INTERDITADO",
    "XJ": "DEVIDO AEROPORTO DE DESTINO INTERDITADO",
    "XL": "FALTA PAX COM PASSAGEM MARCADA - ( APENAS PARA AS LINHAS AEREAS DOMESTICAS REGIONAIS)",
    "XM": "CANCELAMENTO - CONEXAO AERONAVE/VOLTA - VOO DE IDA CANCELADO - AEROPORTO INTERDITADO",
    "XN": "CANCELAMENTO POR MOTIVOS TECNICOS - OPERACIONAIS",
    "XO": "CANCELAMENTO - AEROPORTO ORIGEM ABAIXO LIMITES",
    "XT": "CANCELAMENTO - AEROPORTO DESTINO ABAIXO LIMITES",
    "XR": "CANCELAMENTO DE VOOS OPERADOS EM CODE SHARING",
    "XS": "CANCELAMENTO - CONEXAO AERONAVE/VOLTA - VOO DE IDA CANCELADO - CONDICOES METEOROLOGICAS",
    # C - flight/leg changes
    "ST": "INCLUSAO DE ETAPA DEVIDO CANCELAMENTO DE ESCALAS PREVISTAS - ( EXCLUSIVO PARA LINHAS SUPLEMENTADAS)",
    "IR": "INCLUSAO DE ETAPA (AEROPORTO DE ALTERNATIVA) DEVIDO A UM VOO ESPECIAL RETORNO",
    "VR": "VOO ESPECIAL DE RETORNO (EXCLUSIVO PARA RETORNO AO AEROPORTO DE ORIGEM)",
    "VE": "ESPECIFICO PARA VOO ESPECIAL DE EXPERIENCIA",
    "VI": "ESPECIFICO PARA VOO ESPECIAL DE INSTRUCAO",
    # D - schedule changes
    "HA": "AUTORIZADA",
    "HB": "OPERACAO DE VOO COM MAIS DE 04 HORAS DE ATRASO PANE AERONAVE",
    "HC": "OPERACAO DE VOO COM MAIS DE 04 HORAS DE ATRASO AEROPORTO INTERDITADO",
    "HD": "ANTECIPACAO DE HORARIO AUTORIZADA",
    "HI": "ANTECIPACAO DE HORARIO AUTORIZADA - ESPECIFICO VOOS INTERNACIONAIS",
}
"""IAC 1504 annex 2: justification code to its published description.

Transcribed from the ANAC PDF (``pergamum.anac.gov.br/pergamum/vinculos/IAC1504.pdf``)
with accents and the old ``VÔO`` spelling folded away, because the map is
consumed only after normalisation.
"""

AMBIGUOUS_CAUSE_TEXTS: dict[str, tuple[str, str]] = {
    "AUTORIZADO": ("XB", "OA"),
}
"""Texts that two codes share; the pair is (code when cancelled, code otherwise)."""


def normalise_text(value: str) -> str:
    """Fold a justification text to a comparable key.

    Strips accents, upper-cases, drops the old ``VÔO``/``VOO`` spelling
    difference and collapses every run of punctuation or whitespace to one
    space, so ``"ATRASOS NÃO ESPECÍFICOS, OUTROS"`` and the PDF's
    ``"ATRASOS NÃO ESPECÍFICOS – OUTROS"`` become the same key.

    `NORMALISE_TEXT_SQL` is the DuckDB translation of this function; staging
    uses the SQL form so that ten million rows do not cross the Python
    boundary, and `test_stage` checks that the two agree.
    """
    text = unicodedata.normalize("NFKD", value)
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = text.upper()
    text = re.sub(r"[^A-Z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


NORMALISE_TEXT_SQL = "trim(regexp_replace(upper(strip_accents({col})), '[^A-Z0-9]+', ' ', 'g'))"
"""DuckDB translation of `normalise_text`; ``{col}`` is the column."""


def normalise_text_sql(column: str) -> str:
    """Render `NORMALISE_TEXT_SQL` for `column`."""
    return NORMALISE_TEXT_SQL.format(col=column)


def _build_text_map() -> dict[str, str]:
    out: dict[str, str] = {}
    for code, text in IAC1504_CODES.items():
        key = normalise_text(text)
        if key in AMBIGUOUS_CAUSE_TEXTS or key in out:
            continue
        out[key] = code
    return out


CAUSE_TEXT_TO_CODE: dict[str, str] = _build_text_map()
"""Normalised IAC 1504 description to code, for the 2010-2013 layout."""


def cause_code_from_text(text: str | None, status: str | None = None) -> str | None:
    """Map a 2010-2013 free-text justification back to its IAC 1504 code.

    Returns None for an empty text or a text with no match; the ambiguous
    ``AUTORIZADO`` resolves by `status`.
    """
    if text is None:
        return None
    key = normalise_text(text)
    if not key:
        return None
    if key in AMBIGUOUS_CAUSE_TEXTS:
        cancelled_code, other_code = AMBIGUOUS_CAUSE_TEXTS[key]
        return cancelled_code if status == universe_mod.STATUS_CANCELLED else other_code
    return CAUSE_TEXT_TO_CODE.get(key)


# ------------------------------------------------------------------------- SQL build

_LEGACY_POS = {
    "airline": "c0",
    "flight_number": "c1",
    "di": "c2",
    "line_type": "c3",
    "origin_icao": "c4",
    "dest_icao": "c5",
    "sched_dep": "c6",
    "actual_dep": "c7",
    "sched_arr": "c8",
    "actual_arr": "c9",
    "status": "c10",
    "cause": "c11",
}

_WIDE_POS = {
    "airline": "c0",
    "flight_number": "c2",
    "di": "c3",
    "line_type": "c4",
    "origin_icao": "c7",
    "sched_dep": "c9",
    "actual_dep": "c10",
    "dest_icao": "c11",
    "sched_arr": "c13",
    "actual_arr": "c14",
    "status": "c15",
    "cause": "c16",
}


def positions_for(layout: RawLayout) -> dict[str, str]:
    """Map a meaning to the positional column that carries it in `layout`."""
    return dict(_LEGACY_POS) if layout is LAYOUT_LEGACY else dict(_WIDE_POS)


def _read_csv_sql(glob: str, layout: RawLayout) -> str:
    columns = "{" + ", ".join(f"'c{i}': 'VARCHAR'" for i in range(layout.n_columns)) + "}"
    return (
        f"read_csv('{glob}', header=false, skip=1, delim='{layout.separator}', "
        f"quote='', escape='', encoding='{layout.encoding}', columns={columns}, "
        "ignore_errors=true, filename=true)"
    )


def _cause_case(pos: dict[str, str], layout: RawLayout) -> str:
    """SQL for the two-letter cause code, per layout."""
    raw = f"upper(trim({pos['cause']}))"
    if layout.cause_is_code:
        return (
            f"CASE WHEN {raw} IS NULL OR {raw} IN ('', 'N/A', 'NA') THEN NULL "
            f"WHEN regexp_matches({raw}, '^[A-Z]{{2}}$') THEN {raw} ELSE NULL END"
        )
    return "cause_text_map.code"


def build_select(glob: str, layout: RawLayout, with_groups: bool = False) -> str:
    """The SELECT that turns one year of raw CSV into the staged schema.

    With `with_groups`, `group` and `class` come from the temporary table
    `groups_tbl` that `_register_groups` builds; without it they are null and
    `vra.groups` fills them later.
    """
    pos = positions_for(layout)
    status_case = (
        "CASE upper(trim({col})) "
        + " ".join(f"WHEN '{raw}' THEN '{clean}'" for raw, clean in STATUS_MAP.items())
        + f" ELSE '{universe_mod.STATUS_OTHER}' END"
    ).format(col=pos["status"])
    di_case = (
        f"CASE WHEN regexp_matches(upper(trim({pos['di']})), '^[0-9]$') "
        f"THEN CAST(trim({pos['di']}) AS TINYINT) "
        + " ".join(
            f"WHEN upper(trim({pos['di']})) = '{letter}' THEN CAST({value} AS TINYINT)"
            for letter, value in DI_LETTERS.items()
        )
        + " ELSE NULL END"
    )
    line_type_case = (
        f"CASE WHEN upper(trim({pos['line_type']})) IN ("
        + ", ".join(f"'{value}'" for value in LINE_TYPE_NULLS)
        + f") THEN NULL ELSE nullif(upper(trim({pos['line_type']})), '') END"
    )
    fmt = layout.datetime_format

    def ts(col: str) -> str:
        return f"try_strptime(nullif(trim({col}), ''), '{fmt}')"

    group_select = 'CAST(NULL AS VARCHAR) AS "group",\n    CAST(NULL AS VARCHAR) AS "class"'
    group_join = ""
    if with_groups:
        group_select = 'g."group" AS "group",\n    g."class" AS "class"'
        # The groups table is dated to the month (ADR-0003), so the interval
        # test runs on the year-month key, never on the day.
        group_join = (
            " LEFT JOIN groups_tbl g ON g.airline = dated.airline "
            "AND (g.start_ym IS NULL OR (year(dated.flight_date) * 100 + month(dated.flight_date)) >= g.start_ym) "
            "AND (g.end_ym IS NULL OR (year(dated.flight_date) * 100 + month(dated.flight_date)) <= g.end_ym)"
        )

    join = ""
    if not layout.cause_is_code:
        join = (
            " LEFT JOIN cause_text_map ON cause_text_map.text_key = "
            f"{normalise_text_sql(pos['cause'])} "
            f"AND cause_text_map.cancelled = ({status_case} = '{universe_mod.STATUS_CANCELLED}')"
        )

    return f"""
WITH src AS (
    SELECT * FROM {_read_csv_sql(glob, layout)}
),
typed AS (
    SELECT
        nullif(upper(trim({pos["airline"]})), '')                       AS airline,
        TRY_CAST(trim({pos["flight_number"]}) AS INTEGER)               AS flight_number,
        {line_type_case}                                                AS line_type,
        {di_case}                                                       AS di,
        nullif(upper(trim({pos["origin_icao"]})), '')                   AS origin_icao,
        nullif(upper(trim({pos["dest_icao"]})), '')                     AS dest_icao,
        {status_case}                                                   AS status,
        {_cause_case(pos, layout)}                                      AS cause_code,
        CAST({ts(pos["sched_dep"])} AS TIMESTAMP_S)                     AS sched_dep,
        CAST({ts(pos["actual_dep"])} AS TIMESTAMP_S)                    AS actual_dep,
        CAST({ts(pos["sched_arr"])} AS TIMESTAMP_S)                     AS sched_arr,
        CAST({ts(pos["actual_arr"])} AS TIMESTAMP_S)                    AS actual_arr
    FROM src{join}
),
dated AS (
    SELECT *,
        CAST(coalesce(sched_dep, actual_dep) AS DATE) AS flight_date,
        coalesce(sched_dep, actual_dep)               AS dep_ref,
        coalesce(sched_arr, actual_arr)               AS arr_ref
    FROM typed
)
SELECT
    dated.flight_date AS flight_date,
    CAST(year(dated.flight_date) AS SMALLINT)                                     AS year,
    CAST(month(dated.flight_date) AS TINYINT)                                     AS month,
    CAST(year(dated.flight_date) * 100 + month(dated.flight_date) AS INTEGER)           AS ym,
    dated.airline AS airline,
    dated.flight_number AS flight_number,
    dated.line_type AS line_type,
    dated.di AS di,
    dated.origin_icao AS origin_icao,
    dated.dest_icao AS dest_icao,
    {keys_mod.node_sql("origin_icao")}                                      AS origin_node,
    {keys_mod.node_sql("dest_icao")}                                        AS dest_node,
    {keys_mod.node_sql("origin_icao")} || '-' || {keys_mod.node_sql("dest_icao")} AS route,
    dated.status AS status,
    dated.cause_code AS cause_code,
    dated.sched_dep AS sched_dep,
    dated.actual_dep AS actual_dep,
    dated.sched_arr AS sched_arr,
    dated.actual_arr AS actual_arr,
    {delays_mod.signed_delay_sql("sched_dep", "actual_dep")}                AS dep_delay_min,
    {delays_mod.signed_delay_sql("sched_arr", "actual_arr")}                AS arr_delay_min,
    {delays_mod.block_sql("sched_dep", "sched_arr")}                        AS sched_block_min,
    {delays_mod.block_sql("actual_dep", "actual_arr")}                      AS actual_block_min,
    CAST(hour(dated.dep_ref) AS TINYINT)                                          AS dep_hour,
    CAST(hour(dated.arr_ref) AS TINYINT)                                          AS arr_hour,
    CAST((dayofweek(dated.flight_date) + 6) % 7 AS TINYINT)                       AS dow,
    {group_select},
    {universe_mod.UNIVERSE_REPL_SQL}                                        AS universe_repl,
    {universe_mod.UNIVERSE_ML_SQL}                                          AS universe_ml,
    dated.status = '{universe_mod.STATUS_REALIZED}'                               AS is_realized
FROM dated{group_join}
"""


# ------------------------------------------------------------------------ staging


@dataclass
class YearResult:
    """What staging one year produced."""

    year: int
    rows: int
    files: int
    path: Path
    sha256: str
    bytes: int
    seconds: float
    rows_year_mismatch: int
    rows_no_date: int
    layout: str


def _register_helpers(con: Any) -> None:
    """Register the lookup table the 2010-2013 cause mapping needs."""
    rows = []
    for key, code in CAUSE_TEXT_TO_CODE.items():
        rows.append((key, True, code))
        rows.append((key, False, code))
    for key, (cancelled_code, other_code) in AMBIGUOUS_CAUSE_TEXTS.items():
        rows.append((normalise_text(key), True, cancelled_code))
        rows.append((normalise_text(key), False, other_code))
    con.execute(
        "CREATE OR REPLACE TEMP TABLE cause_text_map (text_key VARCHAR, cancelled BOOLEAN, code VARCHAR)"
    )
    con.executemany("INSERT INTO cause_text_map VALUES (?, ?, ?)", rows)


def _register_groups(con: Any, groups_path: Path | None) -> bool:
    """Register ``data/external/groups.csv`` when it exists. Returns whether it did."""
    if groups_path is None or not Path(groups_path).exists():
        return False
    con.execute(
        "CREATE OR REPLACE TEMP TABLE groups_tbl AS "
        f"SELECT * FROM read_csv('{groups_path}', header=true, auto_detect=true)"
    )
    names = {row[0] for row in con.execute("DESCRIBE groups_tbl").fetchall()}
    required = {"airline", "group", "start", "end", "class"}
    if not required.issubset(names):
        con.execute("DROP TABLE groups_tbl")
        return False
    # `start` and `end` are dated to the month ("2007-03") in ADR-0003's table,
    # but a full date is accepted too. Both collapse to a YYYYMM integer; a
    # TRY_CAST to DATE would silently null every "YYYY-MM" value and turn the
    # interval test into "always true", duplicating every row of an airline
    # that changed group.
    month_key = (
        "CAST(nullif(regexp_replace(substr(trim(CAST({col} AS VARCHAR)), 1, 7), '-', '', 'g'), '') "
        "AS INTEGER)"
    )
    con.execute(
        "CREATE OR REPLACE TEMP TABLE groups_tbl AS SELECT "
        'upper(trim(airline)) AS airline, "group", "class", '
        f"{month_key.format(col='start')} AS start_ym, "
        f"{month_key.format(col=chr(34) + 'end' + chr(34))} AS end_ym FROM groups_tbl"
    )
    overlaps = con.execute(
        "SELECT count(*) FROM groups_tbl a JOIN groups_tbl b "
        "ON a.airline = b.airline AND a.rowid < b.rowid "
        "AND coalesce(a.start_ym, 0) <= coalesce(b.end_ym, 999912) "
        "AND coalesce(b.start_ym, 0) <= coalesce(a.end_ym, 999912)"
    ).fetchone()[0]
    if overlaps:
        raise ValueError(
            f"{groups_path}: {overlaps} overlapping airline intervals; the join "
            "would duplicate flights. Fix the table, do not widen the join."
        )
    return True


def connect(memory_limit: str = DEFAULT_MEMORY_LIMIT, threads: int = DEFAULT_THREADS) -> Any:
    """A DuckDB connection configured for one-year-at-a-time scans."""
    import duckdb

    con = duckdb.connect()
    con.execute(f"SET memory_limit='{memory_limit}'")
    con.execute(f"SET threads={threads}")
    con.execute("SET preserve_insertion_order=false")
    return con


def stage_year(
    year: int,
    raw_dir: Path,
    out_dir: Path,
    groups_path: Path | None = None,
    con: Any = None,
) -> YearResult:
    """Stage one year of raw CSVs into ``out_dir/year=YYYY/part-0.parquet``."""
    import time

    started = time.time()
    raw_dir, out_dir = Path(raw_dir), Path(out_dir)
    year_dir = raw_dir / "vra" / str(year)
    sources = sorted(year_dir.glob("*.csv"))
    if not sources:
        raise FileNotFoundError(f"no raw CSV for {year} under {year_dir}")
    layout = layout_for(year)
    owns_con = con is None
    con = con or connect()
    try:
        _register_helpers(con)
        has_groups = _register_groups(con, groups_path)
        select_sql = build_select(str(year_dir / "*.csv"), layout, with_groups=has_groups)
        target_dir = out_dir / f"year={year}"
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / "part-0.parquet"
        con.execute(
            f"COPY ({select_sql}) TO '{target}' "
            "(FORMAT PARQUET, COMPRESSION zstd, COMPRESSION_LEVEL 9, ROW_GROUP_SIZE 262144)"
        )
        # hive_partitioning=false is load-bearing here: the directory name
        # "year=YYYY" would otherwise add a second `year` column that shadows
        # the one derived from flight_date, and the mismatch count below would
        # be zero by construction.
        stats = con.execute(
            f"SELECT count(*), count(*) FILTER (WHERE year IS DISTINCT FROM {year}), "
            "count(*) FILTER (WHERE flight_date IS NULL) "
            f"FROM read_parquet('{target}', hive_partitioning=false)"
        ).fetchone()
    finally:
        if owns_con:
            con.close()
    return YearResult(
        year=year,
        rows=int(stats[0]),
        files=len(sources),
        path=target,
        sha256=sha256_file(target),
        bytes=target.stat().st_size,
        seconds=time.time() - started,
        rows_year_mismatch=int(stats[1]),
        rows_no_date=int(stats[2]),
        layout=layout.name,
    )


def tool_versions() -> dict[str, str]:
    """Versions of everything that shaped the staged files."""
    import duckdb
    import pyarrow

    return {
        "python": platform.python_version(),
        "duckdb": duckdb.__version__,
        "pyarrow": pyarrow.__version__,
        "platform": f"{platform.system()} {platform.machine()}",
    }


def git_commit(root: Path) -> str:
    """The current commit, or the placeholder the brief asks for when there is none."""
    try:
        out = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        pass
    return "UNCOMMITTED"


def stage(
    raw_dir: Path,
    out_dir: Path,
    years: tuple[int, ...] = tuple(range(2000, 2014)),
    groups_path: Path | None = None,
    root: Path | None = None,
) -> list[YearResult]:
    """Stage every year in `years`, one at a time, and write the staged manifest."""
    raw_dir, out_dir = Path(raw_dir), Path(out_dir)
    root = root or raw_dir.parent.parent
    results: list[YearResult] = []
    con = connect()
    try:
        for year in years:
            result = stage_year(year, raw_dir, out_dir, groups_path=groups_path, con=con)
            results.append(result)
            print(
                f"{year}: {result.rows:>9,d} rows from {result.files} files "
                f"({result.layout}) -> {result.bytes / 1e6:6.1f} MB in {result.seconds:5.1f}s",
                file=sys.stderr,
                flush=True,
            )
    finally:
        con.close()
    write_manifest(
        out_dir, results, root=root, groups_applied=bool(groups_path and Path(groups_path).exists())
    )
    return results


def write_manifest(
    out_dir: Path,
    results: list[YearResult],
    root: Path,
    groups_applied: bool = False,
) -> Path:
    """Write ``data/staged/manifest.json``."""
    out_dir = Path(out_dir)
    path = out_dir / "manifest.json"
    document = {
        "layer": "staged",
        "grain": "one row per flight leg",
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "git_commit": git_commit(root),
        "tool_versions": tool_versions(),
        "compression": {"codec": "zstd", "level": 9},
        "groups_applied": groups_applied,
        "total_rows": sum(result.rows for result in results),
        "years": [
            {
                "year": result.year,
                "rows": result.rows,
                "source_files": result.files,
                "raw_layout": result.layout,
                "path": str(result.path.relative_to(out_dir.parent.parent)),
                "bytes": result.bytes,
                "sha256": result.sha256,
                "rows_year_mismatch": result.rows_year_mismatch,
                "rows_without_flight_date": result.rows_no_date,
                "seconds": round(result.seconds, 2),
            }
            for result in sorted(results, key=lambda item: item.year)
        ],
    }
    path.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def read_staged(out_dir: Path, years: tuple[int, ...] | None = None, con: Any = None) -> Any:
    """A DuckDB relation over the staged parquet.

    ``hive_partitioning`` is off on purpose: the directory name ``year=YYYY``
    would otherwise add a second `year` column that collides with the data
    column derived from `flight_date`.
    """
    out_dir = Path(out_dir)
    con = con or connect()
    if years:
        globs = ", ".join(f"'{out_dir}/year={year}/*.parquet'" for year in years)
        source = f"read_parquet([{globs}], hive_partitioning=false)"
    else:
        source = f"read_parquet('{out_dir}/year=*/*.parquet', hive_partitioning=false)"
    return con.sql(f"SELECT * FROM {source}")


__all__ = [
    "CAUSE_TEXT_TO_CODE",
    "IAC1504_CODES",
    "LAYOUT_2010",
    "LAYOUT_LEGACY",
    "STATUS_MAP",
    "YearResult",
    "build_select",
    "cause_code_from_text",
    "connect",
    "normalise_text",
    "read_staged",
    "stage",
    "stage_year",
    "write_manifest",
]
