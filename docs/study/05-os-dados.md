# Os dados: do registro de voo ao painel rota × mês

Português (ADR-0006).

Este capítulo percorre o caminho dos dados: do registro de uma etapa de voo
nos arquivos públicos da ANAC ao painel rota × mês sobre o qual Bendinelli,
Bettini & Oliveira (2016, *Transportation Research Part A* 85, 39-52, doi
10.1016/j.tra.2016.01.001) estimaram as Tabelas 2–7. Ao terminá-lo, o leitor
sabe o que uma etapa de voo carrega e o que os dois layouts dos arquivos
mudam; como o repositório lê o horário realizado vazio dos arquivos antigos;
qual é o universo de voos, quais são os 27 nós e como um atraso é medido e
truncado; como as empresas viram grupos e conjuntos; como a tabela-fato e o
painel reconstruído são construídos; o que é o painel de estimação do artigo,
coluna a coluna; o que o painel reconstruído não traz, e por quê; e o que liga
os dois painéis. Daqui em diante, "o artigo". Toda definição deste capítulo é
uma decisão registrada em `DECISIONS.md`; todo número é um valor de
`reports/summary.json` ou de um manifesto de `data/analysis/`, com a chave
nomeada ao lado.

## 1. O registro de voo

O VRA — Voo Regular Ativo — é o registro operacional da ANAC. Ele junta o
horário aprovado (HOTRAN) e os Boletins de Alteração de Voo que as empresas
registram sob a IAC 1504. Uma linha é uma etapa de voo: a empresa (código
ICAO), o número do voo, o código de autorização DI, o tipo de linha, o
aeródromo de origem e o de destino, a partida e a chegada previstas, a partida
e a chegada realizadas, a situação do voo e um código de justificativa quando
houve alteração. O repositório baixa os 168 arquivos mensais de 2000 a 2013 —
2,17 GB (`reconstruction.raw.files`, `raw.gigabytes`) — em cerca de 17 minutos
(`raw.fetch_minutes`) e registra o sha256 de cada um em `data/raw/manifest.json`.
Os arquivos brutos não entram no git nem no depósito do Zenodo: qualquer
leitor os refaz com `just fetch`, e os hashes provam que são os mesmos
([apendice-c-direitos-e-licencas.md](apendice-c-direitos-e-licencas.md)).

Os arquivos não têm um layout, têm dois. Até 2009 cada linha traz 12 campos
separados por vírgula; de 2010 em diante, 20 campos separados por ponto e
vírgula, em outra ordem e com o aeroporto de destino entre os horários de
partida e os de chegada. O código de justificativa também muda de natureza:
código de duas letras até 2009, descrição por extenso depois, que o staging
remapeia para os 49 códigos do anexo 2 da IAC 1504 (`external.cause_codes`). A
tabela resume o que `airline-delays layouts` mede no primeiro arquivo de cada
ano (`docs/notes/staging.md`, seção 1).

| Anos | Layout | Campos | Separador | Codificação | Justificativa |
|---|---|---|---|---|---|
| 2000–2009 | `legacy_12col` | 12 | vírgula | latin-1 | código de duas letras |
| 2010–2013 | `wide_20col` | 20 | ponto e vírgula | UTF-8 | texto livre, remapeado ao código |

O staging (`just stage`, um ano por vez) traz os dois layouts para um só
esquema de 32 colunas (`registry.columns_by_layer.staged`), gravado em
`data/staged/year=AAAA/part-0.parquet`: 13.652.322 etapas de voo em 14
partições anuais (`reconstruction.staged.rows`, `staged.partitions`). As
colunas se agrupam em seis famílias; a definição de cada uma está na camada
`staged` de `docs/dictionary.md`.

| Família | Colunas |
|---|---|
| identidade da etapa | `airline`, `flight_number`, `line_type`, `di`, `status`, `cause_code` |
| geografia | `origin_icao`, `dest_icao`, `origin_node`, `dest_node`, `route` |
| horários | `sched_dep`, `actual_dep`, `sched_arr`, `actual_arr` |
| calendário | `flight_date`, `year`, `month`, `ym`, `dep_hour`, `arr_hour`, `dow` |
| medidas derivadas | `dep_delay_min`, `arr_delay_min`, `sched_block_min`, `actual_block_min`, `actual_time_suspect` |
| grupo, classe e universo | `group`, `class`, `universe_repl`, `universe_ml`, `is_realized` |

