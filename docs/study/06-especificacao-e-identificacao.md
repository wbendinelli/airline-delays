# Especificação e identificação: 2SGMM, instrumentos, HAC e Kleibergen–Paap

Português (ADR-0006).

Este capítulo escreve a econometria de Bendinelli, Bettini & Oliveira (2016,
*Transportation Research Part A* 85, 39-52, doi 10.1016/j.tra.2016.01.001)
por inteiro, com as definições do registro de colunas deste repositório. Ao
terminá-lo, o leitor sabe o que são os seis regressandos e por que o
principal é um log de razão de chances; qual é a equação estimada, regressor
a regressor; como as dummies de rota, de tempo e de sazonalidade são
reconstruídas pelo código; quais são os sete instrumentos e por que há duas
listas; o que o 2SGMM, o LIML e o OLS fazem de diferente e como os
erros-padrão HAC são calculados; em que ordem os filtros de amostra do artigo
se aplicam; o que a estatística de Kleibergen–Paap testa e como foi escrita e
validada aqui; e como ler uma coluna da Tabela 3. Daqui em diante, "o
artigo". As constantes da especificação vivem em
`src/airline_delays/estimation/specification.py`; a economia por trás de cada
regressor é o capítulo 4
([04-do-modelo-as-hipoteses.md](04-do-modelo-as-hipoteses.md)); os dados são
o capítulo 5 ([05-os-dados.md](05-os-dados.md)); os resultados, o capítulo 7
([07-resultados-e-replicacao.md](07-resultados-e-replicacao.md)).

## 1. Os regressandos

A unidade de observação é a rota-mês $`(r, t)`$: um par direcional de nós num
mês, no painel de estimação do artigo. O atraso medido é o das empresas de
serviço completo — TAM, grupo Varig até 2007-03, Transbrasil e Vasp
(ADR-0013) —, porque a pergunta é o que a estrutura de mercado faz ao atraso
das incumbentes. Seja $`p_{rt}`$ a proporção das chegadas dessas empresas na
rota-mês com mais de 15 minutos de atraso. O regressando principal é o seu
log da razão de chances:

```math
\mathrm{ODDS}_{rt} = \ln\frac{p_{rt}}{1 - p_{rt}} \tag{6.1}
```

A transformação leva o intervalo $`(0, 1)`$ à reta inteira, trata
simetricamente atrasar e não atrasar, e faz de um coeficiente um efeito sobre
o logaritmo das chances, comparável entre rotas com níveis de atraso
diferentes. Ela tem um custo: não existe quando $`p_{rt}`$ é 0 ou 1. É por
isso que `fsc_oddsarr` tem 3.934 nulos no painel
(`data/analysis/article_panel_manifest.json`, `nulls`), e é por isso que o
filtro de amostra da seção 7 morde por ela.

| Rótulo do artigo | Coluna | Definição (`docs/dictionary.md`, camada `article_panel`) | Onde entra |
|---|---|---|---|
| ODDS | `fsc_oddsarr` | $`\ln[p/(1-p)]`$ da proporção $`p`$ de chegadas das empresas de serviço completo com mais de 15 minutos de atraso; nulo quando $`p`$ é 0 ou 1 | Tabelas 3, 5 e 6, colunas (1) e (2); Tabela 4 inteira |
| MINS | `fsc_minsarr` | atraso médio de chegada, em minutos, dos voos dessas empresas sobre os voos realizados da rota-mês; as antecipações mantêm o sinal, e a média pode ser negativa | Tabelas 3, 5 e 6, colunas (3) e (4) |
| MINS > 15 | `fsc_minsp15arr` | como MINS, contando só os minutos além de 15 de cada voo | Tabelas 3, 5 e 6, colunas (5) e (6) |
| ODDSD | `fsc_oddsdep` | a contraparte de partida de ODDS | Tabela 7, colunas (1) e (2) |
| MINSD | `fsc_minsdep` | a contraparte de partida de MINS | Tabela 7, colunas (3) e (4) |
| MINSD > 15 | `fsc_minsp15dep` | a contraparte de partida de MINS > 15 | Tabela 7, colunas (5) e (6) |

As proporções por trás dos dois ODDS, `fsc_prdelarr` e `fsc_prdeldep`, viajam
no painel ao lado dos regressandos.

## 2. A equação

A especificação é uma só, repetida com três regressandos e com ou sem as duas
binárias de baixo custo. Em notação compacta, com $`y_{rt}`$ um dos
regressandos da seção 1:

