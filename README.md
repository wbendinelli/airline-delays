# airline-delays

[![CI](https://github.com/wbendinelli/airline-delays/actions/workflows/ci.yml/badge.svg)](https://github.com/wbendinelli/airline-delays/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE)
[![Data: CC BY 4.0](https://img.shields.io/badge/data-CC%20BY%204.0-lightgrey.svg)](./LICENSE-CC-BY-4.0.md)
[![Article DOI](https://img.shields.io/badge/article%20DOI-10.1016%2Fj.tra.2016.01.001-blue.svg)](https://doi.org/10.1016/j.tra.2016.01.001)

> **Tier:** `C` · **Class:** `Research`

[English](README.md) · [Português](README.pt-BR.md)

**Brazil's scheduled domestic flights 2000-2013 -- from ANAC's raw records to a
published article's tables, its theory, and a flight-level delay predictor.**

## Overview

Between 2000 and 2013 Brazil's domestic air market grew fast, concentrated at
a handful of airports, and saw two low-cost entrants redraw the competitive
map: Gol in 2001 and Azul in 2008 -- the two carriers the article's low-cost
dummies measure. Whether congestion at those airports is
something airlines internalise -- flying less when they own the delay they
cause -- or something competition cures has direct consequences for slot
allocation, airport pricing and merger review. Bendinelli, Bettini & Oliveira
(2016, *Transportation Research Part A* 85, 39-52, doi
10.1016/j.tra.2016.01.001) addressed it with a route x month panel built from
ANAC's flight-leg, traffic and tariff records and an instrumented design:
concentration at the endpoint cities goes with lower full-service delays,
concentration on the route with higher ones, and a low-cost carrier's presence
at a city spills over onto the incumbents' punctuality. This repository opens
the data, code and theory behind that article, published by its first author.

### Why airport congestion matters

Scheduled domestic flights in the replication universe -- line types N, R and
E, DI 0, every airport -- grew from 659,301 in 2000 to 984,956 in 2013, a rise
of 49.4 per cent. The 2006-2007 crisis --
two fatal accidents and the *apagão aéreo* that followed -- made airport
congestion a matter of national policy (`data/external/events.csv`). Two
hypotheses compete: a dominant carrier internalises the congestion it imposes
on its own flights, or rivalry disciplines delays better than dominance does.

### What the article found

| Estimator | `rthhi` (route HHI) | `maxcthhi` (endpoint-city HHI, larger of the two) | `lcc` (route) | `maxalccfu` (endpoint cities) | N |
|---|---|---|---|---|---|
| 2SGMM (article, Table 3, col. 2) | +0.819** (0.410) | -1.514*** (0.527) | -0.041 (0.072) | -0.423** (0.179) | 19,419 |
| OLS (article, Table 6, col. 2) | -0.313*** (0.068) | +0.106 (0.196) | -0.164*** (0.033) | -0.179 (0.137) | 19,590 |

Standard errors in parentheses; the stars are the article's significance
levels. The regressand is `ODDS`, the log-odds of the share of the
full-service carriers' (TAM, the Varig group, Transbrasil, Vasp) arrivals more
than fifteen minutes late in the route-month. After instrumenting, a higher
HHI at the more concentrated endpoint city goes with lower full-service delay
odds and minutes -- which the article reads as the dominant carrier
internalising its own congestion -- while a higher route HHI goes with higher
ones. A low-cost carrier at either endpoint city lowers the full-service
carriers' delay odds, the "non-price spillover" of the title; its presence on
the route itself is not significant for the odds and enters positively at the
ten per cent level in the minutes columns (article, Table 3, cols. 4 and 6).
The OLS-to-2SGMM sign change is a statement about the `ODDS` columns.

### What this repository gives you

- **The open reconstruction panel** -- `data/analysis/panel_route_month.parquet`:
  31,313 route-months x 228 columns, 310 routes, 168 months, 27 nodes, built
  from 13,652,322 flight legs in 168 monthly files.
- **The article's estimation panel** -- the panel the authors estimated
  Tables 2-7 on, published here as `data/analysis/article_panel_route_month.parquet`
  (24,589 route-months x 52 columns); Tables 2-7 re-estimated in `reports/replication/`.
- **The theory** -- the congestion game the article draws on, Brueckner and
  Van Dender (2008) as set out in the author's 2013 monograph, derived
  symbolically: 29 identities checked and 11 figures in `reports/theory/`.
- **The delay predictor** -- 10,200,560 scheduled flights, 46 day-ahead
  features, evaluated out of time in `reports/prediction/`.

The two panels share the universe, the node map and the carrier sets recorded
in `DECISIONS.md`; the reconstruction follows the article's convention where
the article states one and declares its own where it does not.

## Quickstart

Python 3.12 through `uv`. The smallest reproduction runs offline on the
committed fixture of 19,910 flight legs in about a second; the re-estimation
of Tables 2-7 on the committed article panel takes under a minute.

```bash
git clone https://github.com/wbendinelli/airline-delays.git
cd airline-delays && uv sync
just demo       # fixture -> fact table -> reconstruction panel -> Table 2, offline
just estimate   # Tables 2-7 re-estimated on the article's estimation panel
```

## Reproducing

One machine (16 GB RAM, 10 cores) rebuilds everything from ANAC's files, one
year at a time. Each recipe wraps one command of `uv run airline-delays --help`;
`just pipeline` runs the stages from `data/staged/` onward, and
`just pipeline-full` adds the download, the parse and the prediction.

| Stage | Recipe | Reads -> writes | Wall time |
|---|---|---|---|
| Ingest | `just fetch` | ANAC's monthly CSVs -> `data/raw/` (168 files, 2.17 GB) and `data/raw/manifest.json` | 17.0 min |
| Staging | `just stage` | `data/raw/` -> `data/staged/year=YYYY/part-0.parquet`, 13,652,322 legs | one year at a time |
| Reference | `just reference` | validates every row of `data/external/*.csv` | seconds |
| Fact | `just fact` | staged legs -> `data/analysis/fact_group_route_month.parquet` and the two city projections | 11 s |
| Panel | `just panel` | fact table -> `data/analysis/panel_route_month.parquet`, `docs/dictionary.md`, `datapackage.json` | 8 s |
| Article panel | `just article-panel` | the authors' base -> `data/analysis/article_panel_route_month.parquet`, once, on the owner's machine | -- |
| Estimation | `just estimate` | article panel -> `reports/replication/` | under a minute |
| Prediction | `just predict-dataset`, `just predict` | staged legs -> `data/derived/ml/` -> `reports/prediction/` | 25 s, then 2,344 s |
| Theory | `just theory` | `src/airline_delays/theory/` -> `reports/theory/` | about a second |
| Reporting | `just summary`, `just report` | the artefacts -> `reports/summary.json`; the Typst sources -> `reports/pdf/` | seconds |

## Results at a glance

### Replication

Tables 2-7 re-estimated on the article's estimation panel track the published
tables closely without matching them cell for cell; each gap is measured in
published standard errors:

| Table | Coefficients | Same sign | Within half a s.e. | Median gap (s.e.) | Largest gap (s.e.) |
|---|---|---|---|---|---|
| Table 3, 2SGMM | 60 | 60 | 53 | 0.24 | 0.69 |
| Table 4, robustness | 66 | 65 | 51 | 0.22 | 0.91 |
| Table 5, LIML | 60 | 59 | 53 | 0.23 | 0.67 |
| Table 6, OLS | 60 | 59 | 51 | 0.12 | 0.94 |
| Table 7, departures | 60 | 59 | 51 | 0.24 | 0.66 |

Across the five tables, 306 coefficients are compared: 302 carry the published
sign, 259 (84.6 per cent) sit within half a published standard error, and the
largest gap is 0.94 standard errors. The sign reversal on which the article's
instrumented design rests -- OLS and 2SGMM give opposite signs to both HHI
terms in the `ODDS` columns -- is a pattern over 12 comparisons: the published
tables invert 4 of them, all 4 inversions reproduce, and the pattern agrees in
12 of 12. The re-estimated samples hold
20,447-20,630 observations against 19,408-19,590 published, 5.3 per cent more.
Table 2's 13 descriptive variables and 91 correlations are recovered; the largest absolute difference in a correlation is 0.012.

### Prediction

| Horizon | Information | AUC over the eight rolling folds, 2006-2013 |
|---|---|---|
| Day-ahead (D-1) | schedule, calendar, lagged route and airport aggregates | 0.715-0.741 |
| At the gate (H-1) | D-1 plus the inbound leg's actual delay | 0.757-0.824 |

The target is `late15_arr`, an arrival more than fifteen minutes late, over
10,200,560 scheduled flights of 2000-2013, with 46 day-ahead features and 9
leakage checks. The previous month's route prevalence scores 0.608-0.673 on
the same folds. On the 20-35% of flights with a linked inbound leg, the
at-gate model reaches 0.87-0.93.

### Theory

All 29 identities of the congestion game hold under `sympy`, and 11 figures
draw them. Two results the derivation sharpens: at an interior equilibrium with
the same fare, tax and seats for both carriers, the Stackelberg leader flies at
least twice the follower's flights under convex congestion cost and exactly
twice under linear cost; and the leader's optimal toll at the symmetric
first-best allocation is three quarters (0.75) of the marginal congestion
damage under linear cost (at the Stackelberg equilibrium itself it is two
thirds in that case).

## Data availability

### Data guide

**In git.** Both panels, the fact table, the two city projections, the 13
curated external tables and the four manifests: 636 columns across 7 layers,
defined in English and Portuguese in `docs/dictionary.md` and described as a
Frictionless Data Package in `datapackage.json`; `data/README.md` is the guide.
**Regenerated.** `data/raw/`, `data/staged/` and `data/derived/` are rebuilt
from ANAC's files by `just fetch && just stage` and `just predict-dataset`;
only their `README.md` and `data/raw/manifest.json` are tracked. **Zenodo.**
The GitHub release archives the repository with its curated tables on Zenodo,
which mints the DOI; until it exists, the badge above is the article's.

| Which panel? | Use |
|---|---|
| Re-estimate Tables 2-7, or start from the authors' final base (the published estimation samples are a subset of it that the recorded filters do not reproduce exactly; see Replication) | the article's estimation panel, `data/analysis/article_panel_route_month.parquet`: 2002-2013, 24,589 route-months x 52 columns |
| Study delays, concentration or low-cost presence over the full series, or build features for prediction | the reconstruction panel, `data/analysis/panel_route_month.parquet`: 2000-2013, 31,313 route-months x 228 columns |

### Sources

| Source | Holder | In this repository |
|---|---|---|
| Voo Regular Ativo (VRA), monthly flight-leg files 2000-2013 | ANAC, via dados.gov.br | Regenerated by `just fetch`; a sha256 per file in `data/raw/manifest.json`; every derived table |
| IAC 1504 (justification codes, DI codes, line types) | ANAC | Transcribed into `data/external/cause_codes.csv`, `di_codes.csv` and `line_types.csv` |
| The article's estimation panel | The authors' base of December 2015 | Curated once into `data/analysis/article_panel_route_month.parquet` |
| Tariff microdata and statistical data | ANAC | Upstream of the article panel's concentration and low-cost variables; not redistributed as microdata |
| Airport geography | OurAirports | `data/external/airports_br.csv`, `nodes.csv` and `distances_km.csv` |
| Federal holiday laws | Diário Oficial da União | `data/external/holidays.csv` and the computed `observances.csv` |
| Airport capacity, slot coordination, mergers | BNDES, ANAC, CADE | Transcribed rows in `data/external/capacity.csv`, `slots.csv`, `groups.csv` and `events.csv` |
| METAR weather | DECEA, via REDEMET | Not integrated; the article's weather signal is the VRA's own justification codes |
| The article | Elsevier | Cited by DOI; its published cells parsed into `src/airline_delays/estimation/published.json` |
| The author's 2013 undergraduate monograph (USP) | The author | Cited as an outside document; its airport list in `data/external/monograph_airports.csv` |

The full statement, holder by holder, is `docs/data-availability.md`. Licences
follow the layer: MIT for code, CC BY 4.0 for text and curated data, and the
raw records are "ANAC, Voo Regular Ativo (VRA), via dados.gov.br". In the
terms of the TIER Protocol, `data/raw/` is the original data, `data/staged/`
the importable data, `data/analysis/` the analysis data, `src/` the command
files, and `docs/dictionary.md` the data appendix.

## Learn more

The study -- the final work that joins the economics of airport congestion,
the game-theory model derived step by step, and the article's hypotheses, data,
specification, results and replication -- is `docs/study/`, written in
Portuguese with an English summary on its index page, and compiles to
`reports/pdf/study.pdf`. The research notes behind the decisions are in
`docs/notes/`, and the three Typst reports (study, replication, prediction)
with their PDFs in `reports/`. Sibling repositories:
[citation-audit](https://github.com/wbendinelli/citation-audit) and
[sapians-research](https://github.com/wbendinelli/sapians-research).

## Citation

```bibtex
@article{bendinelli2016airline,
  title   = {Airline delays, congestion internalization and non-price spillover effects of low cost carrier entry},
  author  = {Bendinelli, William E. and Bettini, Humberto F. A. J. and Oliveira, Alessandro V. M.},
  journal = {Transportation Research Part A: Policy and Practice},
  volume  = {85},
  pages   = {39--52},
  year    = {2016},
  doi     = {10.1016/j.tra.2016.01.001}
}

@software{bendinelli2026airlinedelays,
  title   = {airline-delays: Brazil's scheduled domestic flights 2000-2013, from ANAC's raw
             records to a published article's tables, its theory, and a flight-level delay predictor},
  author  = {Bendinelli, William Eduardo},
  year    = {2026},
  url     = {https://github.com/wbendinelli/airline-delays},
  version = {1.1.0}
}
```

`CITATION.cff` carries both entries. The estimation panel as a dataset:
Bendinelli, W. E.; Bettini, H. F. A. J.; Oliveira, A. V. M. (2016 data; 2026
release). *Estimation panel of "Airline delays, congestion internalization and
non-price spillover effects of low cost carrier entry"*, route x month,
2002-2013. Curated and published by W. E. Bendinelli. CC BY 4.0. DOI to follow
the Zenodo deposit.

## License

MIT for code (`src/`, `scripts/`, `tests/`, `.github/`) in `LICENSE`. CC BY 4.0
for text and curated data -- this page, `docs/`, the prose of `reports/`, both
panels, the fact table, the city projections and `data/external/` -- in
`LICENSE-CC-BY-4.0.md`. The raw VRA records are ANAC's, redistributed with
attribution as "ANAC, Voo Regular Ativo (VRA), via dados.gov.br".

## Use and limits

A research dataset for 2000-2013: it supports replication, extension and
methodological work on that window, not live prediction, and the IAC 1504
justification codes it rests on were retired around 2020. Built from the VRA
alone, the reconstruction panel does not carry the article's passenger-weighted
concentration terms (`rthhi`, `maxcthhi`), the codeshare dummy (`cshare`), the
declared-capacity congestion counts (`dailyflcong`, `dailyflncong`), the
endpoint-city delay maximum (`maxprdel`) or the seven instruments
(`h1_maxcthhi`, `h2_maxcthhi`, `h2_rthhi`, `h3_maxcthhi`, `l1h1_maxcthhi`,
`l1h2_maxcthhi`, `lnh1_maxcthhi`); those live in the article's estimation
panel. Every number on this page is printed by `airline-delays summary` into
`reports/summary.json`.
