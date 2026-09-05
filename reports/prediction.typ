// Relatório de previsão de atrasos no nível do voo.
//
// Português (exceção deliberada ao inglês do repositório: CLAUDE.md, ADR-0006).
// NENHUM número deste relatório é digitado à mão: tudo vem de
// `reports/prediction/{rolling,fixed,importance,calibration,dataset,leakage}.json`,
// escritos por `uv run python -m ml.run`.
//
// Compilar:  typst compile reports/prediction.typ reports/build/prediction.pdf

#let rolling = json("prediction/rolling.json")
#let fixed = json("prediction/fixed.json")
#let importance = json("prediction/importance.json")
#let calib = json("prediction/calibration.json")
#let dataset = json("prediction/dataset.json")
#let leakage = json("prediction/leakage.json")
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

= O corte de 2010: o alvo antes e depois

Nos arquivos brutos de 2000 a 2009 o horário realizado só é preenchido quando
houve ocorrência (`docs/notes/staging.md`, seção 4.1). Sob a ADR-0012 com
`legacy_missing_actual_as_zero = False`, um voo realizado sem horário real
#emph[não tem alvo] — não é imputado como pontual. A consequência é direta e
domina a leitura de qualquer métrica anterior a 2010:

#let ds_rows = dataset.by_year.map(r => (
  str(r.year),
  miles(r.rows),
  miles(r.target_rows),
  miles(r.target_excluded_missing_actual),
  miles(r.target_excluded_suspect),
  pct(r.late15_arr_rate),
  pct(r.cancelled_rate),
  pct(r.prev_leg_share),
)).flatten()

#table(
  columns: 8,
  align: (left, right, right, right, right, right, right, right),
  [ano], [voos programados], [com alvo], [sem horário real (ADR-0012)],
  [horário suspeito (ADR-0015)], [taxa > 15 min], [cancelamento], [etapa anterior],
  ..ds_rows,
)

A coluna "taxa > 15 min" de 2000 a 2009 é uma taxa sobre voos #emph[que tiveram
ocorrência]. De 2010 em diante é a taxa sobre praticamente toda a malha. Não são
a mesma grandeza, e o modelo que atravessa 2009 → 2010 enfrenta uma troca de
#emph[amostra], não de mundo. A regra da ADR-0015 é pequena ao lado dessa —
5.249 voos em toda a série, contra 3.981.347 sem horário real — mas tira os
piores rótulos: um atraso de 43.170 minutos é erro de digitação de mês, e treinar
contra ele é treinar contra o cartório.

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

Quatro leituras. #emph[Primeiro], o horizonte H−1 ganha em todos os anos, e o
ganho é grande justamente onde a base é baixa — a informação da etapa anterior é
o que a malha programada não tem. #emph[Segundo], as referências ingênuas não são
espantalhos: a prevalência da rota no mês anterior já ordena os voos bem acima do
acaso, e é contra ela, não contra 0,5, que o modelo precisa ser lido.
#emph[Terceiro], os anos de teste anteriores a 2010 têm PR-AUC altíssima porque a
base é altíssima: com 88 a 94% de positivos, acertar a classe positiva é fácil e
o Brier é o número que distingue os modelos. #emph[Quarto], 2010 e 2011 são os
piores folds do D−1 e não por acaso — são os primeiros anos de teste cuja amostra
é a malha completa enquanto o treino ainda é quase todo amostra selecionada;
quando 2010–2011 entram no treino, a AUC volta a 0,70. É essa degradação que uma
origem rolante existe para tornar visível, e que o split fixo da seção seguinte
resume num número só.

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

Aqui o horizonte aparece pelo que é: em 2013 a AUC sobe de 0,703 para 0,867 e o
Brier cai de 0,138 para 0,086 sobre as mesmas 177.263 linhas. De 2010 a 2013 o
ganho no subconjunto ligado é de 0,16 a 0,25 pontos de AUC — contra 0,04 a 0,10
na tabela anterior, onde ele fica diluído pelos 71% a 80% de voos sem elo
identificável.

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
`ml/leakage_tests.py` rodam sobre a base real (anos
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

+ *A amostra do alvo muda em 2010.* Métricas de anos de teste anteriores a 2010
  descrevem voos com ocorrência registrada; posteriores, praticamente toda a
  malha. A tabela da seção 2 traz os dois números lado a lado exatamente para
  que ninguém compare 2007 com 2013 sem ver isso.
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
  #nf(dataset.seconds, d: 0) segundos por `just ml-dataset`. Reprodução completa:
  `just ml`.
]