```math
y_{rt} = x_{rt}'\beta + \gamma_1\,\mathrm{rthhi}_{rt} + \gamma_2\,\mathrm{maxcthhi}_{rt} + \delta_1\,\mathrm{lcc}_{rt} + \delta_2\,\mathrm{maxalccfu}_{rt} + \alpha_r + \theta_t + \phi_{g(r),\,m(t)} + \varepsilon_{rt} \tag{6.2}
```

Os termos, na ordem em que o artigo os imprime (`COEF_ORDER` e `COEF_LABEL`,
em `specification.py`; definições de `docs/dictionary.md`):

| Símbolo | Coluna | Rótulo impresso pelo artigo | Definição | Papel |
|---|---|---|---|---|
| $`x_{rt}`$ | `dailyflcong` | Nr flights in congested hours | voos programados por dia da rota nas horas que o artigo classifica como congestionadas nos aeroportos-extremo, por capacidade declarada (ADR-0007) | exógeno |
| $`x_{rt}`$ | `dailyflncong` | Nr flights in uncongested hours | o complemento de `dailyflcong` | exógeno |
| $`x_{rt}`$ | `prwheather` | Prop flights with bad weather | parcela dos voos da rota-mês com código de justificativa no conjunto meteorologia-e-aeroporto-restrito do artigo (ADR-0005) | exógeno |
| $`x_{rt}`$ | `princident` | Prop flights with incidents | parcela com código DF, DG, HB, MA ou TD | exógeno |
| $`x_{rt}`$ | `pr_connc` | Prop flights held for late connections | parcela com código RA, rotação de aeronave, que o artigo lê como espera por passageiros em conexão | exógeno |
| $`x_{rt}`$ | `maxprdel` | Max prop city delayed flights | a maior das proporções de voos atrasados das duas cidades-extremo no mês, todas as empresas | exógeno |
| $`x_{rt}`$ | `cshare` | Codeshare agreement | 1 enquanto um acordo de codeshare cobria a rota (TAM–Varig, 2003–2005) | exógeno |
| $`\gamma_1`$ | `rthhi` | HHI city-pair | índice de Herfindahl da rota sobre passageiros pagos por empresa | endógeno |
| $`\gamma_2`$ | `maxcthhi` | HHI max endpoint cities | o maior HHI de passageiros entre as duas cidades-extremo | endógeno |
| $`\delta_1`$ | `lcc` | LCC presence city-pair | 1 quando Gol ou Azul vendeu bilhetes na rota no mês; igual a max(`pres_glo`, `pres_azu`) | exógeno; só nas colunas (2), (4) e (6) e na Tabela 4 |
| $`\delta_2`$ | `maxalccfu` | LCC presence max endpoint cities | 1 quando Gol ou Azul estava presente numa das cidades-extremo; igual a max(`olccfu`, `dlccfu`) | exógeno; idem |

$`\alpha_r`$ é o efeito fixo de rota, $`\theta_t`$ o efeito fixo de
mês-calendário e $`\phi_{g(r),\,m(t)}`$ a sazonalidade região × mês do ano:
uma dummy por região do IBGE tocada pela rota e por mês do ano. As sete
primeiras linhas são o que o capítulo 4 chama de "o que não é do jogo"; as
duas concentrações são os objetos do jogo e as únicas variáveis
instrumentadas. As duas binárias de baixo custo são exógenas por decisão do
código dos autores — o que contradiz a introdução do artigo, que fala em
instrumentar *all of the market structure variables*, mas é inequívoco no
código e é o que reproduz os graus de liberdade publicados do teste J
(`docs/notes/replication.md`). A exposição de referência dos estimadores
deste capítulo é Wooldridge (2010).

## 3. As dummies reconstruídas pelo código

O painel publicado não carrega dummy nenhuma. `add_dummies()`
(`src/airline_delays/estimation/loader.py`) reconstrói, a partir de `ym`,
`o_region` e `d_region`, as 144 dummies de tempo `t_1..t_144` — uma por mês de
2002-01 a 2013-12 — e as 60 dummies sazonais `sz_{regiao}_m_{mes}` — cinco
regiões vezes doze meses —, pela regra: a dummy da região $`g`$ e do mês $`m`$
vale 1 quando o mês da observação é $`m`$ e a rota toca a região $`g`$ numa
das pontas. Cada linha acende uma ou duas dummies sazonais. As dummies
reconstruídas coincidem com as gravadas na base dos autores em todas as 24.589
linhas (`loader.py`, docstring de `add_dummies()`).

