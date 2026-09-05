# Replicação das Tabelas 2–7

Nota de pesquisa em português (exceção deliberada ao inglês do repositório —
`CLAUDE.md`, `DECISIONS.md` ADR-0006). Descreve **como** cada tabela publicada de
Bendinelli, Bettini & Oliveira (2016, *Transportation Research Part A* 85, 39-52,
[`10.1016/j.tra.2016.01.001`](https://doi.org/10.1016/j.tra.2016.01.001)) é
montada aqui, **o que bate** e **o que fica registrado ao lado**.

Nenhum número desta nota é digitado à mão: todos vêm de
`reports/replication/{results,summary,sensitivity}.json` e de
`reports/replication/tables.md`, escritos por `airline-delays estimate`, ou de
`reports/summary.json`. O relatório em PDF é
[`reports/replication.typ`](../../reports/replication.typ), compilado em
`reports/pdf/replication.pdf`.

## 1. Uma fonte, um caminho de código

A entrada da estimação é o painel de estimação do artigo — o painel sobre o
qual os autores estimaram as Tabelas 2–7, publicado neste repositório em
`data/analysis/article_panel_route_month.parquet` (ADR-0020): 24.589
rota-meses × 52 colunas, 209 rotas, 144 meses de 2002-01 a 2013-12, curado uma
vez a partir da base final dos autores (dezembro de 2015) por
`airline-delays article-panel`. O manifesto
`data/analysis/article_panel_manifest.json` registra o sha256 da base de origem
e dos dois arquivos publicados, e a contagem de nulos por coluna.

Sobre ele, `airline-delays estimate` aplica os filtros dos do-files na ordem em
que aparecem (`reports/summary.json`, bloco `estimation.sample`):

| Passo | O que faz | Observações | Rotas |
|---|---|---|---|
| painel publicado | 2002-01 a 2013-12, todas as rotas | 24.589 | 209 |
| `drop if fsc_oddsarr==.` | remove a rota-mês sem o regressando das colunas (1) e (2) | 20.655 | — |
| `findsingletons k ; drop if _count_k<=5` | remove a rota com cinco ou menos observações | 20.630 | 190 |

O contrato do painel é `REQUIRED_COLUMNS`, em
`src/airline_delays/estimation/specification.py`: os nomes de variável do próprio
artigo, porque esta camada é uma porta de uma especificação em Stata e são
esses nomes que identificam cada regressor nas tabelas publicadas. A opção
`--panel` aceita outro painel de rota-mês que traga esse contrato; um painel
que não traga uma coluna é recusado por `PanelIncomplete`
(`src/airline_delays/estimation/loader.py`), que nomeia o que falta. Uma coluna
que mede algo *parecido* com uma variável publicada não é substituta: nenhum
apelido é mapeado. `tests/test_estimation.py` roda os filtros, a Tabela 2 e a
coluna (1) da Tabela 3 sobre um painel sintético construído para esse
contrato, e confere, no painel publicado, que os filtros devolvem a amostra de
estimação.

## 2. A amostra, na ordem exata dos do-files

O bloco de abertura de cada do-file de tabela é o mesmo:

```stata
projbase 18 ; drop fe_* ; drop sz_* ; drop if fsc_oddsarr==. ;
findsingletons k ; drop if _count_k<=5 ; panelset ; effects k ; dummymonthreg
```

Reproduzido em `build_sample()` (`src/airline_delays/estimation/sample.py`).
Dois detalhes que parecem redundância e não são:

1. **O filtro morde pelo regressando das colunas 1–2, não pelo da coluna.**
   `fsc_minsarr` e `fsc_minsp15arr` nunca são *missing*; quem corta é
   `drop if fsc_oddsarr==.`, imposto de propósito para que as seis colunas de
   uma tabela rodem sobre exatamente a mesma amostra. A Tabela 7 troca o filtro
   por `fsc_oddsdep`, e é por isso que o N publicado dela é 19.408/19.579 e não
   19.419/19.590.
2. **`drop fe_*` / `drop sz_*` seguidos de `effects k` / `dummymonthreg`
   existem por causa do corte de *singletons*.** As dummies gravadas na base
   cobrem 209 rotas; depois do corte sobrevivem 190. Recriá-las evita colunas
   identicamente nulas.

As dummies de tempo (`t_1..t_144`) e as 60 sazonais região×mês (`sz_*`) são
**reconstruídas** a partir de `ym`, `o_region` e `d_region` em `add_dummies()`
(`src/airline_delays/estimation/loader.py`), em vez de lidas do painel. A regra
é `sz_{regiao}_m_{mes} = 1` se o mês é `mes` **e** a rota toca a região; cada
linha acende uma ou duas dummies. A base dos autores trazia as 1.052 dummies
geradas; a curadoria não as publicou porque o código as reproduz linha a linha
(`data/analysis/article_panel_manifest.json`, `columns_excluded`).

## 3. As decisões de estimação, e a evidência de cada uma

| Questão | Decisão | Base |
|---|---|---|
| Kernel | Bartlett, `bandwidth=4` | `linearmodels` pesa a defasagem *j* por `1 − j/(bw+1)`; o `ivreg2` com `bw(5)` pesa por `1 − j/5`, j = 0..4. **4 aqui é 5 lá.** E `bw(5)` é o `T^(1/3)` com `T = 144` que o artigo declara. |
| Correção de amostra finita | `debiased=True` | O `ivreg2` sem `small` divide por N; com `small`, por N−K, e só então imprime uma *F statistic* — que aparece nas tabelas publicadas. |
| Dummies sazonais | **entram** | O `dummymonthreg` as cria e o `gregcontrols` não as menciona (§4.6 da especificação); o `.ado` que decidiria não foi entregue. O artigo fala em *seasonality controls*, e incluí-las aproxima mensuravelmente os coeficientes. A escolha é declarada e medida nos dois sentidos (§7). |
| Efeitos fixos | explícitos | O do-file não usa `partial()` nem `xtivreg2`. Entram 189 dummies de rota (uma omitida contra a constante) e `t_2..t_144`; a colinearidade exata cai por QR revelador de posto. |
| Endógenas | só `rthhi` e `maxcthhi` | As dummies de LCC são **exógenas**. Isso contradiz a introdução do artigo, que fala em instrumentar *"all of the market structure variables"*, mas o código é inequívoco — e é o que reproduz os graus de liberdade publicados do J. |
| Instrumentos | duas listas | 5 instrumentos no bloco ODDS (J com 3 g.l.), 3 no bloco MINS (J com 1 g.l.). **Não unificar.** Invertendo os pares (J, p-valor) publicados, os graus de liberdade implícitos batem exatamente com as listas dos do-files — é a evidência mais forte de que os do-files entregues são os que geraram as tabelas. |

As constantes vivem em `src/airline_delays/estimation/specification.py`:
`INSTRUMENTS_ODDS`, `INSTRUMENTS_MINS`, `ENDOG`, `HAC_BANDWIDTH`, `DEBIASED`,
`WITH_SEASONALITY`, `SINGLETON_CUTOFF`.

## 4. Tabela por tabela

* **Tabela 2 (descritivas).** `corr` + `summ` de 13 variáveis sobre a amostra
  filtrada. Mínimos e máximos coincidem até a quarta casa
  (`dailyflcong` máx. 78,8387 contra 78,84; `fsc_minsarr` mín./máx.
  −9,8000/131,9118 contra −9,80/131,91). **É isso que prova a identificação de
  cada variável do código com a coluna do artigo**, em vez de supô-la. O
  triângulo de correlações fecha com diferença absoluta mediana de 0,002 e máxima
  de 0,012 em 91 células (`reports/replication/tables.md`).
* **Tabela 3 (2SGMM, 6 colunas).** O modelo de base: três regressandos (ODDS,
  MINS, MINS > 15) × duas especificações (sem e com as dummies de LCC).
* **Tabela 4 (robustez, 7 colunas, todas ODDS).** O mapa de omissões vem do
  `_tab3.do` e bate célula a célula com o publicado: (2) tira `rthhi`; (3) tira
  `maxcthhi`; (4) tira os dois **e** troca para OLS — é a única coluna sem
  estatísticas de identificação, e a única com a amostra maior, porque não
  precisa dos instrumentos defasados; (5) tira clima, incidentes, conexões e
  atraso máximo da cidade; (6) tira `dailyflncong`; (7) tira as duas contagens de
  voo.
* **Tabela 5 (LIML).** Mesma amostra, mesmos regressores, estimador diferente.
  O `linearmodels.iv.IVLIML` expõe Sargan, não o J de Hansen; aqui o J vem de
  `hansen_j()` (`src/airline_delays/estimation/estimators.py`), que avalia a
  matriz de ponderação ótima HAC nos resíduos do LIML — que é o que o `ivreg2`
  imprime para qualquer estimador robusto, e é por isso que o J publicado da
  Tabela 5 é quase igual ao da Tabela 3.
* **Tabela 6 (OLS).** A demonstração do próprio artigo de que ignorar a
  endogeneidade **inverte o sinal dos dois HHIs**. Replica sem exceção: em ODDS
  o `rthhi` sai negativo no OLS e positivo no 2SGMM, e o `maxcthhi` faz o
  caminho inverso. O argumento central do artigo se sustenta.
* **Tabela 7 (partidas).** Tabela 3 com os regressandos de partida e o filtro de
  amostra correspondente.

## 5. Kleibergen–Paap: por que foi preciso escrever do zero

**Nenhum pacote Python implementa a estatística `rk`** de Kleibergen e Paap
(2006, *Journal of Econometrics* 133, 97–126). Verificado por inspeção do código
instalado, não só da documentação: o `linearmodels` 7.0 dá F parcial e R² parcial
de primeiro estágio, J de Hansen, Wu–Hausman e Sargan, e nenhuma ocorrência de
*kleibergen*, *ranktest* ou *cragg*; o `pyfixest` tem o F efetivo de
Olea–Pflueger para **uma** endógena; o `ivmodels` tem um teste de posto de
Cragg–Donald e o LM de Kleibergen (2002) **para β**, que é teste de parâmetro,
não de posto. Fora do Python: `ranktest` (Stata) e `ivreg2r` (R).

`src/airline_delays/estimation/kp.py` a escreve a partir do artigo. Com `Ỹ` e
`Z̃` as endógenas e os instrumentos excluídos depois de parcializar os
regressores incluídos:

```
Π̂    = (Z̃′Z̃)⁻¹ Z̃′Ỹ
Θ̂    = (Z̃′Z̃/N)^{1/2} · Π̂ · Σ̂_vv^{-1/2}
W_Θ  = (Σ̂_vv^{-1/2} ⊗ (Z̃′Z̃/N)^{1/2}) · W_Π · (·)′
SVD    Θ̂ = U S V′ ;  A⊥ = U[:, q:] ,  B⊥ = V[:, q:]
rk     = N · vec(A⊥′Θ̂B⊥)′ [ (B⊥ ⊗ A⊥)′ W_Θ (B⊥ ⊗ A⊥) ]⁻¹ vec(A⊥′Θ̂B⊥)
```

Três armadilhas:

1. **A normalização importa.** O particionamento da SVD não é invariante à
   métrica — usar `Π̂` cru dá outro número.
2. **`q = k₂−1`** é o teste de *sub*identificação (o *KP statistic* das tabelas);
   os graus de liberdade `(L−q)(k₂−q)` dão 4 nas colunas ODDS e 2 nas MINS.
3. **LM e Wald são duas versões da mesma `rk`.** A LM usa os resíduos da forma
   reduzida **restrita a posto q** na matriz de covariância; a Wald usa os
   irrestritos e, dividida por L, vira o *Weak KP statistic*. O `ivreg2` reporta
   uma de cada.

### A validação não depende de outra implementação da mesma coisa

Com a covariância de `√N vec(Π̂)` na forma i.i.d., `W_Θ` vira a identidade e, na
hipótese `q = k₂−1`, as duas versões têm de colapsar em quantidades com fórmula
fechada:

* a **Wald** na estatística de Cragg–Donald, `N·λ/(1−λ)`;
* a **LM** na estatística de correlação canônica de Anderson, `N·λ`,

com λ a menor correlação canônica ao quadrado. As duas identidades valem **até a
precisão de máquina**, para vários formatos de problema, contra
`cragg_donald()` do mesmo arquivo — que passa por QR de cada bloco e uma SVD das
projeções e **não compartilha código** com `kp_rk()` (raiz quadrada simétrica,
produto de Kronecker, pseudo-inversa). Se a normalização de `Θ̂` estivesse
errada, nenhuma das duas fecharia. Está em `tests/test_estimation_kp.py`.

Contra os valores publicados (`reports/replication/tables.md`, linha "KP
statistic (rk LM)"): nas colunas ODDS a implementação acerta o nível (+3,3% a
+6,4%) e a estrutura interna — a razão Wald/LM implícita no publicado reaparece
na réplica. Nas colunas MINS a distância é maior (+18,7% a +31,0%), porque com 3
instrumentos e 2 endógenas o sistema é quase exatamente identificado e a
estatística fica muito sensível ao N.

## 6. O que bate

O placar de `reports/summary.json` (bloco `estimation`), calculado por
`airline-delays estimate` a partir de `reports/replication/results.json`:

| Medida | Valor | Chave |
|---|---|---|
| coeficientes comparados nas cinco tabelas de regressão | 306 | `totals.coefficients` |
| com o mesmo sinal do publicado | 302 | `totals.sign_agreement` |
| a menos de meio erro-padrão publicado | 259 (84,6%) | `totals.within_half_se`, `totals.within_half_se_pct` |
| maior desvio isolado, em erros-padrão publicados | 0,94 | `totals.max_difference_in_se` |
| comparações da inversão de sinal dos HHI (OLS × 2SGMM) | 12 | `hhi.n_comparisons` |
| inversões publicadas; reproduzidas | 4; 4 | `hhi.n_inverted_published`, `hhi.n_inversion_replicates` |
| concordância sobre haver ou não inversão | 12 de 12 | `hhi.n_pattern_agrees` |
| razão mediana dos erros-padrão, Tabela 3 | 0,946 | `tables.table3.median_se_ratio` |

A inversão de sinal dos HHIs entre OLS e 2SGMM — o argumento central do
artigo — ocorre nas colunas (1) e (2), regressando `ODDS`, e as 4 replicam.
Nas outras 8 (`MINS`, `MINS > 15`) OLS e 2SGMM já saem com o **mesmo** sinal
na tabela publicada, e só a magnitude muda (`reports/replication/tables.md`,
"HHI sign inversion"). Nas 24 colunas que reportam J de Hansen, nenhuma muda de
veredito a 5%: as mesmas 22 não rejeitam ortogonalidade e as mesmas 2 rejeitam
(`reports/replication/results.json`, campo `j_p` de cada coluna). Os
erros-padrão reestimados saem sistematicamente abaixo dos publicados: na
Tabela 3, 51 dos 60 (`results.json`, `replicated_se` contra `published_se`).

**Nota sobre a amostra.** As tabelas publicadas reportam N entre 19.408 e
19.590 (`estimation.n_obs_published_range`); a reestimação sobre o painel
publicado, com os filtros da seção 2, dá N entre 20.447 e 20.630
(`estimation.n_obs_replicated_range`), 5,3% a mais
(`estimation.n_obs_excess_pct`). Os dois valores ficam registrados lado a lado
em cada coluna de `reports/replication/tables.md` e em
`reports/replication/summary.json` (`n_obs`); nenhum filtro é reconstruído
para aproximá-los (ADR-0020).

**Estatísticas não comparáveis.** A *F statistic* das tabelas publicadas é o
Wald conjunto do `ivreg2` sobre cerca de 340 regressores, sob convenção
própria; o análogo do `linearmodels` não mede a mesma coisa, e a célula fica
vazia de propósito. O J de Hansen, o R² ajustado e o RMSE de cada coluna estão
em `reports/replication/tables.md`, publicado e reestimado lado a lado.

## 7. Sensibilidade

Um eixo: as 60 dummies sazonais região×mês, interruptor puro de especificação
(`reports/replication/sensitivity.json`). Nas colunas (1) e (2) da Tabela 3,
`rthhi` vai de 0,8843 para 0,8661 e de 0,9028 para 0,8876 sem elas;
`maxcthhi`, de −1,4551 para −1,4078 e de −1,4839 para −1,4371. Nenhum sinal
muda.

O limiar de *outlier* do atraso (ADR-0008) não varia aqui: ele age no nível do
voo, antes de agregar, e o painel de estimação do artigo chega agregado. Esse
parâmetro é do pipeline de reconstrução (`docs/notes/features.md`).

## 8. Escopo

* **Os instrumentos são colunas do painel publicado.** Os sete instrumentos
  do tipo Hausman (`h1_maxcthhi`, `h2_maxcthhi`, `h3_maxcthhi`,
  `lnh1_maxcthhi`, `l1h1_maxcthhi`, `l1h2_maxcthhi`, `h2_rthhi`) são a
  construção espacial dos autores e entram na estimação como estão;
  `src/airline_delays/schema/columns.py` documenta cada um na camada
  `article_panel`.
* **`_tab7.do`.** Troca `maxcthhi` por um HHI de cidade ponderado por
  passageiros e não corresponde a tabela publicada alguma; não é reestimado.
* **A equação (22) da monografia de 2013** responde a outra pergunta, em outra
  unidade, e não é reestimada (`docs/notes/monografia-2013.md`).

## Como rodar

```bash
# tudo: as seis tabelas, o placar e a grade de sensibilidade (menos de um minuto)
uv run airline-delays estimate

# uma tabela só
uv run airline-delays estimate --tables table2,table3

# outro painel que traga o contrato REQUIRED_COLUMNS, escrevendo fora de reports/
uv run airline-delays estimate --panel /caminho/para/outro_painel.parquet --outdir /tmp/saida

# refazer summary.json e tables.md a partir de results.json, sem reestimar
uv run airline-delays estimate --rescore

# relatório em PDF (`just report` compila os três: study, replication, prediction)
typst compile --root . reports/replication.typ reports/pdf/replication.pdf
```

`just estimate` é a mesma coisa que o primeiro comando. Os números publicados
são reextraídos do texto do artigo por
`src/airline_delays/estimation/published.py` (`--source-text`), que escreve
`src/airline_delays/estimation/published.json`.
