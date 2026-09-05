# Do modelo às hipóteses: o que o artigo de 2016 foi testar

Português (ADR-0006). Este capítulo faz a passagem da teoria ao teste. O leitor
sai sabendo como os três objetos do jogo do capítulo 3 — a parcela do dano
marginal que uma empresa internaliza, o poder de mercado na rota e no
aeroporto, e a entrante de baixo custo — viram hipóteses com sinal esperado; em
que regressor de Bendinelli, Bettini & Oliveira (2016, *Transportation Research Part A* 85, 39-52, doi 10.1016/j.tra.2016.01.001) cada hipótese foi parar e
com que sinal e estrelas saiu publicada; por que a concentração é endógena ao
atraso e por que a resposta do artigo foi instrumentar; e onde cada variável do
modelo vive no registro de colunas deste repositório. Daqui em diante, "o
artigo". A regra de proveniência é uma só: todo coeficiente publicado vem de
`src/airline_delays/estimation/published.json`, lido pela ponte `bridge` de
`reports/theory/model.json`, e é citado como "(artigo, Tabela N)"; todo número
do modelo vem do mesmo `model.json`; nada é reestimado aqui — a replicação é o
capítulo 7 ([07-resultados-e-replicacao.md](07-resultados-e-replicacao.md)). A
monografia de graduação do autor (USP, 2013) entra como documento externo, a
origem da teoria anterior ao artigo, citada e não redistribuída.

## 1. Três objetos teóricos, três hipóteses

O jogo do capítulo 3 ([03-o-jogo-do-congestionamento.md](03-o-jogo-do-congestionamento.md))
tem duas empresas, a líder 1 e a seguidora 2, que escolhem voos $`f_1`$ e
$`f_2`$ num aeroporto congestionado no pico. O tráfego total é
$`F = f_1 + f_2`$, o custo de congestionamento por voo é $`c(F)`$, com
$`c' > 0`$, e a seguidora reage a cada voo extra da líder cortando
$`\lambda = -\partial f_2/\partial f_1`$ dos seus, com $`\lambda`$ entre 1/2 e 1
(`reaction_slope.lambda_lower`, `reaction_slope.lambda_upper_exclusive`). Três
peças desse jogo têm contraparte empírica. Cada uma vira uma hipótese, e cada
hipótese tem um regressor, um sinal esperado e um mecanismo. As três seções
seguintes fazem isso na mesma ordem: definição, intuição, hipótese, regressor.

### 1.1 A parcela internalizada do dano marginal

O dano marginal de congestionamento é o custo que um voo a mais impõe a todos
os voos do aeroporto: $`\mathrm{MCD} = F\,c'(F)`$. Uma empresa que opera $`f_i`$
dos $`F`$ voos sente, desse dano, só a fatia que recai sobre os seus próprios
voos, $`f_i\,c'`$. É essa fatia que ela internaliza: ao programar mais um voo,
pesa o atraso que causa a si mesma e ignora o que causa às demais. A
Proposição 1 do capítulo 3 mede o que falta cobrar para levar o equilíbrio ao
ótimo: no ótimo simétrico, a tarifa da líder é $`(1 + \lambda)/2`$ do dano
marginal e, sob custo linear, exatamente 3/4 (`tolls.leader_over_MCD_linear`
= 0,75). Os casos de referência dão a régua: Cournot 1/2, comportamento
atomístico 1, monopólio 0 (`tolls.cournot_over_MCD`,
`tolls.atomistic_over_MCD`, `tolls.monopoly_over_MCD`).

A intuição é de tamanho. Quanto maior a parcela de uma empresa no aeroporto,
maior a fração do dano que ela já paga por conta própria e menor a tarifa que
falta: o monopolista internaliza tudo, a franja atomística nada. A hipótese
segue direto. **Onde uma empresa domina o aeroporto, os atrasos são menores do
que o volume de voos faria prever, tudo o mais constante.** O regressor do
artigo é a concentração de passageiros na cidade-extremo mais concentrada da
rota, `maxcthhi`, e o sinal esperado é negativo (`bridge.rows`, `maxcthhi`).

O que isso significa para o artigo: um `maxcthhi` negativo e significante é a
Proposição 1 medida, com a parcela própria do dano no lugar da tarifa que
ninguém cobra.

