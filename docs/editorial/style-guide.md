# Style guide for the prose of this repository

Every human-read page of this repository -- the two READMEs, the entry pages,
the governance files, the notes, the tutorial, the theory chapters and the
Typst reports -- follows these rules. They are checked by
`scripts/check_docs_paths.py` (paths and commands), `tests/test_prose_vocabulary.py`
(vocabulary), `scripts/check_prose_numbers.py` (numbers) and
`scripts/check_readme_parity.py` (the two READMEs), and read by the editors
who review a change.

1. **Confident and declarative.** State what the repository does and what the
   article found. No hedging clauses, no self-labels ("honest", "declared, not
   adjusted away"), no arguing with an absent auditor.
2. **One idea per sentence, active voice.** Sentences under about 25 words;
   paragraphs of three to five sentences. Anything with more than three numbers
   is a table.
3. **A path only where the reader must go.** A file path or an ADR appears in
   backticks once per section, when the reader is expected to open it -- never
   as a citation after every clause. The README body names ADRs only in the
   sections that send the reader to `DECISIONS.md`.
4. **Every number is printed by a script.** A number in the entry pages is a
   value of `reports/summary.json` (`airline-delays summary`), rounded as the
   manifest rounds it, or a transcription from a cited outside document marked
   as such: "(article, Table 1)", "(monografia -- documento externo)". Years,
   DOIs, versions, ADR and table numbers are not measurements. Never recompute
   in prose.
5. **Lists the code can print are rendered, never typed:** the columns the
   reconstruction panel does not carry, the resources of the data package.
6. **No exaggeration.** "Published in *Transportation Research Part A*" is the
   claim. "Top journal", "highest level", "state of the art", "world-class" do
   not appear. The contribution is stated by what it is: the article's
   estimation panel published, its tables re-estimated, the theory derived,
   the predictor evaluated out of time.
7. **Vocabulary that does not appear** (test-enforced, case-insensitive):
   gabarito, NECTAR, LABTAR, proj18, vra.dta, "private benchmark", "laboratory
   base" / "base de laboratório", "declared difference(s)" /
   "declared-differences", "not adjusted away", `AIRLINE_DELAYS_PRIVATE_DIR`,
   `data/private`, `taxas.csv`, `reconciliation.md`, "vintage" / "safra" in
   the data sense, "honest" / "honesta" / "honestidade", "nota honesta", "top
   journal". The word "benchmark" appears only in its economics sense inside the
   theory chapters (the Cournot, atomistic and monopoly reference cases); new
   theory prose prefers "reference case" / "caso de referência".
8. **The two panels.** English: "the article's estimation panel" (first
   mention: "the panel the authors estimated Tables 2-7 on, published here")
   and "the open reconstruction panel" ("the reconstruction panel" after the
   first mention). Portuguese: "o painel de estimação do artigo" and "o painel
   reconstruído". Never "public panel", "private panel". Their relation is
   always "the same definitions" (universe, node map, carrier sets, delay
   rules), never "agreement", "verification", "reconciliation".
9. **The article and its authors.** First mention in every file: "Bendinelli,
   Bettini & Oliveira (2016, *Transportation Research Part A* 85, 39-52, doi
   10.1016/j.tra.2016.01.001)"; afterwards "the article". The repository's
   author is "the first author of the article". Co-authors are named in every
   citation of the article and in the dataset citation of the estimation panel.
10. **ANAC and the other holders.** Raw data: "ANAC, Voo Regular Ativo (VRA),
    via dados.gov.br" -- that exact string in every licence statement. Other
    sources by their holder's name, as in `docs/data-availability.md`.
11. **The monograph.** "The author's 2013 undergraduate monograph (USP/ESALQ)":
    an outside document, cited, not redistributed; its numbers are
    transcriptions marked "(monografia -- documento externo)"; the placeholder
    `[DOI-MONOGRAFIA]` stays verbatim until the Zenodo deposit.
12. **Bilingual conventions.** English: `13,652,322`, `0.715`, `2000-2013`,
    "route x month", "2SGMM", "ADR-0001". Portuguese: `13.652.322`, `0,715`,
    `2000-2013`, "rota x mês", "2SGMM", "ADR-0001". Dates `YYYY-MM-DD` in both.
    Column names, CLI commands and file paths are identical in both languages.
    Pages that are Portuguese by ADR-0006 open with "Português (ADR-0006)";
    their index page carries one English paragraph.
13. **Limits are scope, not confession.** "Use and limits" and each module's
    closing section say what the product covers and what the next step is.
14. **Headings.** README H2s are fixed by `readme-outline.md`; H3s are free;
    no H4. No emoji, no exclamation marks, no rhetorical questions in the
    README.
15. **Reader before writer.** Every section opens with what the reader gets,
    then how; a command comes after the sentence that says what it produces and
    how long it takes.
