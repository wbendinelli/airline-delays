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
| `late15_arr` | chegada com mais de 15 min de atraso | voo realizado, com horário real e não suspeito |
| `late30_arr` | chegada com mais de 30 min | idem |
| `arr_delay_min` | atraso de chegada com sinal, em minutos | idem |
| `late15_dep` | partida com mais de 15 min | idem |
| `cancelled` | voo cancelado | **toda** linha |

Três regras decidem se um voo tem alvo de atraso, e as três são registradas:

1. **ADR-0012.** Nos arquivos brutos de 2000 a 2009 o horário realizado só é
   preenchido quando houve ocorrência. Com `legacy_missing_actual_as_zero = False`,
   um voo realizado sem horário real **não tem alvo** — não é imputado como
   pontual.
2. **ADR-0015.** Um horário real a um dia ou mais do previsto
   (|atraso| ≥ 1.440 min) é erro de digitação de mês nos arquivos, não operação.
   O voo continua sendo uma linha da tabela — foi programado e ocupou o slot —
   mas sai de todo alvo de atraso.
3. **Voo cancelado não tem atraso.** Nem sob a convenção antiga: cancelamento é
   um alvo próprio.

A segunda regra tira 5.249 voos de 10.200.578 (0,05%), com pico em 2003 (1.030) e
2013 (990). A primeira tira 3.981.347 — e é ela que reorganiza a leitura de
qualquer métrica anterior a 2010. Sobram 4.965.966 voos com alvo de chegada; 71
linhas do universo saem por não ter partida ou chegada prevista, que é o que
torna impossível prevê-las na véspera.

O efeito da primeira regra, ano a ano:

| ano | voos programados | com alvo de chegada | excluídos (ADR-0012) | taxa > 15 min | cancelamento | com etapa anterior |
|---|---|---|---|---|---|---|
| 2000 | 659.317 | 116.491 | 470.283 | 90,7% | 11,0% | 39,1% |
| 2001 | 691.586 | 147.658 | 462.920 | 86,3% | 11,7% | 39,4% |
| 2002 | 678.948 | 130.377 | 433.937 | 87,6% | 16,9% | 39,0% |
| 2003 | 565.660 | 98.182 | 332.414 | 75,4% | 23,7% | 38,3% |
| 2004 | 536.572 | 110.080 | 345.963 | 79,4% | 15,0% | 38,1% |
| 2005 | 552.036 | 137.877 | 337.932 | 84,6% | 13,7% | 36,7% |
| 2006 | 588.654 | 154.073 | 339.701 | 91,1% | 16,1% | 35,6% |
| 2007 | 641.617 | 209.328 | 303.498 | 93,6% | 20,0% | 34,8% |
| 2008 | 663.782 | 179.046 | 420.905 | 91,8% | 9,6% | 30,7% |
| 2009 | 756.245 | 152.604 | 533.440 | 88,3% | 9,3% | 29,5% |
| 2010 | 874.208 | 796.389 | 83 | 24,3% | 8,8% | 29,2% |
| 2011 | 983.031 | 898.100 | 145 | 24,5% | 8,6% | 28,5% |
| 2012 | 1.023.979 | 942.104 | 115 | 21,5% | 7,9% | 25,1% |
| 2013 | 984.943 | 893.657 | 11 | 16,3% | 9,2% | 19,9% |