As dummies de rota são reconstruídas depois do corte de amostra da seção 7,
não antes: as gravadas na base cobriam 209 rotas, e depois do corte sobrevivem
190; recriá-las evita colunas identicamente nulas (`route_dummies()`, em
`src/airline_delays/estimation/sample.py`). Tudo entra explicitamente na
matriz de desenho — o código dos autores não usa `partial()` nem `xtivreg2`
—, uma dummy de rota é omitida contra a constante e as colunas exatamente
colineares caem por uma QR reveladora de posto (`drop_collinear()`). O
resultado, nas colunas (1) e (2) da Tabela 3, são 396 e 398 parâmetros com as
dummies sazonais e 341 e 343 sem elas (`reports/replication/sensitivity.json`,
`cells[].stats.n_params`).

## 4. Os sete instrumentos, em duas listas

Os instrumentos são do tipo Hausman: a concentração de outros pares de
cidades, em faixas de vizinhança, com e sem defasagem e em logaritmo. São
colunas do painel de estimação do artigo, construção espacial dos autores
(artigo, seção de identificação), e entram na estimação como estão.

| Instrumento | Definição (`docs/dictionary.md`) | Bloco ODDS | Bloco MINS |
|---|---|---|---|
| `h1_maxcthhi` | a concentração de cidade de outros pares na faixa de vizinhança 1 | — | sim |
| `h2_maxcthhi` | idem, faixa 2 | — | sim |
| `h3_maxcthhi` | idem, faixa 3 | sim | sim |
| `lnh1_maxcthhi` | logaritmo natural de `h1_maxcthhi` | sim | — |
| `l1h1_maxcthhi` | `h1_maxcthhi` no mês anterior; nulo no primeiro mês da rota | sim | — |
| `l1h2_maxcthhi` | `h2_maxcthhi` no mês anterior; nulo no primeiro mês da rota | sim | — |
| `h2_rthhi` | a concentração de rota dos pares vizinhos, faixa 2 | sim | — |

Há duas listas (`INSTRUMENTS_ODDS`, `INSTRUMENTS_MINS`): cinco instrumentos
excluídos para as colunas ODDS e ODDSD, três para as colunas em minutos. O
artigo apresenta uma só estratégia de identificação e não explica a
diferença; ela não é unificada aqui. A evidência de que as duas listas são as
que geraram as tabelas está nos graus de liberdade: com duas endógenas, o J
de Hansen tem $`5 - 2 = 3`$ graus de liberdade no bloco ODDS e $`3 - 2 = 1`$
no bloco MINS, e são exatamente esses os graus de liberdade que os pares
publicados (J, p-valor) implicam quando invertidos
(`docs/notes/replication.md`). A hipótese de exclusão é a do capítulo 4, seção
3: choques de estratégia e de custo de uma empresa se refletem na sua
concentração em várias cidades ao mesmo tempo, e o atraso de uma rota-mês não
muda a concentração dos pares vizinhos.

## 5. Os estimadores

**2SGMM.** Com $`z_{rt}`$ o vetor de instrumentos — os regressores incluídos,
as dummies e os instrumentos excluídos —, a condição de momento é

```math
\mathrm{E}[\, z_{rt}\, \varepsilon_{rt} \,] = 0 \tag{6.3}
```

e o estimador GMM em dois passos é

```math
\hat\beta = (X'Z\,\hat W\,Z'X)^{-1}\, X'Z\,\hat W\, Z'y, \qquad \hat W = \hat S^{-1} \tag{6.4}
```

O primeiro passo é o 2SLS, com $`\hat W = (Z'Z)^{-1}`$; os seus resíduos
estimam a covariância de longo prazo $`\hat S`$ dos momentos, com o kernel da
seção 6, e o segundo passo usa $`\hat W = \hat S^{-1}`$, o peso eficiente sob
heterocedasticidade e autocorrelação. É o que `IVGMM(...).fit(iter_limit=2)`
do `linearmodels` faz (`src/airline_delays/estimation/estimators.py`). Com
mais instrumentos que endógenas o sistema é sobreidentificado, e o teste J de
Hansen usa a folga:

```math
J = N\,\bar g'\,\hat S^{-1}\,\bar g \;\sim\; \chi^2_{L - k_2} \tag{6.5}
```

