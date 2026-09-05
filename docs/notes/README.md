# docs/notes/

Research notes in **Portuguese** (didactic material, per `CLAUDE.md` and
`DECISIONS.md` ADR-0006) -- working notes that back a decision or a claim
made elsewhere in the repository. Evidence for the decisions in
`DECISIONS.md` lives here; the decision text itself stays in English,
because that file is part of the public repository.

| File | What it backs |
|---|---|
| `staging.md` | The two raw VRA layouts (12 columns to 2009, 20 from 2010), field by field, and every cleaning decision, with a per-year row count. Backs `DECISIONS.md` ADR-0001, ADR-0002, ADR-0008. |
| `features.md` | The fact table and the public panel: what each column family is, the `legacy_missing_actual_as_zero` flag (ADR-0012), and what the benchmark comparison measured, column by column. |
| `replication.md` | How Tables 2-7 are assembled from the panel -- the sample filters, the HAC and Kleibergen-Paap choices, and what reproduces against the private benchmark and what does not. |
| `references.md` | How every table under `data/external/` was built, what is confidence grade A (a primary source read directly) versus B (a convergent but unverified secondary source), and the open items for each. |
| `prediction.md` | The flight-level prediction layer: the unit and the five targets, the D-1/H-1 horizons, the leakage rule and the nine checks that impose it, the rolling-origin result, and the declared limits. Backs ADR-0009, ADR-0015 and ADR-0017 on the prediction side. |
| `colegiado-adr0012.md` | O colegiado da ADR-0010 sobre o horário real vazio nos arquivos de 2000-2009: a pergunta, o método, os três pareceres na íntegra e a decisão que virou a ADR-0017 (leitura B, com o escopo do revisor cético). |
| `esic-licenca-vra.md` | The e-SIC request text backing ADR-0000's VRA licence decision -- not yet sent, the protocol number and reply go here when they exist. |
| `monografia-2013.md` | The data side of the author's 2013 undergraduate monograph: its sources, its 38 listed airports against the 27 nodes (backs `data/external/monograph_airports.csv`), its six airline groups as a dated convergent source for `groups.csv`, what its surviving do-file does against what its text says, and why its Table 5 is not re-estimated (`docs/declared-differences.md`, "Not attempted"). Backs ADR-0019. |

`docs/tutorial/` cites these same notes repeatedly, module by module
(`docs/tutorial/06-dados-fonte-ao-painel.md` through
`08-o-que-reproduz.md` lean on them most); this index exists so a reader
who lands here first, rather than through the tutorial, knows what each
file backs before opening it.
