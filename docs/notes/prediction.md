# Previsão de atrasos no nível do voo — desenho, vazamento, resultados e limites

Nota de pesquisa, em português (ADR-0006: código e nomes de coluna em inglês, notas
e relatórios em português). Descreve o que a camada `ml/` faz, por que faz assim, e
o que os números querem e não querem dizer. Todos os valores foram medidos pelo
`uv run python -m ml.run` sobre a série completa; os arquivos de origem estão em
`reports/prediction/` e nenhum número aqui foi digitado à mão.

O relatório compilado é `reports/prediction.typ`; esta nota é o registro de
decisões e evidências por trás dele.

## 1. A unidade, os alvos e o que sai do universo

A unidade é o **voo programado** do universo de replicação (ADR-0002: tipos de
linha N, R e E, DI 0), realizado ou cancelado. Não é o voo realizado: se a tabela
começasse pelos realizados, o alvo de cancelamento não teria denominador, e a
contagem de movimentos programados por aeroporto-dia-hora — que é o que um
aeroporto realmente tem na véspera — ficaria enviesada para baixo justamente nos
dias em que houve cancelamento.

Cinco alvos, todos declarados em `src/vra/registry.py` (camada `ml`):

| alvo | definição | onde existe |
|---|---|---|
| `late15_arr` | chegada com mais de 15 min de atraso | voo realizado, horário não suspeito, e horário real presente **ou** sem alteração reportada (ADR-0017) |
| `late30_arr` | chegada com mais de 30 min | idem |
| `arr_delay_min` | atraso de chegada com sinal, em minutos | idem |
| `late15_dep` | partida com mais de 15 min | idem |
| `cancelled` | voo cancelado | **toda** linha |

Três regras decidem se um voo tem alvo de atraso, e as três são registradas:

1. **ADR-0017, leitura B.** Nos arquivos de 2000 a 2009 o horário realizado é
   campo do Boletim de Alteração de Vôo, emitido pela IAC 1504 só "sempre que
   houver alguma alteração" (introdução e §3.1; horários e código em §4.2 n, o,
   p). Campo vazio em voo realizado é, portanto, **ausência de alteração
   reportada**: o atraso vale 0 e a linha recebe a marca `on_time_no_bav`. A
   leitura vale só para voos realizados de anos até 2009 cuja empresa tem classe
   FSC, LCC ou regional em `groups.csv`; para `other` e não rotuladas —
   estrangeiras e o lado não operador de code-share, cuja taxa de nulo é de 83,0%
   contra 72,9% das que estão no escopo (2000–2009, universo de replicação), e
   90% a 100% no corte de 2005 do revisor cético sobre todos os voos — o vazio
   continua desconhecido e o voo **fica sem alvo**. O colegiado que decidiu isso está em
   `docs/notes/colegiado-adr0012.md`; a taxa de nulo por empresa e ano está em
   `docs/declared-differences.md`.
2. **ADR-0015.** Um horário real a um dia ou mais do previsto
   (|atraso| ≥ 1.440 min) é erro de digitação de mês nos arquivos, não operação.
   O voo continua sendo uma linha da tabela — foi programado e ocupou o slot —
   mas sai de todo alvo de atraso. A marca vem do próprio staging, na coluna
   `actual_time_suspect`.
3. **Voo cancelado não tem atraso.** Cancelamento é um alvo próprio.

A segunda regra tira 5.248 voos de 10.200.560 (0,05%), com pico em 2003 (1.032) e
2013 (990). A primeira **inclui** 3.720.757 voos que a leitura anterior deixava
sem alvo, e deixa de fora 260.605 voos realizados de empresas fora do escopo.
Sobram **8.686.697** voos com alvo de chegada, contra 4.965.966 sob a leitura A;
a soma fecha exatamente com os 8.952.550 realizados (8.686.697 + 260.605 +
5.248).

A leitura B é um **piso de pontualidade**: atraso não reportado conta como
pontual, então a taxa anterior a 2010 é limite inferior. A alternativa não é
neutra — a leitura A condicionava no desfecho e devolvia taxas de 88% a 94% antes
de 2010 contra 24,3% em 2010, degrau que nasce na fronteira de layout e não na
operação.

O efeito, ano a ano:

