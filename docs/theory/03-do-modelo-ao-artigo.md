# Do modelo ao artigo — a econometria de 2016 como culminação

Este é o terceiro de quatro capítulos da discussão temática. O capítulo
[01](01-economia-do-congestionamento.md) montou a economia do
congestionamento e o capítulo
[02](02-o-jogo-do-congestionamento.md) fechou o jogo de Stackelberg da
monografia de 2013; o capítulo [04](04-impacto.md) trata do que veio
depois. Aqui fica a passagem: como aquela teoria vira a econometria do
artigo que este repositório replica — Bendinelli, Bettini e Oliveira
(2016, *Transportation Research Part A* 85, 39–52, DOI
10.1016/j.tra.2016.01.001). A regra de proveniência vale linha a linha:
**todo número de 2016** vem de `replication/published.json`, lido através
de `reports/theory/model.json` (objeto `bridge`), ou de
`reports/replication/private/summary.json`; **todo número de 2013** é
externo, transcrito da monografia; e **nada é reestimado aqui**. O artigo
é a culminação, não uma segunda rodada da monografia: as estimativas de
2013 aparecem como citação, jamais como resultado deste repositório.

A monografia é *Efeitos da entrada de uma empresa aérea de baixo custo na
internalização das externalidades do congestionamento* (USP/ESALQ,
Piracicaba, 2013); daqui em diante, "a monografia". Ela não está neste
repositório e sua base é a base de laboratório da monografia (fonte 12 de
`docs/data-availability.md`), não redistribuída.

## 1. A pergunta, a hipótese e os sinais esperados

A pergunta de 2013 é estreita e verificável: a entrada de uma empresa
aérea de baixo custo muda a internalização do congestionamento pelas
demais? A hipótese vem do modelo — a Pressuposição 3, literal:

> "A entrada de uma empresa aérea de baixo custo no mercado quebra a
> estrutura do jogo em Stackelberg. Devido à estrutura do modelo de
> negócios de uma empresa aérea de baixo custo, é coerente pressupor que
> tais empresas procurem internalizar os custos do congestionamento, uma
> vez que tais custos podem afetar o planejamento estratégico de longo
> prazo da empresa que busca o crescimento de sua participação de
> mercado." (monografia, Pressuposição 3)

É essa pressuposição, e só ela, que assina o sinal esperado das duas
binárias na coluna "Sinal esperado" da Tabela 1: `dummy_gol` **negativo**
e `dummy_azul` **negativo** (monografia, Tabela 1 — documento externo).
Não é uma expectativa empírica solta: se a LCC internaliza, a rota (ou o
aeroporto) em que ela está deve ter menos atraso, tudo o mais constante.

O resto da coluna divide-se em três blocos, e cada um tem uma razão
declarada no texto (monografia, seção 5 — documento externo):

- **Operacionais.** `amovtot` **+** (mais movimento, mais atraso);
  `prconex` **+** (mais passageiro em conexão, mais espera);
  `asize` **+** (aeronave maior, mais tempo de pista); `fltime` **−**
  (voo mais longo dá folga para recuperar atraso em rota).
- **Climáticas de controle.** `precip` **+** (chuva reduz o coeficiente
  de frenagem e a visibilidade); `ceiling` **+**; e `wind`
  explicitamente ambíguo, **"−, +"**, porque vento forte tanto atrapalha
  pouso e decolagem quanto dispersa nuvem baixa.
- **Concorrência e barreiras.** `hhi` e `cr2` recebem, os dois, o sinal
  **"−, +"** — ambíguo por decisão, e o texto diz por quê: "espera-se que
  possa haver ou não internalização do congestionamento, uma vez que não
  há consenso na literatura sobre o tema" (monografia, seção 5).

Guardar essa ambiguidade importa para o capítulo inteiro. Em 2013 os dois
índices de concentração entram como **uma** pergunta em aberto, com um só
par de sinais possíveis. Em 2016 eles deixam de ser uma pergunta e viram
**duas**: uma concentração de mercado (a rota) e uma concentração de
aeroporto (a cidade-extremo), com sinais esperados diferentes e
mecanismos diferentes. A separação é o avanço do artigo, e é dela que a
literatura posterior se apropria (seção 6).

