# docs/notes/

Research notes in **Portuguese** (`DECISIONS.md`, ADR-0006) -- the working
notes behind the decisions and the claims made elsewhere in the repository.
The evidence for `DECISIONS.md` lives here; the decision text itself stays in
English, because that file is part of the public repository. This index is the
English summary of the directory.

| Note | What it covers |
|---|---|
| `staging.md` | The two raw VRA layouts (12 columns to 2009, 20 from 2010), field by field, and every cleaning decision, with a per-year row count. Behind ADR-0001, ADR-0002 and ADR-0008. |
| `features.md` | The fact table and the reconstruction panel: what each column family is, how the article's definitions (universe, node map, carrier sets, delay rules) are applied, and the `empty_actual_means_on_time` convention of ADR-0012. |
| `replication.md` | How Tables 2-7 are assembled from the article's estimation panel -- the sample filters, the HAC and Kleibergen-Paap choices -- and how the re-estimated tables compare with the published ones. |
| `references.md` | How every table under `data/external/` was built, what is confidence grade A (a primary source read directly) and what is grade B (a convergent but unverified secondary source), and the open items of each. |
| `prediction.md` | The flight-level prediction layer: the unit and the five targets, the D-1 and H-1 horizons, the leakage rule and the nine checks that impose it, the rolling-origin result and the scope of the pre-2010 target. Behind ADR-0009, ADR-0015 and ADR-0017. |
| `colegiado-adr0012.md` | The review panel of ADR-0010 on the empty actual times of the 2000-2009 files: the question, the method, the three opinions in full and the decision that became ADR-0017. |
| `esic-licenca-vra.md` | The text of the e-SIC request behind the VRA licence reading of ADR-0000; the protocol number and the reply go here when they exist. |
| `monografia-2013.md` | The data side of the author's 2013 undergraduate monograph (USP): its sources, its 38 listed airports against the 27 nodes (`data/external/monograph_airports.csv`), its six airline groups as a dated source for `groups.csv`, what its surviving do-file does, and why its own regression is not re-estimated here. Behind ADR-0019. |

The study, `docs/study/`, cites these notes chapter by chapter
(`docs/study/05-os-dados.md` through `docs/study/07-resultados-e-replicacao.md`
lean on them most); this index exists so that a reader who lands here first
knows what each file covers before opening it.