com $`\bar g`$ a média amostral dos momentos, $`L`$ o número de instrumentos
excluídos e $`k_2`$ o de endógenas. Não rejeitar é não encontrar evidência
contra a ortogonalidade conjunta dos instrumentos.

**LIML.** O estimador de máxima verossimilhança com informação limitada é da
classe $`k`$, com $`k`$ o menor autovalor de um problema generalizado; ele é
menos viesado que o 2SLS e o GMM quando os instrumentos são muitos ou fracos,
ao preço de variância maior. A Tabela 5 o usa como robustez, com a mesma
amostra e os mesmos regressores. O `IVLIML` do `linearmodels` expõe o Sargan,
não o J; aqui o J da Tabela 5 sai de `hansen_j()`, que avalia a matriz de
ponderação HAC nos resíduos do LIML — o que o `ivreg2` imprime para qualquer
estimador robusto, e a razão de o J publicado da Tabela 5 ser quase igual ao
da Tabela 3.

**OLS.** A Tabela 6 estima (6.2) por mínimos quadrados, sem instrumentar, com
os mesmos erros-padrão HAC; a coluna (4) da Tabela 4 faz o mesmo sem as duas
concentrações. É a comparação que dá ao artigo o seu argumento identificador
(capítulo 4, seção 3; capítulo 7).

## 6. Os erros-padrão HAC

Os erros-padrão e a matriz $`\hat S`$ usam o kernel de Bartlett com $`b`$
defasagens:

```math
\hat S = \hat\Gamma_0 + \sum_{j=1}^{b} w_j\,(\hat\Gamma_j + \hat\Gamma_j'), \qquad \hat\Gamma_j = \frac{1}{N}\sum_{i} g_i\, g_{i-j}' \tag{6.6}
```

```math
w_j = 1 - \frac{j}{b + 1} \tag{6.7}
```

A largura de banda é $`b = 4`$ na convenção do `linearmodels`
(`estimation.bandwidth`; `HAC_BANDWIDTH`). É a mesma coisa que `bw(5)` do
`ivreg2` do Stata, que pesa a defasagem $`j`$ por $`1 - j/5`$ para
$`j = 0, \dots, 4`$: quatro aqui é cinco lá, e cinco é o $`T^{1/3}`$ com
$`T = 144`$ meses que o artigo declara — 5,24, que arredonda para 5
(`specification.py`). Um teste fixa a convenção: `bartlett_weights(4)`
devolve $`[0{,}8;\ 0{,}6;\ 0{,}4;\ 0{,}2]`$ (`tests/test_estimation_kp.py`).

Duas decisões acompanham o kernel. A defasagem é medida na ordem das linhas —
o painel ordenado por rota e mês —, que é o que o `linearmodels` faz;
`hac_moment_cov()` (`src/airline_delays/estimation/kp.py`) oferece também a
versão que mede a defasagem só dentro da mesma rota, como um `tsset`, e a
diferença entre as duas é uma grandeza medida, não uma questão de gosto. A
correção de amostra finita está ligada (`debiased=True`): o `ivreg2` sem
`small` divide por $`N`$, com `small` divide por $`N - K`$ e só então imprime
uma estatística F — e as tabelas publicadas imprimem uma.

| Questão | Decisão | Base |
|---|---|---|
| kernel | Bartlett, $`b = 4`$ (`linearmodels`) = `bw(5)` (Stata) | $`T^{1/3}`$ com $`T = 144`$, declarado pelo artigo |
| correção de amostra finita | ligada | as tabelas publicadas imprimem a estatística F, que o `ivreg2` só imprime com `small` |
| dummies sazonais | entram | o artigo fala em *seasonality controls*; a decisão é medida nos dois sentidos (capítulo 7, seção 10) |
| efeitos fixos | explícitos; uma dummy de rota omitida; colineares removidas por QR | o código dos autores não usa `partial()` nem `xtivreg2` |
| endógenas | só `rthhi` e `maxcthhi` | reproduz os graus de liberdade publicados do J |
| instrumentos | duas listas, não unificadas | os graus de liberdade implícitos nos pares (J, p-valor) publicados |

## 7. A amostra, na ordem em que o artigo a aplica

Cada tabela abre com o mesmo bloco de filtros, reproduzido por
`build_sample()` (`src/airline_delays/estimation/sample.py`) na ordem em que o
código dos autores o executa. Os números são de `reports/summary.json`, bloco
`estimation.sample`.