## 2. Da equação (22) à Tabela 3 do artigo

A forma reduzida da monografia é uma equação só:

$$
\begin{aligned}
\text{prdeltot}_{jht} =\ & \beta_0
 + \beta_1\,\text{prconex}_{jht}
 + \beta_2\,\text{amovtot}_{jht}
 + \beta_3\,\text{fltime}_{jht} \\
 & + \beta_4\,\text{asize}_{jht}
 + \beta_5\,\text{wind}_{ht}
 + \beta_6\,\text{precip}_{ht}
 + \beta_7\,\text{ceiling}_{ht} \\
 & + \beta_8\,\text{hhi}_{ht}
 + \beta_9\,\text{cr2}_{ht}
 + \beta_{10}\,\text{dummy\_gol}_{ht}
 + \beta_{11}\,\text{dummy\_azul}_{ht} \\
 & + a_j + b_h + c_t + u_{jht}
\end{aligned}
\tag{22}
$$

A unidade é **empresa $j$ × rota $h$ × mês $t$**, com efeito fixo de
empresa ($a_j$), de rota ($b_h$) e de mês ($c_t$), sobre um painel
desbalanceado de **87.237** observações, janeiro de 2000 a dezembro de
2012, em **36** aeroportos, estimada com pesos analíticos pela frequência
de voos planejados (monografia, seção 5 e seção 7 — documento externo). O
$R^2$ da especificação (5), a que o texto usa para a leitura, é
**0,7294** (monografia, Tabela 5, coluna 5 — documento externo). Detalhe
de transcrição: o objeto de equação grafa a primeira variável como
`prconx` e a Tabela 1 a grafa `prconex`; é a mesma variável.

O artigo de 2016 muda quatro coisas ao mesmo tempo, e as quatro andam
juntas:

1. **A unidade cai a rota × mês.** A empresa some do índice: o
   regressando passa a ser o atraso de **chegada do conjunto FSC** na
   rota-mês, em duas escalas — `ODDS`, o log-odds da proporção de
   chegadas atrasadas, e `MINS`, minutos por voo. As colunas (1) e (2) da
   Tabela 3 são `ODDS`; as (3) a (6), `MINS` — os três regressandos de
   chegada listados em `replication/common.py` como
   `ARRIVAL_REGRESSANDS`: `fsc_oddsarr`, `fsc_minsarr`, `fsc_minsp15arr`.
2. **Os efeitos fixos viram dummies explícitas de rota e de tempo**, mais
   60 sazonais região × mês. `replication/common.py` as reconstrói:
   `SEASONALITY` é o produto de cinco regiões por doze meses, e
   `TIME_DUMMIES` cobre `N_PERIODS = 144` meses entre `FIRST_YM = 200201`
   e `LAST_YM = 201312`.
3. **Os erros passam a ser HAC**, com largura de banda derivada de
   $T^{1/3}$ com $T = 144$.
4. **A concentração deixa de ser exógena.** É a mudança que reorganiza
   tudo o mais.

O motivo da quarta mudança é econômico, não estatístico, e vem direto do
capítulo 02. Se o seguidor reage ao líder — a inclinação
$\partial f_2/\partial f_1 = -\lambda$, com $\lambda$ entre $1/2$ e $1$ —
então a quantidade de voos de cada empresa e, portanto, a participação de
mercado de cada uma **respondem** ao mesmo congestionamento que se quer
explicar. Concentração e atraso são determinados no mesmo equilíbrio. Um
efeito fixo de rota não resolve isso: ele tira o que é constante na rota,
não a simultaneidade dentro dela. Daí os instrumentos: em 2016 `rthhi` e
`maxcthhi` são as duas endógenas (`ENDOG` em `replication/common.py`) e a
identificação é do tipo Hausman — a concentração de **outras** cidades,
próximas e defasada, como fonte de variação que não passa pelo atraso
desta rota-mês. A matriz de distância entre as 27 cidades, a regra de
"cidade próxima" e a fórmula dos pesos não foram entregues, e os
instrumentos são tomados do painel como estão
(`docs/declared-differences.md`, "Not attempted").