| ano | voos programados | realizados | com alvo | sem alteração | % dos realizados | fora de escopo | suspeito | taxa > 15 min | cancelamento | etapa anterior | chegada anterior conhecida |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2000 | 659.299 | 587.005 | 553.524 | 437.035 | 74,5% | 33.239 | 242 | 19,1% | 11,0% | 39,1% | 83,6% |
| 2001 | 691.578 | 610.672 | 581.668 | 434.010 | 71,1% | 28.903 | 101 | 21,9% | 11,7% | 39,4% | 84,1% |
| 2002 | 678.949 | 564.375 | 535.107 | 404.732 | 71,7% | 29.215 | 53 | 21,3% | 16,9% | 39,0% | 79,6% |
| 2003 | 565.658 | 431.632 | 410.046 | 311.863 | 72,3% | 20.554 | 1.032 | 18,0% | 23,7% | 38,3% | 73,7% |
| 2004 | 536.553 | 456.321 | 438.565 | 328.488 | 72,0% | 17.460 | 296 | 19,9% | 15,0% | 38,1% | 81,1% |
| 2005 | 552.055 | 476.191 | 455.094 | 317.219 | 66,6% | 20.724 | 373 | 25,6% | 13,7% | 36,7% | 80,7% |
| 2006 | 588.640 | 493.853 | 465.175 | 311.100 | 63,0% | 28.584 | 94 | 30,2% | 16,1% | 35,6% | 78,1% |
| 2007 | 641.630 | 513.080 | 477.330 | 268.009 | 52,2% | 35.503 | 247 | 41,1% | 20,0% | 34,8% | 73,2% |
| 2008 | 663.781 | 600.121 | 574.534 | 395.495 | 65,9% | 25.417 | 170 | 28,6% | 9,6% | 30,7% | 85,0% |
| 2009 | 756.194 | 686.216 | 665.407 | 512.806 | 74,7% | 20.589 | 220 | 20,2% | 9,3% | 29,5% | 87,0% |
| 2010 | 874.236 | 796.922 | 796.359 | 0 | 0,0% | 146 | 417 | 24,3% | 8,8% | 29,2% | 91,8% |
| 2011 | 983.054 | 898.904 | 898.116 | 0 | 0,0% | 145 | 643 | 24,5% | 8,6% | 28,5% | 92,1% |
| 2012 | 1.023.977 | 942.587 | 942.102 | 0 | 0,0% | 115 | 370 | 21,5% | 7,9% | 25,1% | 91,4% |
| 2013 | 984.956 | 894.671 | 893.670 | 0 | 0,0% | 11 | 990 | 16,3% | 9,2% | 19,9% | 91,1% |

Duas colunas mudam a leitura de tudo o que vem depois. **"sem alteração"** é o
que a leitura B admite: 52% a 75% dos voos realizados de cada ano entre 2000 e
2009, zero de 2010 em diante, porque o layout novo carimba horário real em
praticamente todo voo. **"chegada anterior conhecida"** é a fração das ligações cuja etapa anterior
tem chegada legível — 73% a 87% antes de 2010 contra 91% a 92% depois: mesmo sob
a leitura B a informação de portão é mais completa no layout novo.

A taxa de "mais de 15 minutos" fica agora entre 16% e 41% em toda a série, sem o
degrau de 2009 → 2010 que a leitura A produzia (88% contra 24%). O pico de 2007
(41,1%) é o apagão aéreo, e ele aparece porque a série passou a ser comparável,
não apesar disso. A quebra de layout de 2010 continua sendo quebra de
**instrumento** — antes dela o alvo vem de um boletim de exceção, depois de um
carimbo universal — e é isso que o bloco de sensibilidade da seção 4.3 mede.

## 2. Os dois horizontes

O erro clássico da literatura de previsão de atrasos é misturar informação de
véspera com informação de portão e reportar um número só. Aqui são dois problemas
declarados (ADR-0009):

**D−1, véspera.** 46 variáveis: calendário (mês, dia da semana, fim de semana,
feriado por lei federal, ponto facultativo, janela de feriado, alta temporada),
malha programada (hora prevista de partida e de chegada, bloco previsto, posição
da etapa na cadeia do dia), geografia (ICAO e nó de origem e destino, tipo de
rota, distância ortodrômica, região metropolitana, aeroporto coordenado por
slot), congestão programada (movimentos previstos no aeroporto-dia-hora e no dia
inteiro, dos dois lados, e a marca de hora cheia p90), empresa (empresa, grupo,
classe, participação na rota e no aeroporto no mês anterior, meses na rota), e
histórico de janela fechada.

