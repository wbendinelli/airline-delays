# ROADMAP

What is left to build, organised by the phases named in `justfile`, plus the
didactic modules ported from the archive review. Each pipeline phase names
its `just` target and the `src/vra/` modules it depends on; see
`DECISIONS.md` for decisions already settled and the README's "Declared
differences" section for what does not close yet.

## Pipeline phases

1. **Data** (`just fetch`, `just stage`) — download the ANAC monthly VRA
   CSVs year by year into `data/raw/` with a `manifest.json` (source URL,
   retrieval date, sha256 per file), then parse into the canonical flight
   table (`data/staged/year=YYYY/*.parquet`, zstd, tight types) via
   `src/vra/io.py`, `keys.py`, `universe.py`, `codes.py` and `delays.py`.
2. **References** (`just refs`) — validate `data/external/*.csv` (node map,
   airline groups and mergers, IAC 1504 taxonomy, BNDES capacity,
   holidays): every row cites a `source` and a `url`.
3. **Features and panel** (`just features`, `just panel`) — the
   `group x route x month` fact table (`src/vra/hhi.py`, `congestion.py`,
   `hub.py`), aggregated on demand to any other grain (`aggregate()`,
   tested for additivity) and assembled into the replication panel
   (`panel.py`, the layered design of the archive's `banco_17_final.py`).
4. **Replication** (`just replicate`) — Tables 2-7 of Bendinelli, Bettini &
   Oliveira (2016) from public data only (`replication/table2.py` through
   `table7.py`); `replication/gabarito/` scores the result against the
   private benchmark locally and commits only the agreement rate.
5. **Prediction** (`just ml`) — the flight-level dataset, a temporal split
   and a rolling-origin evaluation over 2006-2013 (ADR-0009),
   XGBoost/LightGBM, with leakage tests as part of the test suite.
6. **Reports** (`just report`) — Typst sources under `reports/`:
   reconstruction, replication, prediction — written in Portuguese, per
   `CLAUDE.md`.
7. **Publication on Zenodo** (`just publish`) — deposit the raw snapshot
   and the prepared data (once the licence confirmation closes as expected,
   `DECISIONS.md` ADR-0000), mint a DOI, update `CITATION.cff` and the
   README badges, and generate `datapackage.json` with `id` set to that
   DOI.

## Didactic modules (ported from the archive review)

The archive review (`avaliacao-comparativa.md` §5, outside this
repository) maps the research arc — from the original 2013 proposal
through to this repository's `citation-audit` sibling — into twelve
modules, M0-M12. They belong under `docs/notes/` (Portuguese, per
`CLAUDE.md`) once written; listed here so the roadmap does not lose them.

- **M0** — how to use this material: a map of the arc, the conventions
  used, and what is missing and why.
- **M1** — the original proposal (Sep 2013): the question was about
  prices, not delays; the target journals; timeline vs. reality
  (submission seven months late).
- **M2** — the advisor's reading list (Jun-Aug 2014): thirteen answers
  without their questions, 1,300 minutes of recordings, the pivot from
  prices to delays.
- **M3** — the first design (Jul 2014): an airport-level model; an
  apron-capacity variable built, then abandoned.
- **M4** — the second design (Mar 2015): OLS with fixed effects, 38
  airports, 29,232 observations; "instrumentation left for later."
- **M5** — the road not taken (Jun 2015): the pricing draft, what it
  reproduces, a 30-vs-15-minute delay threshold, the TRA equation already
  sitting in the folder.
- **M6** — data: from the public source to the panel, and the missing
  link.
- **M7** — specification and estimation (Dec 2015): nine do-files become
  seven tables, shifted numbering, instruments vs. degrees of freedom, an
  unpublished `_tab7`, an `lcc_sr`/`lcc_lr` pair built and never used.
- **M8** — what reproduces and what does not: Table 2 yes, N no, the
  incident maximum no, two dissertation cells that were simply wrong — the
  honest list.
- **M9** — from dissertation to article (Oct 2015-Mar 2016): arbitrated
  dates, a changed title, an authorship question, footnote 20 vs. footnote
  33, a promise removed before submission.
- **M10** — peer review, the gap: nothing survived it in writing; what to
  keep next time.
- **M11** — reception: what the field picked up, what it got wrong, who
  adopted the method (`citation-audit`).
- **M12** — consent, licences and publication: a map of rights holders,
  the licence per layer, and what stays out of the public repository.