| Passo | Regra | Rota-meses | Rotas |
|---|---|---|---|
| o painel de estimação do artigo | 2002-01 a 2013-12; nenhuma linha fora da janela (`n_outside_window`) | 24.589 | 209 |
| `drop if fsc_oddsarr==.` | remove a rota-mês sem o regressando ODDS | 20.655 | — |
| `findsingletons k ; drop if _count_k<=5` | remove a rota com cinco ou menos observações (`SINGLETON_CUTOFF`) | 20.630 | 190 |

Dois detalhes do filtro não são redundância. Primeiro, ele morde pelo
regressando ODDS em todas as colunas da tabela, inclusive nas colunas em
minutos, cujo regressando nunca é nulo: é deliberado, para que as seis colunas
de uma tabela corram sobre a mesma amostra. A Tabela 7 troca o filtro por
`fsc_oddsdep`, e é por isso que o seu N publicado é 19.408 e 19.579, e não
19.419 e 19.590 (artigo, Tabelas 3 e 7). Segundo, as colunas (1) e (2) perdem
ainda as rota-meses em que os instrumentos defasados não existem — o primeiro
mês de cada rota no painel —, e por isso o seu N reestimado é 20.450, contra
20.630 nas colunas em minutos (`reports/replication/summary.json`,
`table3.n_obs`). A coluna (4) da Tabela 4, OLS sem concentrações, não precisa
dos instrumentos e é a única da tabela com a amostra maior.

## 8. Kleibergen–Paap, escrita do zero

**O que a estatística testa.** Com duas endógenas e $`L`$ instrumentos
excluídos, a forma reduzida é $`\tilde Y = \tilde Z\,\Pi + V`$, com $`\Pi`$
uma matriz $`L \times k_2`$ e o til marcando o que sobra depois de parcializar
os regressores incluídos e as dummies. Os instrumentos identificam os
coeficientes das endógenas se, e só se, $`\Pi`$ tem posto pleno, $`k_2`$. A
estatística $`\mathrm{rk}`$ de Kleibergen e Paap (2006) testa a hipótese nula
de que o posto é $`q`$; o "KP statistic" das tabelas do artigo é o teste de
subidentificação, $`q = k_2 - 1`$: rejeitar é dizer que os instrumentos
identificam. Ao contrário do teste de Cragg–Donald, ela é robusta a
heterocedasticidade e autocorrelação, e por isso é a que o `ivreg2` imprime
com erros-padrão HAC.

**Por que foi escrita aqui.** Nenhum pacote Python a implementa, e isso foi
conferido no código instalado, não só na documentação: o `linearmodels` dá F
parcial e R² parcial de primeiro estágio, J de Hansen, Wu–Hausman e Sargan; o
`pyfixest` tem o F efetivo para uma só endógena; o `ivmodels` tem um teste de
posto de Cragg–Donald e um teste LM para $`\beta`$, que é teste de parâmetro,
não de posto. Fora do Python, as implementações de referência são o
`ranktest` do Stata e o `ivreg2r` do R. `src/airline_delays/estimation/kp.py`
a escreve a partir do artigo original, em quatro passos.

```math
\hat\Pi = (\tilde Z'\tilde Z)^{-1}\,\tilde Z'\tilde Y \tag{6.8}
```

```math
\hat\Theta = (\tilde Z'\tilde Z/N)^{1/2}\; \hat\Pi\; \hat\Sigma_{vv}^{-1/2} \tag{6.9}
```

```math
\hat\Theta = U\, S\, V' \tag{6.10}
```

```math
\mathrm{rk} = N\; \mathrm{vec}(A_\perp'\hat\Theta B_\perp)'\; \big[(B_\perp \otimes A_\perp)'\, \hat W_\Theta\, (B_\perp \otimes A_\perp)\big]^{-1}\; \mathrm{vec}(A_\perp'\hat\Theta B_\perp) \tag{6.11}
```

