"""The publication metadata, in one place.

`datapackage.json`, `.zenodo.json` and the consistency test over `CITATION.cff`
and `pyproject.toml` all read these constants, so the title, the version, the
keywords and the creators cannot drift between the four files. The version
comes from `pyproject.toml`; the DOI is ``None`` until Zenodo mints one, and a
placeholder is never written in its place.
"""

from __future__ import annotations

import tomllib
from typing import Any

from airline_delays import paths

TITLE = (
    "airline-delays: Brazil's scheduled domestic flights 2000-2013, from ANAC's raw records to "
    "a published article's tables, its theory, and a flight-level delay predictor"
)
TAGLINE = (
    "Brazil's scheduled domestic flights 2000-2013 -- from ANAC's raw records to a published "
    "article's tables, its theory, and a flight-level delay predictor."
)
DESCRIPTION = (
    "Research compendium of Bendinelli, Bettini & Oliveira (2016, Transportation Research Part A "
    "85, 39-52). Data: the article's estimation panel (24,589 route-months x 52 columns, curated "
    "from the authors' final base of December 2015) and the open reconstruction of ANAC's Voo "
    "Regular Ativo flight-leg records (2000-2013) into a fact table, a route-month panel and two "
    "city projections, with Frictionless Data Package metadata and a bilingual data dictionary. "
    "Code: ingestion, staging, the fact table and panel, the re-estimation of Tables 2-7, the "
    "congestion model derived symbolically, and the flight-level delay predictor. Code under MIT; "
    "curated data and text under CC BY 4.0; VRA-derived tables attributed to ANAC."
)
HOMEPAGE = "https://github.com/wbendinelli/airline-delays"
REPOSITORY = HOMEPAGE
ATTRIBUTION_VRA = "ANAC, Voo Regular Ativo (VRA), via dados.gov.br"
ARTICLE_DOI = "10.1016/j.tra.2016.01.001"
ARTICLE_CITATION = (
    "Bendinelli, W. E., Bettini, H. F. A. J., & Oliveira, A. V. M. (2016). Airline delays, "
    "congestion internalization and non-price spillover effects of low cost carrier entry. "
    "Transportation Research Part A: Policy and Practice, 85, 39-52. "
    "https://doi.org/10.1016/j.tra.2016.01.001"
)
VRA_CATALOGUE_URL = (
    "https://dados.gov.br/dados/conjuntos-dados/"
    "dadosabertos-areas-de-atuacao-voos-e-operacoes-aereas-voo-regular-ativo-vra"
)

#: The concept DOI of the Zenodo record, once minted. ``None`` writes no `id` anywhere.
DOI: str | None = None

KEYWORDS: tuple[str, ...] = (
    "airline delays",
    "air transport",
    "congestion",
    "low cost carriers",
    "reproducible research",
    "econometrics",
    "machine learning",
    "Brazil",
    "ANAC VRA",
    "open data",
)

CREATORS: tuple[dict[str, Any], ...] = (
    {
        "name": "Bendinelli, William Eduardo",
        "given_names": "William Eduardo",
        "family_names": "Bendinelli",
        "affiliation": "Universidade de São Paulo",
        "orcid": None,
    },
)

LICENSES: dict[str, dict[str, str]] = {
    "data": {
        "name": "CC-BY-4.0",
        "title": "Creative Commons Attribution 4.0 International",
        "path": "https://creativecommons.org/licenses/by/4.0/",
    },
    "code": {
        "name": "MIT",
        "title": "MIT License",
        "path": "https://opensource.org/licenses/MIT",
    },
}

SOURCES: tuple[dict[str, str], ...] = (
    {
        "title": ATTRIBUTION_VRA,
        "path": VRA_CATALOGUE_URL,
        "version": "monthly files as published by ANAC, retrieved 2026-09-05; sha256 per file in "
        "data/raw/manifest.json",
    },
    {
        "title": "ANAC, IAC 1504 (justification codes, DI codes, line types)",
        "path": "https://pergamum.anac.gov.br/pergamum/vinculos/IAC1504.pdf",
    },
    {
        "title": "ANAC tariff microdata and statistical data (upstream of the article panel's "
        "concentration and low-cost presence variables)",
        "path": "https://www.gov.br/anac/pt-br/assuntos/dados-e-estatisticas",
    },
    {
        "title": "OurAirports (airport coordinates behind the node map)",
        "path": "https://davidmegginson.github.io/ourairports-data/airports.csv",
    },
    {
        "title": "IBGE, Divisão Regional do Brasil (macro-regions of the seasonality dummies)",
        "path": "https://www.ibge.gov.br/geociencias/organizacao-do-territorio/divisao-regional.html",
    },
    {
        "title": "Diário Oficial da União, federal holiday laws (Lei 662/1949, Lei 10.607/2002)",
        "path": "https://www.planalto.gov.br/ccivil_03/leis/l0662.htm",
    },
    {
        "title": "Bendinelli, Bettini & Oliveira (2016), the article whose tables are replicated",
        "path": f"https://doi.org/{ARTICLE_DOI}",
    },
)

RELATED_IDENTIFIERS: tuple[dict[str, str], ...] = (
    {
        "identifier": ARTICLE_DOI,
        "relation": "isSupplementTo",
        "resource_type": "publication-article",
        "scheme": "doi",
    },
    {"identifier": VRA_CATALOGUE_URL, "relation": "isDerivedFrom", "scheme": "url"},
)


def version() -> str:
    """The project version, from `pyproject.toml` -- the single place it is typed."""
    with (paths.REPO_ROOT / "pyproject.toml").open("rb") as handle:
        return tomllib.load(handle)["project"]["version"]
