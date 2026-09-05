# Os resultados e a replicação das Tabelas 2–7

Português (ADR-0006).

Este capítulo lê o que Bendinelli, Bettini & Oliveira (2016, *Transportation
Research Part A* 85, 39-52, doi 10.1016/j.tra.2016.01.001) encontraram e o
que este repositório encontra ao reestimar as Tabelas 2–7 sobre o painel de
estimação do artigo. Ao terminá-lo, o leitor sabe ler os quatro coeficientes
de estrutura de mercado como economia — internalização no aeroporto,
concorrência na rota, o derrame não-preço de uma empresa de baixo custo e a
inversão de sinal do OLS que justifica instrumentar; sabe o que "replicar"
significa aqui e qual é a régua; conhece o placar das cinco tabelas de
regressão e da Tabela 2, célula a célula onde importa; sabe onde as amostras
publicada e reestimada diferem e o que muda sem as dummies sazonais; e sabe
por que a estimação da monografia de graduação do autor (USP, 2013) não se
compara à do artigo coeficiente a coeficiente. Daqui em diante, "o artigo".
Todo número publicado é uma transcrição de
`src/airline_delays/estimation/published.json`, marcada "(artigo, Tabela N)";
todo número reestimado é um valor de `reports/replication/` ou de
`reports/summary.json`, escritos por `airline-delays estimate` e
`airline-delays summary`; nada é digitado à mão.

## 1. O que o artigo encontrou

O modelo de base é a coluna (2) da Tabela 3: 2SGMM, regressando ODDS, com as
duas binárias de baixo custo; a coluna (2) da Tabela 6 é a mesma
especificação por OLS. A tabela põe os quatro regressores de estrutura de
mercado lado a lado, com os erros-padrão entre parênteses e as estrelas do
artigo — \*\*\* 1%, \*\* 5%, \* 10% (`reports/summary.json`,
`published.table3.col2` e `published.table6.col2`).

| Regressor | O que mede | 2SGMM (artigo, Tabela 3, col. 2) | OLS (artigo, Tabela 6, col. 2) |
|---|---|---|---|
| `rthhi` | HHI de passageiros da rota | +0,8192 (0,410) \*\* | −0,3126 (0,068) \*\*\* |
| `maxcthhi` | HHI de passageiros da cidade-extremo mais concentrada | −1,5144 (0,527) \*\*\* | +0,1057 (0,196) |
| `lcc` | Gol ou Azul vendendo bilhetes na rota | −0,0412 (0,072) | −0,1636 (0,033) \*\*\* |
| `maxalccfu` | Gol ou Azul presente numa das cidades-extremo | −0,4234 (0,179) \*\* | −0,1793 (0,137) |
| N | | 19.419 | 19.590 |

Quatro leituras, na ordem do capítulo 4
([04-do-modelo-as-hipoteses.md](04-do-modelo-as-hipoteses.md)).

**Internalização no aeroporto.** O coeficiente de `maxcthhi` é negativo a 1%
no 2SGMM: onde uma empresa domina a cidade-extremo mais concentrada da rota,
as chances de uma chegada das empresas de serviço completo atrasar mais de
quinze minutos são menores, tudo o mais constante. É a Proposição 1 do
capítulo 3 vista nos dados — quem sofre a maior parte do congestionamento que
causa a si mesmo programa com mais cuidado — e a hipótese H1 confirmada.

**Concorrência na rota.** O coeficiente de `rthhi` é positivo a 5%: mais
concentração na própria rota vem com mais chances de atraso. O modelo deixava
o sinal em aberto, entre menos voos e menos incentivo a cumprir horário; o
artigo lê o sinal positivo como o canal concorrência–qualidade. A separação
entre `rthhi` e `maxcthhi` é o que permite medir os dois canais ao mesmo
tempo: poder de mercado onde a empresa vende, internalização onde ela
congestiona.

**O derrame não-preço.** A presença de uma empresa de baixo custo na rota,
`lcc`, não é significante no 2SGMM; a presença numa das cidades-extremo,
`maxalccfu`, reduz as chances de atraso das incumbentes a 5%. O efeito opera
pela cidade, sobre rotas em que a entrante nem sequer voa — é o *spillover*
não-preço do título do artigo, e a Pressuposição 3 da monografia medida onde
o modelo a colocava.