### 1.2 Poder de mercado na rota

Sob demanda perfeitamente elástica, o caso básico do jogo, o preço é dado e a
única distorção é o congestionamento. O capítulo 3 relaxa isso: com demanda
inversa $`d(sF)`$ e $`d' < 0`$, a condição de primeira ordem da líder, a
equação (12), carrega dois termos de sinais opostos — um de poder de mercado,
que a leva a voar de menos para sustentar o preço, e um de congestionamento não
internalizado, que a leva a voar de mais. A Pressuposição 2 da monografia
descreve o intervalo em que os dois convivem (monografia, seção 4.4 —
documento externo); o capítulo 3 mostra que qual deles vence depende da
inclinação da demanda.

Para o atraso, o poder de mercado na **rota** tem por isso dois canais. Pelo
primeiro, menos concorrência na rota significa menos voos e menos pressão sobre
a pista: menos atraso. Pelo segundo, o canal concorrência–qualidade, uma empresa
sem rival na rota tem menos a perder com um horário mal cumprido: mais atraso.
O modelo não escolhe entre eles, e o sinal fica em aberto. A monografia esperava
"−, +" para os índices de concentração e diz por quê: "espera-se que possa haver
ou não internalização do congestionamento, uma vez que não há consenso na
literatura sobre o tema" (monografia, seção 5 — documento externo). O regressor
é a concentração de passageiros na rota, `rthhi`; o sinal esperado é ambíguo
(`bridge.rows`, `rthhi`); o artigo lê o coeficiente positivo que encontra como
o canal concorrência–qualidade.

O que isso significa para o artigo: a separação entre `rthhi` e `maxcthhi` é a
decisão que permite testar as duas coisas ao mesmo tempo — poder de mercado
onde a empresa vende, internalização onde ela congestiona.

### 1.3 A entrante de baixo custo

> Pressuposição 3: A entrada de uma empresa aérea de baixo custo no mercado
> quebra a estrutura do jogo em Stackelberg. Devido à estrutura do modelo de
> negócios de uma empresa aérea de baixo custo, é coerente pressupor que tais
> empresas procurem internalizar os custos do congestionamento, uma vez que
> tais custos podem afetar o planejamento estratégico de longo prazo da empresa
> que busca o crescimento de sua participação de mercado.
>
> (monografia, seção 4.5 — documento externo)

A Pressuposição 3 é verbal. O capítulo 3 a converte num exemplo imprimível,
marcado como extensão deste repositório: num triopólio de Cournot com custo
linear e uma entrante de custo por assento menor, o tráfego total sobe de 60 no
duopólio de Cournot para 75 (`extension_lcc.duopoly_cournot.F`,
`extension_lcc.triopoly.F`); a entrante voa 45 desses voos contra 15 de cada
incumbente (`extension_lcc.triopoly.flights`) e internaliza 0,6 do dano
marginal contra 0,2 de cada uma delas
(`extension_lcc.triopoly.internalised_share`). A entrante internaliza mais
porque voa mais, e voa mais porque custa menos: é argumento de tamanho, não de
virtude.

A hipótese do artigo não é sobre o atraso da entrante, e sim sobre o das
incumbentes. **A presença de uma empresa de baixo custo reduz o atraso das
empresas de serviço completo — na rota em que entra e na cidade em que
opera.** São dois regressores binários, `lcc` (Gol ou Azul vendendo bilhetes na
rota no mês) e `maxalccfu` (Gol ou Azul presente numa das cidades-extremo),
ambos com sinal esperado negativo (`bridge.rows`, `lcc` e `maxalccfu`). O
segundo é o *spillover* não-preço do título do artigo: um efeito que a entrante
exerce sobre rotas em que nem sequer voa, pela cidade.

O que isso significa para o artigo: `lcc` testa o efeito na rota; `maxalccfu`
testa o derrame pela cidade; os dois têm o mesmo sinal esperado e mecanismos
diferentes.

### 1.4 O que não é do jogo