Três coisas o staging não faz, por decisão. Não imputa horário realizado: o
campo vazio fica nulo, e o atraso construído sobre ele também. Não corta
outlier: o corte é da camada de análise (ADR-0008). Não descarta aeroporto:
voos internacionais e aeródromos fora das capitais ficam na base, fora do
universo de replicação e presentes como contexto.

## 2. O horário realizado vazio (ADR-0012)

Nos arquivos de 2000–2009 um voo realizado sem ocorrência vem com a partida e
a chegada realizadas vazias. A tabela mede isso ano a ano, sobre os voos do
universo de replicação (`reports/summary.json`, `reconstruction.flights_by_year`;
`data/analysis/manifest.json`, `missing_actual_by_year`).

| Ano | Voos programados | Voos realizados | Realizados sem chegada registrada | Parcela |
|---|---|---|---|---|
| 2000 | 659.301 | 587.007 | 470.274 | 80,1% |
| 2001 | 691.582 | 610.676 | 462.913 | 75,8% |
| 2002 | 678.949 | 564.375 | 433.947 | 76,9% |
| 2003 | 565.672 | 431.646 | 332.415 | 77,0% |
| 2004 | 536.555 | 456.323 | 345.947 | 75,8% |
| 2005 | 552.056 | 476.192 | 337.941 | 71,0% |
| 2006 | 588.640 | 493.853 | 339.684 | 68,8% |
| 2007 | 641.635 | 513.081 | 303.510 | 59,2% |
| 2008 | 663.781 | 600.121 | 420.910 | 70,1% |
| 2009 | 756.194 | 686.216 | 533.389 | 77,7% |
| 2010 | 874.236 | 796.922 | 146 | 0,02% |
| 2011 | 983.073 | 898.923 | 145 | 0,02% |
| 2012 | 1.023.977 | 942.587 | 115 | 0,01% |
| 2013 | 984.956 | 894.671 | 11 | 0,001% |

A quebra entre 2009 e 2010 é a mudança de layout, não de pontualidade. O que
o campo vazio significa está registrado como decisão. A ADR-0012 fixa a
convenção sobre a qual as tabelas do artigo se apoiam: um horário realizado
vazio é lido como voo pontual — horário realizado igual ao previsto, atraso
zero —, e o sinal de um atraso medido segue a ADR-0008. No repositório essa
leitura é um parâmetro nomeado, `empty_actual_means_on_time`: `True` no painel
reconstruído, que assim segue a convenção do artigo, e `False` em todo o
resto. O valor vigente viaja com a tabela — o painel reconstruído carrega
`empty_actual_means_on_time = 1` em toda linha — e com o manifesto
(`data/analysis/manifest.json`). A camada de previsão lê o mesmo campo por
outra decisão, a ADR-0017, descrita no
[apendice-a-previsao-de-atrasos.md](apendice-a-previsao-de-atrasos.md).

O parâmetro faz uma coisa só. A tabela-fato guarda lado a lado as chegadas com
horário realizado (`arr_delay_obs`) e as realizadas sem horário
(`arr_missing_actual`); o parâmetro escolhe o denominador das proporções e das
médias (`delay_denominator()`, em `src/airline_delays/fact/projections.py`).
Sob `True` o voo sem ocorrência entra no denominador e não no numerador, que é
exatamente "operou no horário"; sob `False` a ausência não é dado. Nenhuma
contagem de voos atrasados e nenhuma soma de minutos muda entre as duas
leituras — um voo lido como zero minuto não está "acima de 15" e soma zero —,
e um teste fixa isso (`tests/test_fact.py`).

## 3. O universo e os 27 nós (ADR-0002, ADR-0001)

O universo de replicação é o do `f` do artigo: voos programados dos tipos de
linha N, R e E, com DI 0, realizados e cancelados; `prcanc = fl_can / f` é a
parcela cancelada. Voos extras (DI 1 e 2) e de retorno (DI 3) ficam fora de
`f` e entram no painel reconstruído como contexto (`n_extra`, `n_return`,
`n_off_universe`): ocupam a mesma pista na mesma hora sem contar como oferta
programada. O universo de previsão é o mesmo, restrito aos voos realizados
(`universe_ml`).