**H−1, portão.** As mesmas 46 mais três, todas sobre a **etapa anterior** do mesmo
número de voo no mesmo dia: o atraso com que ela chegou, se passou de 15 minutos,
se foi cancelada. Nada do próprio voo. O atraso da etapa anterior segue a mesma
leitura B do alvo (ADR-0017): se ela é um voo realizado pré-2010 de empresa no
escopo e sem horário real, chegou sem alteração reportada, e é isso que a
variável carrega — a alternativa seria alimentar o modelo com uma convenção e
cobrá-lo por outra.

A etapa anterior existe para 19,9% (2013) a 39,4% (2001) dos voos. A ligação é
programada — mesmo dia, mesma empresa, mesmo número, chegada prevista no
aeroporto de origem deste voo antes da partida prevista — e o casamento é feito
por ICAO, não por nó: uma aeronave que pousa em Congonhas não decola de
Guarulhos.

A folga programada (`prev_turnaround_min`) e a marca de existência da etapa
(`prev_leg`) são de **véspera**: já estão na malha publicada. Só o resultado da
etapa anterior é de portão.

## 3. A regra de vazamento, e as nove checagens que a impõem

A regra foi escrita antes da primeira variável (ADR-0009). Em `ml/leakage_tests.py`
ela é executável: as nove checagens rodam sobre a amostra versionada em
`tests/fixtures/` a cada `pytest` (2 a 4 segundos) e sobre a base real a cada
`just ml`, com o resultado gravado em `reports/prediction/leakage.json`.

| checagem | resultado |
|---|---|
| `features_exclude_post_departure` | ok — 49 features checked against 13 forbidden names and 3 prefixes |
| `targets_are_not_features` | ok — 5 targets and 6 diagnostics kept out of both horizons |
| `horizons_are_nested` | ok — H-1 adds ['prev_arr_delay_min', 'prev_late15', 'prev_cancelled'] to D-1's 46 features |
| `lag_windows_closed` | ok — over 1,535,464 rows where t-1 and t differ: 1.0000 match t-1, 0.0000 match t (pandas 2.3.3) |
| `movements_from_schedule` | ok — 1.0000 of 1,644,255 rows match a recount from sched_dep/sched_arr (a dataset reusing the staged dep_hour, which falls back to actual_dep, would not) |
| `previous_leg_precedes_departure` | ok — 453,524 linked legs, 0 with a negative turnaround, 0 with none, 0 turnarounds on unlinked flights |
| `targets_null_without_actual` | ok — 33,250 realised flights out of scope for reading B keep no arrival target (ADR-0017), 437,035 are read as no alteration reported, and 1,232 suspect timestamps are excluded (ADR-0015); 0 rows disagreeing |
| `first_year_has_no_p90` | ok — 2000: 0 rows carry a p90 flag (must be 0); later years: 983,970 of 984,956 |
| `calendar_matches_the_table` | ok — 92 dated holidays, 27,404 flagged flights, 0 wrong |

Duas merecem explicação.

**`movements_from_schedule`.** A camada staged tem `dep_hour` e `arr_hour`, e é
tentador reusá-las. Elas não servem: `vra.stage` as calcula sobre
`coalesce(sched_dep, actual_dep)`, ou seja, **recorrem ao horário real** quando o
previsto falta. Um voo sem partida prevista entraria na base com uma hora
pós-decolagem e nada quebraria. `ml/dataset_flights.py` recalcula as horas só a
partir de `sched_dep`/`sched_arr` e descarta as linhas que ficam sem hora; a
checagem reconta os movimentos por aeroporto-dia-hora a partir do horário previsto
no `data/staged/` e exige concordância total.

**`lag_windows_closed`.** É a forma executável do vazamento que este repositório
já mediu em si mesmo: na rodada de painel, o `fsc_prdeldep` do **mesmo mês** levou
um R² de 0,58 para 0,82. A checagem compara cada `route_late15_l1` com a taxa da
rota em *t−1* **e** em *t*, nas células em que as duas diferem, e exige que bata
com a primeira e não com a segunda. Um teste companheiro
(`test_a_planted_leak_is_caught`) planta o vazamento de propósito e exige que a
checagem falhe — sem ele, todas as outras poderiam estar passando por não olhar.