O restante da especificação são controles. Volumes de voo no pico
(`dailyflcong`) e fora dele (`dailyflncong`) entram com sinal positivo: mais
voos, maior $`c(F)`$; o modelo nada prevê para o período fora do pico, e o
artigo encontra o mesmo sinal nos dois. Três parcelas de causa registram atraso
não estratégico e ficam fora do jogo: clima e restrição de aeroporto
(`prwheather`), incidentes (`princident`) e rotação de aeronave (`pr_connc`). O
estado do aeroporto — a maior proporção de voos atrasados entre as duas
cidades-extremo, todas as empresas — é `maxprdel`: $`c(F)`$ é função do tráfego
de todos, não só do da rota. O acordo de codeshare (`cshare`) é cooperação fora
do modelo e não tem sinal previsto. A tabela resume:

| Hipótese | Objeto teórico | Regressor | Sinal esperado | Mecanismo |
|---|---|---|---|---|
| H1 — internalização no aeroporto | parcela própria do dano marginal, Proposição 1 | `maxcthhi` | − | quem enfrenta o próprio congestionamento contém voos |
| H2 — poder de mercado na rota | $`d' < 0`$ na equação (12) | `rthhi` | ambíguo | menos voos (−) contra menos incentivo a cumprir horário (+) |
| H3 — entrante de baixo custo na rota | Pressuposição 3 | `lcc` | − | a entrante internaliza; a rota com LCC atrasa menos |
| H3 — entrante de baixo custo na cidade | Pressuposição 3, pela cidade | `maxalccfu` | − | o derrame não-preço do título |
| controle | volumes no pico, $`f_1 + f_2`$ com $`c' > 0`$ | `dailyflcong` | + | mais voo na hora cheia, mais atraso |
| controle | volumes fora do pico | `dailyflncong` | + | sem previsão do modelo; o artigo acha o mesmo sinal |
| controle | atraso não estratégico | `prwheather`, `princident`, `pr_connc` | + | fora do jogo (ADR-0005) |
| controle | estado do aeroporto, $`c(F)`$ de todos | `maxprdel` | + | o atraso de todas as empresas na ponta mais movimentada |
| controle | cooperação fora do modelo | `cshare` | sem previsão | — |

Os objetos e os sinais são as linhas de `bridge.rows` em
`reports/theory/model.json`.

## 2. A tabela-ponte: cada hipótese e o que saiu publicado

![Figura 11 — OLS contra 2SGMM nos regressores de estrutura de mercado](../../reports/theory/figures/fig11_inversao_de_sinal.svg)

*A Figura 11 põe lado a lado, para os quatro regressores de estrutura de
mercado, o coeficiente OLS da coluna (2) da Tabela 6 e o 2SGMM da coluna (2)
da Tabela 3, com as estrelas publicadas; o achado no título é que o 2SGMM
inverte o sinal das duas concentrações. Os valores são os de
`src/airline_delays/estimation/published.json`, listados em
`reports/theory/figures.json` (`fig11.quantities`); nada é reestimado.*

A tabela tem uma linha por objeto teórico, na ordem de `bridge.rows`. As duas
colunas de resultados são o coeficiente publicado com as estrelas, lidos de
`bridge.tables.table3.variables.<var>.columns.2` e de
`bridge.tables.table6.variables.<var>.columns.2`: a coluna (2) da Tabela 3 é o
2SGMM com as binárias de LCC, o modelo de base do artigo; a coluna (2) da
Tabela 6 é a mesma especificação por OLS, sem instrumento. Estrelas: \*\*\* 1%,
\*\* 5%, \* 10%.

