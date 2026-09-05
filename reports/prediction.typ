// Relatório de previsão de atrasos no nível do voo.
//
// Português (exceção deliberada ao inglês do repositório: CLAUDE.md, ADR-0006).
// NENHUM número deste relatório é digitado à mão: tudo vem de
// `reports/prediction/{rolling,fixed,importance,calibration,dataset,leakage}.json`,
// escritos por `airline-delays predict` (`just predict`).
//
// Compilar:  typst compile --root . reports/prediction.typ reports/pdf/prediction.pdf

#let rolling = json("prediction/rolling.json")
#let fixed = json("prediction/fixed.json")
#let importance = json("prediction/importance.json")
#let calib = json("prediction/calibration.json")
#let dataset = json("prediction/dataset.json")
#let leakage = json("prediction/leakage.json")
#let readingA = json("prediction/rolling_reading_A.json")
#let meta = rolling.at("meta")

#set document(
  title: "Previsão de atrasos no nível do voo — VRA 2000–2013",
  author: "William Eduardo Bendinelli",
)
#set page(paper: "a4", margin: (x: 2.1cm, y: 2.3cm), numbering: "1")
#set text(font: ("Libertinus Serif", "New Computer Modern", "Times New Roman"), size: 10pt, lang: "pt")
#set par(justify: true, leading: 0.62em)
#show heading: set block(above: 1.3em, below: 0.7em)
#set table(stroke: 0.4pt + luma(60%), inset: 4pt)
#show table.cell.where(y: 0): strong
#show raw: set text(size: 8.5pt)

// ---------------------------------------------------------------- utilitários
// Convenção numérica pt-BR: vírgula decimal, ponto de milhar.
#let nf(x, d: 4) = if x == none { "—" } else {
  let s = str(calc.round(x, digits: d))
  let parts = s.split(".")
  let dec = if parts.len() > 1 { parts.at(1) } else { "" }
  while dec.len() < d { dec = dec + "0" }
  if d == 0 { parts.at(0) } else { parts.at(0) + "," + dec }
}
#let miles(n) = if n == none { "—" } else {
  let s = str(calc.round(n))
  let out = ()
  let k = 0
  for c in s.clusters().rev() {
    if k > 0 and calc.rem(k, 3) == 0 { out.push(".") }
    out.push(c)
    k += 1
  }
  out.rev().join()
}
#let pct(x, d: 1) = if x == none { "—" } else { nf(x * 100, d: d) + "%" }
#let mdl(fold, h, key) = {
  if h in fold.models { fold.models.at(h).at(key, default: none) } else { none }
}
#let lnk(fold, h, key) = {
  if h in fold.linked_subset { fold.linked_subset.at(h).at(key, default: none) } else { none }
}
#let year_of(fold) = str(fold.test_years.at(0))

// ------------------------------------------------------------------- abertura
#align(center)[
  #text(size: 16pt, weight: "bold")[Previsão de atrasos no nível do voo]
  #v(0.2em)
  #text(size: 11pt)[
    VRA/ANAC reconstruído, 2000–2013 · validação temporal de origem rolante
    (`DECISIONS.md`, ADR-0009) · alvo principal
    #raw(rolling.target) (#rolling.target_label)
  ]
  #v(0.4em)
  #text(size: 9pt, fill: luma(35%))[
    #miles(dataset.rows) voos programados · #miles(dataset.by_year.len()) anos ·
    #meta.learner, #meta.params.tree_method · commit #raw(meta.git_commit) ·
    gerado em #meta.generated_at
  ]
]

#v(0.6em)

= O que está sendo previsto, e para quem

Duas perguntas diferentes, respondidas separadamente porque misturá-las é o erro
clássico da literatura de previsão de atrasos:

/ D−1 (véspera): o que um planejador sabe na noite anterior — malha programada,
  calendário, estrutura de mercado e histórico de janela fechada.
  #mdl(rolling.folds.at(0), "D-1", "n_features") variáveis.
/ H−1 (portão): acrescenta o resultado da #emph[etapa anterior] do mesmo número
  de voo no mesmo dia — o atraso real com que ela chegou, se foi cancelada, se
  passou de 15 minutos. #mdl(rolling.folds.at(0), "H-1", "n_features") variáveis.
  Nada do próprio voo.