Que essa quarta mudança seja a última a chegar está documentado: em março
de 2015 o desenho ainda era OLS com efeitos fixos, e a instrumentação era
uma promessa explícita para "futuramente"
([M4](../tutorial/04-segundo-desenho.md)); a especificação final — 2SGMM
com HAC, dois blocos de instrumentos e a estatística de Kleibergen e Paap
(2006) escrita do zero para testá-la — está em
[M7](../tutorial/07-especificacao-e-estimacao.md) e em
`replication/kp.py`.

Os dois blocos de instrumentos ficam lado a lado em
`replication/common.py`: `INSTRUMENTS_ODDS` tem cinco excluídos
(`h3_maxcthhi`, `lnh1_maxcthhi`, `l1h1_maxcthhi`, `l1h2_maxcthhi`,
`h2_rthhi`) e o $J$ com 3 graus de liberdade; `INSTRUMENTS_MINS` tem três
(`h1_maxcthhi`, `h2_maxcthhi`, `h3_maxcthhi`) e o $J$ com 1. O artigo
apresenta os dois como um desenho só e não explica a diferença; o
comentário no código diz isso e não unifica.

## 3. A tabela-ponte

Uma linha por objeto teórico, na ordem de `bridge.rows` de
`reports/theory/model.json`. As duas colunas de 2016 são o coeficiente
publicado com as estrelas, lidos de
`bridge.tables.table3.variables.<var>.columns.2` e de
`bridge.tables.table6.variables.<var>.columns.2`. A coluna de 2013 é
externa: monografia, Tabela 5, coluna 5.

| Objeto teórico | Regressor de 2013 (Tab. 5 col. 5, externo) | Variável de 2016 | Tab. 3 col. (2), publicado | Tab. 6 col. (2), OLS | Sinal esperado e leitura |
|---|---|---|---|---|---|
| **Volumes e custo** — $f_1 + f_2$ com $c' > 0$, no pico | `amovtot` +0,0002 \*\*\* | `dailyflcong` | +0,0043 \* | +0,0016 | **+**; mais voo na hora congestionada, mais atraso |
| Volumes fora do pico | `fltime` −0,0208 \*\*\*; `asize` +0,0001 \*\*\* (custo e tecnologia do voo; a monografia não separa pico de fora-pico) | `dailyflncong` | +0,0044 \*\* | +0,0014 | **+**; o modelo nada prevê aqui e o artigo acha o mesmo sinal do pico |
| **Controles não estratégicos** — clima e restrição de aeroporto | `precip` +0,0001 \*\*\*; `wind` −0,0004 \*\*\* | `prwheather` | +4,7145 \*\*\* | +4,7385 \*\*\* | **+**; fora do jogo (ADR-0005 funde clima e restrição) |
| Incidentes | — | `princident` | +6,1807 \*\*\* | +6,3062 \*\*\* | **+**; fora do jogo |
| Rotação de aeronave (código RA) | `prconex` +0,0089 \* | `pr_connc` | +2,4781 \*\*\* | +2,3032 \*\*\* | **+**; espera por conexão, fora do jogo |
| Estado do aeroporto: $c(F)$ é de todos | — | `maxprdel` | +1,546 \*\*\* | +1,6945 \*\*\* | **+**; o atraso de todas as empresas na ponta mais movimentada |
| Cooperação fora do modelo | — | `cshare` | +0,0081 | +0,0132 | sem previsão |
| **Poder de mercado na rota** — $d' < 0$ na eq. (12) | `hhi` +0,0072 \*\*\* | `rthhi` | +0,8192 \*\* | −0,3126 \*\*\* | ambíguo; 2016 lê como canal concorrência–qualidade |
| **Internalização no aeroporto** — parcela própria do dano marginal (Proposição 1) | `cr2` +0,0271 \*\*\* | `maxcthhi` | −1,5144 \*\*\* | +0,1057 | **−**; quem enfrenta o próprio congestionamento contém voos |
| **Pressuposição 3** — LCC na rota | `dummy_gol` +0,0019 \* | `lcc` | −0,0412 | −0,1636 \*\*\* | **−**; em 2013, presença da Gol na rota, 2001–2005 |
| Pressuposição 3 — LCC na cidade-extremo | `dummy_azul` −0,0108 \*\*\* | `maxalccfu` | −0,4234 \*\* | −0,1793 | **−**; o *spillover* não-preço do título de 2016 |
| **A reação do seguidor** — $\partial f_2/\partial f_1 = -\lambda$ | não tratada em 2013 | nenhuma variável: é a endogeneidade | 2SGMM, $N$ = 19.419, KP LM 139,2305, $J$ = 3,2199 ($p$ = 0,3589) | OLS, $N$ = 19.590, sem instrumento | a reação vira desenho de identificação, não regressor |
| **Pedágios, slots e leilões** | nenhum regressor | nenhum regressor | — | — | aqui viram `data/external/slots.csv` e `data/external/capacity.csv`; a capacidade horária declarada segue não coletada (ADR-0007) |

