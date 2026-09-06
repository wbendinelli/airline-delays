# airline-delays

[![CI](https://github.com/wbendinelli/airline-delays/actions/workflows/ci.yml/badge.svg)](https://github.com/wbendinelli/airline-delays/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE)
[![Data: CC BY 4.0](https://img.shields.io/badge/data-CC%20BY%204.0-lightgrey.svg)](./LICENSE-CC-BY-4.0.md)
[![Article DOI](https://img.shields.io/badge/article%20DOI-10.1016%2Fj.tra.2016.01.001-blue.svg)](https://doi.org/10.1016/j.tra.2016.01.001)

> **Tier:** `C` · **Class:** `Research`

[English](README.md) · [Português](README.pt-BR.md)

Português (ADR-0006) -- a página principal, em inglês, é `README.md`.

**Voos domésticos regulares do Brasil, 2000-2013 -- dos registros brutos da
ANAC às tabelas de um artigo publicado, à sua teoria e a um preditor de atraso
por voo.**

## Visão geral

Entre 2000 e 2013, o mercado aéreo doméstico brasileiro cresceu depressa,
concentrou-se em poucos aeroportos e viu duas entrantes de baixo custo
redesenharem o mapa competitivo: a Gol em 2001 e a Azul em 2008 -- as duas
companhias que as dummies de baixo custo do artigo medem. Saber se o
congestionamento desses aeroportos é algo que as companhias internalizam --
voando menos quando o atraso que causam recai sobre elas mesmas -- ou algo que
a concorrência corrige tem consequências diretas para a alocação de slots, a
precificação aeroportuária e a análise de fusões. Bendinelli, Bettini &
Oliveira (2016, *Transportation Research Part A* 85, 39-52, doi
10.1016/j.tra.2016.01.001) trataram a questão com um painel rota x mês
construído a partir dos registros de etapas de voo, de tráfego e de tarifas da
ANAC e um desenho com variáveis instrumentais: a concentração nas cidades de
origem e destino acompanha atrasos menores das companhias de serviço completo,
a concentração na rota acompanha atrasos maiores, e a presença de uma companhia
de baixo custo numa cidade transborda para a pontualidade das incumbentes. Este
repositório abre os dados, o código e a teoria por trás desse artigo,
publicados pelo seu primeiro autor.

### Por que o congestionamento aeroportuário importa

Os voos domésticos regulares no universo da replicação -- tipos de linha N, R e
E, DI 0, todos os aeroportos -- passaram de 659.301 em 2000 para 984.956 em
2013, uma alta de 49,4 por cento. A crise de 2006-2007 -- dois acidentes fatais
e o apagão aéreo que se seguiu -- fez do congestionamento aeroportuário uma
questão de política nacional (`data/external/events.csv`). Duas hipóteses
concorrem: a companhia dominante internaliza o congestionamento que impõe aos
próprios voos, ou a rivalidade disciplina os atrasos melhor do que a
dominância.

### O que o artigo encontrou

| Estimador | `rthhi` (HHI da rota) | `maxcthhi` (HHI da cidade-extremo, o maior dos dois) | `lcc` (rota) | `maxalccfu` (cidades-extremo) | N |
|---|---|---|---|---|---|
| 2SGMM (artigo, Tabela 3, col. 2) | +0,819** (0,410) | -1,514*** (0,527) | -0,041 (0,072) | -0,423** (0,179) | 19.419 |
| MQO (artigo, Tabela 6, col. 2) | -0,313*** (0,068) | +0,106 (0,196) | -0,164*** (0,033) | -0,179 (0,137) | 19.590 |

Erros-padrão entre parênteses; os asteriscos são os níveis de significância do
artigo. O regressando é `ODDS`, o logaritmo das chances (*log-odds*) da
proporção de chegadas das companhias de serviço completo (TAM, grupo Varig,
Transbrasil, Vasp) com mais de quinze minutos de atraso na rota-mês. Depois de
instrumentar, um HHI maior na cidade-extremo mais concentrada acompanha chances
e minutos de atraso menores para as companhias de serviço completo -- o que o
artigo lê como a companhia dominante internalizando o próprio congestionamento
--, enquanto um HHI maior na rota acompanha chances e minutos maiores. Uma
companhia de baixo custo em qualquer das duas cidades-extremo reduz as chances
de atraso das companhias de serviço completo, o *spillover* não-preço do
título; sua presença na própria rota não é significativa para as chances e
entra com sinal positivo ao nível de dez por cento nas colunas de minutos
(artigo, Tabela 3, cols. 4 e 6). A inversão de sinal entre MQO e 2SGMM é uma
afirmação sobre as colunas `ODDS`.

### O que este repositório oferece

- **O painel reconstruído** -- `data/analysis/panel_route_month.parquet`:
  31.313 rotas-mês x 228 colunas, 310 rotas, 168 meses, 27 nós, construído a
  partir de 13.652.322 etapas de voo em 168 arquivos mensais.
- **O painel de estimação do artigo** -- o painel sobre o qual os autores
  estimaram as Tabelas 2-7, publicado aqui como
  `data/analysis/article_panel_route_month.parquet` (24.589 rotas-mês x 52
  colunas); as Tabelas 2-7 reestimadas em `reports/replication/`.
- **A teoria** -- o jogo de congestionamento em que o artigo se apoia,
  Brueckner e Van Dender (2008) tal como exposto na monografia de 2013 do
  autor, derivado simbolicamente: 29 identidades checadas e 11 figuras em
  `reports/theory/`.
- **O preditor de atraso** -- 10.200.560 voos programados, 46 variáveis de
  véspera, avaliado fora do período de treino em `reports/prediction/`.

Os dois painéis compartilham o universo, o mapa de nós e os conjuntos de
companhias registrados em `DECISIONS.md`; a reconstrução segue a convenção do
artigo onde o artigo a enuncia e declara a sua própria onde ele não o faz.

## Início rápido

Python 3.12 via `uv`. A menor reprodução roda sem rede, sobre a amostra de
teste versionada de 19.910 etapas de voo, em cerca de um segundo; a
reestimação das Tabelas 2-7 sobre o painel do artigo versionado leva menos de
um minuto.

```bash
git clone https://github.com/wbendinelli/airline-delays.git
cd airline-delays && uv sync
just demo       # amostra -> tabela-fato -> painel reconstruído -> Tabela 2, sem rede
just estimate   # Tabelas 2-7 reestimadas sobre o painel de estimação do artigo
```

## Reprodução

Uma máquina (16 GB de RAM, 10 núcleos) reconstrói tudo a partir dos arquivos
da ANAC, um ano por vez. Cada receita encapsula um comando de
`uv run airline-delays --help`; `just pipeline` roda os estágios de
`data/staged/` em diante, e `just pipeline-full` acrescenta o download, a
leitura dos arquivos brutos e a previsão.

| Estágio | Receita | Lê -> escreve | Tempo de execução |
|---|---|---|---|
| Ingestão | `just fetch` | os CSVs mensais da ANAC -> `data/raw/` (168 arquivos, 2,17 GB) e `data/raw/manifest.json` | 17,0 min |
| *Staging* | `just stage` | `data/raw/` -> `data/staged/year=YYYY/part-0.parquet`, 13.652.322 etapas de voo | um ano por vez |
| Referência | `just reference` | valida cada linha de `data/external/*.csv` | segundos |
| Tabela-fato | `just fact` | etapas *staged* -> `data/analysis/fact_group_route_month.parquet` e as duas projeções por cidade | 11 s |
| Painel | `just panel` | tabela-fato -> `data/analysis/panel_route_month.parquet`, `docs/dictionary.md`, `datapackage.json` | 8 s |
| Painel do artigo | `just article-panel` | a base dos autores -> `data/analysis/article_panel_route_month.parquet`, uma única vez, na máquina do primeiro autor | -- |
| Estimação | `just estimate` | painel do artigo -> `reports/replication/` | menos de um minuto |
| Previsão | `just predict-dataset`, `just predict` | etapas *staged* -> `data/derived/ml/` -> `reports/prediction/` | 25 s, depois 2.344 s |
| Teoria | `just theory` | `src/airline_delays/theory/` -> `reports/theory/` | cerca de um segundo |
| Relatórios | `just summary`, `just report` | os artefatos -> `reports/summary.json`; as fontes Typst -> `reports/pdf/` | segundos |

## Resultados em resumo

### Replicação

As Tabelas 2-7 reestimadas sobre o painel de estimação do artigo acompanham de
perto as tabelas publicadas, sem coincidir célula a célula; cada diferença é
medida em erros-padrão publicados:

| Tabela | Coeficientes | Mesmo sinal | Dentro de meio e.p. | Diferença mediana (e.p.) | Maior diferença (e.p.) |
|---|---|---|---|---|---|
| Tabela 3, 2SGMM | 60 | 60 | 53 | 0,24 | 0,69 |
| Tabela 4, robustez | 66 | 65 | 51 | 0,22 | 0,91 |
| Tabela 5, LIML | 60 | 59 | 53 | 0,23 | 0,67 |
| Tabela 6, MQO | 60 | 59 | 51 | 0,12 | 0,94 |
| Tabela 7, partidas | 60 | 59 | 51 | 0,24 | 0,66 |

Nas cinco tabelas, 306 coeficientes são comparados: 302 têm o sinal publicado,
259 (84,6 por cento) ficam a menos de meio erro-padrão publicado, e a maior
diferença é de 0,94 erro-padrão. A inversão de sinal em que se apoia o desenho
instrumental do artigo -- MQO e 2SGMM dão sinais opostos aos dois termos de HHI
nas colunas `ODDS` -- é um padrão sobre 12 comparações: as tabelas publicadas
invertem 4 delas, as 4 inversões se reproduzem, e o padrão coincide em 12 de
12. As amostras reestimadas têm 20.447-20.630 observações contra 19.408-19.590
publicadas, 5,3 por cento a mais. As 13 variáveis descritivas e as 91
correlações da Tabela 2 são recuperadas; a maior diferença absoluta numa
correlação é 0,012.

### Previsão

| Horizonte | Informação | AUC nas oito janelas de origem rolante, 2006-2013 |
|---|---|---|
| Véspera (D-1) | grade horária, calendário, agregados defasados de rota e aeroporto | 0,715-0,741 |
| No portão (H-1) | D-1 mais o atraso realizado da etapa anterior da aeronave | 0,757-0,824 |

O alvo é `late15_arr`, uma chegada com mais de quinze minutos de atraso, sobre
10.200.560 voos programados de 2000-2013, com 46 variáveis de véspera e 9
testes de vazamento. A prevalência de atrasos na rota no mês anterior marca
0,608-0,673 nas mesmas janelas. Nos 20-35% dos voos com etapa anterior
vinculada, o modelo de portão chega a 0,87-0,93.

### Teoria

As 29 identidades do jogo de congestionamento valem sob `sympy`, e 11 figuras
as desenham. Dois resultados que a derivação torna mais precisos: num
equilíbrio interior com a mesma tarifa, o mesmo imposto e os mesmos assentos
para as duas companhias, o líder de Stackelberg opera pelo menos o dobro dos
voos do seguidor sob custo de congestionamento convexo e exatamente o dobro sob
custo linear; e o pedágio ótimo do líder na alocação simétrica de primeiro
melhor é três quartos (0,75) do dano marginal de congestionamento sob custo
linear (no próprio equilíbrio de Stackelberg, é dois terços nesse caso).

## Disponibilidade dos dados

### Guia dos dados

**No git.** Os dois painéis, a tabela-fato, as duas projeções por cidade, as 13
tabelas externas curadas e os quatro manifestos: 636 colunas em 7 camadas,
definidas em inglês e em português em `docs/dictionary.md` e descritas como um
Frictionless Data Package em `datapackage.json`; `data/README.md` é o guia.
**Regenerado.** `data/raw/`, `data/staged/` e `data/derived/` são reconstruídos
a partir dos arquivos da ANAC por `just fetch && just stage` e
`just predict-dataset`; só o `README.md` de cada um e `data/raw/manifest.json`
são versionados. **Zenodo.** O *release* no GitHub arquiva o repositório com
suas tabelas curadas no Zenodo, que emite o DOI; até que ele exista, o selo
acima é o do artigo.

| Qual painel? | Use |
|---|---|
| Reestimar as Tabelas 2-7, ou partir da base final dos autores (as amostras de estimação publicadas são um subconjunto dela que os filtros registrados não reproduzem exatamente; ver Replicação) | o painel de estimação do artigo, `data/analysis/article_panel_route_month.parquet`: 2002-2013, 24.589 rotas-mês x 52 colunas |
| Estudar atrasos, concentração ou presença de baixo custo ao longo de toda a série, ou construir variáveis para previsão | o painel reconstruído, `data/analysis/panel_route_month.parquet`: 2000-2013, 31.313 rotas-mês x 228 colunas |

### Fontes

| Fonte | Detentor | Neste repositório |
|---|---|---|
| Voo Regular Ativo (VRA), arquivos mensais de etapas de voo 2000-2013 | ANAC, via dados.gov.br | Regenerados por `just fetch`; um sha256 por arquivo em `data/raw/manifest.json`; toda tabela derivada |
| IAC 1504 (códigos de justificativa, códigos DI, tipos de linha) | ANAC | Transcrita em `data/external/cause_codes.csv`, `di_codes.csv` e `line_types.csv` |
| O painel de estimação do artigo | A base dos autores, de dezembro de 2015 | Curado uma única vez em `data/analysis/article_panel_route_month.parquet` |
| Microdados tarifários e dados estatísticos | ANAC | A montante das variáveis de concentração e de baixo custo do painel do artigo; não redistribuídos como microdados |
| Geografia dos aeroportos | OurAirports | `data/external/airports_br.csv`, `nodes.csv` e `distances_km.csv` |
| Leis de feriados federais | Diário Oficial da União | `data/external/holidays.csv` e o `observances.csv` calculado |
| Capacidade aeroportuária, coordenação de slots, fusões | BNDES, ANAC, CADE | Linhas transcritas em `data/external/capacity.csv`, `slots.csv`, `groups.csv` e `events.csv` |
| Meteorologia METAR | DECEA, via REDEMET | Não integrada; o sinal meteorológico do artigo são os próprios códigos de justificativa do VRA |
| O artigo | Elsevier | Citado pelo DOI; suas células publicadas transcritas em `src/airline_delays/estimation/published.json` |
| A monografia de graduação do autor, de 2013 (USP) | O autor | Citada como documento externo; sua lista de aeroportos em `data/external/monograph_airports.csv` |

A declaração completa, detentor por detentor, é `docs/data-availability.md`. As
licenças seguem a camada: MIT para o código, CC BY 4.0 para texto e dados
curados, e os registros brutos são "ANAC, Voo Regular Ativo (VRA), via
dados.gov.br". Nos termos do Protocolo TIER, `data/raw/` são os dados
originais, `data/staged/` os dados importáveis, `data/analysis/` os dados de
análise, `src/` os arquivos de comando e `docs/dictionary.md` o apêndice de
dados.

## Para saber mais

O estudo -- o trabalho final que junta a economia do congestionamento
aeroportuário, o modelo de teoria dos jogos derivado passo a passo e as
hipóteses, os dados, a especificação, os resultados e a replicação do artigo --
está em `docs/study/`, escrito em português com resumo em inglês na página de
índice, e compila para `reports/pdf/study.pdf`. As notas de pesquisa por trás
das decisões estão em `docs/notes/`, e os três relatórios Typst (estudo,
replicação, previsão) com seus PDFs em `reports/`. Repositórios irmãos:
[citation-audit](https://github.com/wbendinelli/citation-audit) e
[sapians-research](https://github.com/wbendinelli/sapians-research).

## Citação

```bibtex
@article{bendinelli2016airline,
  title   = {Airline delays, congestion internalization and non-price spillover effects of low cost carrier entry},
  author  = {Bendinelli, William E. and Bettini, Humberto F. A. J. and Oliveira, Alessandro V. M.},
  journal = {Transportation Research Part A: Policy and Practice},
  volume  = {85},
  pages   = {39--52},
  year    = {2016},
  doi     = {10.1016/j.tra.2016.01.001}
}

@software{bendinelli2026airlinedelays,
  title   = {airline-delays: Brazil's scheduled domestic flights 2000-2013, from ANAC's raw
             records to a published article's tables, its theory, and a flight-level delay predictor},
  author  = {Bendinelli, William Eduardo},
  year    = {2026},
  url     = {https://github.com/wbendinelli/airline-delays},
  version = {1.1.0}
}
```

`CITATION.cff` traz as duas entradas. O painel de estimação como conjunto de
dados: Bendinelli, W. E.; Bettini, H. F. A. J.; Oliveira, A. V. M. (dados de
2016; publicação 2026). *Estimation panel of "Airline delays, congestion
internalization and non-price spillover effects of low cost carrier entry"*,
rota x mês, 2002-2013. Curado e publicado por W. E. Bendinelli. CC BY 4.0. DOI
a ser atribuído com o depósito no Zenodo.

## Licença

MIT para o código (`src/`, `scripts/`, `tests/`, `.github/`), em `LICENSE`. CC
BY 4.0 para texto e dados curados -- esta página, `docs/`, a prosa de
`reports/`, os dois painéis, a tabela-fato, as projeções por cidade e
`data/external/` --, em `LICENSE-CC-BY-4.0.md`. Os registros brutos do VRA são
da ANAC, redistribuídos com a atribuição "ANAC, Voo Regular Ativo (VRA), via
dados.gov.br".

## Uso e limites

Um conjunto de dados de pesquisa para 2000-2013: sustenta replicação, extensão
e trabalho metodológico sobre essa janela, não previsão em tempo real, e os
códigos de justificativa da IAC 1504 em que se apoia foram aposentados por
volta de 2020. Construído só a partir do VRA, o painel reconstruído não traz os
termos de concentração ponderados por passageiros do artigo (`rthhi`,
`maxcthhi`), a dummy de codeshare (`cshare`), as contagens de congestionamento
por capacidade declarada (`dailyflcong`, `dailyflncong`), o máximo de atraso
das cidades da rota (`maxprdel`) nem os sete instrumentos (`h1_maxcthhi`,
`h2_maxcthhi`, `h2_rthhi`, `h3_maxcthhi`, `l1h1_maxcthhi`, `l1h2_maxcthhi`,
`lnh1_maxcthhi`); esses vivem no painel de estimação do artigo. Todo número
desta página é impresso por `airline-delays summary` em `reports/summary.json`.
