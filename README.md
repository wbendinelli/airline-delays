# airline-delays

[![CI](https://github.com/wbendinelli/airline-delays/actions/workflows/ci.yml/badge.svg)](https://github.com/wbendinelli/airline-delays/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE)
[![DOI](https://img.shields.io/badge/DOI-pending%20Zenodo%20deposit-lightgrey.svg)](./ROADMAP.md)

> **Tier:** `C` · **Class:** `Research`

## Overview

`airline-delays` reconstructs Brazil's Voo Regular Ativo (VRA) flight-leg
records (ANAC, 2000-2013, about 13.5 million legs) into a single canonical
flight table, replicates the tables of Bendinelli, Bettini & Oliveira (2016,
*Transportation Research Part A*,
[`10.1016/j.tra.2016.01.001`](https://doi.org/10.1016/j.tra.2016.01.001)) from
public data only, and trains a flight-level delay predictor evaluated by a
rolling-origin split. It also documents the theory the article rests on — a
review of the economics of airport congestion and a Stackelberg model of
congestion internalisation, ported from the author's 2013 undergraduate
monograph and re-derived symbolically, ending at the article's reception
(`docs/theory/README.md`, `reports/theory/model.json`, `DECISIONS.md`
ADR-0019).

**This repository supports:** reconstructing the flight table year by year
under a documented universe, node map and delay definition
(`DECISIONS.md`); reproducing the article's headline tables from public
sources, with every divergence against the original benchmark declared, not
adjusted away; predicting per-flight delay probability at two horizons
(day-ahead and at-gate).

**This repository does not support:** exact replication of any table cell
that depended on private laboratory data (`proj18.dta`, LABTAR/NECTAR) or on
the Infraero connections report — those layers are declared unavailable in
[Data availability](#data-availability), never silently dropped or
approximated without saying so.

Measured on the full 2000-2013 series (`data/staged/manifest.json`,
`data/analysis/manifest.json`, `data/analysis/panel_manifest.json`): staging
produces 13,652,322 flight legs from 168 monthly files (265 MB of
zstd-compressed parquet from 2.17 GB of raw CSV); the canonical fact table
(`group x route x month`, the replication universe) holds 165,763 cells
across 87 columns; the public replication panel (`route x month`, the 27
nodes of `DECISIONS.md` ADR-0001) holds 31,313 rows across 228 columns, 310
routes and exactly the 168 months 2000m1-2013m12, unique on `(route, ym)`
(`DECISIONS.md` ADR-0016); the city-month and airline-city-month projections
hold 21,231 and 49,801 rows respectively.

## Quickstart

```bash
git clone https://github.com/wbendinelli/airline-delays.git
cd airline-delays
uv sync
just demo
```

`just demo` runs the smallest end-to-end reproduction over the committed
fixture in `tests/fixtures/` (three routes cut from the 2004, 2009 and 2012
files, about 20,000 staged legs): the same code path as the full pipeline,
from staged legs to the group x route x month fact table, to the route-month
panel, to Table 2 — no network access, no ANAC download, no private
directory, about one second on a laptop (`scripts/demo.py`, which writes
only under the git-ignored `data/derived/demo/` and prints what each layer
produced; `tests/test_demo.py` runs the same thing in CI). Table 2 on that
panel computes 7 of its 13 variables and prints the other 6 as absent or
entirely null, which is the honest shape of a VRA-only reconstruction (see
[Declared differences](#declared-differences)). The full public panel needs
no fetch and no stage either: `data/analysis/panel_route_month.parquet` is
committed (`DECISIONS.md` ADR-0014), so `just replicate` alone reproduces
Table 2 over all 31,313 route-months in well under a second.

## Reproducing

Full reconstruction runs on one machine (16 GB RAM, 10 cores), processing
the raw data year by year, never two full raw scans at once:

```bash
just fetch      # ANAC monthly CSVs -> data/raw/, with manifest.json
just stage      # data/raw/ -> data/staged/year=YYYY/*.parquet (zstd)
just refs       # validates data/external/*.csv (source + URL per row)
just features   # staged + refs -> the group x route x month fact table
just panel      # fact table -> the replication panel, dictionary, datapackage
just replicate           # Tables 2-7 from the public panel
just replicate private   # Tables 2-7 from the private benchmark (needs AIRLINE_DELAYS_PRIVATE_DIR)
just ml         # flight-level dataset, temporal split, rolling evaluation
just theory     # the monograph's congestion model derived and checked, five figures (offline, ~1 s)
```

Every recipe is a thin wrapper over `uv run` on Python 3.12 (pinned in
`.python-version` and `pyproject.toml`) — never the system `python3`, which
lacks pandas; see `justfile` for the exact command each one runs, and
`uv run vra --help` for the underlying CLI.

Measured wall time, one machine (16 GB RAM, 10 cores), full 2000-2013
series: `fetch` about 17 minutes for 2.17 GB over 168 files
(`data/raw/manifest.json`); `stage` about 8.4 seconds total across the 14
years (`data/staged/manifest.json`); `features` about 11.4 seconds
(`data/analysis/manifest.json`); `panel` about 7.5 seconds
(`data/analysis/panel_manifest.json`); `replicate` (public panel) about 0.3
seconds (`reports/replication/public/tables.md`); `replicate private`
about 38.1 seconds (`reports/replication/private/tables.md`); `ml`
**2,344.2 seconds** end to end -- 24.7 seconds to build the
10,200,560-row flight table and the rest to fit 24 models over the eight
rolling-origin folds and the fixed split, plus permutation importance,
calibration and I/O, which is why the total exceeds the 2,141.7 seconds the
fold timings add up to (`runtime` in `reports/prediction/dataset.json`, written
by `ml/run.py`). The prediction phase roughly doubled in
cost when ADR-0017 gave 8.7 million flights an arrival target instead of
5.0 million.

**What does not reproduce from this repository alone.** The private
benchmark (`proj18.dta`, the LABTAR/NECTAR laboratory bases, `vra.dta`) is
never committed and never fetched by any command above. Where a published
number depends on it, `replication/gabarito/` reads it only from the
`AIRLINE_DELAYS_PRIVATE_DIR` environment variable (never a path hardcoded in
code) and commits only the resulting agreement rate
(`data/analysis/taxas.csv`), not the private data itself. Tests that
need that directory carry the pytest marker `gabarito` and are skipped, not
failed, when the variable is unset — see `tests/conftest.py`. See
[Declared differences](#declared-differences) for the numbers that do not
close against the original benchmark, and why.

## Citation

If you use this repository, please cite the software and, for the
underlying econometric model, the original article:

```bibtex
@article{bendinelli2016airline,
  title   = {Airline delays, congestion internalization and non-price
             spillover effects of low cost carrier entry},
  author  = {Bendinelli, William E. and Bettini, Humberto F. A. J. and
             Oliveira, Alessandro V. M.},
  journal = {Transportation Research Part A: Policy and Practice},
  volume  = {85},
  pages   = {39--52},
  year    = {2016},
  doi     = {10.1016/j.tra.2016.01.001}
}

@software{bendinelli2026airlinedelays,
  title   = {airline-delays: from ANAC's raw VRA records to replication and
             delay prediction},
  author  = {Bendinelli, William Eduardo},
  year    = {2026},
  url     = {https://github.com/wbendinelli/airline-delays},
  version = {0.1.0}
}
```

`CITATION.cff` is the machine-readable source for both entries — GitHub
renders it as the repository's "Cite this repository" button.

## License

**MIT** for code — `src/`, `scripts/`, `replication/`, `ml/`, `theory/`, `tests/`,
`.github/` — see [LICENSE](./LICENSE). **CC BY 4.0** for text and for the
derived-data tables this repository curates — this README, `CLAUDE.md`,
`CONTRIBUTING.md`, `ROADMAP.md`, `docs/`, the prose of `reports/`, and
`data/external/*.csv` — see
[LICENSE-CC-BY-4.0.md](./LICENSE-CC-BY-4.0.md). The raw VRA records
themselves are ANAC's; they are redistributed here under CC BY with
attribution ("ANAC, Voo Regular Ativo (VRA), via dados.gov.br") rather than
relicensed — see [Data availability](#data-availability) and `DECISIONS.md`
ADR-0000 for the exact source and the licence trail.

## Data availability

Data Availability Statement, source by source; the full version, with the
holder, how to obtain it, restrictions and cost/time for each, is
[`docs/data-availability.md`](docs/data-availability.md). Every row of
`data/external/*.csv` additionally carries its own `source` and `url`
field; this table is the narrative summary of the same statement. It lists
12 of the statement's 15 sources; the three it leaves out — ANAC's seasonal
declared-capacity bulletins (not yet collected), its slot-coordination
acts (two transcribed rows in `data/external/slots.csv`) and the author's
2013 undergraduate monograph (one derived table,
`data/external/monograph_airports.csv`) — are documented in full there.

| Source | Access | Redistributed here | Cost |
|---|---|---|---|
| VRA — Voo Regular Ativo (ANAC monthly flight-leg CSVs, 2000-2013) | Public, `https://siros.anac.gov.br/siros/registros/diversos/vra/` | Yes — raw snapshot and derived tables, under CC BY with attribution. The federal open-data catalogue declares `Licença: Creative Commons Attribution` for this exact dataset (catalogued 2019-03-01, metadata updated 2024-01-25, read 2026-09-05); see `DECISIONS.md` ADR-0000. A written confirmation has also been requested from ANAC via e-SIC in parallel (`docs/notes/esic-licenca-vra.md`); the redistribution above does not block on that reply. | Free; ~17 minutes to download the 168 files (2.17 GB, `data/raw/manifest.json`) |
| IAC 1504 (delay-cause code taxonomy) | Public regulatory text | Yes — the derived taxonomy tables (`data/external/cause_codes.csv`, `di_codes.csv`, `line_types.csv`), not the instrument's own text | Free |
| ANAC statistical data (paid passengers by airline-route-month) | Public, ANAC website | Not yet collected — needed for the article's passenger-weighted `rthhi`/`maxcthhi` (ADR-0007) | Free; not yet spent |
| ANAC tariff microdata (`yield`, `fare`, ticket counts, 2002+) | Public, ANAC website | Not yet collected — needed for the original price question (`docs/tutorial/13-propor-melhorias.md`) | Free; not yet spent |
| BNDES/McKinsey (2010) airport-capacity study | Public PDF | One transcribed figure only (`data/external/capacity.csv`: Congonhas, 33 movements/hour post-2007), not the report itself | Free; manual-transcription time cost |
| CADE/ANAC merger and grouping acts | Public regulatory decisions | Cited per row of `data/external/groups.csv`, not the decisions themselves | Free |
| REDEMET / DECEA (METAR weather records) | Public via REDEMET today | Not yet integrated; the article's own weather signal comes from VRA justification codes, not METAR | Free; not yet spent |
| OurAirports (airport geography) | Public, community-maintained mirror | Yes — the filtered Brazilian subset (`data/external/airports_br.csv`, 8,035 rows), published as public domain / CC0-equivalent | Free |
| Federal holiday laws (Lei 662/1949, Lei 10.607/2002) | Public, `planalto.gov.br` | Yes — the derived calendar table (`data/external/holidays.csv`, 92 rows) and the computed observances (`observances.csv`), not the statutes' text | Free |
| Private benchmark (`proj18.dta`) and laboratory bases (LABTAR, NECTAR, `vra.dta`) | Not public — laboratory-internal, 2019 vintage | **Not redistributed.** Read only from `AIRLINE_DELAYS_PRIVATE_DIR`, outside this repository; only the derived agreement rate (`data/analysis/taxas.csv`) is committed | Not applicable — declared omission, not a silent drop |
| Infraero connections report | Not public | **Not redistributed** and not reproduced; any figure that depends on it is marked "not reproduced" in [Declared differences](#declared-differences) | Not applicable — declared omission |
| Published article (Elsevier) | DOI only | **Not redistributed** — no accepted manuscript exists in the archive this repository was built from either | Not applicable |

**TIER Protocol.** This repository's layout maps onto the
[TIER Protocol](https://www.projecttier.org/) documentation standard almost
directly: `data/raw/` is TIER's *Original Data*, `data/staged/` is
*Importable Data*, the group x route x month fact table and the replication
panel are *Analysis Data*, `src/`, `replication/` and `ml/` are *Command
Files*, and `docs/` together with this README are the *Documentation*
component. What TIER additionally asks for — a Data Appendix describing
every variable — is `src/vra/registry.py`, together with the dictionary it
generates (`docs/dictionary.md`: 584 columns across six layers — staged
flights, the fact table, city-month, airline-city-month, the replication
panel and the flight-level modelling table).

## Declared differences

Where this reconstruction does not match the original 2016 article or the
private benchmark, the difference is stated here, not adjusted away
(`DECISIONS.md` ADR-0010 governs how a genuine disagreement between two
valid options gets resolved). Full detail, with the cause of every gap as
far as the evidence goes, is in
[`docs/declared-differences.md`](docs/declared-differences.md); this
section summarises it.

**Reconstruction (data layer).** Column by column against the private
benchmark (`data/analysis/taxas.csv`, 24,551 comparable route-months):
`f` (the article's flight count) agrees on 90.2% of route-months overall
and 95.3% on the half of the series where the raw files have not changed
since the benchmark's 2019 vintage — the earlier reconstruction from that
same vintage reported 97.5%, so most of the shortfall is the raw files
changing upstream, not a difference in definitions
(`reports/reconciliation.md`). Departure- and arrival-delay-count
agreement is asymmetric under the identical rule (realised flights more
than 0 minutes late): this reconstruction measures 87.9% (stable vintage)
for departures against 56.3% for arrivals (`data/analysis/taxas.csv`,
`fl_odel`/`fl_ddel`); the earlier reconstruction, reading the 2019 vintage
directly, reported 92.4% and 59.8% for the same two columns — both
readings show the same asymmetry, still unexplained (`DECISIONS.md`
ADR-0002). `prwheather`, reproduced at 92.0% (stable vintage), folds in
more than weather — its dominant code is `AR`,
"aeroporto com restrições operacionais" (ADR-0005). `prcongested` is not
yet reproduced; it needs ANAC's seasonal capacity declarations, not yet
collected (ADR-0007). The node map changes benchmark agreement on `f` from
86.8% to 97.4%: putting Viracopos (SBKP) inside the São Paulo metropolitan
node, rather than treating it as a separate "Campinas" airport the way the
tariff base labels it, closes most of that gap (ADR-0001). The outlier
threshold is a named parameter, not a fixed fact: the laboratory used
313.25 minutes in one script and 117.10/111.75 minutes in another; this
repository defaults to 313.25 minutes, applies it to the **absolute value**
of the delay so that a mistyped month cannot enter a sum of minutes from
either tail (ADR-0015), and ships a sensitivity table across thresholds
instead of picking one silently (ADR-0008).

**Replication (Tables 2-7), against the private benchmark**
(`reports/replication/private/tables.md`, `reports/replication/private/summary.json`).
Across the five regression tables, 306 coefficients are compared: 302
agree in sign, 259 (85%) sit within half a published standard error, and
the largest single gap is 0.94 published standard errors. No conclusion of
the article changes. The article's central argument — instrumenting flips
the sign of both HHI terms between OLS and 2SGMM — is a claim about 12
comparisons (2 HHI terms x 6 columns): an inversion actually occurs in **4**
of them, columns (1) and (2), the `ODDS` regressand, and all 4 replicate.
In the other 8 (`MINS`, `MINS > 15`) OLS and 2SGMM already carry the *same*
sign in the published table and only the magnitude moves; the replication
agrees with the article on *whether* the sign flips in **12 of 12**
(computed by `replication/run.py` into `hhi_sign_inversions` in
`reports/replication/private/summary.json`; the cell-by-cell table is under
"HHI sign inversion" in `reports/replication/private/tables.md`).
What does not close: **N is about 5.3% larger in every column** (20,447-
20,630 replicated against 19,408-19,590 published — 5.31% on arrival
columns, 5.35% on departure columns) for a reason the delivered material
does not explain; the Hansen J, Adj. R-squared and identification
statistics move with it but never change a verdict (22 of 24 J-statistic
columns still fail to reject orthogonality at 5%, the same 2 still reject);
standard errors come out systematically smaller (median ratio 0.94-0.99);
and the `ivreg2`-convention F statistic is not reproduced at all — it is a
different quantity under `linearmodels`, left empty rather than filled
with a number that does not mean the same thing.

**The public panel cannot yet estimate the regression tables.** Built
purely from public VRA data, `data/analysis/panel_route_month.parquet`
loads and filters cleanly through the same code path
(`reports/replication/public/tables.md`: 21,566 observations, 207 routes,
under `just replicate`, no private directory needed), but Table 2 computes
only 7 of its 13 descriptive variables — the other 6 (congested/
uncongested flight counts, max city delay, codeshare, both HHIs) need
columns this panel does not carry at all. Of the 7 it does compute, six now
land close to the published values: weather, incidents and late-connection
shares; `fsc_oddsarr` averaging -1.3927 against the published -1.38; and the
`MINS` regressand, 6.8632 against 7.16 with a standard deviation of 8.79
against 8.29. `MINS` was the one that did not: before the symmetric outlier
rule of ADR-0015 it averaged -1.3404 with a standard deviation of 125 and a
minimum of -4,772 minutes, because the one-sided cut trimmed the late tail
and let a month typo through the early one. One variable still does not
match — `LCC presence city-pair`, 0.7761 against 0.90 published, the
operation-against-ticket-sales difference declared below. Tables 3-7 cannot be estimated at all: they
need `maxprdel`, `cshare`, `dailyflcong`/`dailyflncong` and the seven
Hausman-type instruments, none reconstructible from a VRA-only source,
plus `rthhi`/`maxcthhi` (present as columns, entirely null — the
flight-based `rthhi_flights`/`maxcthhi_flights` are a different index and
are never substituted in under the published name). `just replicate`
(public) prints exactly which variables each table is missing rather than
estimating on a near-equivalent column.

**Panel and feature layer**, benchmark comparison
(`data/analysis/taxas.csv`, `replication/gabarito/compare.py`): the
article's own FSC carrier set (excluding Avianca Brasil) reproduces
`fsc_prdelarr` at 65.1% agreement on the stable-vintage half — matching
the 65.1% the earlier reconstruction reported from the private raw data —
while the class-based variant (`fscc_prdelarr`, which classes Avianca
Brasil as FSC) reaches only 53.5%: a choice of carrier set, not a defect
in the delay definitions (`DECISIONS.md` ADR-0013). `lcc`, `pres_glo`,
`pres_azu` and `pres_tam`, read from VRA *operation*, agree with the
benchmark's ticket-sales convention on 90.7%-93.6% of route-months
(stable vintage) — a genuine source difference, not an error on either
side; the city-level LCC dummies, which the article itself takes from
operations rather than ticket sales, agree on 100% (`maxalccfu`).

**Prediction: the pre-2010 target is a floor, not a measurement**
(`DECISIONS.md` ADR-0017, `reports/prediction/results.md`). In the 2000-2009
files an actual timestamp is a field of the "Boletim de Alteração de Vôo",
which IAC 1504 requires only when there is an alteration, so an empty one on a
realised flight means **no alteration was reported** — it is not evidence that
the flight was measured on time, and it is not evidence that its outcome is
unknown. A panel of three reviewers (ADR-0010, verdicts in
`docs/notes/colegiado-adr0012.md`) adopted that reading for the prediction
layer: delay 0, flagged `on_time_no_bav`, for realised flights of carriers whose
class in `data/external/groups.csv` is FSC, LCC or regional; for `other` and
unlabelled carriers — foreign operators and the non-operating side of a
code-share — the empty field stays unknown and the flight keeps no delay
target. The null rate is not one convention but many: over 2000-2009 it is
**72.9%** for the **5,106,100** realised flights in scope against **83.0%** for
the **313,366** out of it, and the sceptical reviewer's 2005 cross-section over
all flights, not only this universe, found 90-100% for foreign carriers and
code-share legs. Every population count in this paragraph is quoted from one
block and computed nowhere else — `accounting` in
`reports/prediction/dataset.json`, printed under "Dataset (ADR-0017
accounting)" in `reports/prediction/results.md` — which is also where the
per-year table lives (`docs/declared-differences.md` publishes the rate by
carrier and year; `docs/notes/colegiado-adr0012.md` the reviewer's own
measurement).
A delay the carrier never reported therefore counts as on time, so the
published pre-2010 late rate is a lower bound; the replication panel is
untouched, because it has to reproduce a benchmark built under the 2019
vintage's own convention (ADR-0012). The rolling-origin evaluation over
2006-2013 gives a day-ahead AUC between 0.715 and 0.741 and an at-gate AUC
between 0.757 and 0.824, against 0.60-0.67 for the previous month's route
prevalence; on the 20-35% of flights with a linked inbound leg the at-gate
horizon reaches 0.87-0.93. `reports/prediction/results.md` prints the same
headline metrics under the superseded reading, which on the 2010-2013 folds —
where the two readings see exactly the same data — scored 0.636-0.711 day-ahead
against 0.715-0.724 here.

## Use and limits

This is a research reconstruction, not an ANAC product and not an
operational delay predictor. It supports academic replication and
methodological work on the 2000-2013 VRA period. It does not support
real-time flight-delay prediction, and nothing here should be read as a
statement about current Brazilian air-traffic performance — the schema and
the cause-code taxonomy this repository is built on (IAC 1504) were retired
around 2020 (the exact revoking instrument is pending e-SIC confirmation,
`docs/notes/esic-licenca-vra.md`). Numbers in this README and in `reports/`
are printed by versioned scripts under `replication/`, `ml/` and `theory/`,
never typed by hand (`CLAUDE.md`); a number without a script behind it is a
bug in this repository, not a fact about Brazilian aviation. The theory
chapters (`docs/theory/`) derive and review; they estimate nothing, and the
2013 monograph's own coefficients are quoted there as an outside document,
never as a result of this repository.
