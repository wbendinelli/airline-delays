# ROADMAP

What is done, what is in progress, and what is left to build, organised by
the phases named in `justfile`, plus the didactic modules ported from the
archive review. Each pipeline phase names its `just` target and the
`src/vra/` modules it depends on; see `DECISIONS.md` for decisions already
settled and the README's "Declared differences" section for what does not
close yet.

## Pipeline phases

1. **Data** (`just fetch`, `just stage`) — **done.** Downloads the ANAC
   monthly VRA CSVs year by year into `data/raw/` with a `manifest.json`
   (source URL, retrieval date, sha256 per file), then parses into the
   canonical flight table (`data/staged/year=YYYY/*.parquet`, zstd, tight
   types) via `src/vra/io.py`, `keys.py`, `universe.py`, `codes.py` and
   `delays.py`. 13,652,322 flight legs, 168 files (`data/staged/manifest.json`).
2. **References** (`just refs`) — **done.** Validates `data/external/*.csv`
   (node map, airline groups and mergers, IAC 1504 taxonomy, BNDES
   capacity, holidays): every row cites a `source` and a `url`
   (`docs/notes/references.md`). Two of these tables are thin by
   construction and stay open items — see below.
3. **Features and panel** (`just features`, `just panel`) — **done.** The
   `group x route x month` fact table (`src/vra/hhi.py`, `congestion.py`,
   `hub.py`), aggregated on demand to any other grain (`aggregate()`,
   tested for additivity) and assembled into the replication panel
   (`panel.py`). 166,203 fact cells, 31,760 panel rows across 310 routes
   (`data/analysis/manifest.json`, `data/analysis/panel_manifest.json`).
4. **Replication** (`just replicate`) — **done.** Tables 2-7 of
   Bendinelli, Bettini & Oliveira (2016) from public data only
   (`replication/table2.py` through `table7.py`); `replication/gabarito/`
   scores the result against the private benchmark locally and commits
   only the agreement rate. 306 coefficients compared, 302 sign
   agreement, 259 within half a published standard error
   (`reports/replication/private/summary.json`); the public panel
   estimates Table 2 only — the five regression tables need variables it
   does not carry yet (`docs/declared-differences.md`).
5. **Prediction** (`just ml`) — **done.** `ml/dataset_flights.py` builds the
   flight-level table (10,200,578 scheduled flights, 46 D-1 features plus 3
   for H-1, five targets, one DuckDB scan per staged year, about 25 s);
   `ml/split.py` holds the rolling origin 2006-2013 and the fixed
   2002-2010 / 2011 / 2012-2013 split of ADR-0009; XGBoost `hist` with
   early stopping on each fold's validation year, LightGBM optional. The
   nine leakage checks of `ml/leakage_tests.py` run on the fixture in
   `pytest` and on the real dataset in `just ml`. Headline numbers:
   `reports/prediction/results.md`, `reports/prediction.typ` and
   `docs/notes/prediction.md`. The dataset itself stays out of git
   (ADR-0004) and is described in `datapackage.json`.
6. **Reports** (`just report`) — **partial.** `reports/reconciliation.md`
   and `reports/replication.typ` exist and are generated, never
   hand-edited; a reconstruction report and a prediction report do not
   exist yet. `just report` itself is still the placeholder recipe in
   `justfile`.
7. **Publication on Zenodo** (`just publish`) — **pending.** Deposit the
   raw snapshot and the prepared data, mint a DOI, update `CITATION.cff`
   and the README badges (today's DOI badge points at a placeholder,
   `zenodo.XXXXXXX`), and generate `datapackage.json` with `id` set to
   that DOI. Blocked on nothing technical — the licence read of ADR-0000
   already supports redistribution — but not yet done. `just publish`
   itself is still the placeholder recipe.

## Open items, by phase

- **e-SIC reply** (phase 2/7) — `docs/notes/esic-licenca-vra.md` has the
  request text; it has not been sent yet, so there is no protocol number
  or reply to record. The CC BY reading of ADR-0000 does not block on it.
- **Capacity declarations** (phase 2) — `data/external/capacity.csv` holds
  one row (Congonhas, confidence B); ANAC's seasonal declared-capacity
  bulletins for the other 26 nodes have not been located
  (`docs/data-availability.md`, source 6). `prcongested` (ADR-0007) stays
  unreproduced until this exists.
- **Slot-coordination dates** (phase 2) — `data/external/slots.csv` has
  two rows (Guarulhos, Santos Dumont); Congonhas, Recife and Brasília are
  declared absent, not guessed at (`docs/notes/references.md`, §6).
- **HHI by passengers** (phase 2/3) — `rthhi`/`maxcthhi`/`gmchhi` need
  ANAC's paid-passenger statistics by airline-route-month, not yet
  collected (`docs/data-availability.md`, source 3;
  `src/vra/hhi.passenger_weighted_hhi` already has the right signature and
  returns `None` until then).