A unidade geográfica é o nó, não o aeroporto. O `f` do artigo é uma contagem
metropolitana: São Paulo é Congonhas, Guarulhos e Viracopos juntos, embora a
base tarifária rotule Viracopos como "Campinas" (ADR-0001). Os 27 nós são as
24 capitais de um aeroporto mais três áreas metropolitanas, mapeados em
`data/external/nodes.csv` (31 linhas, `external.nodes`). Toda tabela de voo
carrega `origin_icao` e `dest_icao` ao lado dos nós, e um desenho por
aeroporto não exige reextrair nada
([apendice-d-extensoes.md](apendice-d-extensoes.md), seção 7).

| Nó | Aeroportos | Cidade |
|---|---|---|
| `MRSP` | SBSP, SBGR, SBKP | São Paulo |
| `MRRJ` | SBGL, SBRJ | Rio de Janeiro |
| `MRBH` | SBBH, SBCF | Belo Horizonte |
| os 24 nós de um aeroporto | SBAR, SBBE, SBBR, SBBV, SBCG, SBCT, SBCY, SBEG, SBFL, SBFZ, SBGO, SBJP, SBMO, SBMQ, SBNT, SBPA, SBPJ, SBPV, SBRB, SBRF, SBSL, SBSV, SBTE, SBVT | Aracaju, Belém, Brasília, Boa Vista, Campo Grande, Curitiba, Cuiabá, Manaus, Florianópolis, Fortaleza, Goiânia, João Pessoa, Maceió, Macapá, Natal, Porto Alegre, Palmas, Porto Velho, Rio Branco, Recife, São Luís, Salvador, Teresina, Vitória |

Uma rota é um par direcional de nós. A tabela-fato cobre todas as rotas do
universo; o painel reconstruído fica com as rotas entre os 27 nós
(`panel_nodes_only`, em `src/airline_delays/panel/build.py`) — 310 rotas
(`reconstruction.panel.routes`). O painel de estimação do artigo tem 209
(`article_panel.routes`), sobre os mesmos 27 nós.

## 4. O atraso: sinal, limiar e outliers (ADR-0008, ADR-0015)

O atraso de uma etapa é a diferença entre o horário realizado e o previsto, em
minutos, com sinal: uma chegada adiantada é um atraso negativo, e a média de
minutos a vê assim (`arr_delay_min`, `dep_delay_min`). O artigo conta como
atrasado o voo que chega com mais de 15 minutos além do previsto — a convenção
norte-americana —, e é sobre essa contagem que se constroem a proporção
`fsc_prdelarr` e o seu log da razão de chances, `fsc_oddsarr`, o regressando
principal (capítulo 6,
[06-especificacao-e-identificacao.md](06-especificacao-e-identificacao.md)). A
ANAC apura os seus próprios percentuais no corte de 30 minutos, sob a
Resolução ANAC nº 218; o painel reconstruído publica esse corte como variante,
`fsc_prdelarr30m`.

Para contagens por limiar o sinal é irrelevante: "mais de 15 minutos" é o
mesmo teste com ou sem truncar a antecipação em zero. Para somas de minutos
não é, e o painel reconstruído publica as duas convenções: `fsc_minsarr` com
sinal e `fsc_minsarr_trunc` truncada em zero, idem na partida.

O limiar de outlier é um parâmetro nomeado com valor 313,25 minutos
(`reconstruction.fact.outlier_threshold_min`; ADR-0008). A ADR-0015 o aplica
ao valor absoluto do atraso em toda soma, média e parcela de minutos, porque
os arquivos brutos trazem erros de digitação de mês nos horários realizados —
atrasos de milhares de minutos negativos, que um corte unilateral deixaria
passar. As contagens `*_outliers` ficam ao lado para que qualquer média possa
ser refeita com ou sem eles. Uma segunda marca, `actual_time_suspect`,
assinala no staging a etapa cujo atraso de partida ou de chegada tem valor
absoluto de um dia civil ou mais (1.440 minutos); a camada de previsão a
exclui dos alvos, e a de análise nunca a vê numa soma de minutos, porque o
corte simétrico a remove antes. As contagens de voos atrasados nos limiares de
0, 15, 30 e 60 minutos não dependem de nenhum dos dois parâmetros.