A marca de hora cheia (`origin_p90_hour`, `dest_p90_hour`) também é janela
fechada: compara os movimentos programados da hora com o p90 do **ano civil
anterior** do próprio aeroporto, não do ano corrente. É o proxy da ADR-0007 com a
janela fechada, e por construção o primeiro ano de qualquer construção fica sem a
marca — o que a checagem `first_year_has_no_p90` verifica.

## 4. Resultado principal: origem rolante

Treina até *y−2*, escolhe o número de árvores em *y−1* por parada antecipada, e
testa em *y*, para cada ano de teste de 2006 a 2013 (ADR-0009). XGBoost `hist`,
categóricas nativas, hiperparâmetros idênticos em todos os folds e nos dois
horizontes — o resultado desta fase é o desenho de avaliação, não um modelo
afinado.

| ano de teste | n teste | base | D−1 AUC | D−1 PR-AUC | D−1 Brier | H−1 AUC | H−1 PR-AUC | H−1 Brier | rota t−1 AUC | rota t−1 Brier | grupo t−1 AUC | grupo t−1 Brier |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2006 | 465.175 | 0,302 | 0,728 | 0,521 | 0,191 | 0,821 | 0,723 | 0,148 | 0,673 | 0,195 | 0,641 | 0,200 |
| 2007 | 477.330 | 0,411 | 0,741 | 0,645 | 0,206 | 0,824 | 0,788 | 0,167 | 0,647 | 0,227 | 0,609 | 0,232 |
| 2008 | 574.534 | 0,286 | 0,729 | 0,518 | 0,178 | 0,793 | 0,658 | 0,154 | 0,648 | 0,194 | 0,629 | 0,195 |
| 2009 | 665.407 | 0,202 | 0,728 | 0,450 | 0,141 | 0,786 | 0,569 | 0,124 | 0,639 | 0,154 | 0,640 | 0,153 |
| 2010 | 796.359 | 0,243 | 0,724 | 0,460 | 0,162 | 0,790 | 0,610 | 0,141 | 0,624 | 0,179 | 0,621 | 0,179 |
| 2011 | 898.116 | 0,245 | 0,716 | 0,464 | 0,163 | 0,777 | 0,599 | 0,144 | 0,611 | 0,181 | 0,595 | 0,183 |
| 2012 | 942.102 | 0,215 | 0,719 | 0,426 | 0,150 | 0,765 | 0,541 | 0,136 | 0,608 | 0,165 | 0,549 | 0,168 |
| 2013 | 893.670 | 0,163 | 0,715 | 0,348 | 0,124 | 0,757 | 0,464 | 0,113 | 0,613 | 0,134 | 0,566 | 0,135 |

Quatro leituras.

**O horizonte H−1 ganha em todos os anos**, entre 0,04 e 0,09 pontos de AUC — em
2006 vai de 0,728 para 0,821, em 2013 de 0,715 para 0,757. É o mesmo achado da
literatura recente (FlightSense, 2026: AUC 0,732 com malha, 0,875 com
propagação), obtido aqui sem *tail number*, só com o número de voo — e diluído
pelos 65% a 80% de voos sem elo identificável, para os quais o H−1 não acrescenta
nada. A tabela da seção 4.1 mostra o efeito sem essa diluição.

**As referências ingênuas não são espantalhos.** A prevalência da rota no mês
anterior devolve AUC de 0,61 a 0,67 e já ordena os voos bem acima do acaso. O
modelo precisa ser lido como ganho sobre ela, não sobre 0,5.

**Os oito folds agora são comparáveis entre si.** O D−1 fica entre 0,715 e 0,741
e o H−1 entre 0,757 e 0,824 nos oito anos, sem o colapso que a leitura A produzia
em 2010 e 2011 (0,638 e 0,636). Aquele colapso não era do modelo: era o primeiro
ano de teste cuja amostra era a malha completa enquanto o treino ainda era
amostra selecionada pelo desfecho. Com a leitura B, treino e teste medem a mesma
grandeza em toda a série, e o que sobra de variação entre folds é operação.

