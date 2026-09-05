# Apêndice A — Além do artigo: o preditor de atrasos por voo

Português (ADR-0006).

Este apêndice sai do painel rota × mês e desce ao voo. Ao terminá-lo, o leitor
sabe o que o preditor de atrasos deste repositório prevê, com que informação
em cada um de dois horizontes, como o vazamento de informação foi impedido e
medido, como o desempenho foi avaliado ano a ano de 2006 a 2013 e quanto
custa refazê-lo. Nada aqui está em Bendinelli, Bettini & Oliveira (2016,
*Transportation Research Part A* 85, 39-52, doi 10.1016/j.tra.2016.01.001):
o artigo estima um painel agregado; o preditor usa as mesmas etapas de voo, o
mesmo universo (ADR-0002) e as mesmas definições, e responde a outra pergunta
— este voo vai atrasar? Todo número vem de `reports/summary.json` (bloco
`prediction`) ou de `reports/prediction/*.json`, escritos por
`airline-delays predict`; a nota de pesquisa é `docs/notes/prediction.md` e o
relatório compilado, `reports/pdf/prediction.pdf`.

## 1. A unidade e os alvos

A unidade é o **voo programado** do universo de replicação — tipos de linha
N, R e E, DI 0 —, realizado ou cancelado: 10.200.560 linhas de 2000 a 2013
(`prediction.rows`, `prediction.years`). Começar pelo voo programado, e não
pelo realizado, é o que dá denominador ao alvo de cancelamento e o que faz a
contagem de movimentos programados por aeroporto-dia-hora ser a que o
aeroporto tinha na véspera. Cinco alvos (`prediction.targets`), todos
declarados na camada `ml` de `src/airline_delays/schema/columns.py`:

| Alvo | Definição | Onde existe |
|---|---|---|
| `late15_arr` | chegada com mais de 15 minutos de atraso | voo realizado, horário não suspeito, e horário real presente ou "sem alteração reportada" (ADR-0017) |
| `late30_arr` | chegada com mais de 30 minutos de atraso | idem |
| `arr_delay_min` | atraso de chegada com sinal, em minutos | idem |
| `late15_dep` | partida com mais de 15 minutos de atraso | idem |
| `cancelled` | voo cancelado | toda linha |

Três regras decidem se um voo tem alvo de atraso. A primeira é a leitura B da
ADR-0017: nos arquivos de 2000 a 2009 o horário realizado é campo do Boletim
de Alteração de Voo, que a IAC 1504 manda emitir só quando há alteração;
campo vazio em voo realizado é ausência de alteração reportada, o atraso vale
0 e a linha recebe a marca `on_time_no_bav`. A leitura vale para empresas de
classe FSC, LCC ou regional em `data/external/groups.csv`; para as demais —
estrangeiras e o lado não operador de um code-share — o vazio continua
desconhecido e o voo fica sem alvo. A segunda é a ADR-0015: um horário real a
um dia civil ou mais do previsto é erro de digitação de mês, e o voo sai de
todo alvo de atraso (`actual_time_suspect`). A terceira: voo cancelado não tem
atraso; cancelamento é alvo próprio.

| Janela 2000–2009 | Valor | Chave em `reports/summary.json` |
|---|---|---|
| voos realizados no escopo da leitura B | 5.106.100 | `prediction.legacy_window.realised_in_scope` |
| voos realizados fora do escopo | 313.366 | `prediction.legacy_window.realised_out_of_scope` |
| taxa de chegada real vazia, no escopo | 72,9% | `prediction.legacy_window.null_arrival_rate_in_scope` |
| taxa de chegada real vazia, fora do escopo | 83,0% | `prediction.legacy_window.null_arrival_rate_out_of_scope` |
| voos com alvo de chegada | 5.156.450 | `prediction.legacy_window.targets_available` |

A assimetria entre as duas taxas de campo vazio é a evidência em que a
ADR-0017 se apoia. A leitura B é um **piso de pontualidade**: atraso não
reportado conta como pontual, e a taxa anterior a 2010 é um limite inferior.
De 2010 em diante o layout novo do VRA carimba horário real em praticamente
todo voo realizado, e a questão desaparece.

## 2. Os dois horizontes