## 5. Grupos, classes e os conjuntos de empresas do artigo (ADR-0003, ADR-0011, ADR-0013)

`data/external/groups.csv` é uma tabela datada ao mês — `airline, group,
start, end, class` — com 50 linhas (`external.groups`), cada uma com fonte,
URL e grau de confiança, validada por `just reference`. O `group` de uma etapa
é o grupo econômico da empresa na data do voo; a classe — FSC, LCC, regional
ou `other` — segue o grupo absorvedor depois de uma fusão. A tabela codifica o
agrupamento do artigo.

| Empresa (códigos ICAO) | Grupo e classe | Transição |
|---|---|---|
| Varig e os códigos do grupo (VRG, VLO, VRN, NES, RSL) | Varig, FSC, até 2007-03 | Gol, LCC, de 2007-04 |
| Gol (GLO) | Gol, LCC, de 2001-01 | — |
| Webjet (WEB) | Webjet, LCC independente, de 2005-07 a 2011-10 | Gol, LCC, de 2011-11 |
| Azul (AZU) | Azul, LCC, de 2008-12 | — |
| Trip (TIB) | Trip, regional, até 2012-04 | Azul, LCC, de 2012-05 |
| Total (TTL) | Total, regional, até 2007-10 | Trip, regional, de 2007-11; Azul, LCC, de 2012-05 |
| Pantanal (PTN) | Pantanal, regional, até 2009-11 | TAM, FSC, de 2009-12 |
| TAM e os códigos do grupo (TAM, BLC, SUL) | TAM, FSC | — |
| Transbrasil (TBA, ITB) | Transbrasil, FSC, até 2001-12 | — |
| Vasp (VSP) | Vasp, FSC, até 2005-01 | — |
| Avianca Brasil, antes Oceanair (ONE) | Avianca Brasil, FSC | — |
| Passaredo (PTB) | Passaredo, regional | — |
| os demais códigos | o próprio código como grupo, classe `other` (ADR-0011) | — |

Os conjuntos do artigo não são as classes. O conjunto FSC do artigo — as
empresas cujo atraso é o regressando — são os grupos TAM, Varig até 2007-03,
Transbrasil e Vasp (`ARTICLE_FSC_GROUPS`, em
`src/airline_delays/definitions/carriers.py`; ADR-0013); a classe FSC da
ADR-0003 inclui também a Avianca Brasil. O "LCC" do artigo são os grupos Gol e
Azul (`ARTICLE_LCC_GROUPS`); a classe LCC inclui a Webjet enquanto
independente. O painel reconstruído calcula e publica as duas versões, sob
nomes distintos: `fsc_*` e `lccfu_*` pelo conjunto do artigo, `fscc_*` e
`lccclass_*` pela classe. Nenhuma foi ajustada para a outra. Empresa sem
rótulo na tabela é `other`, nunca nula (ADR-0011): descartá-la encolheria o
denominador de toda proporção, e chamá-la de regional seria uma afirmação
sobre modelo de negócio que ninguém conferiu.

## 6. As causas de atraso (ADR-0005)

O código de justificativa da IAC 1504 diz por que um voo foi alterado. O
artigo o usa em três parcelas de voos por rota-mês, e o repositório as mantém
exatamente como são (`ARTICLE_SETS`, em
`src/airline_delays/definitions/cause_codes.py`), com uma segunda taxonomia ao
lado, para quem quiser separar o que o artigo juntou.

| Coluna do artigo | O que mede | Códigos |
|---|---|---|
| `prwheather` | o conjunto meteorologia-e-aeroporto-restrito do artigo; o código dominante é AR, aeroporto com restrições operacionais | AI, AJ, AM, AR, RI, RM, WA, WO, WR, WT, XI, XJ, XM, XO, XS, XT |
| `princident` | incidentes e falhas técnicas | DF, DG, HB, MA, TD |
| `pr_connc` | rotação de aeronave, que o artigo lê como espera por passageiros em conexão | RA |