| Objeto teórico | Variável | Sinal esperado | Tabela 3, col. (2), 2SGMM (artigo, Tabela 3) | Tabela 6, col. (2), OLS (artigo, Tabela 6) | Leitura |
|---|---|---|---|---|---|
| volumes no pico: $`f_1 + f_2`$, com $`c' > 0`$ | `dailyflcong` | + | +0,0043 \* | +0,0016 | sinal esperado; positivo nas seis colunas |
| volumes fora do pico | `dailyflncong` | + | +0,0044 \*\* | +0,0014 | o modelo nada prevê; o artigo acha o sinal do pico |
| atraso não estratégico: clima e restrições de aeroporto | `prwheather` | + | +4,7145 \*\*\* | +4,7385 \*\*\* | fora do jogo; a mesma magnitude nos dois estimadores |
| atraso não estratégico: incidentes | `princident` | + | +6,1807 \*\*\* | +6,3062 \*\*\* | fora do jogo |
| atraso não estratégico: rotação de aeronave (código RA) | `pr_connc` | + | +2,4781 \*\*\* | +2,3032 \*\*\* | fora do jogo |
| o estado de congestionamento do aeroporto | `maxprdel` | + | +1,5460 \*\*\* | +1,6945 \*\*\* | $`c(F)`$ é de todos |
| cooperação fora do modelo | `cshare` | sem previsão | +0,0081 | +0,0132 | sem estrela nos dois |
| poder de mercado na rota: $`d' < 0`$ na equação (12) | `rthhi` | ambíguo | **+0,8192 \*\*** | **−0,3126 \*\*\*** | o 2SGMM lê o canal concorrência–qualidade; o OLS tem o sinal oposto |
| internalização no aeroporto: a parcela própria do dano marginal, Proposição 1 | `maxcthhi` | − | **−1,5144 \*\*\*** | **+0,1057** | H1 confirmada no 2SGMM; o OLS a perde |
| uma LCC na rota: Pressuposição 3 | `lcc` | − | −0,0412 | −0,1636 \*\*\* | o efeito de rota não sobrevive à instrumentação |
| uma LCC numa cidade-extremo: o *spillover* não-preço | `maxalccfu` | − | **−0,4234 \*\*** | −0,1793 | o efeito de cidade sobrevive; é o título do artigo |
| a reação da seguidora, $`\partial f_2/\partial f_1 = -\lambda`$ | nenhuma variável: é a endogeneidade | — | $`N`$ = 19.419; KP LM 139,2305; $`J`$ = 3,2199 ($`p`$ = 0,3589) | $`N`$ = 19.590; sem instrumento | a reação vira desenho de identificação, não regressor |

As estatísticas da última linha são `table3.columns.2.stats` e
`table6.columns.2.stats` de `src/airline_delays/estimation/published.json`; a
coluna (1) da Tabela 3, sem as binárias de LCC, tem o mesmo $`N`$ = 19.419,
KP LM 154,2698 e $`J`$ = 3,1132 ($`p`$ = 0,3745) (artigo, Tabela 3).

Três leituras.

**(a) As duas concentrações contam duas histórias, e o par OLS/2SGMM é a
demonstração.** No OLS, `rthhi` sai negativo a 1% e `maxcthhi` positivo sem
estrela; no 2SGMM os dois invertem: `rthhi` +0,8192 a 5%, `maxcthhi` −1,5144 a
1% (artigo, Tabelas 3 e 6). Concentração na rota associada a mais atraso é o
canal concorrência–qualidade; concentração no aeroporto associada a menos
atraso é internalização. A inversão não é anedota de uma célula: ela ocorre nas
duas colunas ODDS de cada tabela e em nenhuma coluna MINS, onde OLS e 2SGMM já
têm o mesmo sinal e só a magnitude muda — o padrão completo, e a sua
replicação, estão no capítulo 7.

**(b) A LCC age pela cidade, não pela rota.** Na coluna (2) da Tabela 3, `lcc`
é −0,0412 sem estrela e `maxalccfu` é −0,4234 a 5%. No OLS a ordem se inverte:
`lcc` −0,1636 a 1% e `maxalccfu` −0,1793 sem estrela (artigo, Tabelas 3 e 6).
Instrumentar as concentrações desloca o efeito da rota para a cidade — e é o
efeito de cidade, o derrame sobre rotas em que a entrante não voa, que dá título
ao artigo. Nas colunas em minutos, `lcc` muda de sinal e sai positivo a 10%
(+2,4889 e +2,7123 nas colunas (4) e (6)), enquanto `maxalccfu` segue negativo
e sem estrela (artigo, Tabela 3); o padrão por coluna está em
`bridge.tables.table3.variables.lcc.pattern`.

**(c) Os controles são estáveis.** Clima, incidentes, rotação e estado do
aeroporto saem positivos a 1% com magnitudes quase iguais nos dois estimadores;
os volumes saem positivos nos dois, com estrela só no 2SGMM (artigo, Tabelas 3
e 6). É o que se espera de variáveis que não estão no jogo: a endogeneidade da
concentração não as contamina.

## 3. A lógica da identificação, em uma página