Nos anos de 2000 a 2009 a taxa de "mais de 15 minutos" é uma taxa **sobre voos que
tiveram ocorrência** e fica entre 74% e 94%; de 2010 em diante, com quase toda a
malha carimbada, ela cai para a faixa de 16% a 25%. Não são a mesma grandeza. Um
modelo treinado até 2009 e testado em 2010 não enfrenta uma mudança de mundo:
enfrenta uma troca de **amostra**, e é isso que a tabela da seção 4 mostra.

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
número de voo no mesmo dia: o atraso real com que ela chegou, se passou de 15
minutos, se foi cancelada. Nada do próprio voo.

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
| `targets_are_not_features` | ok — 5 targets and 5 diagnostics kept out of both horizons |
| `horizons_are_nested` | ok — H-1 adds ['prev_arr_delay_min', 'prev_late15', 'prev_cancelled'] to D-1's 46 features |
| `lag_windows_closed` | ok — over 1,427,305 rows where t-1 and t differ: 1.0000 match t-1, 0.0000 match t (pandas 2.3.3) |
| `movements_from_schedule` | ok — 1.0000 of 1,644,260 rows match a recount from sched_dep/sched_arr (a dataset reusing the staged dep_hour, which falls back to actual_dep, would not) |
| `previous_leg_precedes_departure` | ok — 453,524 linked legs, 0 with a negative turnaround, 0 with none, 0 turnarounds on unlinked flights |
| `targets_null_without_actual` | ok — 470,294 realised flights with no actual arrival time (ADR-0012) and 1,235 with a suspect timestamp (ADR-0015) are excluded from the arrival target; 0 rows disagreeing |
| `first_year_has_no_p90` | ok — 2000: 0 rows carry a p90 flag (must be 0); later years: 983,957 of 984,962 |
| `calendar_matches_the_table` | ok — 92 dated holidays, 27,386 flagged flights, 0 wrong |

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
| 2006 | 154.073 | 0,911 | 0,810 | 0,969 | 0,065 | 0,864 | 0,982 | 0,056 | 0,718 | 0,075 | 0,788 | 0,071 |
| 2007 | 209.328 | 0,936 | 0,788 | 0,977 | 0,050 | 0,840 | 0,985 | 0,045 | 0,717 | 0,055 | 0,630 | 0,059 |
| 2008 | 179.046 | 0,918 | 0,761 | 0,969 | 0,067 | 0,803 | 0,976 | 0,063 | 0,679 | 0,072 | 0,629 | 0,074 |
| 2009 | 152.604 | 0,883 | 0,767 | 0,953 | 0,086 | 0,804 | 0,963 | 0,080 | 0,680 | 0,098 | 0,583 | 0,103 |
| 2010 | 796.389 | 0,243 | 0,638 | 0,337 | 0,250 | 0,736 | 0,511 | 0,207 | 0,621 | 0,208 | 0,621 | 0,205 |
| 2011 | 898.100 | 0,245 | 0,636 | 0,355 | 0,203 | 0,735 | 0,543 | 0,169 | 0,610 | 0,182 | 0,595 | 0,183 |
| 2012 | 942.104 | 0,215 | 0,698 | 0,398 | 0,153 | 0,754 | 0,531 | 0,138 | 0,608 | 0,165 | 0,548 | 0,168 |
| 2013 | 893.657 | 0,163 | 0,711 | 0,348 | 0,124 | 0,749 | 0,457 | 0,114 | 0,613 | 0,134 | 0,566 | 0,135 |

Quatro leituras.

**O horizonte H−1 ganha em todos os anos**, e o ganho é maior justamente depois
de 2010, quando a base é baixa: em 2013 a AUC vai de 0,711 para 0,749 e a PR-AUC
de 0,348 para 0,457 — 31% de ganho relativo na métrica que enxerga a classe
positiva. Em 2010 e 2011 o salto é ainda maior, de 0,638 para 0,736 e de 0,636
para 0,735. É o mesmo achado da literatura recente (FlightSense, 2026: AUC 0,732
com malha, 0,875 com propagação), obtido aqui sem *tail number*, só com o número
de voo — e diluído pelos 71% a 80% de voos sem elo identificável, para os quais o
H−1 não acrescenta nada. A tabela 3 mostra o efeito sem essa diluição.

**As referências ingênuas não são espantalhos.** A prevalência da rota no mês
anterior já ordena os voos bem acima do acaso. O modelo precisa ser lido como
ganho sobre ela, não sobre 0,5.