**A inversão de sinal.** No OLS as duas concentrações têm o sinal oposto:
`rthhi` negativo a 1%, `maxcthhi` positivo sem estrela. Se a endogeneidade
fosse inócua, os dois estimadores dariam o mesmo sinal. A direção do viés é a
que a simultaneidade do jogo prevê — no equilíbrio, voos, participações e
atraso são decididos juntos —, e é isso que faz da Tabela 6 o argumento
identificador do artigo, não um exercício de robustez. Nas colunas em minutos
os dois estimadores já concordam no sinal e só a magnitude muda: na coluna (4)
da Tabela 3, `rthhi` é +30,0753 (8,853) \*\*\*, `maxcthhi` é −19,1045 (6,514)
\*\*\*, `lcc` sai positivo a 10%, +2,4889 (1,464), e `maxalccfu` é −0,4861
(1,683), sem estrela (artigo, Tabela 3).

## 2. O que "replicar" significa aqui

A reestimação roda sobre o mesmo painel em que os autores estimaram — o painel
de estimação do artigo, publicado neste repositório (ADR-0020; capítulo 5,
[05-os-dados.md](05-os-dados.md)) —, com os filtros de amostra na ordem do
código dos autores e a especificação do capítulo 6
([06-especificacao-e-identificacao.md](06-especificacao-e-identificacao.md)),
portada do Stata para Python (`linearmodels`), com as dummies reconstruídas
pelo código. `airline-delays estimate` (`just estimate`) estima as seis
tabelas em 39,3 s (`estimation.seconds`) e compara cada coeficiente com o
publicado.

A régua é uma só: a diferença entre o coeficiente reestimado e o publicado,
medida em erros-padrão publicados (`difference_in_se`). É a coluna que decide
se duas estimativas são materialmente diferentes — acima de cerca de dois
erros-padrão elas seriam; a menos de meio, contam a mesma história. O
resultado é lido com três medidas por tabela: quantos coeficientes têm o
sinal publicado, quantos ficam a menos de meio erro-padrão publicado, e a
mediana e o máximo da diferença. "Acompanha de perto" quer dizer exatamente
isso: o mesmo sinal e a mesma ordem de grandeza em quase todas as células, e
nenhuma célula a mais de um erro-padrão publicado. Não quer dizer "reproduz
exatamente": a amostra reestimada é maior que a publicada (seção 9), o kernel
HAC e a correção de amostra finita seguem convenções de software que se
traduzem, não se copiam, e uma decisão de especificação — as dummies sazonais
— teve de ser tomada e medida (seção 10).

## 3. A Tabela 2: as descritivas identificam as variáveis

A Tabela 2 é `corr` mais `summ` de 13 variáveis sobre a amostra de estimação
— 20.630 rota-meses de 190 rotas (`estimation.sample.n_after_singleton_cut`,
`routes`). Reproduzi-la é o que prova que a variável nomeada no código é a
coluna impressa no artigo: os mínimos e máximos são distintivos o bastante
para identificar cada uma (artigo, Tabela 2; `reports/replication/results.json`,
`table2.comparison.univariate`).

| Variável | mín. publicado | mín. reestimado | máx. publicado | máx. reestimado |
|---|---|---|---|---|
| `dailyflcong` | 0,00 | 0,0000 | 78,84 | 78,8387 |
| `dailyflncong` | 0,00 | 0,0000 | 115,80 | 115,8108 |
| `maxprdel` | 0,05 | 0,0496 | 0,70 | 0,6965 |
| `rthhi` | 0,21 | 0,2054 | 1,00 | 1,0000 |
| `maxcthhi` | 0,23 | 0,2295 | 1,00 | 1,0000 |
| `fsc_oddsarr` (ODDS) | −4,90 | −4,8978 | 4,03 | 4,0254 |
| `fsc_minsarr` (MINS) | −9,80 | −9,8000 | 131,91 | 131,9118 |