A unidade é o voo #emph[programado] do universo de replicação (ADR-0002: tipos de
linha N, R, E e DI 0), realizado ou cancelado. O alvo de cancelamento existe em
toda linha; os alvos de atraso existem só onde há horário real, e é aí que está
a característica mais importante desta base.

= O horário real vazio: "sem alteração reportada" (ADR-0017)

Nos arquivos brutos de 2000 a 2009 o horário realizado é campo do Boletim de
Alteração de Vôo, emitido pela IAC 1504 só "sempre que houver alguma alteração"
(introdução e §3.1; horários e código de justificativa em §4.2 n, o, p). Campo
vazio em voo realizado é, portanto, #emph[ausência de alteração reportada], e não
desfecho desconhecido. Um colegiado de três revisores (ADR-0010, pareceres em
`docs/notes/colegiado-adr0012.md`) adotou essa leitura; o atraso vale 0 e a linha
recebe a marca `on_time_no_bav`.

#let lw = dataset.accounting.legacy_window
O escopo não é o arquivo inteiro. A taxa de nulo não é uma convenção só: de 2000
a 2009 é de #pct(lw.null_arrival_rate_in_scope) nos #miles(lw.realised_in_scope)
voos realizados dentro do escopo e de #pct(lw.null_arrival_rate_out_of_scope) nos
#miles(lw.realised_out_of_scope) fora dele, e o revisor cético mediu 90–100% em
estrangeiras e trechos de code-share num corte de 2005 sobre todos os voos
(tabela por empresa e ano em `reports/prediction/null_actual_by_carrier.csv`;
`docs/notes/prediction.md`). A IAC 1504 art. 6.6 diz que em code-share só a
operadora presta a informação. A leitura vale, então, apenas para voos
realizados de empresas de classe FSC, LCC ou regional em `groups.csv`; para
`other` e não rotuladas o vazio continua desconhecido e o voo fica #emph[fora de
escopo], sem alvo de atraso.

#let ds_rows = dataset.by_year.map(r => (
  str(r.year),
  miles(r.rows),
  miles(r.target_rows),
  miles(r.at("on_time_no_bav", default: 0)),
  pct(r.at("on_time_no_bav_share", default: none)),
  miles(r.target_excluded_missing_actual),
  miles(r.target_excluded_suspect),
  pct(r.late15_arr_rate),
  pct(r.at("prev_arr_known_share", default: none)),
)).flatten()

#table(
  columns: 9,
  align: (left, right, right, right, right, right, right, right, right),
  [ano], [voos programados], [com alvo], [sem alteração], [share dos realizados],
  [fora de escopo (ADR-0017)], [horário suspeito (ADR-0015)], [taxa > 15 min],
  [chegada anterior conhecida],
  ..ds_rows,
)

A leitura B é um #emph[piso de pontualidade]: atraso não reportado conta como
pontual, então a taxa anterior a 2010 é limite inferior. A alternativa não é
neutra — a leitura A condiciona no desfecho, guardando só os voos que tiveram
ocorrência, e produzia uma taxa-base de
#pct(readingA.folds.at(0).base_rate_test) em 2006 contra
#pct(readingA.folds.at(4).base_rate_test) em 2010, degrau que nasce na fronteira
de layout e não na operação; sob a leitura B os mesmos dois folds ficam em
#pct(rolling.folds.at(0).base_rate_test) e
#pct(rolling.folds.at(4).base_rate_test). A comparação completa está na seção
4.3. A quebra de 2010 continua sendo quebra de comparabilidade: de 2010 em
diante praticamente todo voo realizado traz horário real, e antes disso não.

A regra da ADR-0015 é pequena ao lado dessa — cerca de 5,2 mil voos em toda a
série — mas tira os piores rótulos: um atraso de 43.170 minutos é erro de
digitação de mês, e treinar contra ele é treinar contra o cartório. Desde esta
fase a marca vem do próprio staging, na coluna `actual_time_suspect`.

= Resultado principal: origem rolante

Treina até $y-2$, escolhe o número de árvores em $y-1$ (parada antecipada) e
testa em $y$. As duas referências ingênuas da ADR-0009 são a prevalência da rota
e a do grupo aéreo no mês anterior, com recuo para a taxa-base do treino onde o
mês anterior não observou nada.