A grafia `prwheather` é a do artigo e não é corrigida: a coluna existe para
ser comparada com a publicada. A segunda taxonomia tem sete categorias —
meteorologia; aeroporto fechado ou restrito; rotação de aeronave; técnica;
operacional e tráfego aéreo; autorizada; outra — e está em
`data/external/cause_codes.csv`, uma linha por código, e em
`docs/dictionary.md`.

## 7. A tabela-fato e o painel reconstruído (ADR-0004, ADR-0016)

Há um grão canônico, e todo o resto é projeção dele. A tabela-fato é `grupo ×
rota × mês` no universo de replicação: 165.763 células × 87 colunas
(`reconstruction.fact.rows`, `fact.columns`), construídas em 10,97 s por
`just fact` (`fact.seconds`), numa varredura por ano civil do voo. Ela
carrega as chaves, as contagens de voos (`flights` = realizados + cancelados =
o `f` do artigo), as famílias simétricas de partida e chegada — observações,
atrasos acima de 0, 15, 30 e 60 minutos, antecipações, outliers, somas de
minutos —, o bloco programado e o realizado, as sete categorias de causa e os
três conjuntos do artigo, os motivos de cancelamento e 24 contagens horárias.
Estatísticas de ordem — mediana, p90 — não somam e são recalculadas dos voos
em cada grão; é por isso que a convenção da ADR-0012 é parâmetro de
`build_fact()` (`src/airline_delays/fact/build.py`) e não uma decisão
implícita.

`aggregate()` (`src/airline_delays/fact/projections.py`) projeta a tabela-fato
em três grãos, e um teste de aditividade confere que a soma da projeção bate
com a contagem direta sobre os voos (`tests/test_fact.py`). As chaves são
únicas por construção e por teste (ADR-0016): `(group, route, ym)` na
tabela-fato, `(route, ym)` no painel.

| Tabela | Grão | Linhas × colunas | Chave em `reports/summary.json` |
|---|---|---|---|
| `data/analysis/fact_group_route_month.parquet` | grupo × rota × mês | 165.763 × 87 | `reconstruction.fact` |
| `data/analysis/panel_route_month.parquet` | rota × mês: o painel reconstruído | 31.313 × 228 | `reconstruction.panel` |
| `data/analysis/city_month.parquet` | nó × mês | 21.231 × 91 | `reconstruction.city_month` |
| `data/analysis/airline_city_month.parquet` | grupo × nó × mês | 49.801 × 81 | `reconstruction.airline_city_month` |

O painel reconstruído é a projeção rota × mês acrescida do que só existe nesse
grão: 31.313 rota-meses × 228 colunas, 310 rotas, 168 meses de 2000-01 a
2013-12, 27 nós (`reconstruction.panel.rows`, `columns`, `routes`, `months`,
`ym_range`, `nodes`), construído em 7,63 s por `just panel` (`panel.seconds`).
Três blocos convivem nele, e os nomes dizem qual é qual
(`src/airline_delays/panel/build.py`). O bloco do artigo traz as colunas do
artigo com os nomes do artigo, calculadas do VRA sob as definições do artigo —
`f`, `fl_can`, `fsc_prdelarr`, `fsc_oddsarr`, `prwheather`, `lcc`,
`maxalccfu` e as demais da seção 9. O bloco de variantes existe onde o
repositório oferece uma segunda definição documentada ao lado da do artigo:
`fscc_*` pela classe FSC, `*_trunc` pelo atraso truncado. O bloco de novas
colunas é tudo o que o artigo não usou: estrutura de mercado sobre voos
(`hhi_flights`, `rthhi_flights`, `maxcthhi_flights`, `sh_leader`, `n_groups`),
forma da malha, a taxonomia de causas, recuperação em voo e folga de bloco, os
agregados de cidade nas duas pontas e o proxy de congestionamento da ADR-0007
— dentro de um nó e de um ano, é congestionada a dia-hora igual ou acima do
percentil 90 da própria distribuição de movimentos do nó
(`docs/notes/features.md`, seção 5).