O erro clássico da literatura de previsão de atrasos é misturar informação de
véspera com informação de portão e reportar um número só. Aqui são dois
problemas declarados (ADR-0009), e o segundo contém o primeiro.

**D-1, a véspera.** 46 variáveis (`prediction.features_d1`), todas conhecidas
na véspera do voo, listadas por nome em `reports/prediction/dataset.json`
(`features_d1`):

| Família | Variáveis |
|---|---|
| calendário | `month`, `dow`, `is_weekend`, `is_holiday`, `is_observance`, `is_holiday_window`, `is_high_season` |
| malha programada | `sched_dep_hour`, `sched_arr_hour`, `sched_block_min`, `leg_index`, `prev_leg`, `prev_turnaround_min` |
| geografia | `origin_icao`, `dest_icao`, `origin_node`, `dest_node`, `route_kind`, `distance_km`, `origin_metro`, `dest_metro`, `origin_slot_coordinated`, `dest_slot_coordinated` |
| congestão programada | `origin_movements_hour`, `dest_movements_hour`, `origin_movements_day`, `dest_movements_day`, `origin_p90_hour`, `dest_p90_hour` |
| empresa | `airline`, `group`, `class`, `airline_route_share_l1`, `airline_origin_share_l1`, `months_on_route`, `is_new_on_route` |
| histórico de janela fechada | `route_late15_l1`, `route_obs_l1`, `route_late15_l12`, `group_late15_l1`, `flight_no_late15_l3`, `flight_no_obs_l3`, `origin_late15_l1`, `dest_late15_l1`, `origin_weather_l1`, `dest_weather_l1` |

**H-1, o portão.** As mesmas 46 mais três (`prediction.features_h1_only`),
todas sobre a **etapa anterior** do mesmo número de voo no mesmo dia:
`prev_arr_delay_min`, `prev_late15` e `prev_cancelled`. Nada do próprio voo.
A ligação entre etapas é programada — mesmo dia, mesma empresa, mesmo
número, chegada prevista no aeroporto de origem antes da partida prevista —
e é feita por aeroporto (ICAO), não por nó: uma aeronave que pousa em
Congonhas não decola de Guarulhos. Existe etapa anterior ligada para 19,8% a
35,1% dos voos de cada ano de teste (`prediction.rolling.linked_share_min`,
`linked_share_max`); o VRA não publica a matrícula da aeronave, e a cadeia do
dia é a do número de voo.

## 3. A regra de vazamento e as nove checagens

A regra foi escrita antes da primeira variável (ADR-0009): nenhuma variável
pode conter informação posterior ao momento do horizonte. Em
`src/airline_delays/prediction/leakage.py` ela é executável — nove checagens
(`prediction.leakage_checks`) que rodam sobre a amostra versionada de
`tests/fixtures/` a cada `pytest` e sobre a base completa a cada
`just predict`, com o resultado em `reports/prediction/leakage.json`:

| Checagem | O que impõe |
|---|---|
| `features_exclude_post_departure` | nenhum nome de variável pós-decolagem entra em nenhum horizonte |
| `targets_are_not_features` | os cinco alvos e os seis diagnósticos ficam fora dos dois horizontes |
| `horizons_are_nested` | o H-1 é o D-1 mais as três variáveis da etapa anterior, e nada mais |
| `lag_windows_closed` | toda taxa defasada bate com a taxa em t-1 e não com a de t, nas células em que as duas diferem |
| `movements_from_schedule` | a contagem de movimentos por aeroporto-dia-hora é refeita só a partir dos horários previstos |
| `previous_leg_precedes_departure` | toda etapa anterior ligada chega, no previsto, antes da partida prevista do voo |
| `targets_null_without_actual` | o alvo segue exatamente as três regras da seção 1 |
| `first_year_has_no_p90` | a marca de hora cheia usa o p90 do ano civil anterior; o primeiro ano não a tem |
| `calendar_matches_the_table` | as marcas de feriado batem com `data/external/holidays.csv` |