O triângulo de correlações fecha: 91 células comparadas, diferença absoluta
mediana de 0,0023 e máxima de 0,0123 (`estimation.table2.n_correlations`,
`median_abs_correlation_difference`, `max_abs_correlation_difference`). As
médias e os desvios-padrão diferem na segunda casa em algumas variáveis —
`dailyflncong` 7,87 contra 7,7359, por exemplo (artigo, Tabela 2;
`table2.comparison.univariate.mean`) — pela mesma razão pela qual os N
diferem (seção 9).

## 4. O placar

As cinco tabelas de regressão, com os números de `reports/summary.json`,
bloco `estimation.tables`: coeficientes comparados, quantos com o sinal
publicado, quantos a menos de meio erro-padrão publicado, a mediana e o
máximo da diferença em erros-padrão publicados, e a mediana da razão entre o
erro-padrão reestimado e o publicado.

| Tabela | Estimador | Coeficientes | Sinal igual | A menos de ½ e.p. | Mediana da diferença | Máximo da diferença | Mediana da razão de e.p. |
|---|---|---|---|---|---|---|---|
| Tabela 3 | 2SGMM | 60 | 60 | 53 | 0,240 | 0,691 | 0,946 |
| Tabela 4 | 2SGMM, robustez | 66 | 65 | 51 | 0,221 | 0,907 | 0,992 |
| Tabela 5 | LIML | 60 | 59 | 53 | 0,229 | 0,675 | 0,942 |
| Tabela 6 | OLS | 60 | 59 | 51 | 0,120 | 0,941 | 0,971 |
| Tabela 7 | 2SGMM, partidas | 60 | 59 | 51 | 0,241 | 0,660 | 0,941 |
| **Total** (`estimation.totals`) | | **306** | **302** | **259 (84,6%)** | | **0,94** | |

A maior diferença isolada em todo o conjunto é 0,94 erro-padrão publicado
(`estimation.totals.max_difference_in_se`): `lcc` na coluna (2) da Tabela 6,
−0,1636 (0,033) publicado contra −0,1325 reestimado (artigo, Tabela 6;
`reports/replication/tables.md`). Nenhuma célula chega a um erro-padrão. A
razão mediana dos erros-padrão fica abaixo de 1 em todas as tabelas: os
erros-padrão reestimados são sistematicamente menores que os publicados, o
que é coerente com uma amostra maior.

## 5. Célula a célula, onde importa

As células que sustentam a leitura da seção 1, publicadas e reestimadas, com
a diferença em erros-padrão publicados (`reports/replication/tables.md`).

| Tabela, coluna | Regressor | Publicado [e.p.] | Reestimado [e.p.] | Diferença em e.p. |
|---|---|---|---|---|
| 3, (2) ODDS, 2SGMM | `rthhi` | +0,8192 [0,410] | +0,9028 [0,3993] | 0,20 |
| 3, (2) | `maxcthhi` | −1,5144 [0,527] | −1,4839 [0,5212] | 0,06 |
| 3, (2) | `lcc` | −0,0412 [0,072] | −0,0013 [0,0704] | 0,55 |
| 3, (2) | `maxalccfu` | −0,4234 [0,179] | −0,4417 [0,1869] | 0,10 |
| 3, (2) | `prwheather` | +4,7145 [0,093] | +4,7696 [0,0927] | 0,59 |
| 3, (2) | `maxprdel` | +1,5460 [0,228] | +1,5080 [0,2286] | 0,17 |
| 3, (4) MINS, 2SGMM | `rthhi` | +30,0753 [8,853] | +24,7541 [7,3726] | 0,60 |
| 3, (4) | `maxcthhi` | −19,1045 [6,514] | −16,0126 [5,9779] | 0,47 |
| 3, (4) | `lcc` | +2,4889 [1,464] | +1,8309 [1,2356] | 0,45 |
| 6, (2) ODDS, OLS | `rthhi` | −0,3126 [0,068] | −0,2914 [0,0669] | 0,31 |
| 6, (2) | `maxcthhi` | +0,1057 [0,196] | +0,0938 [0,1911] | 0,06 |
| 6, (2) | `lcc` | −0,1636 [0,033] | −0,1325 [0,0327] | 0,94 |
| 6, (2) | `maxalccfu` | −0,1793 [0,137] | −0,2117 [0,1424] | 0,24 |