**Por que a concentração é endógena ao atraso.** No jogo, cada empresa escolhe
voos olhando o congestionamento que os outros voos causam — a seguidora reage a
$`f_1`$ com $`\partial f_2/\partial f_1 = -\lambda`$. Voos determinam
participações, e participações determinam o HHI. Logo o HHI de uma rota-mês e o
atraso dessa rota-mês são decididos no **mesmo** equilíbrio: uma rota que
atrasa muito pode perder o rival marginal e ficar mais concentrada, e uma rota
concentrada pode ser mais ou menos pontual pelos dois canais da seção 1.2. Um
efeito fixo de rota não resolve isso. Ele remove o que é constante na rota —
distância, tamanho das cidades, a geografia —, não a simultaneidade dentro de
cada mês. Um coeficiente OLS de `rthhi` ou `maxcthhi` mistura o efeito da
concentração sobre o atraso com o efeito do atraso sobre a concentração, e a
Tabela 6 mostra o resultado dessa mistura.

**Por que instrumentos, e quais.** Um instrumento precisa mover a concentração
desta rota-mês sem passar pelo atraso desta rota-mês. A escolha do artigo é do
tipo Hausman: a concentração de **outras** cidades e rotas, em faixas de
vizinhança e com defasagem — sete colunas do painel de estimação do artigo,
`h1_maxcthhi`, `h2_maxcthhi`, `h3_maxcthhi`, `lnh1_maxcthhi`, `l1h1_maxcthhi`,
`l1h2_maxcthhi` e `h2_rthhi`, construção espacial dos autores (artigo, seção de
identificação). A hipótese de exclusão é que choques de estratégia e de custo
de uma empresa se refletem na sua concentração em várias cidades ao mesmo
tempo, enquanto o atraso de uma rota-mês específica não muda a concentração das
vizinhas. As duas endógenas são só `rthhi` e `maxcthhi`; as binárias de LCC
entram como exógenas. As listas de instrumentos, os estimadores e a estatística
que testa a força dos instrumentos são o capítulo 6
([06-especificacao-e-identificacao.md](06-especificacao-e-identificacao.md)).

**Por que a inversão de sinal é o argumento do artigo.** A Tabela 6 existe para
ser comparada com a Tabela 3: é a mesma especificação sem instrumentar. Se a
endogeneidade fosse inócua, os dois estimadores dariam o mesmo sinal; eles dão
sinais opostos para as duas concentrações, exatamente nas colunas em que o
regressando é a proporção de atrasos (Figura 11). A direção do viés é a que a
simultaneidade prevê: no OLS a concentração da rota parece reduzir o atraso e a
do aeroporto parece aumentá-lo. O 2SGMM devolve os sinais que a teoria da seção
1 espera, e o teste de sobreidentificação não rejeita os instrumentos
($`J`$ = 3,2199, $`p`$ = 0,3589 na coluna (2); artigo, Tabela 3). É por isso
que a replicação do capítulo 7 trata a inversão como a afirmação mais afiada do
artigo e a mais barata de conferir.

## 4. Do modelo ao registro de colunas

Cada variável do modelo tem um endereço no registro
`src/airline_delays/schema/columns.py`, renderizado em `docs/dictionary.md`. A
camada `article_panel` é o painel de estimação do artigo (52 colunas,
ADR-0020); a camada `panel` é o painel reconstruído (228 colunas), que traz as
mesmas definições onde o VRA as sustenta e declara as suas próprias onde não. A
tabela diz onde cada objeto vive.

