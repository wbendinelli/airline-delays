# Data availability

Data Availability Statement for `airline-delays`, source by source: who
holds each source, how to obtain it, what restricts its use, and what it
costs in money and time. The README's "Data availability" section is the
short version of this page. `data/external/*.csv` is the machine-readable
version -- every row there carries its own `source`, `url`, `retrieved_at`
and `confidence`, validated by `uv run airline-delays reference` -- and
`datapackage.json` describes every published table with its hashes, licence
and sources.

Two data products come out of these sources, and this page says which source
feeds which. The **article's estimation panel** -- the final base of Bendinelli, Bettini &
Oliveira (2016, *Transportation Research Part A* 85, 39-52, doi
10.1016/j.tra.2016.01.001), from which Tables 2-7 were estimated, curated to
52 columns and published here as source 12 -- carries the authors' own variables, among them terms
built from sources this repository does not collect. The **open
reconstruction panel** is built from source 1 and the reference tables
alone. The two panels share the universe, the node map and the carrier sets recorded
in `DECISIONS.md`; the reconstruction follows the article's empty-actual-time
convention (ADR-0012) and declares its own delay threshold (ADR-0008,
ADR-0015). Every number
on this page is a value of `reports/summary.json`.

## Summary table

| # | Source | Holder | Redistributed here | Cost / time |
|---|---|---|---|---|
| 1 | VRA -- Voo Regular Ativo (flight-leg CSVs, 2000-2013) | ANAC | Derived tables, CC BY with attribution; the raw files are refetched, not redistributed | Free; about 17 minutes and 2.17 GB for the 168 monthly files |
| 2 | IAC 1504 (delay-cause code taxonomy) | ANAC | Derived code tables, not the instrument's text | Free |
| 3 | ANAC statistical data (paid passengers by airline-route-month) | ANAC | Not collected here; the article panel carries the authors' concentration terms and instruments built from it | Free; not spent |
| 4 | ANAC tariff microdata (tickets sold by airline and route) | ANAC | Not collected here; the article panel carries the authors' low-cost presence dummies built from it | Free; not spent |
| 5 | BNDES/McKinsey (2010) airport-capacity study | BNDES | One transcribed row (Congonhas) | Free; transcription time |
| 6 | ANAC seasonal declared-capacity bulletins | ANAC | Not collected; the article panel carries the authors' congestion counts | Free; not spent |
| 7 | ANAC slot-coordination acts (Relatórios de Atividades) | ANAC | Two transcribed rows (Guarulhos, Santos Dumont) | Free; PDF-reading time |
| 8 | CADE/ANAC merger and grouping decisions | CADE / ANAC | Cited per row of `data/external/groups.csv`, not the decisions themselves | Free |
| 9 | METAR weather (REDEMET/DECEA) | DECEA | Not integrated; the authors' weather columns are excluded from the published panel | Free; not spent |
| 10 | OurAirports (airport geography) | OurAirports (community) | Yes -- filtered table, public domain / CC0 | Free |
| 11 | Federal holiday laws | Diário Oficial da União | Yes -- derived calendar tables | Free |
| 12 | The article's estimation panel (route x month, 2002-2013) | The article's authors; released by the first author | **Yes** -- `data/analysis/article_panel_route_month.parquet` and `.csv.gz`, CC BY 4.0 | Free |
| 13 | Infraero connections report | Infraero | Not public; feeds no published column | Not applicable |
| 14 | Published article (Elsevier) | Elsevier Ltd | DOI only | Not applicable |
| 15 | The author's 2013 undergraduate monograph (USP) | The author | One derived table and quoted passages; Zenodo deposit pending | Not applicable |

## 1. VRA -- Voo Regular Ativo

**Holder.** ANAC (Agência Nacional de Aviação Civil), published through
`https://siros.anac.gov.br/siros/registros/diversos/vra/{year}/` and
catalogued at `dados.gov.br`.

