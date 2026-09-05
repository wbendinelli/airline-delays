# Apêndice B — Como reproduzir cada número deste estudo

Português (ADR-0006).

Este apêndice é o guia prático. Ao terminá-lo, o leitor sabe montar o
ambiente, rodar a menor reprodução em cerca de um segundo, reestimar as
Tabelas 2–7 de Bendinelli, Bettini & Oliveira (2016, *Transportation Research
Part A* 85, 39-52, doi 10.1016/j.tra.2016.01.001) em menos de um minuto,
derivar o modelo, compilar o PDF, refazer a cadeia inteira a partir dos
arquivos da ANAC, e sabe de qual artefato e de qual comando sai cada número
de cada capítulo. Os tempos citados são os medidos e gravados em
`reports/summary.json`, com a chave ao lado.

## 1. O ambiente

Python 3.12 gerido pelo `uv`; `just` como executor de receitas; `typst` no
PATH só para compilar os PDF. A CLI é `airline-delays <etapa>`, e cada
receita do `justfile` embrulha um comando dela.

```bash
git clone https://github.com/wbendinelli/airline-delays.git
cd airline-delays && uv sync
uv run airline-delays --help      # as etapas, na ordem da cadeia
just --list                       # as receitas, agrupadas por etapa
```

Quem vai alterar o repositório instala também os ganchos de pré-commit,
`uv run pre-commit install`; a política de contribuição é `CONTRIBUTING.md`.

## 2. A menor reprodução: `just demo`

Roda a cadeia de ponta a ponta sobre a amostra versionada em
`tests/fixtures/` — 19.910 etapas de voo de 3 rotas nos anos de 2004, 2009 e
2012 (`fixture.legs`, `fixture.routes`, `fixture.years`) —, das etapas
staged à tabela-fato, ao painel reconstruído e à Tabela 2, sem rede, em cerca
de um segundo, escrevendo só sob `data/derived/demo/`. É `scripts/demo.py`, e
`tests/test_demo.py` o mantém funcionando.

```bash
just demo
```

## 3. As Tabelas 2–7: `just estimate`

Reestima as seis tabelas sobre o painel de estimação do artigo,
`data/analysis/article_panel_route_month.parquet` — 24.589 rota-meses × 52
colunas (`article_panel.rows`, `article_panel.columns`) —, compara célula a
célula com as tabelas publicadas em
`src/airline_delays/estimation/published.json` e escreve
`reports/replication/results.json`, `summary.json`, `sensitivity.json` e
`tables.md`. Tempo medido: 39,3 s (`estimation.seconds`).

```bash
just estimate                                   # as seis tabelas, o placar e a sensibilidade
uv run airline-delays estimate --tables table2,table3
uv run airline-delays estimate --rescore        # refaz summary.json e tables.md sem reestimar
uv run airline-delays estimate --panel outro_painel.parquet --outdir saida/
```

Outro painel de rota-mês entra por `--panel` se trouxer o contrato
`REQUIRED_COLUMNS` de `src/airline_delays/estimation/specification.py`; um
que não traga uma coluna é recusado com o nome do que falta. A suíte de
testes inclui o teste de frescor da replicação, que reestima as tabelas sobre
o painel versionado e falha quando `reports/replication/results.json` ficou
para trás.

## 4. O modelo: `just theory`

Deriva o modelo com `sympy`, confere as 29 identidades (`theory.n_identities`,
`theory.n_holding`), desenha as 11 figuras (`theory.n_figures`) e escreve
`reports/theory/model.json`, `figures.json`, `figures/*.svg` e `results.md`,
sem carimbo de tempo — uma segunda rodada sobre uma árvore inalterada não
muda nada. Cerca de um segundo; nenhum dado é lido.

```bash
just theory
uv run pytest tests/test_theory.py -q   # fixa cada identidade e falha se o relatório ficou para trás
```

## 5. Os PDF: `just report`

Compila as três fontes Typst de `reports/` — `reports/study.typ`, este
estudo; `reports/replication.typ`; `reports/prediction.typ` — em
`reports/pdf/study.pdf`, `reports/pdf/replication.pdf` e
`reports/pdf/prediction.pdf`, que são versionados (ADR-0022), com o carimbo
de criação tomado do commit da fonte, para que uma rodada sobre uma árvore
inalterada reescreva bytes idênticos. Cada fonte lê os seus JSON com `json()`
e nada é digitado à mão. Precisa do `typst` no PATH.

