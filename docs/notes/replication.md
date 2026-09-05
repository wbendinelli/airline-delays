# Replicação das Tabelas 2–7

Nota de pesquisa em português (exceção deliberada ao inglês do repositório —
`CLAUDE.md`, `DECISIONS.md` ADR-0006). Descreve **como** cada tabela publicada de
Bendinelli, Bettini e Oliveira (2016, *Transportation Research Part A* 85, 39–52,
[`10.1016/j.tra.2016.01.001`](https://doi.org/10.1016/j.tra.2016.01.001)) é
montada aqui, **o que bate**, **o que não bate** e **por quê**.

Nenhum número desta nota é digitado à mão: todos vêm de
`reports/replication/private/{results,summary,sensitivity}.json` e de
`reports/replication/private/tables.md` (a execução pública escreve em `reports/replication/public/`), escritos por
`uv run python -m replication.run`. A lista formal de divergências está em
[`docs/declared-differences.md`](../declared-differences.md); o relatório em PDF
é [`reports/replication.typ`](../../reports/replication.typ).

## 1. Duas fontes, um caminho de código

`replication/common.py` expõe um interruptor, `Source`:

* **`private`** — o painel final dos autores, alcançado *só* pela variável de
  ambiente `AIRLINE_DELAYS_PRIVATE_DIR`. Nada dele é copiado para o repositório,
  nada dele é versionado (`SECURITY.md`, gancho `no-private-data`). É o
  **gabarito**: é a base de onde saíram as tabelas publicadas, então uma
  diferença contra ela é uma diferença da *nossa* econometria, não dos dados.
* **`public`** — `data/analysis/panel_route_month.parquet`, reconstruído pelo
  próprio repositório a partir do VRA bruto da ANAC. Se o arquivo não existir,
  `PublicPanelNotBuilt` nomeia o caminho e o comando que o constrói
  (`just panel`), em vez de estourar dentro do pandas. Hoje o painel existe
  (31.760 linhas, 310 rotas, 2000m1–2014m1): restrito à janela 2002m1–2013m12 do
  artigo e passado pelos filtros dos do-files, dá **22.490 rota-mês em 211
  rotas**, e a Tabela 2 sai em 9 das 13 variáveis (`fsc_oddsarr` com média
  −1,3844 contra −1,38 publicado; o ADR-0013 corrigiu esta coluna para o
  conjunto de empresas do artigo, e a variante por classe é `fscc_oddsarr`).
  O que falta — `maxprdel`, `cshare`,
  `dailyflcong`, `dailyflncong`, os sete instrumentos tipo Hausman, e `rthhi`/
  `maxcthhi`, que existem como coluna mas estão inteiramente nulas — impede as
  cinco tabelas de regressão, e é **reportado por escrito**, nunca substituído
  por coluna parecida (o painel traz `rthhi_flights` e `maxcthhi_flights`, que
  são outra definição). Ver
  [`docs/declared-differences.md`](../declared-differences.md).

O contrato do painel público é `replication.common.REQUIRED_COLUMNS`: os nomes de
variável do próprio artigo, porque este módulo é uma porta de uma especificação
em Stata e são esses nomes que identificam cada regressor nas tabelas
publicadas. Um painel incompleto **carrega no `attrs` a lista exata do que
falta**, e `PublicPanelIncomplete` a nomeia no instante em que uma coluna do
modelo precisa daquilo — de modo que a execução pública estima o que dá e
declara por escrito o que não dá. Quando o painel completar, nada aqui muda:
basta o arquivo estar no caminho padrão, ou `AIRLINE_DELAYS_PANEL` apontar para
um. Um painel que escreve uma coluna com
**outro nome** é aceito (`route` no lugar de `od`; as regiões saem dos códigos de
nó via `data/external/nodes.csv`); um painel que traz algo *parecido* com uma
variável publicada, não — a coluna conta como ausente.
`tests/test_replication_public.py` roda a Tabela 2 e a coluna 1 da Tabela 3 de
ponta a ponta sobre um painel sintético construído para esse contrato — filtros,
dummies, poda de colinearidade, 2SGMM com kernel HAC, J de Hansen e
Kleibergen–Paap — e verifica, no painel real, que o que falta é nomeado.

## 2. A amostra, na ordem exata dos do-files

O bloco de abertura de cada do-file de tabela é o mesmo:

```stata
projbase 18 ; drop fe_* ; drop sz_* ; drop if fsc_oddsarr==. ;
findsingletons k ; drop if _count_k<=5 ; panelset ; effects k ; dummymonthreg
```

Reproduzido em `common.build_sample()`. Dois detalhes que parecem redundância e
não são:

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
**reconstruídas** a partir de `ym`, `o_region` e `d_region` em
`common.add_dummies()`, em vez de lidas do painel — é o que faz o caminho
público e o privado serem o mesmo código. A regra é
`sz_{regiao}_m_{mes} = 1` se o mês é `mes` **e** a rota toca a região; cada linha
acende uma ou duas dummies. Conferido contra as 60 colunas `sz_*` e as 144
colunas `t_*` gravadas no painel privado: **concordância exata nas 24.589
linhas**.

## 3. As decisões de estimação, e a evidência de cada uma

| Questão | Decisão | Base |
|---|---|---|
| Kernel | Bartlett, `bandwidth=4` | `linearmodels` pesa a defasagem *j* por `1 − j/(bw+1)`; o `ivreg2` com `bw(5)` pesa por `1 − j/5`, j = 0..4. **4 aqui é 5 lá.** E `bw(5)` é o `T^(1/3)` com `T = 144` que o artigo declara. |
| Correção de amostra finita | `debiased=True` | O `ivreg2` sem `small` divide por N; com `small`, por N−K, e só então imprime uma *F statistic* — que aparece nas tabelas publicadas. |
| Dummies sazonais | **entram** | O `dummymonthreg` as cria e o `gregcontrols` não as menciona (§4.6 da especificação); o `.ado` que decidiria não foi entregue. O artigo fala em *seasonality controls*, e incluí-las aproxima mensuravelmente os coeficientes. A escolha é declarada e medida nos dois sentidos (§6). |
| Efeitos fixos | explícitos | O do-file não usa `partial()` nem `xtivreg2`. Entram 189 dummies de rota (uma omitida contra a constante) e `t_2..t_144`; a colinearidade exata cai por QR revelador de posto. |
| Endógenas | só `rthhi` e `maxcthhi` | As dummies de LCC são **exógenas**. Isso contradiz a introdução do artigo, que fala em instrumentar *"all of the market structure variables"*, mas o código é inequívoco — e é o que reproduz os graus de liberdade publicados do J. |
| Instrumentos | duas listas | 5 instrumentos no bloco ODDS (J com 3 g.l.), 3 no bloco MINS (J com 1 g.l.). **Não unificar.** Invertendo os pares (J, p-valor) publicados, os graus de liberdade implícitos batem exatamente com as listas dos do-files — é a evidência mais forte de que os do-files entregues são os que geraram as tabelas. |

## 4. Tabela por tabela

* **Tabela 2 (descritivas).** `corr` + `summ` de 13 variáveis sobre a amostra
  filtrada. Mínimos e máximos coincidem até a quarta casa
  (`dailyflcong` máx. 78,8387 contra 78,84; `fsc_minsarr` mín./máx.
  −9,8000/131,9118 contra −9,80/131,91). **É isso que prova a identificação de
  cada variável do código com a coluna do artigo**, em vez de supô-la. O
  triângulo de correlações fecha com diferença absoluta mediana de 0,002 e máxima
  de 0,012 em 91 células.
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
  `common.hansen_j()`, que avalia a matriz de ponderação ótima HAC nos resíduos
  do LIML — que é o que o `ivreg2` imprime para qualquer estimador robusto, e é
  por isso que o J publicado da Tabela 5 é quase igual ao da Tabela 3.
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

`replication/kp.py` a escreve a partir do artigo. Com `Ỹ` e `Z̃` as endógenas e
os instrumentos excluídos depois de parcializar os regressores incluídos:

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
`replication.kp.cragg_donald()` — que passa por QR de cada bloco e uma SVD das
projeções e **não compartilha código** com `kp_rk` (raiz quadrada simétrica,
produto de Kronecker, pseudo-inversa). Se a normalização de `Θ̂` estivesse
errada, nenhuma das duas fecharia. Está em `tests/test_replication_kp.py`.

Contra os valores publicados: nas colunas ODDS a implementação acerta o nível
(+3,3% a +6,4% no rk LM) e a estrutura interna — a razão Wald/LM implícita no
publicado reaparece na réplica. Nas colunas MINS a distância é maior (+18,7% a
+31,0%), porque com 3 instrumentos e 2 endógenas o sistema é quase exatamente
identificado e a estatística fica muito sensível ao N.

## 6. O que bate, o que não bate

**Bate.** 306 coeficientes comparados nas cinco tabelas de regressão: **302
sinais iguais**, 259 (85%) a menos de meio erro-padrão publicado, maior desvio
isolado 0,94 erro-padrão. Nas 24 colunas que reportam J de Hansen, **nenhuma
muda de veredito** a 5%: as mesmas 22 não rejeitam ortogonalidade e as mesmas 2
rejeitam. A inversão de sinal dos HHIs entre OLS e 2SGMM — o argumento central do
artigo — replica nas 12 comparações.

**Não bate**, e está declarado em
[`docs/declared-differences.md`](../declared-differences.md): o N (+5,31% nas
chegadas, +5,35% nas partidas, sistematicamente, sem que nenhum filtro visível
nos do-files produza os números publicados); o J, que muda de tamanho sem mudar
de conclusão; o R² e o RMSE das colunas MINS, em que a réplica ajusta **melhor**
que o publicado; e a *F statistic*, que não é reproduzida de propósito — o F do
`ivreg2` é o Wald conjunto de ~340 regressores sob convenção própria, e preencher
a célula seria comparar coisas diferentes.

Os erros-padrão saem sistematicamente **menores** (razão mediana 0,94 na
Tabela 3; 51 de 60 abaixo do publicado), o que é exatamente o que uma amostra
5,3% maior produz.

## 7. Sensibilidade (ADR-0008)

Dois eixos, e eles não são simétricos.

* **Dummies sazonais** — puro interruptor de especificação, sempre disponível.
  Move `rthhi` na coluna 1 da Tabela 3 de 0,8843 (com) para 0,8661 (sem);
  `maxcthhi`, de −1,4551 para −1,4078. **Não muda nenhum sinal nem nenhuma
  conclusão.**
* **Limiar de *outlier*** — 313,25 min (padrão da ADR-0008), 117,10 min e sem
  corte. O limiar se aplica ao atraso **no nível do voo**, antes de agregar, de
  modo que variá-lo exige que a fonte ofereça o regressando reconstruído. O
  painel privado é entregue já agregado, sob uma regra que seus autores nunca
  documentaram: nessa fonte as duas linhas alternativas aparecem como
  **indisponíveis**, com o motivo escrito, e não como aproximação. Quando o
  painel público trouxer as variantes sufixadas
  (`replication.common.regressand_column`, p.ex. `fsc_oddsarr__out11710`), as
  linhas se preenchem sozinhas.

Declarar a indisponibilidade é o comportamento correto aqui: a alternativa seria
inventar um limiar sobre dados já agregados, que é exatamente o tipo de ajuste
que `CLAUDE.md` proíbe.

## 8. O que não foi tentado

* **Reconstruir o painel final dos autores.** Não existe script entre os brutos e
  a base final; 14 arquivos intermediários não foram entregues.
* **Reconstruir os instrumentos tipo Hausman.** Falta a matriz de distâncias
  entre as 27 cidades, a regra de "cidade próxima" e a fórmula dos pesos.
* **`_tab7.do`.** Troca `maxcthhi` por um HHI de cidade ponderado por
  passageiros e não corresponde a tabela publicada alguma.

## Como rodar

```bash
# modo privado (exige a variável de ambiente; nunca escreva o caminho no código)
AIRLINE_DELAYS_PRIVATE_DIR=... uv run python -m replication.run --source private

# modo público (quando o painel existir)
uv run python -m replication.run --source public

# uma tabela só
uv run python -m replication.run --source private --tables table2,table3

# reextrair os números publicados do texto do artigo
uv run python -m replication.published --source-text /caminho/para/airline.txt

# relatório em PDF
typst compile reports/replication.typ reports/build/replication.pdf
```