**A base varia e o Brier varia com ela.** 2007 tem base 0,411 (o apagão aéreo) e
Brier 0,206; 2013 tem base 0,163 e Brier 0,124. Comparar Briers entre folds sem
olhar a taxa-base ao lado é comparar coisas diferentes — a AUC, que é invariante
à prevalência, é a coluna que se compara direto.

### 4.1. Só onde existe etapa anterior ligada

O H−1 só diz algo onde a etapa anterior existe. Os dois horizontes são
reavaliados exatamente nessas linhas, para que a diferença seja o horizonte e não
a população.

| ano | share ligado | n ligado | D−1 AUC | H−1 AUC | D−1 Brier | H−1 Brier |
|---|---|---|---|---|---|---|
| 2006 | 35,1% | 163.136 | 0,730 | 0,924 | 0,199 | 0,086 |
| 2007 | 34,3% | 163.788 | 0,760 | 0,934 | 0,203 | 0,091 |
| 2008 | 30,1% | 173.131 | 0,750 | 0,910 | 0,179 | 0,098 |
| 2009 | 29,2% | 194.630 | 0,726 | 0,891 | 0,145 | 0,087 |
| 2010 | 29,4% | 233.841 | 0,713 | 0,897 | 0,166 | 0,094 |
| 2011 | 28,7% | 258.137 | 0,707 | 0,881 | 0,170 | 0,103 |
| 2012 | 25,0% | 235.399 | 0,713 | 0,869 | 0,159 | 0,101 |
| 2013 | 19,8% | 177.265 | 0,705 | 0,870 | 0,138 | 0,086 |

Aqui o H−1 aparece pelo que é: em 2013 a AUC sobe de 0,705 para 0,870 e o Brier
cai de 0,138 para 0,086 sobre as mesmas 177.265 linhas. Em toda a série o ganho
de AUC no subconjunto ligado fica entre 0,16 e 0,19 pontos — a favor do portão
contra a véspera, medido na mesma população.

### 4.3. Sensibilidade: leitura A ao lado da leitura B

A leitura A, superada pela ADR-0017, tratava horário real vazio como
*desconhecido*. As colunas "A" vêm da rodada anterior, preservada em
`reports/prediction/rolling_reading_A.json`; nada foi reestimado sob a convenção
superada, porque reestimar dá a impressão de que as duas são alternativas vivas.

| ano de teste | n A | n B | base A | base B | D−1 AUC A | D−1 AUC B | H−1 AUC A | H−1 AUC B | D−1 Brier A | D−1 Brier B |
|---|---|---|---|---|---|---|---|---|---|---|
| 2006 | 154.073 | 465.175 | 0,911 | 0,302 | 0,810 | 0,728 | 0,864 | 0,821 | 0,065 | 0,191 |
| 2007 | 209.328 | 477.330 | 0,936 | 0,411 | 0,788 | 0,741 | 0,840 | 0,824 | 0,050 | 0,206 |
| 2008 | 179.046 | 574.534 | 0,918 | 0,286 | 0,761 | 0,729 | 0,803 | 0,793 | 0,067 | 0,178 |
| 2009 | 152.604 | 665.407 | 0,883 | 0,202 | 0,767 | 0,728 | 0,804 | 0,786 | 0,086 | 0,141 |
| 2010 | 796.389 | 796.359 | 0,243 | 0,243 | 0,638 | 0,724 | 0,736 | 0,790 | 0,250 | 0,162 |
| 2011 | 898.100 | 898.116 | 0,245 | 0,245 | 0,636 | 0,716 | 0,735 | 0,777 | 0,203 | 0,163 |
| 2012 | 942.104 | 942.102 | 0,215 | 0,215 | 0,698 | 0,719 | 0,754 | 0,765 | 0,153 | 0,150 |
| 2013 | 893.657 | 893.670 | 0,163 | 0,163 | 0,711 | 0,715 | 0,749 | 0,757 | 0,124 | 0,124 |

