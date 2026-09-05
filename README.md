# airline-delays

[![CI](https://github.com/wbendinelli/airline-delays/actions/workflows/ci.yml/badge.svg)](https://github.com/wbendinelli/airline-delays/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.XXXXXXX.svg)](https://doi.org/10.5281/zenodo.XXXXXXX)

> **Tier:** `C` · **Class:** `Research`

## Overview

`airline-delays` reconstructs Brazil's Voo Regular Ativo (VRA) flight-leg
records (ANAC, 2000-2013, about 13.5 million legs) into a single canonical
flight table, replicates the tables of Bendinelli, Bettini & Oliveira (2016,
*Transportation Research Part A*,
[`10.1016/j.tra.2016.01.001`](https://doi.org/10.1016/j.tra.2016.01.001)) from
public data only, and trains a flight-level delay predictor evaluated by a
rolling-origin split.

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

<!-- TODO: filled in phase N -- row/column counts and coverage once `stage` first runs end to end -->

## Quickstart

```bash
git clone https://github.com/wbendinelli/airline-delays.git
cd airline-delays
uv sync
just demo
```

`just demo` is meant to run the smallest end-to-end reproduction over the
committed fixture in `tests/fixtures/` (a deterministic, few-MB slice of the
flight table) — no network access, no ANAC download, no private directory.
<!-- TODO: filled in phase N -- the fixture and the `vra` CLI ship with the
data and features phases; until then `just demo` prints "not implemented
yet" and exits 0, per the justfile's convention for unimplemented targets. -->

## Reproducing

Full reconstruction runs on one machine (16 GB RAM, 10 cores), processing
the raw data year by year, never two full raw scans at once:

```bash
uv run vra fetch      # ANAC monthly CSVs -> data/raw/, with manifest.json
uv run vra stage      # data/raw/ -> data/staged/year=YYYY/*.parquet (zstd)
uv run vra refs       # validates data/external/*.csv (source + URL per row)
uv run vra features   # staged + refs -> the group x route x month fact table
uv run vra panel      # fact table -> the replication panel
uv run vra replicate  # Tables 2-7, public data only
uv run vra ml         # flight-level dataset, temporal split, rolling evaluation
```

Everything runs through `uv run` on Python 3.12 (pinned in `.python-version`
and `pyproject.toml`) — never the system `python3`, which lacks pandas.

<!-- TODO: filled in phase N -- expected wall time per phase, recorded here
once the first full 2000-2013 run completes. -->

**What does not reproduce from this repository alone.** The private
benchmark (`proj18.dta`, the LABTAR/NECTAR laboratory bases, `vra.dta`) is
never committed and never fetched by any command above. Where a published
number depends on it, `replication/gabarito/` reads it only from the
`AIRLINE_DELAYS_PRIVATE_DIR` environment variable (never a path hardcoded in
code) and commits only the resulting agreement rate
(`replication/gabarito/taxas.csv`), not the private data itself. Tests that
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

**MIT** for code — `src/`, `scripts/`, `replication/`, `ml/`, `tests/`,
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

Data Availability Statement, source by source. Every row of
`data/external/*.csv` additionally carries its own `source` and `url` field;
this section is the narrative version of the same statement.

| Source | Access | Redistributed here | Cost |
|---|---|---|---|
| VRA — Voo Regular Ativo (ANAC monthly flight-leg CSVs, 2000-2013) | Public, `https://siros.anac.gov.br/siros/registros/diversos/vra/` | Yes — raw snapshot and derived tables, under CC BY with attribution. The federal open-data catalogue declares `Licença: Creative Commons Attribution` for this exact dataset (catalogued 2019-03-01, metadata updated 2024-01-25, read 2026-09-05); see `DECISIONS.md` ADR-0000. A written confirmation has also been requested from ANAC via e-SIC in parallel (`docs/notes/esic-licenca-vra.md`); the redistribution above does not block on that reply. | Free; the time cost is the download and parse, recorded here once a full `fetch`/`stage` run completes |
| IAC 1504 (delay-cause code taxonomy) | Public regulatory text | Yes — the derived taxonomy table (`data/external/codigos_iac1504.csv`), not the instrument's own text | Free |
| ANAC statistical data (aggregate air-transport statistics) | Public, ANAC website | Cited for cross-checks only, not bulk-redistributed | Free |
| ANAC tariff base | Public, ANAC website | Cited for cross-checks only (it is the source of the metropolitan-node agreement in ADR-0001) | Free |
| BNDES/McKinsey (2010) airport-capacity study | Public PDF | Manually transcribed capacity figures only (`data/external/capacidade_bndes.csv`), not the report itself | Free; manual-transcription time cost |
| CADE/ANAC merger and grouping acts | Public regulatory decisions | Cited per row of `data/external/groups.csv`, not the decisions themselves | Free |
| REDEMET / INMET (weather records) | Public | Used only as a cross-check for weather-coded delays; not bulk-redistributed here | Free |
| Private benchmark (`proj18.dta`) and laboratory bases (LABTAR, NECTAR, `vra.dta`) | Not public — laboratory-internal, 2019 vintage | **Not redistributed.** Read only from `AIRLINE_DELAYS_PRIVATE_DIR`, outside this repository; only the derived agreement rate (`replication/gabarito/taxas.csv`) is committed | Not applicable — declared omission, not a silent drop |
| Infraero connections report | Not public | **Not redistributed** and not reproduced; any figure that depends on it is marked "not reproduced" in [Declared differences](#declared-differences) | Not applicable — declared omission |

**TIER Protocol.** This repository's layout maps onto the
[TIER Protocol](https://www.projecttier.org/) documentation standard almost
directly: `data/raw/` is TIER's *Original Data*, `data/staged/` is
*Importable Data*, the group x route x month fact table and the replication
panel are *Analysis Data*, `src/`, `replication/` and `ml/` are *Command
Files*, and `docs/` together with this README are the *Documentation*
component. What TIER additionally asks for — a Data Appendix describing
every variable — is `src/vra/registry.py`, together with the dictionary it
generates (`docs/dicionario.md`, <!-- TODO: filled in phase N -->, once
`registry.py` exists).

## Declared differences

Where this reconstruction does not match the original 2016 article or the
private benchmark, the difference is stated here, not adjusted away
(`DECISIONS.md` ADR-0010 governs how a genuine disagreement between two
valid options gets resolved). Known differences so far:

- **Departure- and arrival-delay-count agreement against the benchmark is
  asymmetric.** Under the same replication universe (ADR-0002),
  departure-delay counts reproduce the benchmark at 92.4% agreement and
  arrival-delay counts at 59.8%. The asymmetry is declared, not resolved.
- **`prwheather` folds in more than weather.** The article's weather-delay
  share, reproduced at 98.5% agreement, actually merges weather with closed
  or restricted airports — its dominant code is `AR`, "aeroporto com
  restrições operacionais" (ADR-0005). This repository ships a second delay-
  cause taxonomy alongside the article's original three columns, so both
  readings are available and neither hides inside the other.
- **`prcongested` is not yet reproduced.** The article's declared-capacity
  congestion measure needs ANAC's seasonal capacity declarations, which have
  not been collected yet; an internal p90-based proxy ships in the meantime
  (ADR-0007).
- **The outlier threshold is a named parameter, not a fixed fact.** The
  laboratory used 313.25 minutes in one script and 117.10/111.75 minutes in
  another; this repository defaults to 313.25 minutes and ships a
  sensitivity table across thresholds instead of picking one silently
  (ADR-0008).
- **The node map changes benchmark agreement on `f` from 86.8% to 97.4%.**
  Putting Viracopos (SBKP) inside the São Paulo metropolitan node, rather
  than treating it as a separate "Campinas" airport the way the tariff base
  labels it, is what closes most of that gap (ADR-0001).

<!-- TODO: filled in phase N -- full detail moves to
docs/declared-differences.md once the reconstruction scripts land; this
section will then summarise it instead of duplicating it. -->

## Use and limits

This is a research reconstruction, not an ANAC product and not an
operational delay predictor. It supports academic replication and
methodological work on the 2000-2013 VRA period. It does not support
real-time flight-delay prediction, and nothing here should be read as a
statement about current Brazilian air-traffic performance — the schema and
the cause-code taxonomy this repository is built on (IAC 1504) were retired
around 2020 (the exact revoking instrument is pending e-SIC confirmation,
`docs/notes/esic-licenca-vra.md`). Numbers in this README and in `reports/`
are printed by versioned scripts under `replication/` and `ml/`, never typed
by hand (`CLAUDE.md`); a number without a script behind it is a bug in this
repository, not a fact about Brazilian aviation.