**A PR-AUC antes de 2010 é altíssima porque a base é altíssima.** Com 88% a 94%
de positivos, uma regra que chuta "atrasado" acerta quase sempre; o Brier é o
número que separa os modelos nesses anos.

**2010 e 2011 são os piores folds do D−1** (0,638 e 0,636), e não por acaso: são
os primeiros anos de teste cuja amostra é a malha completa enquanto o treino
ainda é quase todo amostra selecionada. Em 2012 e 2013, com 2010–2011 já dentro
do treino, a AUC volta para 0,698 e 0,711. A degradação é do desenho da fonte,
não do modelo, e é exatamente o que uma origem rolante existe para tornar
visível — o split fixo da seção 4.2, que treina em 2002–2010 e testa em
2012–2013, devolve 0,702 e esconde tudo isso num número só.

### 4.1. Só onde existe etapa anterior ligada

O H−1 só diz algo onde a etapa anterior existe. Os dois horizontes são
reavaliados exatamente nessas linhas, para que a diferença seja o horizonte e não
a população.

| ano | share ligado | n ligado | D−1 AUC | H−1 AUC | D−1 Brier | H−1 Brier |
|---|---|---|---|---|---|---|
| 2006 | 38,1% | 58.660 | 0,803 | 0,927 | 0,064 | 0,043 |
| 2007 | 35,4% | 74.121 | 0,806 | 0,922 | 0,049 | 0,033 |
| 2008 | 32,5% | 58.141 | 0,773 | 0,880 | 0,062 | 0,051 |
| 2009 | 31,0% | 47.360 | 0,751 | 0,845 | 0,094 | 0,077 |
| 2010 | 29,4% | 233.843 | 0,616 | 0,863 | 0,254 | 0,124 |
| 2011 | 28,7% | 258.134 | 0,626 | 0,849 | 0,207 | 0,124 |
| 2012 | 25,0% | 235.397 | 0,689 | 0,864 | 0,164 | 0,102 |
| 2013 | 19,8% | 177.263 | 0,703 | 0,867 | 0,138 | 0,086 |

Aqui o H−1 aparece pelo que é: em 2013 a AUC sobe de 0,703 para 0,867 e o Brier
cai de 0,138 para 0,086 sobre as mesmas 177.263 linhas. Nos anos de 2010 a 2013 o
ganho de AUC no subconjunto ligado é de 0,16 a 0,25 pontos — a favor do portão
contra a véspera, medido na mesma população.

### 4.2. Split fixo (ilustrativo)

Treino 2002–2010, validação 2011, teste 2012–2013 — o desenho que a literatura
usa. Reportado porque é comparável, não porque responde melhor.

| alvo | n teste | base | D−1 AUC | D−1 PR-AUC | D−1 Brier | H−1 AUC | H−1 PR-AUC | H−1 Brier |
|---|---|---|---|---|---|---|---|---|
| `late15_arr` | 1.835.761 | 0,189 | 0,702 | 0,372 | 0,140 | 0,751 | 0,499 | 0,127 |
| `late30_arr` | 1.835.761 | 0,090 | 0,684 | 0,190 | 0,079 | 0,752 | 0,360 | 0,070 |
| `late15_dep` | 1.835.761 | 0,164 | 0,658 | 0,279 | 0,131 | 0,732 | 0,451 | 0,115 |
| `cancelled` | 2.008.922 | 0,085 | 0,693 | 0,210 | 0,075 | 0,769 | 0,370 | 0,066 |

O alvo `cancelled` é o único sem exclusão da ADR-0012 e o único definido sobre a
malha inteira; o H−1 nele deve ser lido com cuidado, porque no portão o
cancelamento muitas vezes já foi decidido.

## 5. O que o modelo usa

Queda na AUC de teste quando a coluna é embaralhada, no último fold da origem
rolante (teste 2013), média de 3 repetições.