**How to obtain.** `uv run airline-delays fetch` (`just fetch`) downloads the
168 monthly CSVs for 2000-2013 into `data/raw/` and checks each file against
the sha256 committed in `data/raw/manifest.json`, which also records the
source URL and the retrieval timestamp of every file. No authentication. All
168 files were retrieved on 2026-09-05; the download took about 17 minutes
for 2,166,489,628 bytes (2.17 GB), and `just stage` parses them into
13,652,322 flight legs over the 14 years.

**Composition.** The VRA is built from the HOTRAN -- the approved schedule
document, normed by IAC 1223 and Portaria DGAC nº 33/2000 -- plus the
Boletins de Alteração de Voo the airlines file under IAC 1504 (source 2).
ANAC's own delay and cancellation percentages are computed from it under
Resolução ANAC nº 218 in two cuts, 30 minutes or more and 60 minutes or
more, with cancellations over scheduled legs and delays over realised legs;
the reconstruction panel's `fsc_prdelarr30m` is that 30-minute cut, and the
article's 15-minute cut is the United States convention. The author's 2013
monograph (source 15) is the earliest description of this composition in the
project's material (`docs/notes/monografia-2013.md`).

**Restrictions.** ANAC's website footer states CC BY-ND 3.0 for "todo o
conteúdo deste sítio"; no ANAC page for the VRA dataset declares its own
licence. The federal open-data catalogue declares `Licença: Creative Commons
Attribution` for this exact dataset (catalogued 2019-03-01, metadata updated
2024-01-25, responsible unit GOPE; read 2026-09-05). This repository follows
the catalogue's more specific and more recent declaration: CC BY, attributed
as "ANAC, Voo Regular Ativo (VRA), via dados.gov.br" (`DECISIONS.md`
ADR-0000). A written confirmation has been drafted for ANAC's e-SIC channel
(`docs/notes/esic-licenca-vra.md`); nothing here blocks on that reply.

**Redistributed here.** The derived tables under `data/analysis/` -- the
fact table, the reconstruction panel and its two city projections, with their
manifests -- and the description of the staged layer in `datapackage.json`.
The raw files themselves are not in git and not in the Zenodo record: a
reader refetches them from ANAC with the command above, and the committed
hashes prove the files are the same.

## 2. IAC 1504 -- delay-cause code taxonomy

**Holder.** ANAC. The instrument (Instrução de Aviação Civil 1504, 30 Apr
2000) is public regulatory text, PDF at
`https://pergamum.anac.gov.br/pergamum/vinculos/IAC1504.pdf`; download it
directly, no authentication, free.

**Restrictions.** ANAC states the IAC 1504 was revoked around April 2020 and
that the "Justificativa" field stopped being required from then on; the
revoking instrument and its replacement code table were not located
(`docs/notes/references.md`). This does not affect the 2000-2013 window; it
limits any extension past 2020.

**Redistributed here.** The derived taxonomy tables
(`data/external/cause_codes.csv`, 49 rows; `data/external/di_codes.csv`, 12
rows; `data/external/line_types.csv`, 8 rows), transcribed from the
instrument's Annex 2 and body text -- not the instrument's own PDF.

## 3. ANAC statistical data -- paid passengers by airline-route-month

**Holder.** ANAC ("Dados Estatísticos do Transporte Aéreo"), a public
download from the ANAC statistics portal; free; not collected in this
repository, no restriction known.

**What depends on it.** The article's passenger-weighted concentration
terms -- `rthhi`, `maxcthhi` and the alternative city term `gmchhi` -- and
the seven Hausman-type instruments the authors built from neighbouring
city-pairs (`h1_maxcthhi`, `h2_maxcthhi`, `h3_maxcthhi`, `lnh1_maxcthhi`,
`l1h1_maxcthhi`, `l1h2_maxcthhi`, `h2_rthhi`). The article's estimation
panel (source 12) carries the authors' values of all of them. The
reconstruction panel carries the flight-share counterparts `rthhi_flights`
and `maxcthhi_flights` under their own names, and the passenger-weighted
columns as null until this source is collected
(`src/airline_delays/definitions/concentration.py`, `DECISIONS.md` ADR-0007).