Toda coluna de toda tabela tem uma entrada em
`src/airline_delays/schema/columns.py`, o registro do qual `docs/dictionary.md`
e `datapackage.json` são renderizações; nenhuma coluna existe fora dele.

| Camada do registro | Tabela | Colunas |
|---|---|---|
| `staged` | etapas de voo | 32 |
| `fact` | grupo × rota × mês | 87 |
| `city` | nó × mês | 91 |
| `airline_city` | grupo × nó × mês | 81 |
| `panel` | o painel reconstruído | 228 |
| `article_panel` | o painel de estimação do artigo | 52 |
| `ml` | a tabela de modelagem por voo (Apêndice A) | 65 |

Sete camadas e 636 colunas (`registry.layers`, `registry.columns_total`,
`registry.columns_by_layer`).

## 8. O painel de estimação do artigo (ADR-0020)

As Tabelas 2–7 foram estimadas sobre um painel rota × mês que os autores
fecharam em dezembro de 2015: um arquivo Stata de 24.589 rota-meses e 1.829
variáveis, com carimbo de cabeçalho de 2015-12-03
(`article_panel.rows_in_source`, `variables_in_source`,
`source_header_timestamp`). O primeiro autor do artigo, autor deste
repositório, detém essa base e a curou uma vez, com
`airline-delays article-panel` na sua própria máquina, para
`data/analysis/article_panel_route_month.parquet` e o mesmo conteúdo em
`.csv.gz`, sob CC BY 4.0, com os três autores creditados em toda citação
(ADR-0020; [apendice-c-direitos-e-licencas.md](apendice-c-direitos-e-licencas.md)).
O resultado é o painel de estimação do artigo: 24.589 rota-meses × 52 colunas,
209 rotas direcionais, 144 meses de 2002-01 a 2013-12 (`article_panel.rows`,
`columns`, `routes`, `months`, `ym_range`). Curar não é transformar: nenhum
valor foi arredondado, imputado ou truncado; os tipos foram apertados só onde
a conversão é comprovadamente sem perda; a unicidade de `(od, ym)` e as
identidades das binárias compostas são afirmadas, não presumidas
(`src/airline_delays/estimation/article_panel.py`).
`data/analysis/article_panel_manifest.json` registra o sha256 e o carimbo da
base de origem, os nulos por coluna e o sha256 dos dois arquivos publicados —
nunca um caminho.

As 52 colunas são uma lista explícita, a camada `article_panel` do registro,
em sete famílias. A definição de cada uma está em `docs/dictionary.md`.

| Família | Colunas | O que são |
|---|---|---|
| chaves e geografia | `od`, `ym`, `year`, `month`, `o`, `d`, `o_uf`, `d_uf`, `o_region`, `d_region`, `km`, `ndays` | a rota direcional nos 27 nós, o mês, as duas pontas, as regiões de que as dummies sazonais são reconstruídas, a distância e os dias do mês |
| volumes | `f`, `fl_can`, `fl_odel`, `fl_ddel`, `prcanc`, `dailyfl` | os voos programados de que toda parcela é construída, os cancelados, os atrasados e os voos por dia |
| regressandos | `fsc_prdelarr`, `fsc_prdeldep`, `fsc_oddsarr`, `fsc_minsarr`, `fsc_minsp15arr`, `fsc_oddsdep`, `fsc_minsdep`, `fsc_minsp15dep` | as duas proporções e os seis regressandos das Tabelas 3–7 |
| exógenos | `maxprdel`, `prwheather`, `princident`, `pr_connc`, `dailyflcong`, `dailyflncong`, `cshare`, `lcc`, `maxalccfu` | os nove regressores exógenos, inclusive as duas binárias de baixo custo |
| concentração e congestionamento | `rthhi`, `maxcthhi`, `gmchhi`, `prcongested` | os dois termos endógenos, o termo alternativo de cidade e a parcela de voos em horas congestionadas |
| instrumentos | `h1_maxcthhi`, `h2_maxcthhi`, `h3_maxcthhi`, `lnh1_maxcthhi`, `l1h1_maxcthhi`, `l1h2_maxcthhi`, `h2_rthhi` | os sete instrumentos do tipo Hausman, construção espacial dos autores |
| componentes das binárias de baixo custo | `pres_glo`, `pres_azu`, `pres_tam`, `pres_web`, `olccfu`, `dlccfu` | a venda de bilhetes por empresa na rota e a presença de baixo custo em cada ponta |