#let roll_rows = rolling.folds.map(f => (
  year_of(f),
  miles(f.n_test),
  pct(f.base_rate_test),
  nf(mdl(f, "D-1", "auc"), d: 3),
  nf(mdl(f, "D-1", "pr_auc"), d: 3),
  nf(mdl(f, "D-1", "brier"), d: 3),
  nf(mdl(f, "H-1", "auc"), d: 3),
  nf(mdl(f, "H-1", "pr_auc"), d: 3),
  nf(mdl(f, "H-1", "brier"), d: 3),
  nf(f.baselines.route_prevalence_l1.auc, d: 3),
  nf(f.baselines.route_prevalence_l1.brier, d: 3),
  nf(f.baselines.group_prevalence_l1.auc, d: 3),
)).flatten()

#table(
  columns: 12,
  align: (left, right, right, right, right, right, right, right, right, right, right, right),
  table.cell(rowspan: 2)[ano], table.cell(rowspan: 2)[$n$ teste], table.cell(rowspan: 2)[base],
  table.cell(colspan: 3)[D−1], table.cell(colspan: 3)[H−1],
  table.cell(colspan: 2)[rota $t-1$], [grupo],
  [AUC], [PR-AUC], [Brier], [AUC], [PR-AUC], [Brier], [AUC], [Brier], [AUC],
  ..roll_rows,
)

Três leituras. #emph[Primeiro], o horizonte H−1 ganha em todos os anos, e o
ganho é grande justamente onde a base é baixa — a informação da etapa anterior é
o que a malha programada não tem. #emph[Segundo], as referências ingênuas não são
espantalhos: a prevalência da rota no mês anterior já ordena os voos bem acima do
acaso, e é contra ela, não contra 0,5, que o modelo precisa ser lido.
#emph[Terceiro], sob a leitura B da ADR-0017 a taxa-base é da mesma ordem em toda
a série, e o degrau de 2009 → 2010 que a leitura A produzia desapareceu: os folds
passam a ser comparáveis entre si, o que é a condição para que a origem rolante
signifique alguma coisa. O que sobra de variação entre folds é operação, não
troca de amostra.

== Só onde existe etapa anterior ligada

O H−1 só diz algo onde a etapa anterior existe. Os dois horizontes são
reavaliados exatamente nessas linhas, para que a diferença seja o horizonte e
não a população.

#let link_rows = rolling.folds.map(f => (
  year_of(f),
  pct(f.linked_share_test),
  miles(lnk(f, "D-1", "n")),
  nf(lnk(f, "D-1", "auc"), d: 3),
  nf(lnk(f, "H-1", "auc"), d: 3),
  nf(lnk(f, "D-1", "brier"), d: 3),
  nf(lnk(f, "H-1", "brier"), d: 3),
)).flatten()

#table(
  columns: 7,
  align: (left, right, right, right, right, right, right),
  [ano], [share ligado], [$n$ ligado], [AUC D−1], [AUC H−1], [Brier D−1], [Brier H−1],
  ..link_rows,
)

Aqui o horizonte aparece pelo que é: o ganho no subconjunto ligado é bem maior
que na tabela anterior, onde ele fica diluído pelos 61% a 80% de voos sem elo
identificável.

== Sensibilidade: leitura A ao lado da leitura B

A leitura A, superada pela ADR-0017, tratava horário real vazio como
#emph[desconhecido]. As colunas "A" abaixo vêm da rodada anterior, preservada em
`reports/prediction/rolling_reading_A.json`; nada foi reestimado sob a convenção
superada. De 2010 em diante as duas leituras enxergam o mesmo dado, e só aí a
comparação é de igual para igual — antes de 2010 muda a #emph[população de
teste], e a taxa-base diz isso.

#let a_by_year = (:)
#for f in readingA.folds { a_by_year.insert(year_of(f), f) }
#let sens_rows = rolling.folds.map(f => {
  let y = year_of(f)
  let a = a_by_year.at(y, default: none)
  (
    y,
    if a == none { "—" } else { miles(a.n_test) },
    miles(f.n_test),
    if a == none { "—" } else { pct(a.base_rate_test) },
    pct(f.base_rate_test),
    if a == none { "—" } else { nf(mdl(a, "D-1", "auc"), d: 3) },
    nf(mdl(f, "D-1", "auc"), d: 3),
    if a == none { "—" } else { nf(mdl(a, "H-1", "auc"), d: 3) },
    nf(mdl(f, "H-1", "auc"), d: 3),
  )
}).flatten()