(6.8) é a forma reduzida por mínimos quadrados. (6.9) a normaliza na métrica
das correlações canônicas: $`\hat\Sigma_{vv}`$ é a covariância dos resíduos
da forma reduzida, e a normalização importa — a partição da decomposição em
valores singulares não é invariante à métrica, e alimentar $`\hat\Pi`$ cru dá
outro número. (6.10) é a decomposição em valores singulares de
$`\hat\Theta`$; $`A_\perp`$ são as $`L - q`$ últimas colunas de $`U`$ e
$`B_\perp`$ as $`k_2 - q`$ últimas de $`V`$, que geram o complemento do posto
$`q`$. (6.11) é a forma quadrática sobre a parte de $`\hat\Theta`$ que teria
de ser zero sob a nula, com $`\hat W_\Theta`$ a covariância de
$`\sqrt N\,\mathrm{vec}(\hat\Theta)`$, HAC com o mesmo kernel da seção 6; sob
a nula, $`\mathrm{rk}`$ é $`\chi^2`$ com $`(L - q)(k_2 - q)`$ graus de
liberdade — 4 no bloco ODDS e 2 no bloco MINS. As tabelas do artigo trazem
duas versões da mesma $`\mathrm{rk}`$: a **LM**, que constrói a covariância
com os resíduos da forma reduzida restrita ao posto $`q`$ e é o "KP
statistic"; e a **Wald**, com os resíduos irrestritos, que dividida por $`L`$
é o "Weak KP statistic".

**Como foi validada.** A validação não depende de outra implementação da
mesma coisa. Com a covariância dos coeficientes da forma reduzida na forma
i.i.d., $`\hat W_\Theta`$ vira a identidade e, na nula de subidentificação,
as duas versões têm de colapsar em quantidades com fórmula fechada: a Wald na
estatística de Cragg–Donald, $`N\lambda/(1 - \lambda)`$, e a LM na estatística
de correlação canônica de Anderson, $`N\lambda`$, com $`\lambda`$ a menor
correlação canônica ao quadrado entre endógenas e instrumentos parcializados.
As duas identidades valem até a precisão de máquina, em vários formatos de
problema, contra `cragg_donald()` do mesmo arquivo — que passa por uma QR de
cada bloco e uma decomposição em valores singulares das projeções e não
compartilha código com `kp_rk()`. Se a normalização de (6.9) estivesse errada,
nenhuma das duas fecharia. Os testes estão em `tests/test_estimation_kp.py`:
`test_wald_collapses_to_cragg_donald_under_iid_errors`,
`test_lm_collapses_to_anderson_under_iid_errors`,
`test_collapse_holds_across_shapes`, `test_normalisation_matters` e, contra o
painel de estimação do artigo,
`test_identification_statistics_against_the_published_table_3`.

**Contra os valores publicados.** A tabela compara, nas quatro colunas
distintas da Tabela 3, o KP publicado com o reestimado — as colunas (5) e (6)
repetem as estatísticas de (3) e (4), porque têm as mesmas endógenas, os
mesmos instrumentos e a mesma amostra (`reports/replication/results.json`,
`table3.comparison.<coluna>.stats.kp_lm` e `weak_kp_f`, com
`relative_difference`).

| Coluna | Bloco | KP (rk LM) publicado | reestimado | diferença relativa | Weak KP (rk Wald F) publicado | reestimado | diferença relativa |
|---|---|---|---|---|---|---|---|
| (1) | ODDS, 5 instrumentos | 154,2698 | 159,4329 | +3,3% | 34,0972 | 36,2908 | +6,4% |
| (2) | ODDS, 5 instrumentos | 139,2305 | 145,5067 | +4,5% | 30,5968 | 32,8812 | +7,5% |
| (3) e (5) | MINS, 3 instrumentos | 30,7876 | 40,2264 | +30,7% | 10,3854 | 14,0710 | +35,5% |
| (4) e (6) | MINS, 3 instrumentos | 29,8792 | 35,4730 | +18,7% | 10,0724 | 12,3757 | +22,9% |

Nas colunas ODDS a implementação acerta o nível e a estrutura interna — a
razão entre a Wald e a LM implícita no publicado reaparece no reestimado. Nas
colunas MINS a distância é maior porque, com três instrumentos e duas
endógenas, o sistema é quase exatamente identificado e a estatística fica
muito sensível ao tamanho da amostra — e as amostras diferem (capítulo 7,
seção 9). O que fecha até a precisão de máquina é a álgebra; o que acompanha a
amostra é o nível.

## 9. Como ler uma coluna da Tabela 3

Uma coluna publicada traz coeficientes com o erro-padrão entre parênteses e
estrelas — \*\*\* a 1%, \*\* a 5%, \* a 10% —, seguidos das estatísticas da
coluna. A coluna (2), o modelo de base com as binárias de baixo custo, lê-se
assim (artigo, Tabela 3; `src/airline_delays/estimation/published.json`,
`table3.columns.2`).