**Redistributed here.** Nothing from the source itself; the derived terms
ship inside the article's estimation panel.

## 4. ANAC tariff microdata

**Holder.** ANAC ("Microdados de Tarifas Aéreas Domésticas"), covering 2002
onward, a public download from the ANAC statistics portal; free; not
collected in this repository, no restriction known. It records tickets sold,
not operations, and is therefore a different source from the VRA.

**What depends on it.** The article's low-cost presence variables: `lcc`
(Gol or Azul sold tickets on the route in the month) with its components
`pres_glo`, `pres_azu`, `pres_tam` and `pres_web`, and `maxalccfu` with its
components `olccfu` and `dlccfu`. The article's estimation panel carries the
authors' values of all of them; the prices, yields, revenues and ticket
counts of the authors' base do not ship. The reconstruction panel's own
`lcc` and `pres_*` columns are read from VRA operation instead -- a different
measure under the same name, documented in `docs/notes/features.md`.

**Redistributed here.** Nothing from the source itself; the derived dummies
ship inside the article's estimation panel.

## 5. BNDES/McKinsey (2010) airport-capacity study

**Holder.** BNDES (Banco Nacional de Desenvolvimento Econômico e Social).
*Estudo do Setor de Transporte Aéreo do Brasil*, 25 Jan 2010, public PDF at
`www.bndes.gov.br`, cited by page number; free, the cost being the manual
transcription of the declared hourly capacity per airport, which the study
does not tabulate in one place.

**Redistributed here.** One row (`data/external/capacity.csv`): Congonhas
(SBSP), the commercial-aviation movements per hour in force after the
2007-07-17 accident, at confidence grade B (`docs/notes/references.md`). The
study gives passengers per year for the large airports, a different unit,
deliberately not entered into the table's numeric columns.

## 6. ANAC seasonal declared-capacity bulletins

**Holder.** ANAC. Not located; needed to complete `data/external/capacity.csv`
beyond the single Congonhas row. Free in principle; not spent.

**What depends on it.** The article's congestion variables `dailyflcong`,
`dailyflncong` and `prcongested` classify each scheduled hour as congested
or not against the airport's declared capacity. The article's estimation
panel carries the authors' values under their declared-capacity
classification. The reconstruction panel carries the internal p90 proxy of
`src/airline_delays/definitions/congestion.py` instead and no `prcongested`
(`DECISIONS.md` ADR-0007).

**Redistributed here.** Nothing from the source; the authors' congestion
counts ship inside the article's estimation panel.

## 7. ANAC slot-coordination acts

**Holder.** ANAC. Read directly from ANAC's annual "Relatório de Atividades"
PDFs (2009, 2010, 2012, 2013), public downloads from `gov.br/anac`, via
`pdftotext -layout`; free, the cost being four years of activity reports to
read.

**Redistributed here.** Two rows (`data/external/slots.csv`, confidence grade
A): Guarulhos (coordination process from 2009, full IATA-conference slot
allocation by 2010) and Santos Dumont (route restriction lifted,
hour-distribution procedures published March 2009). Congonhas, Recife and
Brasília are recorded as not found, not guessed at (`docs/notes/references.md`).

## 8. CADE/ANAC merger and grouping decisions

**Holder.** CADE (Conselho Administrativo de Defesa Econômica) and ANAC:
public regulatory decisions and press coverage of record; free.

**Redistributed here.** Cited per row of `data/external/groups.csv` (50
rows) and `data/external/events.csv` (29 rows), with a source, a URL and a
confidence grade each -- not the decisions themselves. Most merger-date rows
are grade B; `docs/notes/references.md` lists which dates are grade A.

## 9. METAR weather (REDEMET/DECEA)

**Holder.** DECEA (Departamento de Controle do Espaço Aéreo), published today
through REDEMET's public API and portal; free; not integrated into this
repository, and REDEMET's own terms not verified.