| Objeto do modelo | Variável do artigo (camada `article_panel`) | Definição no registro | No painel reconstruído (camada `panel`) |
|---|---|---|---|
| tráfego $`F = f_1 + f_2`$ | `f`, `dailyfl` | voos programados na rota-mês, realizados mais cancelados (ADR-0002); `f` por dia do mês | mesmos nomes e definições |
| tráfego no pico e fora dele | `dailyflcong`, `dailyflncong` | voos por dia nas horas classificadas como congestionadas pela capacidade declarada, e o complemento (ADR-0007) | não carregados; o proxy interno p90 tem outro nome (`docs/notes/features.md`) |
| o atraso $`t(F)`$ das incumbentes | `fsc_oddsarr`, `fsc_minsarr`, `fsc_minsp15arr` e as três de partida | log-odds da proporção de chegadas FSC com mais de 15 minutos de atraso; minutos médios; minutos além de 15 — conjunto FSC do artigo (ADR-0013) | mesmos nomes e definições |
| o estado do aeroporto, $`c(F)`$ | `maxprdel` | a maior proporção de voos atrasados entre as duas cidades-extremo, todas as empresas | `maxprdel_proxy`, sob outro nome: a definição exata não foi recuperada |
| a parcela própria do dano marginal | `maxcthhi` (e `gmchhi`) | o maior HHI de passageiros entre as duas cidades-extremo (dados estatísticos da ANAC); a média geométrica como alternativa | existe e é nulo; `maxcthhi_flights` é a versão sobre voos (ADR-0007) |
| poder de mercado na rota, $`d' < 0`$ | `rthhi` | HHI da rota sobre passageiros pagos | existe e é nulo; `rthhi_flights` é a versão sobre voos |
| a entrante de baixo custo | `lcc`, `maxalccfu`; componentes `pres_glo`, `pres_azu`, `olccfu`, `dlccfu` | Gol ou Azul vendeu bilhetes na rota (microdados tarifários); presente numa cidade-extremo | mesmos nomes, lidos da operação no VRA e não da venda de bilhetes |
| atraso não estratégico | `prwheather`, `princident`, `pr_connc` | parcelas de voos por código de justificativa IAC 1504 (ADR-0005) | mesmos nomes e definições |
| a reação da seguidora, $`-\lambda`$ | `h1_maxcthhi`, `h2_maxcthhi`, `h3_maxcthhi`, `lnh1_maxcthhi`, `l1h1_maxcthhi`, `l1h2_maxcthhi`, `h2_rthhi` | concentração de outros pares de cidades, por faixa de vizinhança e defasagem: os sete instrumentos | não carregados: derivam dos HHI de passageiros |
| tarifas $`T_1`$, $`T_2`$ e slots | nenhum regressor | — | `data/external/slots.csv`, `data/external/capacity.csv` (ADR-0007) |

O que o painel reconstruído não traz com valor é a lista
`reconstruction.article_columns_missing` de `reports/summary.json`, renderizada
no capítulo 5 ([05-os-dados.md](05-os-dados.md)); a razão é a fonte, não a
definição: os HHI de passageiros e os instrumentos esperam os dados
estatísticos da ANAC, as contagens no pico esperam as declarações de capacidade
(`docs/data-availability.md`, fontes 3 e 6).

## 5. A crítica de 2018

Guo, Jiang e Wan (2018) constroem sobre a separação da seção 1.2 —
concentração de mercado ligada ao canal de qualidade, concentração de aeroporto
ligada à internalização — e apontam que controlar por tráfego do aeroporto
remove, junto com o efeito residual de mercado, a parte da internalização que
opera por preço. A resposta deles é mudar o teste de lugar, do atraso para a
tarifa. O que encontraram, e o que isso muda na leitura da Pressuposição 3, é
o capítulo 8 ([08-recepcao.md](08-recepcao.md)).

## Escopo e próximos passos

Este capítulo traduz o modelo em hipóteses e mostra o que saiu publicado; não
reestima nada e não compara a monografia com o artigo coeficiente a
coeficiente, porque unidade de observação, base do HHI, estimador, regressando
e limiar de atraso diferem entre os dois estudos. O passo seguinte é o capítulo
5, que descreve os dados de que as variáveis desta tabela são construídas, e o
capítulo 6, que fecha a especificação e a identificação.

## Onde conferir

- `reports/theory/model.json`: `bridge.rows` (objetos, sinais esperados),
  `bridge.tables.table3` e `bridge.tables.table6` (coeficientes publicados por
  coluna e padrão de sinais), `tolls`, `reaction_slope`, `extension_lcc`.
  Regenerado por `just theory`.
- `src/airline_delays/estimation/published.json`: as Tabelas 2–7 transcritas
  do artigo, inclusive `stats` de cada coluna.
- `reports/theory/figures.json`, `fig11`: os valores desenhados na Figura 11.
- `docs/dictionary.md`, camadas `article_panel` e `panel`: a definição de cada
  coluna da seção 4.

Referências completas em [bibliografia.md](bibliografia.md).
