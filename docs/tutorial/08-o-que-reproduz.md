# M8 — A replicação: as Tabelas 2-7 reproduzidas do painel publicado

**Objetivo.** Ler o placar da replicação — as cinco tabelas de regressão do
artigo reestimadas sobre o painel de estimação que os autores usaram,
publicado neste repositório — e saber onde cada número do placar nasce.

## Contexto: o painel sobre o qual os autores estimaram está aqui

O painel de estimação do artigo — Bendinelli, Bettini e Oliveira (2016,
*Transportation Research Part A* 85, 39-52, doi 10.1016/j.tra.2016.01.001)
— está publicado em `data/analysis/article_panel_route_month.parquet`
(ADR-0020): 24.589 rota-meses x 52 colunas, 2002m1 a 2013m12, curado uma
vez a partir da base final dos autores, de dezembro de 2015, por
`airline-delays article-panel`. O manifesto
`data/analysis/article_panel_manifest.json` guarda o sha256 da base de
origem e dos dois arquivos publicados. A replicação é de fonte única:
`airline-delays estimate` roda as Tabelas 2-7 sobre esse painel e compara
cada coeficiente com o valor publicado, extraído do texto do artigo para
`src/airline_delays/estimation/published.json`.

## Arquivos deste repositório

- [`reports/replication/tables.md`](../../reports/replication/tables.md)
  — o placar e, tabela por tabela, publicado contra reestimado, com a
  diferença em erros-padrão publicados.
- [`reports/replication/summary.json`](../../reports/replication/summary.json)
  — os mesmos números em JSON, por tabela: `n_coefficients`,
  `sign_agreement`, `within_half_se`, `n_obs`, e o bloco
  `hhi_sign_inversions`.
- [`docs/notes/replication.md`](../notes/replication.md) — como cada tabela
  é montada: a amostra dos do-files, o kernel HAC, os dois blocos de
  instrumentos, o Kleibergen-Paap escrito do zero.
- [`reports/replication.typ`](../../reports/replication.typ) — o relatório
  em PDF, que lê os mesmos JSON.

## Comandos

`just estimate` reestima as seis tabelas sobre o painel commitado em menos
de um minuto (`reports/summary.json`, `estimation.seconds`) e reescreve
`reports/replication/`. Quem só quer ler o placar abre o arquivo já
commitado:

```bash
just estimate
grep -A8 "^## Scorecard" reports/replication/tables.md
```

## Números esperados

O placar, de `reports/summary.json`, bloco `estimation.tables`:

| Tabela | coeficientes | sinais iguais | dentro de meio e.p. |
|---|---|---|---|
| Tabela 3 (2SGMM) | 60 | 60 | 53 |
| Tabela 4 (robustez, 2SGMM) | 66 | 65 | 51 |
| Tabela 5 (LIML) | 60 | 59 | 53 |
| Tabela 6 (OLS) | 60 | 59 | 51 |
| Tabela 7 (partidas) | 60 | 59 | 51 |
| **total** (`estimation.totals`) | **306** | **302** | **259** |

A maior diferença isolada entre um coeficiente reestimado e o publicado é
0,94 erro-padrão publicado (`estimation.totals.max_difference_in_se`), na
Tabela 6. A inversão de sinal dos dois HHI entre OLS (Tabela 6) e 2SGMM
(Tabela 3) — o argumento central do artigo — é uma afirmação sobre 12
comparações: as 4 inversões publicadas se reproduzem, e réplica e artigo
concordam sobre haver ou não inversão em 12 de 12 (`estimation.hhi`). A
Tabela 2 fecha até a quarta casa nos mínimos e máximos, e o triângulo de
correlações tem diferença absoluta mediana de 0,002 em 91 células
(`estimation.table2`).

## Exercício

Confira as três somas do placar direto de
`reports/replication/summary.json`: some `n_coefficients`,
`sign_agreement` e `within_half_se` das cinco tabelas e compare com
`estimation.totals` em `reports/summary.json`. Depois localize a tabela
cujo `sign_agreement` é 65: qual é, e qual coeficiente inverteu o sinal?
A resposta está em `reports/replication/tables.md`, na coluna cujo
coeficiente publicado e reestimado têm sinais opostos — repare no tamanho
do erro-padrão publicado ao lado.

## Limites e próximos passos

**Nota sobre a amostra.** As tabelas publicadas reportam N entre 19.408 e
19.590; a reestimação sobre o painel publicado, com os filtros dos
do-files na ordem em que aparecem, dá N entre 20.447 e 20.630 —
5,3% a mais (`reports/summary.json`, `estimation.n_obs_published_range`,
`estimation.n_obs_replicated_range`, `estimation.n_obs_excess_pct`). Os
dois N ficam registrados lado a lado em cada coluna de
`reports/replication/tables.md`; a estatística F do `ivreg2` não é
comparável à do `linearmodels` e a célula fica vazia.

**Sensibilidade.** A grade de `reports/replication/sensitivity.json` varia
as 60 dummies sazonais região x mês nas colunas (1) e (2) da Tabela 3, e
nenhum sinal muda. O limiar de *outlier* do atraso (ADR-0008) age no nível
do voo e não varia num painel que chega agregado; ele é parâmetro do
pipeline de reconstrução (M6). O próximo passo natural é a comparação
formal do painel reconstruído com o painel do artigo nas colunas que os
dois trazem com o mesmo nome (`docs/notes/features.md`, seção 6).
