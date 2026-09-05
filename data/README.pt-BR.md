# data/

Português (ADR-0006) -- a versão em inglês desta página é o `README.md` deste
diretório.

Os dados de `airline-delays`, camada por camada: o que cada diretório contém, o
que é versionado no git, o que é regenerado a partir dos arquivos da ANAC e
qual dos dois painéis usar para quê. `docs/dictionary.md` define cada coluna e
`datapackage.json` descreve cada tabela versionada como um Frictionless Data
Package; esta página é o guia de ambos.

## As camadas

```text
 bruto  -------->  staged  -------->  fato / análise  -------->  derivado
 data/raw/         data/staged/       data/analysis/              data/derived/ml/
 168 CSVs          13.652.322         a tabela-fato, as duas      a tabela de
 mensais, 2,17 GB  etapas de voo,     projeções por cidade e o    modelagem por voo,
 (just fetch)      um parquet por     painel reconstruído         10.200.560 linhas
                   ano (just stage)   (just fact, just panel)     (just predict-dataset)
                                          ^
                                          |  o painel de estimação do artigo entra em
                                          |  data/analysis/ pela lateral: curado uma única
                                          |  vez a partir da base dos autores, não produzido
                                          |  pelo pipeline (just article-panel)
```

Os dois painéis compartilham o universo, o mapa de nós e os conjuntos de
companhias registrados em `DECISIONS.md`; a reconstrução segue a convenção do
artigo onde o artigo a enuncia e declara a sua própria onde ele não o faz.
`data/external/` guarda as tabelas de referência curadas à mão de onde essas
definições são lidas.

## O que é versionado

| Arquivo | Grão | Linhas x colunas | Chave | Licença | Regenerado por |
|---|---|---|---|---|---|
| `data/analysis/fact_group_route_month.parquet` | grupo aéreo x rota x mês, universo da replicação | 165.763 x 87 | `(group, route, ym)` | CC BY 4.0 | `airline-delays fact` |
| `data/analysis/city_month.parquet` | cidade-nó x mês | 21.231 x 91 | `(node, ym)` | CC BY 4.0 | `airline-delays fact` |
| `data/analysis/airline_city_month.parquet` | grupo aéreo x cidade-nó x mês | 49.801 x 81 | `(group, node, ym)` | CC BY 4.0 | `airline-delays fact` |
| `data/analysis/panel_route_month.parquet`, e a mesma tabela como `.csv.gz` | rota x mês, 2000-2013: o painel reconstruído | 31.313 x 228 | `(route, ym)` | CC BY 4.0 | `airline-delays panel` |
| `data/analysis/article_panel_route_month.parquet`, e a mesma tabela como `.csv.gz` | rota x mês, 2002-2013: o painel de estimação do artigo | 24.589 x 52 | `(route, ym)` | CC BY 4.0 | `airline-delays article-panel`, na máquina do primeiro autor |
| `data/analysis/manifest.json`, `panel_manifest.json`, `article_panel_manifest.json` | proveniência das três construções: commit, versões das ferramentas, parâmetros, dimensões, hashes | -- | -- | CC BY 4.0 | escritos pelos três comandos acima |
| `data/raw/manifest.json` | uma entrada por arquivo bruto: URL, data de obtenção, bytes, sha256 | 168 entradas | arquivo | CC BY 4.0 | `airline-delays fetch` |
| `data/external/*.csv` | treze tabelas de referência, uma linha por fato, cada linha com fonte, URL e grau de confiança | abaixo | por tabela | CC BY 4.0 | curadas à mão; validadas por `airline-delays reference` |

| Tabela de referência | Linhas | O que codifica |
|---|---|---|
| `airports_br.csv` | 8.035 | todos os registros do OurAirports para o Brasil |
| `nodes.csv` | 31 | a correspondência aeroporto-nó dos 27 nós (ADR-0001) |
| `distances_km.csv` | 702 | distâncias ortodrômicas entre nós |
| `groups.csv` | 50 | companhia a grupo econômico, fusões datadas, classe de modelo de negócio (ADR-0003, ADR-0011) |
| `cause_codes.csv` | 49 | os códigos de justificativa da IAC 1504 e as duas taxonomias (ADR-0005) |
| `di_codes.csv` | 12 | os códigos DI de autorização do filtro de universo (ADR-0002) |
| `line_types.csv` | 8 | os códigos de tipo de linha |
| `holidays.csv` | 92 | feriados federais 2000-2013, por lei |
| `observances.csv` | 56 | Carnaval, Sexta-feira Santa e Corpus Christi, calculados a partir da Páscoa |
| `events.csv` | 29 | entradas, saídas, fusões e choques do período |
| `capacity.csv` | 1 | capacidade horária declarada (ADR-0007) |
| `slots.csv` | 2 | atos de coordenação de slots |
| `monograph_airports.csv` | 38 | a lista de aeroportos da monografia de graduação do autor, de 2013 |

## O que é regenerado

`data/raw/`, `data/staged/` e `data/derived/` ficam fora do git além do seu
`README.md` (e, para `data/raw/`, do manifesto). `just fetch && just stage`
reconstrói os arquivos brutos (168 arquivos, 2,17 GB) e a tabela de voos
*staged* (13.652.322 etapas de voo, um parquet por ano) a partir dos servidores
da ANAC; `just fact` escreve dois intermediários sob `data/derived/`;
`just predict-dataset` escreve a tabela de modelagem por voo sob
`data/derived/ml/` (10.200.560 linhas x 65 colunas); `just demo` escreve sob
`data/derived/demo/`. O registro no Zenodo da publicação v1.0.0 arquiva o
repositório com suas tabelas versionadas; as camadas regeneradas são
reconstruídas a partir dos arquivos da ANAC.

## Qual painel?

| Você quer | Use |
|---|---|
| Reestimar as Tabelas 2-7 do artigo, ou partir da base final dos autores (as amostras de estimação publicadas são um subconjunto dela que os filtros registrados não reproduzem exatamente) | o painel de estimação do artigo, `data/analysis/article_panel_route_month.parquet`: 2002-2013, 24.589 rotas-mês x 52 colunas |
| Estudar atrasos, concentração ou presença de baixo custo ao longo de toda a série, ou construir variáveis para previsão | o painel reconstruído, `data/analysis/panel_route_month.parquet`: 2000-2013, 31.313 rotas-mês x 228 colunas |

## Licenças

MIT para o código que constrói estas tabelas. CC BY 4.0 para os dados curados:
os dois painéis, a tabela-fato, as projeções por cidade, as tabelas de
referência e os manifestos (`LICENSE-CC-BY-4.0.md`). Toda tabela derivada dos
registros de voo traz a atribuição "ANAC, Voo Regular Ativo (VRA), via
dados.gov.br" (`DECISIONS.md`, ADR-0000).

## Como citar o painel de estimação do artigo

Bendinelli, W. E.; Bettini, H. F. A. J.; Oliveira, A. V. M. (dados de 2016;
publicação 2026). *Estimation panel of "Airline delays, congestion
internalization and non-price spillover effects of low cost carrier entry"*,
rota x mês, 2002-2013. Curado e publicado por W. E. Bendinelli. CC BY 4.0. DOI
a ser atribuído com o depósito no Zenodo. O artigo é Bendinelli, Bettini &
Oliveira (2016, *Transportation Research Part A* 85, 39-52, doi
10.1016/j.tra.2016.01.001).