**What depends on it.** For the 2016 article the weather data came by
nominal cession from DECEA/ICEA, as monthly means per airport, and the
article's weather-delay signal did not end up using it: `prwheather` is
built from the VRA's own justification codes and is in the published panel.
The weather columns of the authors' base are excluded from the article's
estimation panel, because they came from a cession and not from an open
channel. The same records are independently obtainable from REDEMET today,
at the station x hour grain the flight-level layer would want
(`docs/study/apendice-d-extensoes.md`).

**Redistributed here.** No.

## 10. OurAirports (airport geography)

**Holder.** OurAirports, a community-maintained mirror, not an official
Brazilian government source:
`https://davidmegginson.github.io/ourairports-data/airports.csv`, a direct
CSV download, no authentication, published as public domain / CC0-equivalent.

**Redistributed here.** Yes: `data/external/airports_br.csv` (8,035 rows,
every OurAirports record with `iso_country == BR`), `data/external/nodes.csv`
(31 rows, the airport-to-node crosswalk of the 27 nodes of ADR-0001) and
`data/external/distances_km.csv` (702 rows, great-circle distances computed
from it).

## 11. Federal holiday laws

**Holder.** The Brazilian federal government (Diário Oficial da União), read
directly at `planalto.gov.br`: Lei 662/1949, Lei 10.607/2002, Lei
9.093/1995. Public law, no restriction, free.

**Redistributed here.** Yes: `data/external/holidays.csv` (92 rows) and
`data/external/observances.csv` (56 rows: Carnival, Good Friday and Corpus
Christi, computed from Easter Sunday, not looked up).

## 12. The article's estimation panel

**Holder.** The final estimation base (a Stata file with header timestamp
2015-12-03, 24,589 route-months and 1,829 variables) is held by the first
author of the article, who is the author of this repository, curated it and
releases the panel on their own responsibility (`DECISIONS.md` ADR-0020). The
article's three authors -- W. E. Bendinelli, H. F. A. J. Bettini and
A. V. M. Oliveira -- are credited in every citation of the panel as the authors
of the underlying research.

**How to obtain.** This repository:
`data/analysis/article_panel_route_month.parquet` (canonical) and
`data/analysis/article_panel_route_month.csv.gz` (the same values, for
readers without a parquet reader). After the deposit, the Zenodo record of
the repository. Free; `just estimate` re-estimates Tables 2-7 on it in under a
minute.

**Restrictions.** CC BY 4.0. Cite the panel with its three authors (below);
the upstream ANAC data it was built from (sources 1, 3 and 4) are attributed
to ANAC, not relicensed.

**What it contains.** 24,589 route-months x 52 columns: 209 directional
city-pair routes over the 144 months of 2002-2013. Keys and geography, the
flight counts every share is built on, the six regressands of Tables 3-7,
the nine exogenous regressors, the two concentration terms with the
alternative city term, the seven instruments and the components of the two
low-cost dummies. Every column is declared in the registry (layer
`article_panel`, `src/airline_delays/schema/columns.py`), rendered in
`docs/dictionary.md` and described in `datapackage.json`. Values are never
rounded, imputed or clipped by the curation
(`src/airline_delays/estimation/article_panel.py`).

**What it excludes.** The generated route, time and region x month
seasonality dummies, rebuilt exactly by `src/airline_delays/estimation/loader.py`
when `airline-delays estimate` runs; every variable from a non-open source --
the weather cession (source 9), the airport-operator report (source 13), the
prices and revenues of the tariff microdata (source 4); and the base's own
bookkeeping.

**Provenance.** `data/analysis/article_panel_manifest.json` records the
sha256 and the header timestamp of the source base, its number of rows and
variables, the sha256 and size of both published files and the per-column
null counts -- never a path. `airline-delays estimate` records the panel's
path, row count and sha256 in `reports/replication/results.json`.

**Citation.** Bendinelli, W. E.; Bettini, H. F. A. J.; Oliveira, A. V. M.
(2016 data; 2026 release). *Estimation panel of "Airline delays, congestion
internalization and non-price spillover effects of low cost carrier entry"*,
route x month, 2002-2013. Curated and published by W. E. Bendinelli. CC BY
4.0. DOI to follow the Zenodo deposit (`ROADMAP.md`).