**De 2010 em diante a comparação é de igual para igual** — as duas leituras
enxergam o mesmo dado, e as poucas linhas de diferença em `n` são o ajuste de ano
civil da ADR-0016 — e é aí que está o achado: a leitura B ganha 0,086 pontos de
AUC em 2010 (0,638 → 0,724), 0,080 em 2011, 0,021 em 2012 e 0,004 em 2013, com o
Brier de 2010 caindo de 0,250 para 0,162. O ganho vem inteiro do **treino**: sob
a leitura A, um modelo testado em 2010 tinha sido treinado quase todo sobre voos
com ocorrência registrada, uma amostra selecionada pelo desfecho, e o efeito
encolhe conforme os anos de layout novo entram no treino, até quase desaparecer
em 2013. Isso é evidência de que a leitura A distorcia o aprendizado, não só a
contagem.

**Antes de 2010 as duas colunas não são comparáveis** e a tabela existe para
mostrar por quê: a base de teste vai de 0,911 para 0,302 em 2006, porque a
população de teste é outra. Uma AUC de 0,810 sobre 154.073 voos que tiveram
ocorrência e uma de 0,728 sobre 465.175 voos programados não medem o mesmo
problema, e a primeira não é "melhor".

### 4.2. Split fixo (ilustrativo)

Treino 2002–2010, validação 2011, teste 2012–2013 — o desenho que a literatura
usa. Reportado porque é comparável, não porque responde melhor.

| alvo | n teste | base | D−1 AUC | D−1 PR-AUC | D−1 Brier | H−1 AUC | H−1 PR-AUC | H−1 Brier |
|---|---|---|---|---|---|---|---|---|
| `late15_arr` | 1.835.772 | 0,189 | 0,720 | 0,396 | 0,137 | 0,762 | 0,506 | 0,126 |
| `late30_arr` | 1.835.772 | 0,090 | 0,704 | 0,207 | 0,078 | 0,765 | 0,373 | 0,069 |
| `late15_dep` | 1.835.772 | 0,164 | 0,676 | 0,297 | 0,129 | 0,744 | 0,463 | 0,114 |
| `cancelled` | 2.008.933 | 0,085 | 0,723 | 0,233 | 0,073 | 0,791 | 0,392 | 0,065 |

O alvo `cancelled` é o único definido sobre a malha inteira, sem exclusão de
ADR-0015 nem de ADR-0017; o H−1 nele deve ser lido com cuidado, porque no portão
o cancelamento muitas vezes já foi decidido. O split fixo devolve, para
`late15_arr`, AUC de 0,720 na véspera contra 0,715 a 0,741 dos oito folds da
origem rolante: um número só, sem a informação de como o desempenho se move ao
longo da série, que é a razão de a origem rolante ser o resultado principal.

## 5. O que o modelo usa

Queda na AUC de teste quando a coluna é embaralhada, no último fold da origem
rolante (teste 2013), média de 3 repetições.

| # | D−1 variável | queda AUC | H−1 variável | queda AUC |
|---|---|---|---|---|
| 1 | `flight_no_late15_l3` | 0,1060 | `flight_no_late15_l3` | 0,0728 |
| 2 | `sched_block_min` | 0,0607 | `sched_block_min` | 0,0710 |
| 3 | `distance_km` | 0,0373 | `distance_km` | 0,0505 |
| 4 | `month` | 0,0139 | `prev_arr_delay_min` | 0,0476 |
| 5 | `origin_movements_hour` | 0,0119 | `prev_turnaround_min` | 0,0172 |
| 6 | `dow` | 0,0091 | `origin_movements_hour` | 0,0155 |
| 7 | `route_late15_l1` | 0,0069 | `month` | 0,0116 |
| 8 | `sched_dep_hour` | 0,0059 | `dow` | 0,0067 |
| 9 | `origin_icao` | 0,0051 | `origin_icao` | 0,0058 |
| 10 | `dest_icao` | 0,0027 | `route_late15_l1` | 0,0052 |

O ranking diz quatro coisas.

A primeira: o histórico do **próprio número de voo** nos três meses anteriores é
a variável isolada mais forte dos dois horizontes (queda de 0,106 na AUC do D−1 e
0,073 na do H−1). Uma malha carrega atraso estrutural por horário e por trecho, e
o número de voo é o identificador mais fino disponível sem tipo de aeronave.

A segunda: `sched_block_min` e `distance_km` vêm logo atrás nos dois horizontes.
São quase a mesma informação — o bloco previsto é distância mais folga da empresa
— e é a **folga** que carrega o sinal: um trecho com bloco generoso absorve
atraso de partida antes da chegada.

