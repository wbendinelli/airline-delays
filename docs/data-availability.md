# Data availability

Data Availability Statement for `airline-delays`, source by source: who
holds each source, how to obtain it, what restricts its use, and what it
costs in money and time. The README's "Data availability" section is the
short version of this file; `data/external/*.csv` is the machine-readable
version — every row there carries its own `source`, `url`, `retrieved_at`
and `confidence` fields, validated by `uv run vra refs`.

Two rules govern everything below (`CLAUDE.md`, `DECISIONS.md` ADR-0010):
a source that is not public is never redistributed here, under any name or
in any derived column, and a restriction is stated, never quietly designed
around. Where a number depends on a non-public source, the affected column
is documented as unavailable rather than filled with a substitute
(`docs/declared-differences.md`).

## Summary table

| # | Source | Holder | Redistributed here | Cost / time |
|---|---|---|---|---|
| 1 | VRA — Voo Regular Ativo (flight-leg CSVs, 2000-2013) | ANAC | Yes — raw snapshot and derived tables, CC BY with attribution | Free; ~17 minutes / 2.17 GB to download the 168 monthly files (`data/raw/manifest.json`) |
| 2 | IAC 1504 (delay-cause code taxonomy) | ANAC | Derived tables only, not the instrument's text | Free |
| 3 | ANAC statistical data (paid passengers by airline-route-month) | ANAC | Not yet collected | Free; not yet spent |
| 4 | ANAC tariff microdata (`yield`, `fare`, ticket counts) | ANAC | Not yet collected | Free; not yet spent |
| 5 | BNDES/McKinsey (2010) airport-capacity study | BNDES | One transcribed figure (Congonhas) | Free; manual-transcription time |
| 6 | ANAC seasonal declared-capacity bulletins | ANAC | Not yet collected | Free; not yet spent |
| 7 | ANAC slot-coordination acts (Relatórios de Atividades) | ANAC | Two transcribed rows (Guarulhos, Santos Dumont) | Free; PDF-extraction time |
| 8 | CADE/ANAC merger and grouping decisions | CADE / ANAC | Cited per row of `groups.csv`, not the decisions themselves | Free |
| 9 | METAR weather (REDEMET/DECEA) | DECEA | Not yet integrated | Free; ~4.2M observations, not yet fetched |
| 10 | OurAirports (airport geography) | OurAirports (community) | Yes — filtered table, public domain / CC0 | Free |
| 11 | Federal holiday laws | Diário Oficial da União | Yes — derived calendar table | Free |
| 12 | Private benchmark (`proj18.dta`, LABTAR/NECTAR, `vra.dta` 2019) | ITA/LABTAR laboratory | **Not redistributed** — only the derived agreement rate | Not applicable — declared omission |
| 13 | Infraero connections report | Infraero | **Not redistributed, not reproduced** | Not applicable — declared omission |
| 14 | Published article (Elsevier) | Elsevier Ltd | **Not redistributed** — DOI link only | Not applicable |

## 1. VRA — Voo Regular Ativo

**Holder.** ANAC (Agência Nacional de Aviação Civil), published through
`https://siros.anac.gov.br/siros/registros/diversos/vra/{year}/` and
catalogued at `dados.gov.br`.

**How to obtain.** `uv run vra fetch` downloads all 168 monthly CSVs
(2000-2013) directly from the SIROS listing; `data/raw/manifest.json`
records the source URL, retrieval timestamp and sha256 of every file. No
authentication, no request form.

**Restrictions.** The ANAC website's own footer states "Creative Commons
Atribuição-SemDerivações 3.0" (CC BY-ND) for "todo o conteúdo deste sítio",
which would forbid derivatives if read as covering the dataset itself; no
ANAC page for the VRA dataset declares its own licence. The federal
open-data catalogue, however, declares `Licença: Creative Commons
Attribution` for this exact dataset (catalogued 2019-03-01, metadata
updated 2024-01-25, responsible unit GOPE; read 2026-09-05) — see
`DECISIONS.md` ADR-0000 for the full evidence trail. This repository
follows the catalogue's more specific and more recent declaration: CC BY,
attributed as "ANAC, Voo Regular Ativo (VRA), via dados.gov.br". A written
confirmation has also been requested from ANAC via e-SIC in parallel
(`docs/notes/esic-licenca-vra.md`); redistribution here does not block on
that reply.