As estatísticas da última linha são de `replication/published.json`:
`table3.columns.2.stats.n_obs`, `.kp_lm`, `.j_stat` e `.j_p`, e
`table6.columns.2.stats.n_obs`. A coluna (1) da mesma tabela, sem as
binárias de LCC, tem o mesmo $N$ = 19.419, KP LM 154,2698 e $J$ = 3,1132
($p$ = 0,3745) — `table3.columns.1.stats`.

**(a) Concentração.** Em 2013, com efeitos fixos e sem instrumentar nada,
`hhi` e `cr2` saem positivos e a 1%: +0,0072 e +0,0271 (monografia,
Tabela 5, coluna 5 — documento externo); em elasticidade, +0,0207 e
+0,1285 (monografia, Tabela 6, coluna 5 — documento externo). O texto lê
isso como um resultado só:

> "Portanto, o aumento do HHI e da razão de concentração das empresas
> líderes do mercado elevam a quantidade de atrasos. Deve-se ressaltar
> que tal fato relaciona-se com o termo econômico Tragédia dos Comuns, um
> tipo de armadilha envolvendo um conflito sobre um bem comum, finito e
> escasso, mas de benefício para a maioria, e que tem que ser repartidos
> de acordo com interesses individuais." (monografia, seção 7)

Em 2016 o mesmo par de índices conta duas histórias, e o par
OLS/2SGMM é a demonstração. No OLS (Tabela 6, coluna 2) `rthhi` sai
**−0,3126 \*\*\*** e `maxcthhi` sai **+0,1057**, sem estrela; no 2SGMM
(Tabela 3, coluna 2) os dois **invertem**: `rthhi` **+0,8192 \*\*** e
`maxcthhi` **−1,5144 \*\*\***. Concentração na rota associada a *mais*
atraso é o canal concorrência–qualidade; concentração no aeroporto
associada a *menos* atraso é internalização — a Proposição 1 do capítulo
02 medida, com a parcela própria do dano marginal no lugar do pedágio que
ninguém cobra. A inversão não é anedota de uma célula: o campo
`hhi_sign_inversions` de `reports/replication/private/summary.json`
compara as duas variáveis nas seis colunas de cada tabela,
`n_comparisons` = 12, e encontra `n_inverted_published` = 4 e
`n_inverted_replicated` = 4, nas colunas `ODDS` (1) e (2), com
`n_pattern_agrees` = 12 — a réplica reproduz o padrão em todas as doze
comparações. É a mesma demonstração que o docstring de
`replication/table6.py` descreve como a afirmação mais afiada do artigo e
a mais barata de conferir.