| Linha da coluna | Valor publicado | O que diz |
|---|---|---|
| `rthhi` | +0,8192 (0,410) \*\* | mais concentração na rota, mais chances de atraso: o canal concorrência–qualidade |
| `maxcthhi` | −1,5144 (0,527) \*\*\* | mais concentração na cidade-extremo mais concentrada, menos chances de atraso: internalização |
| `lcc` | −0,0412 (0,072) | sem estrela: a presença na rota não é significante |
| `maxalccfu` | −0,4234 (0,179) \*\* | uma empresa de baixo custo numa cidade-extremo reduz as chances de atraso das incumbentes |
| Nr observations | 19.419 | a amostra da coluna, depois dos filtros da seção 7 e da perda dos instrumentos defasados |
| Adj. R-squared; RMSE | 0,6800; 0,5890 | ajuste e erro da regressão, em unidades do log da razão de chances |
| J statistic; p-value | 3,2199; 0,3589 | com 3 graus de liberdade, não rejeita a ortogonalidade dos instrumentos |
| KP statistic (rk LM) | 139,2305 | com 4 graus de liberdade, rejeita a subidentificação: os instrumentos identificam |
| Weak KP statistic (rk Wald F) | 30,5968 | a versão Wald dividida por $`L = 5`$: a régua de instrumentos fracos robusta a HAC |
| Weak CD statistic (Cragg–Donald F) | 83,4722 | a mesma régua sob erros i.i.d. |
| F statistic | 76,576 | o Wald conjunto do `ivreg2` sobre todos os regressores; não reproduzido aqui (capítulo 7, seção 8) |

A regra prática são quatro perguntas, nesta ordem. Os instrumentos identificam
(KP)? São fortes (Weak KP, Weak CD)? São ortogonais ao erro (J)? Só então o
coeficiente e as suas estrelas. É a ordem em que o capítulo 7 lê cada coluna
publicada e a sua reestimação.

## Escopo e próximos passos

Este capítulo fixa a especificação e a identificação; não reestima nada. As
constantes das seções 2 a 7 estão em
`src/airline_delays/estimation/specification.py`, e qualquer painel de
rota-mês que traga o contrato `REQUIRED_COLUMNS` — os nomes de variável do
próprio artigo — entra em `airline-delays estimate --panel`; um que não traga
uma coluna é recusado com o nome do que falta, porque uma coluna que mede algo
parecido não é substituta. O passo seguinte é o capítulo 7: as Tabelas 2–7
reestimadas sobre o painel de estimação do artigo, célula a célula contra o
publicado. Para a estatística de Kleibergen–Paap, o passo seguinte é um painel
sintético com estatísticas conhecidas em forma fechada, que tornaria a
checagem contra a Tabela 3 independente do artigo (`ROADMAP.md`).

## Onde conferir

- `src/airline_delays/estimation/specification.py` — `EXOG_PARTIAL`,
  `LCC_TERMS`, `ENDOG`, `INSTRUMENTS_ODDS`, `INSTRUMENTS_MINS`,
  `HAC_BANDWIDTH`, `DEBIASED`, `WITH_SEASONALITY`, `SINGLETON_CUTOFF`,
  `COEF_ORDER`, `COEF_LABEL`.
- `src/airline_delays/estimation/loader.py`, `sample.py`, `estimators.py` e
  `kp.py` — as dummies, a amostra, os estimadores e a estatística de
  Kleibergen–Paap; as colunas de cada tabela, de
  `src/airline_delays/estimation/table3.py` a `table7.py`.
- `tests/test_estimation_kp.py` e `tests/test_estimation.py` — as identidades
  algébricas, e os filtros e a Tabela 2 sobre um painel sintético e sobre o
  painel publicado.
- `reports/summary.json` — `estimation.sample`, `estimation.bandwidth`;
  `reports/replication/results.json` — as estatísticas de identificação de
  cada coluna, com `relative_difference`;
  `reports/replication/sensitivity.json` — `n_params`.
- `docs/dictionary.md`, camada `article_panel` — a definição de cada
  regressando, regressor e instrumento.
- `docs/notes/replication.md` — a nota de pesquisa com a base de cada decisão
  de estimação.

Referências completas em [bibliografia.md](bibliografia.md).
