# The README outline

`README.md` (English, the main page) and `README.pt-BR.md` (Portuguese) share
this skeleton: the same H2s in the same order, the same tables, the same
numbers -- each number a value of `reports/summary.json`, named below by its
key. The Portuguese page is written natively, not translated sentence by
sentence. `scripts/check_readme_parity.py` fails when the two pages quote
different numbers, paths or recipes.

## Header

- `# airline-delays`
- Badges (first 40 lines): CI, License MIT, Data CC BY 4.0, DOI (the article's
  `doi.org/10.1016/j.tra.2016.01.001` until Zenodo mints the software DOI).
- The identity line `> **Tier:** \`C\` · **Class:** \`Research\`` (required by
  the docs lint; keep verbatim).
- The language switch: `[English](README.md) · [Português](README.pt-BR.md)`.
- One bold tagline: *Brazil's scheduled domestic flights 2000-2013 -- from
  ANAC's raw records to a published article's tables, its theory, and a
  flight-level delay predictor.*

## Overview  (`## Overview` / `## Visão geral`)

Thesis paragraph (see the plan): the boom, the two low-cost entrants (Gol
2001, Azul 2008 -- years from `data/external/events.csv`), the policy question
(internalise congestion or let competition cure it), the article's answer, and
what this repository is: the research programme made fully open by its first
author.

### Why airport congestion matters
Growth of scheduled domestic flights among the 27 nodes from the first to the
last year of the series (`reconstruction.flights_scheduled_first_year`,
`reconstruction.flights_scheduled_last_year`, `reconstruction.flights_growth_pct`);
the 2006-2007 crisis as the moment congestion became national policy
(`events.csv`); the two hypotheses in one sentence.

### What the article found
A two-row table, Table 3 column (2) (2SGMM) against Table 6 column (2) (OLS):
`published.table3.col2.{rthhi,maxcthhi,lcc,maxalccfu}.{b,se,stars}` and
`published.table6.col2.*`, with `n_obs`. The reading: after instrumenting,
airport concentration lowers delays (internalisation), route concentration
raises them, low-cost presence at the city lowers rivals' delay odds -- the
"non-price spillover" of the title; the OLS-to-2SGMM sign change is a statement
about the ODDS columns.

### What this repository gives you
Four products, one line each, with the path: the open reconstruction panel
(`reconstruction.panel.rows/columns/routes/months/nodes`, from
`reconstruction.staged.rows` legs in `reconstruction.raw.files` files); the
article's estimation panel and the replication of Tables 2-7
(`article_panel.rows/columns`); the theory (`theory.n_identities`,
`theory.n_figures`); the delay predictor (`prediction.rows`,
`prediction.features_d1`). One sentence: the two panels share one set of
definitions recorded in `DECISIONS.md`.

## Quickstart  (`## Quickstart` / `## Início rápido`)

`git clone`, `uv sync`, `just demo` (offline, the fixture of `fixture.legs`
legs, seconds); `just estimate` re-estimates Tables 2-7 on the committed
article panel (`estimation.seconds`); Python 3.12 via `uv`.

## Reproducing  (`## Reproducing` / `## Reprodução`)

The pipeline table: stage · `just` recipe · reads -> writes · wall time
(`reconstruction.raw.fetch_minutes`, `reconstruction.fact.seconds`,
`reconstruction.panel.seconds`, `estimation.seconds`,
`prediction.runtime_seconds`). Stages: fetch, stage, reference, fact, panel,
article-panel, estimate, predict-dataset / predict, theory, summary / report.
Machine line (16 GB, 10 cores, year by year). `uv run airline-delays --help`.

## Results at a glance  (`## Results at a glance` / `## Resultados em resumo`)

(a) Replication scorecard, five rows (`estimation.tables.table3..table7.*`) and
the totals sentence (`estimation.totals.*`, `estimation.hhi.*`). (b) Prediction:
horizon · AUC range over the rolling folds
(`prediction.rolling.horizons.D-1/H-1.auc_min/auc_max`) · route-prevalence
baseline (`prediction.rolling.baselines.route_prevalence_l1.*`); the linked
inbound-leg subset (`prediction.rolling.horizons.H-1.linked_subset_auc_*`,
`prediction.rolling.linked_share_min/max`). (c) Theory line
(`theory.n_identities`, `theory.leader_toll_share_linear`, the leader flies at
least twice the follower's flights).

## Data availability  (`## Data availability` / `## Disponibilidade dos dados`)

### Data guide: what is in git (both panels, the fact table, the two
projections, the 13 curated external tables, the manifests --
`registry.columns_total` columns across `registry.layers` layers in
`docs/dictionary.md`; `datapackage.json`), what is regenerated (`data/raw`,
`data/staged`, `data/derived`) and what goes to Zenodo; the "Which panel?" box.
### Sources: a table of about ten rows (VRA; IAC 1504; the article's estimation
panel; ANAC tariff and statistical data; OurAirports; federal holiday laws;
BNDES / slots / CADE reference tables; METAR; the article by DOI; the
monograph). Licence per layer with the ANAC attribution string; TIER Protocol
in four lines.

## Learn more  (`## Learn more` / `## Para saber mais`)

`docs/tutorial/` (M0-M14), `docs/theory/` (four chapters), `docs/notes/`,
`reports/` (three Typst reports) -- each "written in Portuguese; the index page
carries an English summary". The sibling repositories `citation-audit` and
`sapians-research`.

## Citation  (`## Citation` / `## Citação`)

The fenced BibTeX block with the article and the software entries (kept
identical in both pages); one line on `CITATION.cff`; the dataset citation of
the estimation panel: Bendinelli, W. E.; Bettini, H. F. A. J.; Oliveira,
A. V. M. (2016 data; 2026 release). *Estimation panel of "Airline delays,
congestion internalization and non-price spillover effects of low cost carrier
entry"*, route x month, 2002-2013. Curated and published by W. E. Bendinelli.
CC BY 4.0. DOI to follow the Zenodo deposit.

## License  (`## License` / `## Licença`)

MIT for code; CC BY 4.0 for text and curated data (both panels, the external
tables); the raw VRA records are ANAC's, redistributed as "ANAC, Voo Regular
Ativo (VRA), via dados.gov.br".

## Use and limits  (`## Use and limits` / `## Uso e limites`)

Scope, not confession: a research dataset for 2000-2013; not a live predictor;
the IAC 1504 taxonomy retired around 2020; the reconstruction panel does not
carry the article's passenger-weighted concentration terms, the codeshare
dummy, the declared-capacity congestion counts or the instruments
(`reconstruction.article_columns_missing`, rendered as a list); every number
on the page is printed by `airline-delays summary`.