**(b) LCC.** A tradução mais visível é a das binárias. Em 2013 são duas
coisas heterogêneas: `dummy_gol` é presença da Gol **na rota**, restrita
a 2001–2005, quando a empresa ainda era classificada como *low cost*; e
`dummy_azul` é uma binária de **aeroporto**, ligada para todo voo com
origem ou destino em Viracopos entre 2009 e 2012 (monografia, Tabela 1 —
documento externo). Os resultados seguem essa assimetria: a da Gol sai
+0,0019 \*, e o texto a chama de ambígua — "a dummy de entrada da Gol na
rota apresenta um efeito ambíguo" (monografia, seção 7) —; a da Azul sai
−0,0108 \*\*\*, e o texto lê internalização no aeroporto próprio. Em 2016
as duas viram `lcc` (LCC na rota) e `maxalccfu` (LCC na maior das duas
cidades-extremo), com o mesmo sinal esperado negativo. Um `lcc` negativo
diz que a rota com LCC tem menos atraso de FSC; um `maxalccfu` negativo
diz que a presença de LCC **na cidade** derrama efeito sobre a rota
inteira, e é esse derrame — não-preço, no nível da cidade — que dá título
ao artigo. Na coluna (2) da Tabela 3, `lcc` é −0,0412 sem estrela e
`maxalccfu` é −0,4234 \*\*: o efeito de rota não sobrevive à
instrumentação, e o de cidade sobrevive.

**(c) Os sinais não são comparáveis entre os dois estudos.** Vale dizer
isso com todas as letras, porque a tabela acima convida ao erro. Cinco
diferenças, qualquer uma delas suficiente: a base do HHI (voos planejados
em 2013, passageiros pagos em 2016); a unidade (empresa × rota × mês
contra rota × mês); o estimador (efeitos fixos ponderados contra 2SGMM
com HAC); o regressando (média geométrica ponderada de atrasos totais
contra log-odds ou minutos de chegada do conjunto FSC); e o limiar (30
minutos em 2013; o artigo trabalha também com a variante de 15). A
tabela-ponte alinha **objetos teóricos**, não coeficientes: ela diz onde
cada peça do modelo foi parar, não que os números conversem.

## 4. O mapa da equação (22) para o registro deste repositório

A pergunta seguinte é operacional: do regressando e das onze
explicativas da equação (22), o que existe no registro de colunas deste
repositório, em que camada, e com que ressalva? `docs/dictionary.md` tem
uma seção por camada (staged, fact, city, airline_city, panel, ml), e é
essa a coluna "camada".

| Variável de 2013 | O que existe aqui | Camada | Status |
|---|---|---|---|
| `prdeltot` | `arr_delayed_gt30` e `dep_delayed_gt30` | fact, city, airline_city, panel | mesma unidade de contagem; **duas ressalvas**: aqui é "> 30", a Resolução ANAC 218 conta "≥ 30"; e a monografia não diz se `prdeltot` é partida, chegada ou uma média das duas |
| `prdeltot` (regressando do artigo) | `fsc_prdelarr30m` | panel | existe, no conjunto FSC do artigo |
| `hhi` | `rthhi_flights` (a mesma construção de `hhi_flights`, sobre voos planejados) | panel (`hhi_flights` também em city) | substituto declarado: o `rthhi` do artigo é sobre passageiros e fica **nulo** no painel público (ADR-0004; `src/vra/hhi.py`) |
| `cr2` | ausente | — | calculável a partir dos voos por grupo da tabela de fatos; nenhuma coluna o declara hoje |
| `fltime` | `sched_block_mean_min` | panel | existe |
| `asize` | ausente | — | assentos por aeronave vêm do HOTRAN, não do VRA |
| `amovtot` | `movements` da cidade-mês | city | existe, mas só no universo de replicação (ADR-0002) |
| `prconex` | ausente (fonte 13 de `docs/data-availability.md`, não reproduzida) | — | `src/vra/hub.py` oferece um substituto **estrutural**, não comportamental |
| `wind`, `precip`, `ceiling` | ausentes (fonte 9, METAR, não integrada) | — | nada no painel os aproxima |
| `dummy_gol` | `pres_glo`, restrito a 2001m1–2005m12 | panel | reconstruível; o gabarito lê presença de venda de bilhete, aqui é operação |
| `dummy_azul` | `pres_azu`, mais a condição de ponta em SBKP | panel; `origin_icao`/`dest_icao` só em staged e ml | **não reconstruível no painel**: exige o grão par-de-aeroportos, e ADR-0001 dobra SBKP dentro do nó MRSP |
| $a_j$, $b_h$, $c_t$ | dummies de rota e de tempo do artigo | — | `replication/common.py` (`TIME_DUMMIES`, `SEASONALITY`) |
| pesos por voos planejados | `f` | panel (e `flights` em fact) | existe |