## 13. Infraero connections report

**Holder.** Infraero (Empresa Brasileira de Infraestrutura Aeroportuária),
cited in the article's Table 1 as an unpublished monthly airport movement
report. It is not public, no channel to obtain it is known, and nothing
published here needs it: the article's connecting-passenger columns are not
among the 52 columns of the estimation panel, and the reconstruction panel's
hub measure (`src/airline_delays/definitions/hubs.py`) is a structural
measure built from VRA movement shares, published under its own name. The
author's 2013 monograph (source 15) records why the underlying RPE series is
not uniform across the window (`docs/notes/monografia-2013.md`).

## 14. Published article (Elsevier)

**Holder.** Elsevier Ltd. Bendinelli, Bettini & Oliveira (2016),
*Transportation Research Part A* 85, 39-52,
[`10.1016/j.tra.2016.01.001`](https://doi.org/10.1016/j.tra.2016.01.001),
obtained through the DOI under Elsevier's access terms. The typeset PDF is
not redistributable, and no accepted manuscript exists in the material this
repository was built from.

**Redistributed here.** No. `CITATION.cff`'s `preferred-citation` and the
README's BibTeX block point to the DOI; the published coefficients the
replication compares against are parsed from the article's text into
`src/airline_delays/estimation/published.json` and marked as the article's.

## 15. The author's 2013 undergraduate monograph

**Holder.** The author. *Efeitos da entrada de uma empresa aérea de baixo
custo na internalização das externalidades do congestionamento*, undergraduate
monograph in Economics, USP, 2013: the document in which the
congestion-internalisation theory behind the 2016 article was first worked
out (`DECISIONS.md` ADR-0019, `docs/study/`).

**How to obtain.** A Zenodo deposit is pending; its DOI is carried as the
placeholder `[DOI-MONOGRAFIA]` until it exists. Until then the monograph is
cited, not redistributed. The author holds the rights and intends to deposit
the document openly; the regression base behind its Tables 5 and 6 is not
redistributed and is read by nothing here.

**Redistributed here.** One derived table,
`data/external/monograph_airports.csv` (38 rows, confidence grade A: the
verbatim transcription of the monograph's Lista de Siglas, with a flag for
the airports that also appear in its Tables 3 and 4), and short quoted
passages in `docs/notes/monografia-2013.md` and `docs/study/`. Its own
estimates are quoted there as an outside document, never as a result of
this repository.

## What is not in git, and why

`data/raw/`, `data/staged/` and `data/derived/` hold only their own
`README.md` (`data/raw/` also tracks `manifest.json`): the raw CSVs, the
staged flight table and the flight-level modelling table are regenerated
locally by `just fetch`, `just stage`, `just fact` and `just predict-dataset`,
never pulled from git (`DECISIONS.md` ADR-0004). Everything a reader needs
to run the estimation and read the tables is in git (ADR-0014): the article's
estimation panel, the reconstruction panel, the fact table, the two city
projections, the reference tables under `data/external/` and the four
manifests under `data/analysis/`. The Zenodo record archives the repository
as tagged; the heavy layers are described in `datapackage.json` under
`x-regenerated`, with the command that rebuilds each.

## Licence, by layer

MIT for code (`src/`, `scripts/`, `tests/`, `sql/`, `.github/`; `LICENSE`).
CC BY 4.0 for this repository's own text and for the curated data it
publishes -- the article's estimation panel (credited to its three authors,
curated and published by W. E. Bendinelli), the reconstruction panel, the
fact table, the projections and `data/external/*.csv`
(`LICENSE-CC-BY-4.0.md`). VRA-derived tables are attributed as "ANAC, Voo
Regular Ativo (VRA), via dados.gov.br", not relicensed; the OurAirports rows
keep their public-domain status. The README's "License" section states the
same boundary.