```bash
just report
uv run airline-delays report --only study    # um relatório só
```

## 6. O manifesto de números: `just summary`

Lê os manifestos de `data/`, as tabelas de `data/analysis/`, os relatórios de
`reports/` e `DECISIONS.md`, e escreve `reports/summary.json`, o único lugar
de onde as páginas de entrada — e este estudo — tiram números.
`airline-delays summary --check` falha quando o arquivo versionado difere de
uma reconstrução; `scripts/check_prose_numbers.py` recusa nas páginas de
entrada qualquer número que não seja um valor dele; `tests/test_summary.py`
falha quando ele fica para trás.

```bash
just summary
uv run airline-delays summary --check
uv run python scripts/check_prose_numbers.py docs/study/apendice-b-como-reproduzir.md
```

## 7. A cadeia completa

Uma máquina de 16 GB e 10 núcleos refaz tudo a partir dos arquivos da ANAC,
um ano por vez — nunca duas varreduras completas de `data/raw/` ao mesmo
tempo, porque uma única varredura das catorze partições com um `GROUP BY`
largo é o que faz a máquina usar swap. `just pipeline` roda, a partir de
`data/staged/`, as etapas 3, 4, 5, 7 e 9 e o `just summary` da etapa 10 —
referência, tabela-fato, painel, estimação, teoria e o manifesto de números —,
sem rede e sem reajustar nada; `just pipeline-full` acrescenta o download, o
parse e a previsão (etapas 1, 2 e 8). A etapa 6 corre uma vez só, na máquina
do primeiro autor.

| # | Etapa | Receita | Lê → escreve | Tempo medido | Chave em `reports/summary.json` |
|---|---|---|---|---|---|
| 1 | ingestão | `just fetch` | os CSV mensais da ANAC → `data/raw/` (168 arquivos, 2,17 GB) e `data/raw/manifest.json`, com o sha256 de cada arquivo | 17,0 min | `reconstruction.raw.files`, `raw.gigabytes`, `raw.fetch_minutes` |
| 2 | staging | `just stage` | `data/raw/` → `data/staged/year=YYYY/part-0.parquet`, 13.652.322 etapas de voo | um ano por vez | `reconstruction.staged.rows` |
| 3 | referência | `just reference` | valida cada linha de `data/external/*.csv`: fonte, URL, grau de confiança e os conjuntos das ADR | segundos | `external.*` |
| 4 | tabela-fato | `just fact` | etapas staged → `data/analysis/fact_group_route_month.parquet` (165.763 × 87) e as duas projeções de cidade | 10,97 s | `reconstruction.fact.rows`, `fact.columns`, `fact.seconds` |
| 5 | painel | `just panel` | tabela-fato → `data/analysis/panel_route_month.parquet` (31.313 × 228), depois `docs/dictionary.md` e `datapackage.json` | 7,63 s | `reconstruction.panel.rows`, `panel.columns`, `panel.seconds` |
| 6 | painel do artigo | `just article-panel` | a base final dos autores → `data/analysis/article_panel_route_month.parquet` (24.589 × 52), uma vez, na máquina do primeiro autor | — | `article_panel.rows`, `article_panel.columns` |
| 7 | estimação | `just estimate` | painel de estimação do artigo → `reports/replication/` | 39,3 s | `estimation.seconds` |
| 8 | previsão | `just predict-dataset`, `just predict` | etapas staged → `data/derived/ml/` (10.200.560 linhas) → `reports/prediction/` | 24,73 s; 2.344,2 s | `prediction.rows`, `prediction.dataset_build_seconds`, `prediction.runtime_seconds` |
| 9 | teoria | `just theory` | `src/airline_delays/theory/` → `reports/theory/` (29 identidades, 11 figuras) | cerca de um segundo | `theory.n_identities`, `theory.n_figures` |
| 10 | relatórios | `just summary`, `just report` | os artefatos → `reports/summary.json`; as fontes Typst → `reports/pdf/` | segundos | — |

`just check-analysis` (ADR-0014) reconstrói em memória as tabelas versionadas
de `data/analysis/` e falha quando uma delas deixou de corresponder ao
código. `data/raw/`, `data/staged/` e `data/derived/` são regenerados e não
entram no git além dos seus `README.md` e de `data/raw/manifest.json`.