Os quatro coeficientes de estrutura de mercado da coluna de base saem com o
sinal publicado, três deles a menos de um quarto de erro-padrão; a exceção é
`lcc`, cujo coeficiente publicado já não era significante e cujo reestimado
fica ainda mais perto de zero. Nas colunas em minutos os coeficientes
reestimados das duas concentrações são menores em valor absoluto que os publicados,
com o mesmo sinal; a diferença fica entre 0,44 e 0,69 erro-padrão publicado
nas oito células de HHI das colunas (3) a (6) da Tabela 3
(`reports/replication/tables.md`).

## 6. A inversão de sinal dos HHI, comparação a comparação

O argumento central do artigo é uma afirmação sobre 12 comparações: dois HHI
vezes seis colunas, OLS (Tabela 6) contra 2SGMM (Tabela 3). O bloco
`estimation.hhi` de `reports/summary.json` conta: 4 inversões nas tabelas
publicadas, 4 na reestimação, as 4 publicadas reproduzidas, e concordância
sobre haver ou não inversão em 12 de 12 (`n_inverted_published`,
`n_inverted_replicated`, `n_inversion_replicates`, `n_pattern_agrees`). As
inversões estão nas colunas (1) e (2), regressando ODDS
(`columns_with_inversion`); nas colunas em minutos OLS e 2SGMM já saem com o
mesmo sinal no artigo, e só a magnitude muda — e o mesmo acontece aqui
(`reports/replication/summary.json`, `hhi_sign_inversions.detail`).

| Coluna | Regressando | Variável | OLS publicado | 2SGMM publicado | Inverte? | OLS reestimado | 2SGMM reestimado | Inverte? |
|---|---|---|---|---|---|---|---|---|
| (1) | ODDS | `rthhi` | −0,2086 | +0,8050 | sim | −0,2080 | +0,8843 | sim |
| (1) | ODDS | `maxcthhi` | +0,1614 | −1,4772 | sim | +0,1540 | −1,4551 | sim |
| (2) | ODDS | `rthhi` | −0,3126 | +0,8192 | sim | −0,2914 | +0,9028 | sim |
| (2) | ODDS | `maxcthhi` | +0,1057 | −1,5144 | sim | +0,0938 | −1,4839 | sim |
| (3) | MINS | `rthhi` | +3,3899 | +30,6290 | não | +3,2388 | +25,0753 | não |
| (3) | MINS | `maxcthhi` | −2,4930 | −19,4278 | não | −1,5739 | −16,5621 | não |
| (4) | MINS | `rthhi` | +2,4833 | +30,0753 | não | +2,3997 | +24,7541 | não |
| (4) | MINS | `maxcthhi` | −2,9092 | −19,1045 | não | −2,0808 | −16,0126 | não |
| (5) | MINS > 15 | `rthhi` | +3,2958 | +31,9607 | não | +3,1446 | +25,8908 | não |
| (5) | MINS > 15 | `maxcthhi` | −2,9449 | −20,9849 | não | −2,0368 | −17,9201 | não |
| (6) | MINS > 15 | `rthhi` | +2,3998 | +31,5567 | não | +2,3180 | +25,7167 | não |
| (6) | MINS > 15 | `maxcthhi` | −3,3809 | −20,6986 | não | −2,5603 | −17,3922 | não |

A afirmação mais afiada do artigo é também a mais barata de conferir, e ela
se sustenta: instrumentar inverte o sinal das duas concentrações exatamente
onde o artigo diz que inverte, e em nenhum outro lugar.

## 7. As quatro células com sinal diferente

Dos 306 coeficientes, 4 saem com sinal diferente do publicado
(`estimation.totals.sign_agreement` = 302). Os quatro são coeficientes muito
menores que o seu próprio erro-padrão publicado, sem estrela no artigo, e a
diferença fica entre 0,09 e 0,52 erro-padrão (`reports/replication/tables.md`).