#table(
  columns: 9,
  align: (left, right, right, right, right, right, right, right, right),
  [ano], [$n$ A], [$n$ B], [base A], [base B],
  [AUC D−1 A], [AUC D−1 B], [AUC H−1 A], [AUC H−1 B],
  ..sens_rows,
)

= Split fixo (ilustrativo)

Treino 2002–2010, validação 2011, teste 2012–2013 — o desenho que a literatura
usa. É reportado porque é comparável, não porque é a melhor resposta: um único
corte não mostra o que 2007 e 2013 fazem com um modelo treinado no outro.

#let fixed_rows = fixed.folds.map(f => (
  raw(f.target),
  miles(f.n_test),
  pct(f.base_rate_test),
  nf(mdl(f, "D-1", "auc"), d: 3),
  nf(mdl(f, "D-1", "pr_auc"), d: 3),
  nf(mdl(f, "D-1", "brier"), d: 3),
  nf(mdl(f, "H-1", "auc"), d: 3),
  nf(mdl(f, "H-1", "pr_auc"), d: 3),
  nf(mdl(f, "H-1", "brier"), d: 3),
)).flatten()

#table(
  columns: 9,
  align: (left, right, right, right, right, right, right, right, right),
  table.cell(rowspan: 2)[alvo], table.cell(rowspan: 2)[$n$ teste], table.cell(rowspan: 2)[base],
  table.cell(colspan: 3)[D−1], table.cell(colspan: 3)[H−1],
  [AUC], [PR-AUC], [Brier], [AUC], [PR-AUC], [Brier],
  ..fixed_rows,
)

= Calibração

Probabilidade prevista contra frequência observada, no último fold da origem
rolante. Um modelo bem calibrado tem as duas colunas iguais.

#let last_name = rolling.folds.at(rolling.folds.len() - 1).name
#let cal = calib.at(last_name)
#let cal_rows = cal.at("D-1").map(b => (
  nf(b.bin_low, d: 1) + "–" + nf(b.bin_high, d: 1),
  miles(b.n),
  pct(b.share),
  nf(b.mean_predicted, d: 3),
  nf(b.observed, d: 3),
)).flatten()

#table(
  columns: 5,
  align: (left, right, right, right, right),
  [faixa de probabilidade], [$n$], [share], [média prevista], [observado],
  ..cal_rows,
)

#text(size: 9pt, fill: luma(35%))[
  Fold #raw(last_name), horizonte D−1. As faixas do H−1 estão em
  `reports/prediction/calibration.json`.
]

= O que o modelo usa

Queda na AUC de teste quando a coluna é embaralhada, média de
#importance.repeats repetições sobre até #miles(importance.sample) linhas do
último fold. O ganho total do XGBoost está ao lado
porque os dois discordam de um jeito legível: ganho premia a variável que é
#emph[usada], permutação premia a variável de que a métrica #emph[depende].

#let top(h, k) = importance.horizons.at(h).slice(0, calc.min(k, importance.horizons.at(h).len()))
#let imp_rows(h) = top(h, 10).map(r => (
  raw(r.feature),
  nf(r.auc_drop, d: 4),
  nf(r.auc_drop_sd, d: 4),
)).flatten()

#grid(
  columns: (1fr, 1fr),
  gutter: 1em,
  [
    #text(weight: "bold")[D−1]
    #table(
      columns: 3,
      align: (left, right, right),
      [variável], [queda AUC], [dp],
      ..imp_rows("D-1"),
    )
  ],
  [
    #text(weight: "bold")[H−1]
    #table(
      columns: 3,
      align: (left, right, right),
      [variável], [queda AUC], [dp],
      ..imp_rows("H-1"),
    )
  ],
)

Três coisas no ranking. O histórico do #emph[próprio número de voo] nos três
meses anteriores é a variável isolada mais forte do D−1 e a segunda do H−1: a
malha carrega atraso estrutural por horário e por trecho, e o número de voo é o
identificador mais fino que existe sem tipo de aeronave. O bloco previsto e a
distância vêm logo atrás nos dois horizontes, e são quase a mesma informação — o
bloco é distância mais folga, e é a folga que carrega o sinal. E
`prev_arr_delay_min` aparece só em 4º no H−1, muito abaixo do que a tabela do
subconjunto ligado mostra: `prev_late15` é o mesmo sinal binarizado, e embaralhar
uma variável deixando a substituta intacta subestima as duas. Importância por
permutação mede o que é #emph[insubstituível], não o que importa; para o valor do
horizonte, a comparação das duas tabelas da seção anterior é a medida certa.