## 8. De onde vem cada número do estudo

| Capítulo | Artefato | Comando |
|---|---|---|
| Apresentação | `reports/summary.json`; `src/airline_delays/estimation/published.json` | `just summary`; `just estimate` |
| 1. A economia do congestionamento | `reports/theory/figures.json` e `reports/theory/figures/` (Figuras 1 a 5) | `just theory` |
| 2. Teoria dos jogos: fundamentos | `reports/theory/model.json`, bloco `primer` | `just theory` |
| 3. O jogo do congestionamento | `reports/theory/model.json` (`identities`, `reaction_slope`, `leader_follower`, `tolls`, `benchmarks`, `linear_closed_forms`, `inelastic`, `examples`, `comparative_statics`, `extension_lcc`); Figuras 6 a 10 | `just theory` |
| 4. Do modelo às hipóteses | `reports/theory/model.json`, bloco `bridge`; `src/airline_delays/estimation/published.json`; Figura 11 | `just theory` |
| 5. Os dados | `data/analysis/manifest.json`, `panel_manifest.json`, `article_panel_manifest.json`; `reports/summary.json` (`reconstruction`, `article_panel`) | `just fact`, `just panel`, `just summary` |
| 6. Especificação e identificação | `src/airline_delays/estimation/specification.py` (as constantes da especificação); `reports/replication/results.json` (as estatísticas de identificação) | `just estimate` |
| 7. Resultados e replicação | `reports/replication/results.json`, `summary.json`, `sensitivity.json`, `tables.md`; `src/airline_delays/estimation/published.json`; `reports/summary.json` (`estimation`, `published`) | `just estimate`, `just summary` |
| 8. A recepção | nenhum número medido aqui; as obras citadas estão em [`bibliografia.md`](bibliografia.md) | — |
| Apêndice A | `reports/prediction/*.json`; `reports/summary.json` (`prediction`) | `just predict-dataset`, `just predict`, `just summary` |
| Apêndice D | `docs/dictionary.md`; `reports/summary.json` (`reconstruction.article_columns_missing`, `external`, `prediction`) | `just panel`, `just summary` |

Os números marcados "(artigo, Tabela N)" são transcrições das tabelas
publicadas; os marcados "(monografia — documento externo)" só existem na
monografia de graduação do autor (USP, 2013). Nenhum dos dois é medição deste
repositório.

## 9. As verificações

Antes de abrir um pull request, `just check` roda o pré-commit sobre a árvore
inteira, o conferidor de caminhos e comandos e o conferidor de Markdown;
`just test` roda a suíte. A integração contínua repete tudo a cada pull
request, e uma falha se corrige na causa, nunca enfraquecendo a checagem.

```bash
uv run pytest -q                                   # a suíte: fixture, tabelas versionadas, replicação, teoria, vazamento, vocabulário, números, paridade dos READMEs
uv run python scripts/check_docs_paths.py          # todo caminho e comando citado nos READMEs, em docs/ e nos guias de dados existe
uv run python scripts/check_markdown_math.py       # matemática inline como $`...`$, display em cerca ```math, tabelas e cercas bem formadas
uv run python scripts/check_prose_numbers.py       # todo número das páginas de entrada é um valor de reports/summary.json
uv run python scripts/check_readme_parity.py       # README.md e README.pt-BR.md citam os mesmos números, caminhos e receitas
just check-analysis                                # as tabelas versionadas de data/analysis/ correspondem ao código (ADR-0014)
just publish                                       # dicionário, datapackage, summary e .zenodo.json são reconstruções; CITATION.cff válido
```

| Job de CI | O que garante |
|---|---|
| `lint` | `ruff check` e `ruff format --check` sobre a árvore inteira |
| `test` | `pytest` contra a amostra versionada e as tabelas de `data/analysis/`; sem rede, sem `data/raw/` |
| `citation` | `CITATION.cff` válido contra o esquema |
| `docs-paths` | `scripts/check_docs_paths.py` e `scripts/check_markdown_math.py` |
| `metadata` | `docs/dictionary.md`, `datapackage.json`, `.zenodo.json` e `reports/summary.json` são reconstruções do registro, das tabelas e dos relatórios; o pacote de dados valida |
| `docs-lint` | `README.md` segue o perfil `research` de `.sapians-repo.yml` |
| `security` | `gitleaks` varre o histórico inteiro |