| Tabela, coluna | Regressor | Publicado [e.p.] | Reestimado | Diferença em e.p. |
|---|---|---|---|---|
| 4, (5) | `dailyflncong` | +0,0007 [0,003] | −0,0003 | 0,33 |
| 5, (2) | `lcc` | −0,0280 [0,073] | +0,0100 | 0,52 |
| 6, (6) | `dailyflcong` | +0,0010 [0,032] | −0,0018 | 0,09 |
| 7, (1) | `cshare` | −0,0053 [0,065] | +0,0092 | 0,22 |

Um coeficiente que vale uma fração pequena do seu erro-padrão não tem sinal
no sentido estatístico; o que estas quatro células registram é que a
reestimação o coloca do outro lado do zero, a uma fração do erro-padrão de
distância. Nenhuma das quatro é um regressor de estrutura de mercado com
estrela.

## 8. Estatísticas de identificação e erros-padrão

**J de Hansen.** Nas 24 colunas que o reportam — as Tabelas 3, 5 e 7 inteiras
e seis colunas da Tabela 4 —, o veredito a 5% é o mesmo no publicado e no
reestimado em todas: as colunas (3) e (5) da Tabela 4 rejeitam a
ortogonalidade nos dois casos, com p-valores publicados de 0,0178 e 0,0047
(artigo, Tabela 4), e as outras 22 não rejeitam nos dois
(`reports/replication/tables.md`, linhas "J p-value"; a contagem é a da seção
7 de `reports/replication.typ`). As duas rejeições são as colunas que retiram
`maxcthhi` ou os controles de atraso da especificação — as que o próprio
artigo apresenta como especificações incompletas.

**Kleibergen–Paap.** As estatísticas de identificação estão no capítulo 6,
seção 8: nas colunas ODDS a reestimação acerta o nível a poucos por cento;
nas colunas em minutos a distância é maior, e a razão é a amostra.

**Erros-padrão.** A mediana da razão entre o erro-padrão reestimado e o
publicado é 0,946 na Tabela 3 e fica abaixo de 1 em todas as tabelas
(`estimation.tables.<tabela>.median_se_ratio`).

**Estatística F.** Não é reproduzida. A F das tabelas publicadas é o Wald
conjunto do `ivreg2` sobre todos os regressores, inclusive as dummies, sob
convenção própria; o análogo do `linearmodels` não mede a mesma coisa, e a
célula fica vazia de propósito (`src/airline_delays/estimation/estimators.py`).
O R² ajustado, o RMSE e o J de cada coluna estão em
`reports/replication/tables.md`, publicado e reestimado lado a lado.

## 9. Nota sobre a amostra

As tabelas publicadas reportam N entre 19.408 e 19.590
(`estimation.n_obs_published_range`). A reestimação sobre o painel publicado,
com os filtros do capítulo 6 na ordem em que o código dos autores os aplica,
dá N entre 20.447 e 20.630 (`estimation.n_obs_replicated_range`), 5,3% a
mais (`estimation.n_obs_excess_pct`). Os dois N ficam registrados lado a lado
em cada coluna de `reports/replication/tables.md` e em
`reports/replication/summary.json` (`n_obs`), e nenhum filtro é reconstruído
para aproximá-los: a ADR-0020 fixa que o placar das tabelas reestimadas
contra as publicadas é o resultado da replicação, e que os dois tamanhos de
amostra são reportados como estão.

## 10. Sensibilidade: as dummies sazonais

O código dos autores cria as 60 dummies sazonais região × mês, e o programa
que decidiria se elas entram na regressão não foi entregue; o artigo fala em
*seasonality controls*. A decisão de incluí-las foi tomada e medida nos dois
sentidos, nas colunas (1) e (2) da Tabela 3
(`reports/replication/sensitivity.json`).

| Coluna | Dummies sazonais | N | Parâmetros | `rthhi` [e.p.] | `maxcthhi` [e.p.] | R² ajustado | J |
|---|---|---|---|---|---|---|---|
| (1) | sim | 20.450 | 396 | +0,8843 [0,3652] | −1,4551 [0,5185] | 0,6713 | 1,7234 |
| (1) | não | 20.450 | 341 | +0,8661 [0,3588] | −1,4078 [0,5103] | 0,6712 | 2,2337 |
| (2) | sim | 20.450 | 398 | +0,9028 [0,3993] | −1,4839 [0,5212] | 0,6710 | 1,7011 |
| (2) | não | 20.450 | 343 | +0,8876 [0,3905] | −1,4371 [0,5133] | 0,6708 | 2,1977 |