**Cost and time.** Free. The 168 files total 2,166,489,628 bytes (2.17 GB,
`data/raw/manifest.json`); a sequential, polite download took about 17
minutes end to end in this session. Parsing into the canonical flight
table (`uv run vra stage`) takes about 8.4 seconds total across the 14
years (`data/staged/manifest.json`, sum of the per-year `seconds` field).

**Redistributed here.** Yes: the raw monthly snapshot (via
`data/raw/manifest.json`'s hashes, not the CSVs themselves — see
"What is not in git" below) and every derived table under
`data/analysis/`.

## 2. IAC 1504 — delay-cause code taxonomy

**Holder.** ANAC. The instrument (`Instrução de Aviação Civil 1504`, 30
Apr 2000) is public regulatory text, PDF at
`https://pergamum.anac.gov.br/pergamum/vinculos/IAC1504.pdf`.

**How to obtain.** Download the PDF directly; no authentication.

**Restrictions.** ANAC states the IAC 1504 was revoked around April 2020
and that the "Justificativa" field stopped being required from then on;
the revoking instrument and its replacement code table were not located
this session (`docs/notes/references.md` §3, `docs/notes/esic-licenca-vra.md`
question 4). This does not affect the 2000-2013 window this repository
covers, but limits any future extension past 2020.

**Cost and time.** Free.

**Redistributed here.** The *derived* taxonomy tables
(`data/external/cause_codes.csv`, 49 rows; `data/external/di_codes.csv`, 12
rows; `data/external/line_types.csv`, 8 rows), transcribed from the
instrument's Annex 2 and body text — not the instrument's own PDF.

## 3. ANAC statistical data — paid passengers by airline-route-month

**Holder.** ANAC ("Dados Estatísticos do Transporte Aéreo").

**How to obtain.** Public download from the ANAC statistics portal; not
yet attempted in this repository.

**Restrictions.** None known; not yet verified.