Uma verificação que roda agora, sem dado privado:

```bash
grep -n -E '^\| `(arr_delayed_gt30|rthhi_flights|sched_block_mean_min)`' docs/dictionary.md
```

**Número esperado.** Seis linhas. Quatro são de `arr_delayed_gt30` — uma
por camada em que a coluna existe (fact, city, airline_city, panel) —, uma
é `sched_block_mean_min` e uma é `rthhi_flights`, ambas só no painel
rota-mês. As duas variáveis da equação (22) mais fáceis de traduzir
aparecem uma vez cada; a mais fácil de todas aparece quatro vezes, porque
`aggregate()` a projeta em cada grão a partir do mesmo fato.

## 5. O que reproduz

Contra o gabarito privado, as cinco tabelas de regressão do artigo somam
**306** coeficientes comparados — a soma do campo `n_coefficients` das
cinco entradas de `reports/replication/private/summary.json` (60, 66, 60,
60 e 60). Somando `sign_agreement` (60, 65, 59, 59, 59) dá **302** sinais
iguais; somando `within_half_se` (53, 51, 53, 51, 51) dá **259**, ou 85%,
dentro de meio erro-padrão publicado. O que não fecha é o tamanho da
amostra: $N$ é cerca de **5,3%** maior em toda coluna (5,31% nas de
chegada, 5,35% nas de partida — `docs/declared-differences.md`, item 1),
sem que nenhum filtro visível no material entregue produza os números
publicados. Nenhum veredito muda com isso, inclusive o do $J$ de Hansen.
A leitura completa, coluna a coluna, é
[M8](../tutorial/08-o-que-reproduz.md), sobre
`reports/replication/private/tables.md`.

## 6. A crítica de 2018 e a pergunta de preços fechada

Guo, Jiang e Wan (2018) constroem em cima da separação de 2016. Eles
citam o artigo exatamente pela distinção que a seção 3 acabou de
descrever — concentração de mercado ligada ao canal de qualidade,
concentração de aeroporto ligada à auto-internalização — e a adotam na
sua própria especificação. E fazem uma crítica precisa (paráfrase): ao
incluir tráfego no nível do aeroporto como controle, o desenho remove o
efeito residual de mercado, mas remove **junto** a parte da
internalização que opera *reduzindo* tráfego via preço mais alto; o que
sobra nos coeficientes é só o canal de reprogramação de voos.

A resposta deles é mudar o teste de lugar: em vez de olhar atraso, olham
**tarifa**. Se a empresa internaliza, o preço carrega um *markup*
proporcional ao tráfego próprio no aeroporto vezes o atraso marginal, e
isso aparece como interação positiva entre atraso e tráfego próprio. É o
que encontram: a interação é positiva e significante a 1% no conjunto das
empresas (0,0348, 0,0498 e 0,0274 — Guo, Jiang e Wan 2018, Tabela 3,
documento externo) e, separada por tipo, sobrevive só nas FSC (0,0436 a
0,0564, Tabela 4), enquanto os coeficientes das LCC não são
significantes. A conclusão deles, em paráfrase: as FSC internalizam a
externalidade de congestionamento do aeroporto e as LCC não — o que
inverte, para o mercado americano de 2014–2015, a expectativa da
Pressuposição 3 de 2013.