Duas merecem explicação. `movements_from_schedule` existe porque a camada
staged calcula `dep_hour` sobre o horário previsto com recurso ao real quando
o previsto falta; reusá-la poria uma hora pós-decolagem numa variável de
véspera sem que nada quebrasse. `lag_windows_closed` é a forma executável de
um vazamento que este repositório mediu em si mesmo, no painel, quando uma
taxa do mesmo mês entrou como regressor; um teste companheiro planta o
vazamento de propósito e exige que a checagem falhe
(`tests/test_prediction_leakage.py`).

## 4. O desenho de avaliação: origem rolante

Para cada ano de teste $`y`$ de 2006 a 2013, o modelo treina até $`y-2`$,
escolhe o número de árvores em $`y-1`$ por parada antecipada e testa em
$`y`$: oito folds (`prediction.rolling.folds`, `test_years`). O aprendiz é o
XGBoost (`prediction.rolling.learner`) com árvores `hist` e categóricas
nativas; os hiperparâmetros são idênticos em todos os folds e nos dois
horizontes (`reports/prediction/rolling.json`, `meta.params`). O resultado é
o desenho de avaliação, não um modelo afinado. O alvo é `late15_arr`.

| Horizonte | Informação | AUC nos oito folds | AUC mediana | PR-AUC mediana | Brier mediano |
|---|---|---|---|---|---|
| D-1, véspera | malha, calendário, agregados defasados de rota e aeroporto | 0,715–0,741 | 0,726 | 0,462 | 0,163 |
| H-1, portão | D-1 mais a chegada realizada da etapa anterior | 0,757–0,824 | 0,788 | 0,604 | 0,143 |
| referência: prevalência da rota em t-1 | a taxa da rota no mês anterior | 0,608–0,673 | — | — | — |
| referência: prevalência do grupo em t-1 | a taxa do grupo no mês anterior | 0,549–0,641 | — | — | — |

Chaves: `prediction.rolling.horizons.D-1` e `.H-1` (`auc_min`, `auc_max`,
`auc_median`, `pr_auc_median`, `brier_median`) e
`prediction.rolling.baselines.route_prevalence_l1` e `.group_prevalence_l1`
(`auc_min`, `auc_max`).

Três leituras. O H-1 ganha do D-1 em todos os anos, e o ganho é o valor da
informação de portão. As referências não são espantalhos: a prevalência da
rota no mês anterior já ordena os voos bem acima do acaso, e o modelo se lê
como ganho sobre ela, não sobre 0,5. Os oito folds são comparáveis entre si
porque treino e teste medem a mesma grandeza em toda a série, sob a leitura
B; o que resta de variação entre anos é operação — o Brier acompanha a
taxa-base do ano, e a AUC, invariante à prevalência, é a coluna que se compara
direto.

## 5. Onde existe etapa anterior ligada

O H-1 só diz algo onde a etapa anterior existe. Os dois horizontes são
reavaliados exatamente nessas linhas, para que a diferença seja o horizonte e
não a população.

| Horizonte | AUC no subconjunto ligado, oito folds | Chave |
|---|---|---|
| D-1 | 0,705–0,760 | `prediction.rolling.horizons.D-1.linked_subset_auc_min`, `linked_subset_auc_max` |
| H-1 | 0,869–0,934 | `prediction.rolling.horizons.H-1.linked_subset_auc_min`, `linked_subset_auc_max` |

Medido na mesma população, o portão vale bem mais do que a tabela da seção 4
sugere: lá o H-1 está diluído pelos voos sem elo identificável, para os quais
ele não acrescenta nada. A importância por permutação conta a mesma história
pelo avesso: no fold de 2013, `flight_no_late15_l3` — o histórico do próprio
número de voo nos três meses anteriores — é a variável isolada mais forte
dos dois horizontes, seguida de `sched_block_min` e `distance_km`
(`reports/prediction/importance.json`); `prev_arr_delay_min` aparece atrás
delas no H-1 porque `prev_late15` é o mesmo sinal binarizado, e embaralhar
uma deixando a outra intacta subestima as duas. A calibração do D-1 no mesmo
fold está em `reports/prediction/calibration.json`: boa nas faixas de
probabilidade baixa e intermediária, que concentram quase todas as linhas, e
confiante demais nas faixas altas, na direção que se espera de um modelo
treinado num período de taxa-base mais alta.

## 6. O split fixo, para comparação