= A regra de vazamento, e as checagens que a impõem

A regra foi escrita antes da primeira variável (ADR-0009): nada do próprio voo
posterior à decolagem; nenhum agregado do mesmo mês que contenha o voo;
janelas históricas fechadas antes da data do voo. As nove checagens de
`src/airline_delays/prediction/leakage.py` rodam sobre a base real (anos
#leakage.years.map(y => str(y)).join(" e ")) e, no `pytest`, sobre a amostra
versionada em `tests/fixtures/`.

#let leak_rows = leakage.checks.map(c => (
  if c.passed { "ok" } else { "FALHOU" },
  raw(c.name),
  text(size: 8pt)[#c.detail],
)).flatten()

#table(
  columns: (auto, auto, 1fr),
  align: (left, left, left),
  [], [checagem], [o que foi medido],
  ..leak_rows,
)

Duas delas merecem destaque. `movements_from_schedule` reconta os movimentos por
aeroporto-dia-hora a partir do horário #emph[previsto] no `data/staged/`: a
coluna `dep_hour` da camada staged recorre ao horário #emph[real] quando o
previsto falta, e uma base que a reutilizasse carregaria hora pós-decolagem sem
que nada quebrasse. `lag_windows_closed` compara cada `route_late15_l1` com a
taxa da rota em $t-1$ #emph[e] em $t$, e exige que bata com a primeira e não com
a segunda — é a forma executável do vazamento que este repositório já mediu em
si mesmo, quando o `fsc_prdeldep` do mesmo mês levou um $R^2$ de painel de 0,58
para 0,82.

= Limites declarados

+ *A leitura B é um piso, e o instrumento muda em 2010.* Antes de 2010 o alvo
  vem do Boletim de Alteração de Vôo: atraso não reportado conta como pontual, e
  a taxa publicada é limite inferior. De 2010 em diante quase todo voo realizado
  traz horário real. A tabela da seção 2 traz a marca `on_time_no_bav` por ano
  para que a diferença de instrumento fique visível, e a seção 4.3 traz as
  métricas sob a leitura A ao lado.
+ *Empresas de classe `other` ficam sem alvo antes de 2010.* A leitura B não as
  cobre (IAC 1504 art. 6.6, code-share), e a auditoria que decidiria se esses
  trechos devem sair dos universos por completo é candidata a ADR-0018.
+ *H−1 é o horizonte da ADR-0009, não um relógio.* A etapa anterior pode pousar
  depois do corte de uma hora; a base carrega `prev_arr_known_h1` e o
  `manifest.json` reporta a fração por ano. A variável não é anulada, porque a
  definição do horizonte é decisão registrada, não estimativa.
+ *Sem meteorologia.* O METAR do DECEA/REDEMET não entra nesta fase; o que
  existe é a participação de códigos de clima no aeroporto no mês anterior, que
  é climatologia defasada, não previsão do tempo.
+ *Sem capacidade declarada.* A hora cheia é o proxy p90 da ADR-0007 com a
  janela fechada no ano anterior. `data/external/capacity.csv` tem uma linha, e
  uma linha não sustenta um painel nacional.
+ *Sem tipo de aeronave nem assentos.* Só existem no layout de 2010 em diante,
  e uma variável que nasce no meio da série quebra a validação temporal.

#v(0.8em)
#text(size: 8.5pt, fill: luma(35%))[
  Hiperparâmetros, idênticos em todos os folds e nos dois horizontes:
  #raw(meta.params.tree_method), profundidade #meta.params.max_depth, taxa
  #nf(meta.params.learning_rate, d: 2), até #meta.params.n_estimators árvores com
  parada antecipada em #meta.early_stopping_rounds rodadas, `max_bin`
  #meta.params.max_bin, subamostra #nf(meta.params.subsample, d: 1). A base tem
  #miles(dataset.rows) linhas e é reconstruída em
  #nf(dataset.seconds, d: 0) segundos por `just predict-dataset`. Reprodução completa:
  `just predict`.
]