O laço se fecha aí. A pergunta original do mestrado, em setembro de 2013,
era sobre **preços** — o título da proposta é "efeito dos atrasos nos
preços das passagens aéreas quando as empresas aéreas têm poder de
mercado" ([M1](../tutorial/01-a-proposta.md)). Ela foi deixada de lado,
retomada por conta própria em uma semana de junho de 2015 num projeto
irmão que nunca circulou, e abandonada de novo
([M5](../tutorial/05-caminho-nao-tomado.md)). A própria monografia já
tinha apontado o buraco duas vezes: ao dizer que a contradição com
Silveira e Oliveira (2007) "pode estar relacionada à falta da variável
preço no atual estudo" (monografia, seção 7), e ao listar como limitação
final que "não se verificou a relação ambígua entre concorrência e a
qualidade do serviço, que pode ser verificada através do preço do
produto conforme mostra Forbes (2008)" (monografia, seção 8). Dois anos
depois do artigo, a pergunta de preços foi respondida — por outros, e em
cima do artigo que a substituiu. Quem quiser retomá-la aqui precisa da
fonte 4 de `docs/data-availability.md`, ainda não coletada; o caminho
está em `docs/tutorial/13-propor-melhorias.md`.

## 7. Limites declarados

- **Nada de 2013 foi reestimado.** Todos os coeficientes da monografia
  neste capítulo são transcrições de um documento externo. Reconstruir
  aquela base não é tentado e não está previsto — é a mesma política da
  seção "Not attempted" de `docs/declared-differences.md`, que já declara
  não reconstruir o painel do gabarito nem os instrumentos do tipo
  Hausman.
- **Os rótulos de linha da Tabela 5 foram recuperados**, não lidos da
  tabela: a extração de texto entrega as células sem os nomes das
  variáveis, e a ordem das linhas foi recuperada dos objetos de equação
  do próprio documento. O mapeamento é leitura, não inferência, mas é
  leitura de outro lugar do documento — quem for citar a Tabela 5 deve
  conferir no original.
- **"≥ 30" contra "> 30" e partida contra chegada** seguem em aberto. A
  Resolução ANAC 218 conta atrasos de trinta minutos **ou mais**; a
  coluna deste repositório conta **mais de** trinta
  (`docs/dictionary.md`, `arr_delayed_gt30`). E a monografia não diz se
  `prdeltot` mede partida, chegada ou uma combinação.
- **A contagem de aeroportos não fecha.** O texto declara **36**
  aeroportos; a Lista de Siglas da própria monografia tem **38** códigos
  ICAO; as Tabelas 3 e 4 listam **37** (Porto Seguro, SBPS, está na
  lista e não nas tabelas). O seminário de março de 2015 (M4) fala em 38,
  a mesma contagem da lista — listas não comparadas.
  `docs/notes/monografia-2013.md` e `scripts/monograph_airports.py`
  declaram as três contagens; nenhuma é reconciliada aqui.

## 8. Como reproduzir

O que roda sem dado privado:

```bash
just replicate
```

Sobre o painel público rota-mês, esse comando monta a amostra pelos
mesmos filtros dos do-files e imprime a Tabela 2 descritiva. Ele **não**
estima as tabelas de regressão: faltam `maxprdel`, `cshare`,
`dailyflcong` e `dailyflncong`, e faltam os sete instrumentos do tipo
Hausman, que não são reconstrutíveis a partir do material entregue
(`docs/declared-differences.md`, seção "The public panel cannot yet
estimate the regression tables").

A tabela-ponte da seção 3 é regenerada por:

```bash
just theory
```

que reescreve `reports/theory/model.json`, incluindo `bridge.rows` e as
células publicadas de cada coluna das Tabelas 3 e 6.

A verificação de dicionário da seção 4 roda com o `grep` ali mesmo, sem
nenhum pré-requisito.

O que **não** roda: o confronto contra o gabarito
(`reports/replication/private/tables.md`,
`reports/replication/private/summary.json`) exige
`AIRLINE_DELAYS_PRIVATE_DIR` apontando para a base de laboratório da
monografia (fonte 12 de `docs/data-availability.md`), que não é
redistribuída. Os arquivos gerados na última execução privada estão
versionados e podem ser lidos sem rodar nada.

Referências completas em [bibliografia.md](bibliografia.md).