Seis colunas têm nulos, e cada nulo tem uma razão definicional
(`data/analysis/article_panel_manifest.json`, `nulls`).

| Coluna | Nulos | Razão |
|---|---|---|
| `fsc_prdelarr`, `fsc_prdeldep` | 3.043 e 3.043 | a proporção não existe sem chegada ou partida de empresa de serviço completo na rota-mês |
| `fsc_oddsarr` | 3.934 | o log da razão de chances não existe quando a proporção é 0 ou 1 |
| `fsc_oddsdep` | 3.937 | idem, nas partidas |
| `l1h1_maxcthhi`, `l1h2_maxcthhi` | 308 e 308 | a primeira defasagem não existe no primeiro mês de cada rota no painel |

O que não foi publicado também é uma lista. As dummies geradas — os efeitos
fixos de rota e de tempo e as dummies sazonais região × mês — são
reconstruídas pelo código quando a estimação roda
(`src/airline_delays/estimation/loader.py`; capítulo 6) e não viajam com o
painel. Toda variável de fonte não aberta fica fora: a cessão de dados
meteorológicos, o relatório do operador aeroportuário, os preços e as receitas
dos microdados tarifários (`docs/data-availability.md`, fontes 4, 9 e 13). E a
contabilidade interna da base.

## 9. O que o painel reconstruído não traz, e por quê

O painel reconstruído traz, sob o mesmo nome e a mesma definição, as contagens
(`f`, `fl_can`, `fl_odel`, `fl_ddel`, `dailyfl`, `ndays`, `prcanc`), os seis
regressandos e as duas proporções, as três parcelas de causa, as binárias de
baixo custo (`lcc`, `olccfu`, `dlccfu`, `maxalccfu`) e as de presença
(`pres_glo`, `pres_azu`, `pres_tam`) — as duas últimas famílias lidas da
operação registrada no VRA, e não da venda de bilhetes, que é outra medida sob
o mesmo nome (`docs/notes/features.md`, seção 6). As colunas do modelo do
artigo que ele não traz com valor são a lista
`reconstruction.article_columns_missing` de `reports/summary.json`,
renderizada abaixo na ordem em que o arquivo a imprime. A razão é sempre a
fonte, nunca a definição.

| Coluna | O que é | O que a traria |
|---|---|---|
| `cshare` | acordo de codeshare na rota | uma tabela de acordos de codeshare por rota-mês |
| `dailyflcong` | voos por dia nas horas congestionadas | as declarações sazonais de capacidade da ANAC (`docs/data-availability.md`, fonte 6; ADR-0007) |
| `dailyflncong` | voos por dia nas horas não congestionadas | idem |
| `h1_maxcthhi` | instrumento | os HHI de passageiros de que deriva (fonte 3) |
| `h2_maxcthhi` | instrumento | idem |
| `h2_rthhi` | instrumento | idem |
| `h3_maxcthhi` | instrumento | idem |
| `l1h1_maxcthhi` | instrumento | idem |
| `l1h2_maxcthhi` | instrumento | idem |
| `lnh1_maxcthhi` | instrumento | idem |
| `maxcthhi` | HHI de passageiros da cidade-extremo mais concentrada | os dados estatísticos da ANAC, passageiros pagos por empresa-rota-mês (fonte 3) |
| `maxprdel` | a maior proporção de voos atrasados nas duas cidades-extremo | a definição exata do artigo; o painel traz `maxprdel_proxy` sob outro nome |
| `rthhi` | HHI de passageiros da rota | fonte 3 |

Os dois HHI de passageiros existem no painel reconstruído e são inteiramente
nulos, como `gmchhi` e `prcongested`: `passenger_weighted_hhi()`
(`src/airline_delays/definitions/concentration.py`) tem a assinatura certa e
devolve nulo até a fonte 3 ser coletada; as versões sobre participação em voos
vão ao lado sob nome próprio, `rthhi_flights` e `maxcthhi_flights`. O
congestionamento por capacidade declarada espera a fonte 6:
`data/external/capacity.csv` tem uma linha (`external.capacity`), Congonhas, e
uma linha não sustenta um painel nacional — daí o proxy interno da ADR-0007. As
Tabelas 2–7 não esperam por nada disso: `just estimate` roda sobre o painel de
estimação do artigo, que traz as treze colunas.