| # | D−1 variável | queda AUC | H−1 variável | queda AUC |
|---|---|---|---|---|
| 1 | `flight_no_late15_l3` | 0,1035 | `sched_block_min` | 0,0792 |
| 2 | `sched_block_min` | 0,0635 | `flight_no_late15_l3` | 0,0617 |
| 3 | `distance_km` | 0,0412 | `distance_km` | 0,0587 |
| 4 | `month` | 0,0156 | `prev_arr_delay_min` | 0,0480 |
| 5 | `origin_movements_hour` | 0,0102 | `origin_movements_hour` | 0,0176 |
| 6 | `dow` | 0,0068 | `month` | 0,0112 |
| 7 | `origin_icao` | 0,0052 | `origin_icao` | 0,0091 |
| 8 | `sched_dep_hour` | 0,0041 | `dest_icao` | 0,0067 |
| 9 | `route_late15_l1` | 0,0035 | `dow` | 0,0064 |
| 10 | `dest_icao` | 0,0030 | `prev_turnaround_min` | 0,0053 |

O ranking diz quatro coisas.

A primeira: o histórico do **próprio número de voo** nos três meses anteriores é
a variável isolada mais forte do D−1 (queda de 0,104 na AUC) e a segunda do H−1.
Uma malha carrega atraso estrutural por horário e por trecho, e o número de voo é
o identificador mais fino disponível sem tipo de aeronave.

A segunda: `sched_block_min` e `distance_km` vêm logo atrás nos dois horizontes.
São quase a mesma informação — o bloco previsto é distância mais folga da empresa
— e é a **folga** que carrega o sinal: um trecho com bloco generoso absorve
atraso de partida antes da chegada.

A terceira é metodológica. `prev_arr_delay_min` aparece só em 4º no H−1, com
queda de 0,048, muito abaixo do que a tabela 3 mostra (0,16 a 0,25 pontos de AUC
no subconjunto ligado). A razão é conhecida: `prev_late15` é o mesmo sinal
binarizado, e embaralhar uma variável deixando sua substituta intacta subestima
as duas — `prev_late15` sozinha cai para 0,0013. **Importância por permutação com
variáveis correlacionadas mede o que é insubstituível, não o que importa**; para
o valor do horizonte, a comparação de tabelas 2 e 3 é a medida certa.

A quarta é negativa e vale registrar: congestão programada, marca de slot e
região metropolitana contribuem quase nada depois de condicionar no aeroporto e
na hora (`origin_p90_hour` cai 0,0005, `origin_slot_coordinated` e
`origin_metro` cerca de zero). É consistente com a ADR-0007 — o proxy p90 é
interno ao VRA e não substitui capacidade declarada — e com o fato de o ICAO de
origem já carregar o que aquele aeroporto tem de estrutural.

### 5.1. Calibração

| faixa | n | share | média prevista | observado |
|---|---|---|---|---|
| 0,0–0,1 | 281.892 | 31,5% | 0,071 | 0,066 |
| 0,1–0,2 | 370.950 | 41,5% | 0,143 | 0,140 |
| 0,2–0,3 | 143.586 | 16,1% | 0,242 | 0,241 |
| 0,3–0,4 | 56.046 | 6,3% | 0,343 | 0,349 |
| 0,4–0,5 | 23.019 | 2,6% | 0,443 | 0,442 |
| 0,5–0,6 | 10.427 | 1,2% | 0,542 | 0,524 |
| 0,6–0,7 | 4.624 | 0,5% | 0,643 | 0,636 |
| 0,7–0,8 | 1.897 | 0,2% | 0,745 | 0,670 |
| 0,8–0,9 | 1.042 | 0,1% | 0,841 | 0,759 |
| 0,9–1,0 | 174 | 0,0% | 0,921 | 0,644 |

Fold de teste 2013, horizonte D−1. Até 0,7 de probabilidade prevista — 99,3% das
linhas — a calibração é boa: as duas colunas coincidem na terceira casa em cinco
das sete primeiras faixas. Acima disso o modelo fica confiante demais: prevê 0,92
onde observa 0,64, em 174 voos. Não é um problema prático nesse volume, mas é a
direção do erro que se deve esperar de um modelo treinado num período em que a
taxa-base era muito mais alta, e é o tipo de coisa que a AUC sozinha não mostra.
As faixas do H−1 estão em `reports/prediction/calibration.json`.

