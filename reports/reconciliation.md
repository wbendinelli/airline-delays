# Reconciliação — VRA bruto de hoje contra o `vra.dta` do acervo (2019)

Gerado em 2026-09-05T04:32:18+00:00 por `scripts/verify_reconcile.py`.
Nada foi ajustado para bater: as divergências abaixo estão declaradas, não corrigidas
(regra 6 do brief).

## 1. Procedência

| item | valor |
|---|---|
| CSV bruto (hoje) | `https://siros.anac.gov.br/siros/registros/diversos/vra/{year}/` |
| linhas staged | 13,652,322 |
| `vra.dta` (acervo, 2019) | `Base de dados bruta/vra.dta` |
| bytes do `.dta` | 1,471,916,451 |
| sha256 do `.dta` | `a9a55629c5421facf9479cf16db39849a2e6f1e0d407e9eb16f9df04e3d296b0` |
| linhas do `.dta` | 13,503,778 |
| `git_commit` | `UNCOMMITTED` |
| amostra determinística | CRC32 da chave módulo 68 |

A chave é `(airline, flight_number, origin_icao, dest_icao, sched_dep)`, formatada
igual dos dois lados; os dois lados selecionam **as mesmas chaves**, então a amostra
não favorece nenhuma das bases.

## 2. Linhas por ano

| year | rows_staged | rows_dta | diff |
|---|---|---|---|
| -1 | 0 | 1 | -1 |
| 2000 | 883016 | 872850 | 10166 |
| 2001 | 927308 | 919857 | 7451 |
| 2002 | 917574 | 904287 | 13287 |
| 2003 | 801479 | 796733 | 4746 |
| 2004 | 752780 | 699839 | 52941 |
| 2005 | 787610 | 757432 | 30178 |
| 2006 | 831899 | 826372 | 5527 |
| 2007 | 940109 | 933558 | 6551 |
| 2008 | 894353 | 891672 | 2681 |
| 2009 | 990010 | 972165 | 17845 |
| 2010 | 1125949 | 1116255 | 9694 |
| 2011 | 1252890 | 1258807 | -5917 |
| 2012 | 1289289 | 1292673 | -3384 |
| 2013 | 1255647 | 1261277 | -5630 |
| 2014 | 69 | 0 | 69 |
| 2018 | 1 | 0 | 1 |
| 2019 | 3 | 0 | 3 |
| 2020 | 88 | 0 | 88 |
| 2030 | 1 | 0 | 1 |
| 2032 | 1 | 0 | 1 |
| 2070 | 1 | 0 | 1 |
| 2071 | 1 | 0 | 1 |
| 2088 | 7 | 0 | 7 |
| 2092 | 1 | 0 | 1 |
| 2099 | 136 | 0 | 136 |


## 3. Linhas por (ano, mês) — as 20 maiores diferenças

| year | month | rows_staged | rows_dta | diff |
|---|---|---|---|---|
| 2004 | 8 | 64566.0 | 16351.0 | 48215 |
| 2005 | 5 | 66678.0 | 42097.0 | 24581 |
| 2010 | 1 | 104197.0 | 90476.0 | 13721 |
| 2013 | 10 | 104690.0 | 115028.0 | -10338 |
| 2009 | 12 | 101428.0 | 92989.0 | 8439 |
| 2009 | 3 | 87535.0 | 79756.0 | 7779 |
| 2002 | 1 | 82383.0 | 74942.0 | 7441 |
| 2012 | 2 | 101509.0 | 105222.0 | -3713 |
| 2011 | 10 | 105013.0 | 108485.0 | -3472 |
| 2013 | 11 | 101391.0 | 98453.0 | 2938 |
|  |  | 2100.0 |  | 2100 |
| 2007 | 7 | 82513.0 | 81118.0 | 1395 |
| 2000 | 2 | 73711.0 | 72370.0 | 1341 |
| 2010 | 4 | 85908.0 | 87212.0 | -1304 |
| 2000 | 3 | 78286.0 | 77010.0 | 1276 |
| 2007 | 6 | 77197.0 | 76088.0 | 1109 |
| 2000 | 1 | 79608.0 | 78523.0 | 1085 |
| 2006 | 12 | 75768.0 | 74921.0 | 847 |
| 2000 | 8 | 73784.0 | 72986.0 | 798 |
| 2001 | 3 | 78847.0 | 78063.0 | 784 |


Tabela completa por mês em `reports/reconciliation_by_month.csv`.

## 4. Concordância coluna a coluna na amostra

Chaves em comum: **184,522**. Só no staged: 1,419. Só no `.dta`: 226.