- **The `fl_ddel` asymmetry** (phase 3) — arrival-delay counts reproduce
  the benchmark at 56.0% (stable vintage) against 87.7% for departures
  under the identical rule; declared in `DECISIONS.md` ADR-0002 and still
  unexplained.
- **Duplicate fact cells across file years** (phase 3) — `build_fact` groups
  within each file year and concatenates, so a staged row whose derived
  year differs from the year of its source file (3,723 rows, 0.03%,
  `docs/notes/staging.md` §5) can produce the same
  `group x route x month` cell twice: 844 of 166,203 rows of
  `data/analysis/fact_group_route_month.parquet` share their key with
  another row. Sums over the table are unaffected; joins on the key are
  not, and the prediction layer collapses the table before using it
  (`ml.dataset_flights.collapse_fact`). Re-grouping the fact table itself
  across years would move the panel and the replication, so it has not
  been done here.
- **KP fixture status** (phase 4) — `replication/kp.py`'s algebraic
  self-check (`tests/test_replication_kp.py`, the Wald-to-Cragg-Donald and
  LM-to-Anderson collapses) runs in CI on synthetic data and needs no
  fixture. The regression test against the *published* Table 3 values
  (`test_identification_statistics_against_the_published_table_3`) is
  `gabarito`-marked and needs `AIRLINE_DELAYS_PRIVATE_DIR`; there is no
  public fixture that lets it run in CI, and building one (a small
  synthetic panel with known KP statistics) has not been attempted.
- **Zenodo deposit** (phase 7) — see above; also the sole remaining step
  before the README's DOI badge and `datapackage.json`'s `id` stop being
  placeholders.

## Didactic modules

**Done.** `docs/tutorial/00-como-usar.md` plus modules
`01-a-proposta.md` through `13-propor-melhorias.md` — the archive review
(`avaliacao-comparativa.md` §5, outside this repository) maps the
research arc, from the original 2013 proposal through this repository's
`citation-audit` sibling, into thirteen modules, M0-M12; a fourteenth,
"propor melhorias", was added here because the repository this arc led to
has its own extensions worth proposing, which the archive review's arc
predates. Contrary to what this file said before the modules existed,
they live under `docs/tutorial/` (not `docs/notes/`), because they are
the didactic walkthrough the README's "Data availability" and
`docs/tutorial/README.md` already point to, not research-evidence notes.

- **M0** (`00-como-usar.md`) — how to use this material: a map of the arc,
  the conventions used, and what is missing and why.
- **M1** (`01-a-proposta.md`) — the original proposal (Sep 2013): the
  question was about prices, not delays; the target journals; timeline
  vs. reality (submission seven months late).
- **M2** (`02-a-leitura-do-orientador.md`) — the advisor's reading list
  (Jun-Aug 2014): thirteen answers without their questions, 1,300 minutes
  of editing, the pivot from prices to delays.
- **M3** (`03-primeiro-desenho.md`) — the first design (Jul 2014): an
  airport-level model; an apron-capacity variable built, then abandoned.
- **M4** (`04-segundo-desenho.md`) — the second design (Mar 2015): OLS
  with fixed effects, 38 airports, 29,232 observations; "instrumentation
  left for later," and the OLS-to-cautionary-tale inversion this
  repository's own Table 6 still shows.
- **M5** (`05-caminho-nao-tomado.md`) — the road not taken (Jun 2015): the
  pricing draft, what it reproduces, a 30-vs-15-minute delay threshold,
  the TRA equation already sitting in the folder.
- **M6** (`06-dados-fonte-ao-painel.md`) — data: from the public source to
  the panel, with the reconciliation against the private benchmark.
- **M7** (`07-especificacao-e-estimacao.md`) — specification and
  estimation: 2SGMM, HAC, and the Kleibergen-Paap statistic written from
  scratch because no Python package implements it.
- **M8** (`08-o-que-reproduz.md`) — what reproduces and what does not,
  number by number: 302 of 306 coefficients agree in sign, N 5.3% larger
  in every column, no verdict changed.
- **M9** (`09-da-dissertacao-ao-artigo.md`) — from dissertation to article
  (Oct 2015-Mar 2016): arbitrated dates, a changed title, an authorship
  question, footnote 20 vs. footnote 33, a promise removed before
  submission.
- **M10** (`10-revisao-por-pares.md`) — peer review, the hole: nothing
  survived it in writing; what this repository does instead.
- **M11** (`11-recepcao.md`) — reception: what the field picked up, what
  it got wrong, who adopted the method (`citation-audit`).
- **M12** (`12-consentimento-licencas-publicacao.md`) — consent, licences
  and publication: a map of rights holders, the licence per layer, and
  what stays out of this repository.
- **M13** (`13-propor-melhorias.md`) — propose improvements: the eight
  extensions this repository's architecture already supports, what each
  one still needs, and the next concrete step for each.