A terceira é metodológica. `prev_arr_delay_min` aparece em 4º no H−1, com queda
de 0,048, muito abaixo do que a seção 4.1 mostra (0,16 a 0,19 pontos de AUC no
subconjunto ligado). A razão é conhecida: `prev_late15` é o mesmo sinal
binarizado, e embaralhar uma variável deixando sua substituta intacta subestima
as duas — `prev_late15` sozinha cai 0,0007. **Importância por permutação com
variáveis correlacionadas mede o que é insubstituível, não o que importa**; para
o valor do horizonte, a comparação entre a tabela da seção 4 e a da 4.1 é a
medida certa.

A quarta é negativa e vale registrar: congestão programada, marca de slot e
região metropolitana contribuem quase nada depois de condicionar no aeroporto e
na hora (`origin_p90_hour` cai 0,0001, `origin_slot_coordinated`, `origin_metro`
e `dest_p90_hour` cerca de zero ou negativo). É consistente com a ADR-0007 — o
proxy p90 é interno ao VRA e não substitui capacidade declarada — e com o fato de
o ICAO de origem já carregar o que aquele aeroporto tem de estrutural.

### 5.1. Calibração

| faixa | n | share | média prevista | observado |
|---|---|---|---|---|
| 0,0–0,1 | 273.927 | 30,7% | 0,068 | 0,063 |
| 0,1–0,2 | 346.502 | 38,8% | 0,145 | 0,134 |
| 0,2–0,3 | 158.407 | 17,7% | 0,243 | 0,227 |
| 0,3–0,4 | 65.932 | 7,4% | 0,342 | 0,331 |
| 0,4–0,5 | 28.329 | 3,2% | 0,444 | 0,434 |
| 0,5–0,6 | 12.141 | 1,4% | 0,542 | 0,519 |
| 0,6–0,7 | 5.076 | 0,6% | 0,644 | 0,604 |
| 0,7–0,8 | 2.369 | 0,3% | 0,740 | 0,679 |
| 0,8–0,9 | 757 | 0,1% | 0,840 | 0,696 |
| 0,9–1,0 | 230 | 0,0% | 0,936 | 0,543 |

Fold de teste 2013, horizonte D−1. Até 0,6 de probabilidade prevista — 99,1% das
linhas — a calibração é boa: a diferença entre previsto e observado fica em 0,005
a 0,023. Acima disso o modelo fica confiante demais, e cada vez mais: prevê 0,740
onde observa 0,679 (2.369 voos), 0,840 onde observa 0,696 (757) e 0,936 onde
observa 0,543 (230). Não é problema prático nesse volume — as três faixas juntas
são 0,4% das linhas — mas é a direção do erro que se deve esperar de um modelo
treinado num período de taxa-base mais alta, e é o tipo de coisa que a AUC
sozinha não mostra. As faixas do H−1 estão em
`reports/prediction/calibration.json`.

## 6. Custo

Uma varredura DuckDB por **ano civil** de `data/staged/` constrói a base inteira
— o diretório `year=AAAA` é o ano do arquivo de origem e não o do voo (ADR-0016,
`vra.features.year_source_sql`); cada ano é materializado uma vez em tabela temporária e todos os agregados daquele ano —
movimentos por aeroporto-dia-hora, taxas mensais por número de voo, a ligação de
rotação — saem dessa mesma materialização. As taxas mensais que precisam de anos
anteriores vêm da tabela de fatos já versionada
(`data/analysis/fact_group_route_month.parquet`, ADR-0014) mais um resto de três
meses carregado de uma iteração para a seguinte. Nenhum ano é lido duas vezes.

| etapa | tempo | saída |
|---|---|---|
| construção da base (14 anos) | 25 s | 10.200.560 linhas, 65 colunas, 320 MB |
| origem rolante, 8 folds x 2 horizontes | 1.140 s | `reports/prediction/rolling.json` |
| importâncias por permutação (2 horizontes) | 175 s | `reports/prediction/importance.json` |
| split fixo, 4 alvos x 2 horizontes | 1.001 s | `reports/prediction/fixed.json` |
| **total `uv run python -m ml.run`** | **2.344 s** | 39 min em 8 threads, 16 GB |