| column | n | equal | agreement | both_null | differ | staged_null_dta_set | dta_null_staged_set | n_comparable |
|---|---|---|---|---|---|---|---|---|
| status | 184522 | 184378 | 0.99922 | 0 | 144 | 0 | 0 | 184522 |
| cause_code | 184522 | 183835 | 0.996277 | 118728 | 687 | 251 | 336 | 65794 |
| line_type | 184522 | 184193 | 0.998217 | 0 | 329 | 1 | 268 | 184522 |
| di | 184522 | 184451 | 0.999615 | 0 | 71 | 1 | 23 | 184522 |
| actual_dep | 184522 | 111060 | 0.601879 | 23557 | 73462 | 72381 | 34 | 160965 |
| actual_arr | 184522 | 111046 | 0.601804 | 23557 | 73476 | 72388 | 34 | 160965 |


`equal` conta como iguais os pares em que ambos os lados são nulos; `differ` é o
complemento. `staged_null_dta_set` são as linhas em que o staged não tem valor e o
`.dta` tem — o caso mais informativo, porque indica campo perdido na extração.

### Principais pares divergentes


**status**

| staged | dta | n |
|---|---|---|
| cancelled | realized | 117 |
| realized | cancelled | 27 |

**cause_code**

| staged | dta | n |
|---|---|---|
| MX |  | 160 |
|  | HD | 144 |
| XN |  | 98 |
| RI | AR | 27 |
|  | MX | 21 |
| AT |  | 20 |
|  | XN | 19 |
| AJ | AR | 15 |
|  | AR | 11 |
|  | AT | 10 |

**line_type**

| staged | dta | n |
|---|---|---|
| N |  | 237 |
| L |  | 31 |
| R | N | 18 |
| C | L | 17 |
| N | E | 6 |
| N | R | 5 |
| E | N | 4 |
| I | N | 4 |
| N | I | 2 |
| 1 | R | 1 |

**di**

| staged | dta | n |
|---|---|---|
| 11 |  | 13 |
| 4 | 2 | 11 |
| 10 |  | 9 |
| 6 | 2 | 5 |
| 7 | 9 | 4 |
| 2 | 6 | 3 |
| 2 | 1 | 3 |
| 7 | 2 | 2 |
| 2 | 4 | 2 |
| 3 | 4 | 2 |

## 5. Horários realizados: o `.dta` preenche o que o CSV de hoje deixa vazio

O achado mais consequente da reconciliação. Nos arquivos de 2000-2009 um voo
`REALIZADO` sem ocorrência vem com `Partida Real` e `Chegada Real` **vazios**; o
staging deixa o atraso nulo, sem imputar (ADR-0008). O `.dta` de 2019 carrega valor
justamente nessas linhas.

| medida | partida | chegada |
|---|---|---|
| linhas casadas na amostra | 184,522 | 184,522 |
| staged nulo e `.dta` preenchido | 72,381 | 72,388 |
| dessas, `.dta` gravou exatamente o horário previsto | 72,375 | 72,382 |
| no total da amostra, `.dta` tem realizado igual ao previsto | 117,502 | 116,719 |

Se a terceira linha for praticamente igual à segunda, a leitura é direta: a safra de
2019 tratou "campo vazio" como "operou no horário previsto". **Esta é a explicação da
concordância de 60% em `actual_dep`/`actual_arr` na tabela da seção 4** — não é campo
perdido na extração de hoje, é uma convenção diferente sobre o vazio. A divergência
fica declarada; a escolha de imputar ou não pertence à camada de análise, não ao
staging, e trocar uma pela outra muda toda média de atraso de 2000-2009.

## 6. `delarrive` é `max(chegreal - chegprog, 0)`?

Resposta curta: **sim**.

| medida | linhas | fração |
|---|---|---|
| linhas com `chegreal`, `chegprog` e `delarrive` presentes | 10,774,607 | — |
| `delarrive` igual a `max(chegreal - chegprog, 0)` (tolerância 0,51 min) | 10,768,192 | 0.9994 |
| `delarrive` igual ao atraso **com sinal** `chegreal - chegprog` | 10,403,932 | 0.9656 |
| `delarrive` negativo em alguma linha | 0 | — |
| `deldepart` negativo em alguma linha | 0 | — |

A pergunta é respondida dentro do próprio `.dta`, comparando `delarrive` com os
horários que o próprio arquivo carrega, para não misturar duas fontes.

## 7. Divergências declaradas

As diferenças acima **não foram corrigidas**. Elas entram em
`docs/declared-differences.md` e são o insumo de qualquer decisão futura sobre
mudar a extração. Este relatório é gerado; não editar à mão.
