# docs/theory/

The theory behind the replicated article, as a thematic discussion in
**Portuguese** (the deliberate exception of `CLAUDE.md` and `DECISIONS.md`
ADR-0006): from the economics of airport congestion, through the game the
author's 2013 undergraduate monograph derived, to the 2016 article that is
this repository's econometrics of reference, and to its reception. It is
not chronological and it renumbers nothing in `docs/tutorial/`; module M14
(`docs/tutorial/14-a-teoria-por-tras-do-artigo.md`) is the door into it.
Every number about the model is printed by `just theory`
(`reports/theory/model.json`, `reports/theory/figures.json`); every number
about the 2016 article comes from `replication/published.json` or the
replication's own outputs; everything else is marked as an outside
document. Nothing here is estimated (`DECISIONS.md` ADR-0019).

Read in order:

| File | What it covers |
|---|---|
| `01-economia-do-congestionamento.md` | Congestion as an externality; the efficient level; price versus quantity regulation under uncertainty; airport expansion; network externalities; the internalisation literature; the low-cost business model. The five diagrams of the monograph's section 2, redrawn by `theory/figures.py`. |
| `02-o-jogo-do-congestionamento.md` | The Stackelberg game of the monograph's section 4, derived step by step and checked by `theory/model.py`: equations (1)-(12), the follower's reaction and its bounds, Proposition 1, the Cournot, atomistic and monopoly benchmarks, inelastic demand, the low-cost entrant; and where the formulation was taken to airfares, Guo, Jiang and Wan (2018). |
| `03-do-modelo-ao-artigo.md` | How the theory becomes the 2016 econometrics: the bridge from each theory object to the article's regressors and their published signs (`theory/bridge.py`), the identification logic, the map from the monograph's equation (22) to this repository's registry, what reproduces, and the 2018 critique. |
| `04-impacto.md` | The reception of the article, the place of the 2018 paper in it, and what remains open. |
| `bibliografia.md` | The single literature list of the four chapters, with the corrections made to the monograph's own list and a DOI only where it was resolved. |

Three labels run through the chapters: **[BVD]** a result of Brueckner and
Van Dender (2008) restated; **[monografia]** the monograph's own statement,
quoted literally; **[aqui]** what this repository's derivation adds. The
evidence note behind the data side of the monograph -- its airports, its
sources, its variables, what its surviving code does -- is
`docs/notes/monografia-2013.md`.