Ficou mais lento que a rodada anterior (1.427 s) por um motivo só: a leitura B da
ADR-0017 dá alvo a 8.686.697 voos em vez de 4.965.966, então cada fold treina em
quase o dobro das linhas. O fold mais caro é o de 2013 (444 s): treina em
5.715.733 voos com alvo, valida em 942.102 e testa em 893.670. O pico de memória
fica em 1,8 GB porque `ml/split.py` lê e filtra um ano por vez.

## 7. Limites declarados

1. **A leitura B é um piso, e o instrumento muda em 2010** (ADR-0017). Antes de
   2010 o alvo vem de um boletim de exceção: atraso que a empresa não reportou
   conta como pontual, e a taxa publicada é limite inferior. De 2010 em diante
   quase todo voo realizado traz horário real. A tabela da seção 1 traz a marca
   `on_time_no_bav` por ano exatamente para que a troca de instrumento fique
   visível, e a seção 4.3 traz as métricas sob a leitura A ao lado.
2. **H−1 é o horizonte da ADR-0009, não um relógio.** A etapa anterior pode
   pousar depois do corte de uma hora antes da partida prevista. A base carrega
   `prev_arr_known_h1` — 1 quando a chegada real da etapa anterior ocorreu ao
   menos 60 minutos antes — e o manifesto reporta a fração por ano. A variável
   **não** é anulada, porque a definição do horizonte é decisão registrada e não
   estimativa; mas o número está na frente de quem for usar o H−1 como previsão
   operacional. Sob a leitura B a chegada da etapa anterior é legível em 73% a
   87% das ligações antes de 2010 e em 91% a 92% depois (coluna "chegada anterior
   conhecida" da seção 1): para um voo sem BAV, "chegou no horário previsto" é
   informação que a véspera já tinha.
3. **Sem meteorologia.** O METAR do DECEA/REDEMET não entra nesta fase. O que
   existe é a participação de códigos de clima no aeroporto no mês anterior, que
   é climatologia defasada, não previsão do tempo. O acervo tem 4,2 milhões de
   observações METAR de 2000–2013; incorporá-las é a extensão de maior retorno
   esperado.
4. **Sem capacidade declarada.** A hora cheia é o proxy p90 da ADR-0007 com a
   janela fechada no ano anterior. `data/external/capacity.csv` tem uma linha
   (Congonhas), e uma linha não sustenta um painel nacional.
5. **Sem tipo de aeronave nem número de assentos.** Só existem no layout de 2010
   em diante; uma variável que nasce no meio da série quebra a validação
   temporal, que é o ativo desta fase.
6. **A ligação de rotação é por número de voo, não por aeronave.** Sem *tail
   number* — que o VRA não publica — a cadeia do dia é a do número de voo, e
   19,9% a 39,4% dos voos têm um elo identificável. É um limite inferior do que a
   propagação real explica.
7. **Um único conjunto de hiperparâmetros.** Nada foi afinado por fold ou por
   horizonte, de propósito: o resultado é o desenho, e um modelo afinado por fold
   traria a tentação de escolher o fold.
8. **Empresas de classe `other` ficam sem alvo antes de 2010.** São 260.605 voos
   realizados de 2000 a 2009 (estrangeiras, o lado não operador de code-share,
   operadores sem perfil público). A leitura B não os cobre, por decisão
   registrada e não por omissão (IAC 1504 art. 6.6); se esses trechos deveriam
   sair dos universos por completo é auditoria própria, candidata a ADR-0018.

## 8. Como reproduzir

```bash
just ml-dataset   # a tabela de voos, uma varredura por ano de data/staged
just ml           # reconstrói a tabela e roda a avaliação completa
uv run pytest -q  # inclui as nove checagens de vazamento sobre o fixture
typst compile reports/prediction.typ reports/build/prediction.pdf
```

`data/derived/ml/` é git-ignorado (ADR-0004): 320 MB de tabela de voos não entram
no repositório. As 65 colunas estão declaradas em `src/vra/registry.py`,
renderizadas em `docs/dictionary.md` e descritas como recurso em
`datapackage.json` — quem clonar reconstrói a tabela em 25 segundos e sabe
exatamente o que vai encontrar.