## 10. Os dois painéis: as mesmas definições

| | O painel reconstruído | O painel de estimação do artigo |
|---|---|---|
| arquivo | `data/analysis/panel_route_month.parquet` | `data/analysis/article_panel_route_month.parquet` |
| origem | os 168 arquivos do VRA, pela cadeia deste capítulo | a base final dos autores, dezembro de 2015, curada uma vez (ADR-0020) |
| rota-meses × colunas | 31.313 × 228 | 24.589 × 52 |
| rotas; meses | 310; 168, de 2000-01 a 2013-12 | 209; 144, de 2002-01 a 2013-12 |
| nós | os 27 da ADR-0001 | os mesmos 27 |
| tamanho do parquet | 9.941.210 bytes | 2.202.177 bytes |
| papel | a base aberta estendida e a entrada do preditor | a entrada única de `just estimate` |
| chave em `reports/summary.json` | `reconstruction.panel` | `article_panel` |

O que liga os dois é o conjunto de definições registrado em `DECISIONS.md` e
reenunciado pelo primeiro autor do artigo: o universo de voos (ADR-0002), o
mapa de nós (ADR-0001), os conjuntos de empresas (ADR-0003 com ADR-0013), a
taxonomia das causas (ADR-0005), o sinal e o corte do atraso (ADR-0008 com
ADR-0015) e a leitura do horário realizado vazio (ADR-0012). Onde o artigo
enuncia uma regra, o painel reconstruído a segue; onde não enuncia, ele
declara a sua e a publica sob nome próprio (ADR-0007, ADR-0015). Quem compara
uma coluna `fsc_*` entre os dois painéis compara a mesma definição sobre duas
leituras dos mesmos arquivos brutos, colhidos em datas diferentes — a base dos
autores em 2015, o VRA em 2026-09-05 (`data/raw/manifest.json`).

## Escopo e próximos passos

Este capítulo descreve os dados e as definições; não estima nada. O passo
seguinte é o capítulo 6, que escreve a especificação sobre as 52 colunas da
seção 8 — regressandos, regressores, instrumentos, dummies reconstruídas e
estimadores —, e o capítulo 7
([07-resultados-e-replicacao.md](07-resultados-e-replicacao.md)), que
reestima as Tabelas 2–7 sobre o painel de estimação do artigo. Para o painel
reconstruído, o passo de maior alcance é a fonte 3 de
`docs/data-availability.md`: com ela entram os dois HHI de passageiros e,
deles, os sete instrumentos ([apendice-d-extensoes.md](apendice-d-extensoes.md),
seção 2).

## Onde conferir

- `reports/summary.json` — `reconstruction.raw`, `staged`, `fact`, `panel`,
  `city_month`, `airline_city_month`, `flights_by_year`,
  `article_columns_missing`; `article_panel`; `registry`; `external`.
- `data/analysis/manifest.json` (`missing_actual_by_year`,
  `empty_actual_means_on_time`, `outlier_threshold_min`),
  `data/analysis/panel_manifest.json` e
  `data/analysis/article_panel_manifest.json` (`source`, `nulls`, `files`).
- `docs/dictionary.md` — as camadas `staged`, `panel` e `article_panel`,
  renderizadas de `src/airline_delays/schema/columns.py` por
  `airline-delays dictionary`.
- `data/external/nodes.csv`, `data/external/groups.csv` e
  `data/external/cause_codes.csv` — os mapas de nós, grupos e causas,
  validados por `just reference`.
- `docs/notes/staging.md` e `docs/notes/features.md` — as notas de pesquisa do
  staging e da construção da tabela-fato e do painel.
- `DECISIONS.md` — ADR-0001, 0002, 0003, 0004, 0005, 0007, 0008, 0011, 0012,
  0013, 0015, 0016, 0017 e 0020.
