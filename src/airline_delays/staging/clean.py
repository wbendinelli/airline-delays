"""The cleaning decisions of the staging stage: status labels, DI letters, null line types and the IAC 1504
cause-code map that turns the 2010-2013 free-text justifications back into codes."""

from __future__ import annotations

import re
import unicodedata

from airline_delays.definitions import universe as universe_mod

STATUS_MAP: dict[str, str] = {
    "REALIZADO": universe_mod.STATUS_REALIZED,
    "CANCELADO": universe_mod.STATUS_CANCELLED,
}

DI_LETTERS: dict[str, int] = {"A": 10, "B": 11}

LINE_TYPE_NULLS: tuple[str, ...] = ("NA", "N/A", "N/I", "NI", "")

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