## 6. Custo

Uma varredura DuckDB por ano de `data/staged/` constrói a base inteira; cada ano
é materializado uma vez em tabela temporária e todos os agregados daquele ano —
movimentos por aeroporto-dia-hora, taxas mensais por número de voo, a ligação de
rotação — saem dessa mesma materialização. As taxas mensais que precisam de anos
anteriores vêm da tabela de fatos já versionada
(`data/analysis/fact_group_route_month.parquet`, ADR-0014) mais um resto de três
meses carregado de uma iteração para a seguinte. Nenhum ano é lido duas vezes.

| etapa | tempo | saída |
|---|---|---|
| construção da base (14 anos) | 33 s | 10.200.578 linhas, 64 colunas, 313 MB |
| origem rolante, 8 folds x 2 horizontes | 597 s | `reports/prediction/rolling.json` |
| importâncias por permutação (2 horizontes) | 116 s | `reports/prediction/importance.json` |
| split fixo, 4 alvos x 2 horizontes | 628 s | `reports/prediction/fixed.json` |
| **total `just ml`** | **1.427 s** | 23 min em 8 threads, 16 GB |

O fold mais caro é o de 2013 (295 s): treina em 2.866.056 voos com alvo, valida
em 942.104 e testa em 893.657. O pico de memória fica abaixo de 2 GB porque
`ml/split.py` lê e filtra um ano por vez — 2002–2011 são 6,9 milhões de voos
programados, mas só 2,9 milhões têm alvo de chegada, e os outros 4 milhões nunca
precisam existir como quadro.

## 7. Limites declarados

1. **A amostra do alvo muda em 2010** (ADR-0012). Métricas de anos de teste
   anteriores descrevem voos com ocorrência registrada; posteriores, praticamente
   toda a malha. Comparar 2007 com 2013 sem ler as duas taxas-base ao lado é
   comparar coisas diferentes.
2. **H−1 é o horizonte da ADR-0009, não um relógio.** A etapa anterior pode
   pousar depois do corte de uma hora antes da partida prevista. A base carrega
   `prev_arr_known_h1` — 1 quando a chegada real da etapa anterior ocorreu ao
   menos 60 minutos antes — e o manifesto reporta a fração por ano, que é baixa:
   de 1,7% a 8,4% das ligações. A variável **não** é anulada, porque a definição
   do horizonte é decisão registrada e não estimativa; mas o número está na
   frente de quem for usar o H−1 como previsão operacional.
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
8. **A tabela de fatos ainda tem chaves duplicadas.** 844 linhas sobre 422 chaves
   `group × rota × mês`, porque `build_fact` agrupa dentro de cada ano de arquivo
   e concatena (`ROADMAP.md`, itens em aberto). `ml.dataset_flights.collapse_fact`
   colapsa a tabela antes de qualquer junção — sem isso, 1.128 voos a mais só em
   2001 — e vira operação nula assim que a ADR-0016 estiver implementada a
   montante.

## 8. Como reproduzir

```bash
just ml-dataset   # a tabela de voos, uma varredura por ano de data/staged
just ml           # reconstrói a tabela e roda a avaliação completa
uv run pytest -q  # inclui as nove checagens de vazamento sobre o fixture
typst compile reports/prediction.typ reports/build/prediction.pdf
```

`data/derived/ml/` é git-ignorado (ADR-0004): 313 MB de tabela de voos não entram
no repositório. As 64 colunas estão declaradas em `src/vra/registry.py`,
renderizadas em `docs/dictionary.md` e descritas como recurso em
`datapackage.json` — quem clonar reconstrói a tabela em 33 segundos e sabe
exatamente o que vai encontrar.
