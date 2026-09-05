# M6 — Dados: da fonte pública ao painel

**Objetivo.** Percorrer o caminho completo do CSV bruto da ANAC ao painel
reconstruído de rota-mês — bruto, *staged*, tabela-fato, painel — com o
número que cada etapa imprime e o arquivo que cada uma escreve em disco.

## O elo que o artigo não documentou

O artigo cita o VRA como fonte ("a maior parte dos dados utilizados nesta
pesquisa é publicamente disponível pela ANAC"), e nenhum script entre o
arquivo bruto e o painel de estimação sobreviveu no acervo (*avaliação em
oito critérios*, seção C2 — análise externa, não incluída aqui; ver M12).
Este módulo é esse elo, escrito do zero: quatro etapas, cada uma com um
comando, um manifesto e um número medido. O painel de estimação do artigo é
outro produto, publicado neste repositório e tratado em M8; os dois painéis
compartilham as mesmas definições — universo, mapa de nós, conjuntos de
companhias, regras de atraso (`DECISIONS.md`).

## Arquivos deste repositório

- [`docs/notes/staging.md`](../notes/staging.md) — os dois layouts brutos
  (12 colunas até 2009, 20 de 2010 em diante), campo a campo, com cada
  decisão de limpeza contada.
- [`docs/notes/features.md`](../notes/features.md) — a tabela-fato, as
  projeções e o painel reconstruído; a seção 6 diz o que ele compartilha
  com o painel de estimação do artigo.
- `DECISIONS.md` ADR-0001 (nós metropolitanos), ADR-0002 (universo de
  voos), ADR-0012 (horário realizado ausente nos arquivos de 2000-2009).

## Comandos

Cinco receitas, na ordem do pipeline. As duas primeiras custam tempo real
(download e leitura de 168 arquivos); as três últimas rodam em segundos
sobre o que já está em disco.

```bash
just fetch      # ~17 min, 2,17 GB -> data/raw/ e data/raw/manifest.json
just stage      # um ano por vez -> data/staged/year=AAAA/part-0.parquet e data/staged/manifest.json
just reference  # valida data/external/*.csv: procedência em cada linha
just fact       # ~11 s -> data/analysis/fact_group_route_month.parquet e data/analysis/manifest.json
just panel      # ~8 s -> data/analysis/panel_route_month.parquet, .csv.gz e panel_manifest.json
```

`just panel` regenera em seguida `docs/dictionary.md` e `datapackage.json`,
que descrevem cada coluna. Quem só quer os números pode pular os comandos:
`reports/summary.json` e os manifestos commitados dizem a mesma coisa.

## Números esperados

Todos de `reports/summary.json`, bloco `reconstruction`.

| Etapa | O que mede | Valor | Chave |
|---|---|---|---|
| bruto | arquivos mensais, 2000-2013 | 168 arquivos, 2,17 GB | `raw.files`, `raw.gigabytes` |
| bruto | tempo de download | 17 min | `raw.fetch_minutes` |
| staged | etapas de voo | 13.652.322 | `staged.rows` |
| tabela-fato | células grupo x rota x mês, colunas | 165.763 x 87 | `fact.rows`, `fact.columns` |
| tabela-fato | tempo de construção | 10,97 s | `fact.seconds` |
| painel | rota-meses, colunas | 31.313 x 228 | `panel.rows`, `panel.columns` |
| painel | rotas, meses, nós | 310, 168, 27 | `panel.routes`, `panel.months`, `panel.nodes` |
| painel | tempo de construção | 7,63 s | `panel.seconds` |

O bruto tem dois layouts, não um: 12 colunas separadas por vírgula até
2009, 20 por ponto e vírgula de 2010 em diante, com ordem de colunas
diferente (`docs/notes/staging.md`, seção 1). O *staged* os traz num só
esquema, e é dele que a tabela-fato e o painel saem.

## Exercício

Abra `data/analysis/manifest.json` e localize o bloco
`missing_actual_by_year`. Para 2002, qual é a fração dos voos realizados do
universo de replicação **sem** chegada real registrada (`sh_arr_missing`)?
Compare com 2010. O que muda entre os dois anos é o layout do arquivo
bruto, não a pontualidade (`docs/notes/staging.md`, seção 4.1): até 2009 o
horário realizado é campo do Boletim de Alteração de Vôo, emitido só quando
houve alteração. Depois, responda: que convenção o painel reconstruído
adota para esse campo vazio, e onde ela viaja com a tabela? A resposta está
na chave `empty_actual_means_on_time` do mesmo manifesto e na ADR-0012.

## Limites e próximos passos

O painel reconstruído cobre o que o VRA permite calcular. As colunas do
modelo do artigo que ele não traz com valor estão em `reports/summary.json`,
lista `reconstruction.article_columns_missing`; por família:

| Família | Colunas | O que traria a coluna |
|---|---|---|
| HHI ponderados por passageiros | `rthhi`, `maxcthhi` | os dados estatísticos da ANAC por empresa-rota-mês (`docs/data-availability.md`, fonte 3; `ROADMAP.md`, "Passenger HHIs for the reconstruction panel") |
| codeshare | `cshare` | uma tabela de acordos de codeshare por rota-mês, ainda sem item no roteiro |
| contagens por capacidade declarada | `dailyflcong`, `dailyflncong` | as declarações sazonais de capacidade da ANAC (fonte 6; ADR-0007; `ROADMAP.md`, "Capacity declarations") |
| atraso máximo da cidade-extremo | `maxprdel` | a definição exata do artigo; o painel traz `maxprdel_proxy` sob outro nome (`docs/dictionary.md`) |
| os sete instrumentos | `h1_maxcthhi`, `h2_maxcthhi`, `h3_maxcthhi`, `lnh1_maxcthhi`, `l1h1_maxcthhi`, `l1h2_maxcthhi`, `h2_rthhi` | os HHI de passageiros de que derivam, na construção espacial dos autores |

As Tabelas 2-7 não esperam por isso: `airline-delays estimate` roda sobre
o painel de estimação do artigo, que traz as treze colunas (M8). O próximo
passo do painel reconstruído é a fonte 3 — com ela entram os dois HHI e,
deles, os instrumentos.