**Cost and time.** Free to obtain; the time cost of collecting and joining
it has not yet been spent. This is what `rthhi`, `maxcthhi` and `gmchhi`
(the article's passenger-weighted HHIs) need —
`src/vra/hhi.passenger_weighted_hhi` already has the right signature and
returns `None` until this source is collected (`DECISIONS.md` ADR-0007;
`docs/declared-differences.md` §6).

**Redistributed here.** Not applicable yet — nothing has been collected.

## 4. ANAC tariff microdata

**Holder.** ANAC ("Microdados de Tarifas Aéreas Domésticas"), covering
2002 onward.

**How to obtain.** Public download from the ANAC statistics portal; not
yet attempted.

**Restrictions.** None known; not yet verified. This is a different source
from the VRA (which records operations, not tickets sold) — the original
article's `yield`, `fare`, `nyield`, `nfare` and the `pax_rev` column, and
the tariff-base–derived `lcc`/`pres_glo`/`pres_azu`/`pres_tam` presence
dummies, come from here
(`/Users/wbendinelli/Documents/pesquisa-acervo/01-atrasos-concentracao/_analises/avaliacao-vra-como-fonte.md`,
class D). This repository's own `lcc`/`pres_*` columns are computed from
VRA *operation* instead, and the two sources disagree on about 11% of
route-months (`docs/declared-differences.md` §5) — a declared difference,
not an error in either source.

**Cost and time.** Free to obtain; not yet collected.

**Redistributed here.** Not applicable yet.

## 5. BNDES/McKinsey (2010) airport-capacity study

**Holder.** BNDES (Banco Nacional de Desenvolvimento Econômico e Social).
*Estudo do Setor de Transporte Aéreo do Brasil*, 25 Jan 2010, public PDF at
`www.bndes.gov.br` (cited in the original dissertation's footnote 25).

**How to obtain.** Public PDF download; no authentication.

**Restrictions.** None known — a public study, cited by page number.

**Cost and time.** Free; the cost is manual transcription of the figures
that matter (declared hourly capacity per airport), which the study does
not tabulate in one place.

**Redistributed here.** One row (`data/external/capacity.csv`): Congonhas
(SBSP), 33 movements/hour for commercial aviation after the 2007-07-17 TAM
3054 accident, at confidence grade B (a convergent news-retrospective
summary, no regulatory act opened directly — see
`docs/notes/references.md` §6). No pre-2007 figure and no other airport of
the panel has a transcribed value yet; `prcongested` (ADR-0007) stays
unreproduced until this table has one row per panel airport with a
declared-capacity figure, not a passengers/year figure (the BNDES study
gives 2009 passengers/year, a different unit, for GRU/CGH/SDU/VCP/GIG —
deliberately not entered into `capacity.csv`'s numeric columns, since that
would be filling a gap with the wrong quantity).

## 6. ANAC seasonal declared-capacity bulletins

**Holder.** ANAC.

**How to obtain.** Not yet located; needed to complete `capacity.csv`
beyond the single Congonhas row above.

**Restrictions.** Unknown — not yet collected.

**Cost and time.** Free to obtain in principle; not yet spent.

**Redistributed here.** Not applicable yet.

## 7. ANAC slot-coordination acts

**Holder.** ANAC. Read directly from ANAC's own annual "Relatório de
Atividades" PDFs (2009, 2010, 2012, 2013), via `pdftotext -layout` —
primary documents, not a search summary.

**How to obtain.** Public PDF downloads from `gov.br/anac`.

**Restrictions.** None known.

**Cost and time.** Free; the cost is reading four years of activity
reports to find the relevant sections.

**Redistributed here.** Two rows (`data/external/slots.csv`, confidence
grade A): Guarulhos (coordination process from 2009, full IATA-conference
slot allocation by 2010) and Santos Dumont (route restriction lifted,
hour-distribution procedures published March 2009). Congonhas, Recife and
Brasília are declared absent, not guessed at — see
`docs/notes/references.md` §6 for exactly what was checked and not found.

## 8. CADE/ANAC merger and grouping decisions

**Holder.** CADE (Conselho Administrativo de Defesa Econômica) and ANAC.

**How to obtain.** Public regulatory decisions and press coverage of
record.

**Restrictions.** None known.

**Cost and time.** Free.

**Redistributed here.** Cited per row of `data/external/groups.csv` and
`data/external/events.csv` (source + URL + confidence grade each) — not the
decisions themselves. Most merger-date rows are confidence grade B (a
convergent secondary source, not the regulatory act itself opened
directly) — see `docs/notes/references.md` §2 for exactly which dates are
grade A.

## 9. METAR weather (REDEMET/DECEA)

**Holder.** DECEA (Departamento de Controle do Espaço Aéreo), published
today through REDEMET. For the original 2016 article, the equivalent data
was obtained by nominal cession from DECEA/ICEA, not an open download —
and the article's own weather-delay signal did not end up using it (its
`prwheather` comes from the VRA's own justification codes, not from METAR;
`especificacao.md` §3.7 in the archive review).

**How to obtain.** REDEMET's public API/portal; not yet integrated into
this repository. The archive review's companion project already extracted
about 4.2 million METAR observations for 2000-2013 from the historical
cession (outside this repository, not redistributable from that source —
but the same records are independently obtainable from REDEMET today).

**Restrictions.** REDEMET's own terms have not been verified this session.

**Cost and time.** Free to obtain from REDEMET today; not yet spent.

**Redistributed here.** Not applicable yet — this is one of the extensions
listed in `docs/tutorial/13-propor-melhorias.md`.

## 10. OurAirports (airport geography)

**Holder.** OurAirports, a community-maintained mirror (not an official
Brazilian government source).

**How to obtain.**
`https://davidmegginson.github.io/ourairports-data/airports.csv`, a direct
CSV download, no authentication.

**Restrictions.** Published as public domain / CC0-equivalent ("no rights
reserved").

**Cost and time.** Free.

**Redistributed here.** Yes — `data/external/airports_br.csv` (8,035 rows,
every OurAirports record with `iso_country == BR`), `data/external/nodes.csv`
(the 27-node crosswalk of ADR-0001) and `data/external/distances_km.csv`
(great-circle distances computed from it), all under CC BY 4.0 alongside
this repository's own derived text (see License below).

## 11. Federal holiday laws

**Holder.** The Brazilian federal government (Diário Oficial da União);
read directly at `planalto.gov.br`.

**How to obtain.** Public law text, no authentication (Lei 662/1949, Lei
10.607/2002, Lei 9.093/1995).

**Restrictions.** None — public law.

**Cost and time.** Free.

**Redistributed here.** Yes — `data/external/holidays.csv` (92 rows) and
`data/external/observances.csv` (56 rows, Carnival/Good Friday/Corpus
Christi, computed from Easter Sunday, not looked up).

## 12. Private benchmark — `proj18.dta`, LABTAR/NECTAR, `vra.dta` (2019 vintage)

**Holder.** The LABTAR/NECTAR laboratory (Instituto Tecnológico de
Aeronáutica), specifically Alessandro V. M. Oliveira, the original
article's co-author, orientador and the author of the underlying `.ado`
estimation code. Full inventory and consent map in the archive review's
`avaliacao-8-criterios.md` §C2, §C7 (external to this repository, in
`pesquisa-acervo/01-atrasos-concentracao/_analises/`).

**How to obtain.** Not public. It is the laboratory's own final-panel file
and two of its intermediate research bases, reached in this project only
through the archive review that preceded this repository, not through any
open channel.

**Restrictions — absolute.** Never committed to this repository, under
any name, in any directory, in any derived form beyond a single agreement
statistic (`CLAUDE.md` hard rule 1). Reached only through the environment
variable `AIRLINE_DELAYS_PRIVATE_DIR` (never a path hardcoded in code),
and only by `replication/gabarito/compare.py` or a `scripts/verify*.py`.
Tests that need it carry the pytest marker `gabarito` and are skipped —
never failed — when the variable is unset (`tests/conftest.py`); CI never
sets it, so these tests never run there. The only artefact this benchmark
ever produces on disk is `data/analysis/taxas.csv` — a table of agreement
rates, medians and percentiles, with a structural guard
(`replication.gabarito.compare.assert_no_values`) that refuses to write
anything else, tested in `tests/test_gabarito.py::test_only_agreement_statistics_may_be_written`.

**Cost and time.** Not applicable — this is a declared omission, not a
priced acquisition. A prospective reader cannot obtain this source through
any channel this repository documents.

**Redistributed here.** No. Only the derived, aggregate comparison:
`data/analysis/taxas.csv` and the generated block of
`docs/declared-differences.md`.

## 13. Infraero connections report

**Holder.** Infraero (Empresa Brasileira de Infraestrutura Aeroportuária).
Cited in the original article's Table 1 as "Infraero, unpublished monthly
airport movement report, 2002-2013".

**How to obtain.** Not public; no channel is known.

**Restrictions.** Not redistributable and not reproducible from any source
this repository has access to. It fed the original article's `o_percon`,
`d_percon` and `dhub` (passengers in connection); this repository's own
hub measure (`src/vra/hub.py`) is a structural substitute built from VRA
movement shares, published under its own name — never presented as a
reconstruction of Infraero's figure (`DECISIONS.md`; `docs/declared-differences.md`).

**Cost and time.** Not applicable — declared omission.

**Redistributed here.** No, and no derived column is named as if it were.

## 14. Published article (Elsevier)

**Holder.** Elsevier Ltd, `© 2016`. Bendinelli, Bettini & Oliveira (2016),
*Transportation Research Part A* 85, 39-52,
[`10.1016/j.tra.2016.01.001`](https://doi.org/10.1016/j.tra.2016.01.001).

**How to obtain.** Through the DOI, subject to Elsevier's own access
terms; a reader without institutional access should look for the accepted
manuscript through the author's institutional repository (see below).

**Restrictions.** The typeset PDF is never redistributable under any
circumstance. Elsevier's own sharing policy would allow the *accepted
manuscript* (the peer-reviewed but not typeset version) to be deposited
under embargo with a CC BY-NC-ND licence — but no version of that
manuscript exists in the archive this repository was built from
(`avaliacao-8-criterios.md` §C1, §C8: the archive holds the Portuguese
dissertation and the do-files, never an English-language draft of the
article itself, published or accepted).

**Cost and time.** Not applicable.

**Redistributed here.** No. `CITATION.cff`'s `preferred-citation` and the
README's BibTeX block point to the DOI; no PDF, typeset or accepted, is
in this repository.

## What is not in git, and why

Per `CLAUDE.md` and `.gitignore`: `data/raw/`, `data/staged/` and
`data/derived/` hold only their own `README.md` (`data/raw/` also tracks
`manifest.json`, the fetch provenance) — the actual CSVs and parquet files
are regenerated locally by `just fetch`/`just stage`/`just features`, never
pulled from git. `data/private/` never holds anything beyond its
`README.md`; source 12 above is reached only through
`AIRLINE_DELAYS_PRIVATE_DIR`, which points *outside* this repository
entirely. `data/analysis/*.parquet` and `*.csv.gz` are the one exception
to "generated data stays out of git" (`DECISIONS.md` ADR-0014): they are
public, small (2-12 MB) and tracked so a reviewer can run
`just replicate` without rebuilding anything first.

## License, by layer

MIT for code; CC BY 4.0 for this repository's own text and derived-data
tables (this file included); the VRA itself redistributed under CC BY with
attribution to ANAC, not relicensed. See the README's "License" section
and `LICENSE-CC-BY-4.0.md` for the exact boundary.