Nenhum sinal muda, e as diferenças ficam na segunda casa; incluí-las aproxima
os coeficientes dos publicados. O limiar de outlier do atraso (ADR-0008) não
varia aqui: ele age no nível do voo, antes de agregar, e o painel de
estimação do artigo chega agregado; esse parâmetro pertence à cadeia de
reconstrução do capítulo 5.

## 11. O que 2013 estimou e o que 2016 estimou

A monografia de graduação do autor (USP, 2013) — documento externo, citado e
não redistribuído — estimou a mesma pergunta em outro desenho: um painel
empresa × rota × mês, com a parcela de voos atrasados acima de 30 minutos como
dependente, 87.237 observações, efeitos fixos ponderados, um HHI de rota sobre
voos planejados e uma razão de concentração das duas maiores no aeroporto
(monografia, seções 5 a 7 — documento externo). Encontrou coeficientes
positivos e significantes para as duas medidas de concentração, um efeito
ambíguo para a presença da Gol e um efeito negativo para a Azul no seu próprio
aeroporto, e leu as concentrações como uma "tragédia dos comuns" (monografia,
seção 7 — documento externo). O artigo estimou um painel rota × mês, com o
atraso das empresas de serviço completo acima de 15 minutos, HHI de
passageiros, 2SGMM com instrumentos e erros-padrão HAC.

Os coeficientes não se comparam: unidade de observação, base do HHI,
estimador, regressando e limiar de atraso diferem entre os dois estudos. O que
se compara é a pergunta, e ela é a mesma. É por isso que a regressão da
monografia não é reestimada aqui, nem o seu sinal de concentração é posto ao
lado do do artigo como se fosse a mesma grandeza
(`docs/notes/monografia-2013.md`). O que o painel reconstruído oferece de
comparável é a construção: `rthhi_flights` é o HHI de rota sobre voos
programados, a mesma operação do `hhi` da monografia, e `fsc_prdelarr30m`
carrega o corte de 30 minutos ([apendice-d-extensoes.md](apendice-d-extensoes.md),
seções 3 e 9).

## Escopo e próximos passos

Este capítulo lê os resultados publicados e a sua reestimação sobre o painel
de estimação do artigo; não estima o painel reconstruído, que não traz os HHI
de passageiros nem os instrumentos (capítulo 5, seção 9). O passo seguinte da
replicação é o mesmo da estatística de Kleibergen–Paap: um painel sintético
com estatísticas conhecidas em forma fechada (`ROADMAP.md`). O passo seguinte
do estudo é o capítulo 8 ([08-recepcao.md](08-recepcao.md)): o que o campo
levou destes resultados e o que continua em aberto.

## Onde conferir

- `reports/summary.json` — `published.table3`, `published.table6`;
  `estimation.tables`, `totals`, `hhi`, `table2`, `sample`,
  `n_obs_published_range`, `n_obs_replicated_range`, `n_obs_excess_pct`,
  `seconds`.
- `reports/replication/tables.md` — cada tabela, publicado contra reestimado,
  com a diferença em erros-padrão publicados;
  `reports/replication/summary.json` — o placar por tabela e
  `hhi_sign_inversions.detail`; `reports/replication/results.json` — cada
  célula e cada estatística; `reports/replication/sensitivity.json` — a grade
  da seção 10. Todos escritos por `just estimate`.
- `src/airline_delays/estimation/published.json` — as Tabelas 2–7 transcritas
  do artigo por `src/airline_delays/estimation/published.py`.
- `reports/replication.typ` e `reports/pdf/replication.pdf` — o relatório de
  replicação, que lê os mesmos JSON.
- `docs/notes/replication.md` — a nota de pesquisa da replicação;
  `docs/notes/monografia-2013.md` — a nota sobre a monografia.

Referências completas em [bibliografia.md](bibliografia.md).