Treino 2002–2010, validação 2011, teste 2012–2013: o desenho que a literatura
usa, reportado porque é comparável, não porque responde melhor. Um número só
não mostra como o desempenho se move ao longo da série, e é por isso que a
origem rolante é o resultado principal.

| Alvo | AUC D-1 | AUC H-1 |
|---|---|---|
| `late15_arr` | 0,720 | 0,762 |
| `late30_arr` | 0,704 | 0,765 |
| `late15_dep` | 0,676 | 0,744 |
| `cancelled` | 0,723 | 0,791 |

Chaves: `prediction.fixed.<alvo>.D-1` e `.H-1`. O alvo `cancelled` é o único
definido sobre a malha inteira, sem as exclusões das ADR-0015 e ADR-0017; o
seu H-1 pede cautela, porque no portão o cancelamento muitas vezes já foi
decidido.

## 7. Custo

Uma varredura DuckDB por ano civil de `data/staged/` constrói a base inteira,
com o ano lido pela coluna `year` do voo e não pelo diretório de origem
(ADR-0016); as taxas mensais que precisam de anos anteriores vêm da
tabela-fato versionada, `data/analysis/fact_group_route_month.parquet`.
Nenhum ano é lido duas vezes.

| Etapa | Tempo medido | Chave |
|---|---|---|
| construção da base, 14 anos (`just predict-dataset`) | 24,73 s | `prediction.dataset_build_seconds` |
| avaliação completa: origem rolante, importâncias e split fixo (`just predict`) | 2.344,2 s | `prediction.runtime_seconds` |

A tabela por voo, `data/derived/ml/`, é regenerada e não versionada
(ADR-0004); as suas 65 colunas (`registry.columns_by_layer.ml`) estão
declaradas em `src/airline_delays/schema/columns.py` e renderizadas em
`docs/dictionary.md`.

## Escopo e próximos passos

O preditor cobre 2000–2013 e o que o VRA permite saber de véspera e no
portão. Quatro limites de escopo, cada um com o passo seguinte:

1. **A leitura B é um piso e o instrumento muda em 2010.** Antes de 2010 o
   alvo vem de um boletim de exceção; depois, de um carimbo universal. A marca
   `on_time_no_bav` por ano e a sensibilidade sob a leitura superada
   (`reports/prediction/rolling_reading_A.json`) deixam a troca visível.
2. **H-1 é o horizonte da ADR-0009, não um relógio.** A etapa anterior pode
   pousar depois do corte de uma hora antes da partida; `prev_arr_known_h1`
   mede, por ano, a fração em que a chegada real já era conhecida a tempo.
3. **Sem meteorologia, capacidade declarada nem tipo de aeronave.** O sinal
   de clima é a participação de códigos de clima no mês anterior; a hora cheia
   é o proxy p90 da ADR-0007; assentos e equipamento só existem no layout de
   2010 em diante. O METAR da REDEMET é a extensão de maior retorno esperado
   ([`apendice-d-extensoes.md`](apendice-d-extensoes.md)).
4. **Empresas de classe `other` ficam sem alvo antes de 2010**, por decisão
   registrada (IAC 1504, art. 6.6); se os trechos de code-share da não
   operadora devem sair dos universos por completo é auditoria própria,
   candidata a ADR-0018.

## Onde conferir

- `reports/summary.json` — bloco `prediction`: `rows`, `years`,
  `features_d1`, `features_h1_only`, `targets`, `leakage_checks`, `rolling`,
  `fixed`, `legacy_window`, `runtime_seconds`, `dataset_build_seconds`.
- `reports/prediction/rolling.json`, `fixed.json`, `leakage.json`,
  `dataset.json`, `calibration.json`, `importance.json` e `results.md` —
  escritos por `airline-delays predict`; `rolling_reading_A.json` e
  `dataset_reading_A.json`, a sensibilidade sob a leitura superada.
- `docs/notes/prediction.md` — a nota de pesquisa, com as tabelas ano a ano;
  `docs/notes/colegiado-adr0012.md`, o colegiado que decidiu a leitura B.
- `src/airline_delays/prediction/` — a camada de previsão; `just predict-dataset`
  e `just predict` a executam.
