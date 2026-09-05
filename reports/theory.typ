// Relatório da camada de teoria — o modelo de Stackelberg da monografia de 2013,
// derivado e verificado, e as cinco figuras da economia do congestionamento.
//
// Português (exceção deliberada ao inglês do repositório: CLAUDE.md, ADR-0006).
// NENHUM número deste relatório é digitado à mão: tudo vem de
// `reports/theory/model.json` e `reports/theory/figures.json`, escritos por
// `uv run python -m theory.run` (`just theory`). As figuras são os SVG de
// `reports/theory/figures/`, desenhados por `theory/figures.py`.
//
// Compilar:  typst compile reports/theory.typ reports/build/theory.pdf

#let model = json("theory/model.json")
#let figs = json("theory/figures.json")

#set document(
  title: "A teoria por trás do artigo — o modelo de Stackelberg da monografia de 2013, derivado",
  author: "William Eduardo Bendinelli",
)
#set page(paper: "a4", margin: (x: 2.2cm, y: 2.4cm), numbering: "1")
#set text(font: ("Libertinus Serif", "New Computer Modern", "Times New Roman"), size: 10pt, lang: "pt")
#set par(justify: true, leading: 0.62em)
#show heading: set block(above: 1.3em, below: 0.7em)
#set table(stroke: 0.4pt + luma(60%), inset: 4pt)
#show table.cell.where(y: 0): strong

// ---------------------------------------------------------------- utilitários
#let nf(x, d: 4) = if x == none { "—" } else if type(x) == bool { if x { "sim" } else { "não" } } else { str(calc.round(x, digits: d)).replace(".", ",") }
#let sgn(x, d: 4) = if x == none { "—" } else if x >= 0 { "+" + nf(x, d: d) } else { nf(x, d: d) }
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
#let origem = (monograph: "monografia", BVD: "Brueckner e Van Dender (2008)", here: "este repositório")
#let rot_origem(o) = origem.at(o, default: o)

// ------------------------------------------------------------------- abertura
#align(center)[
  #text(size: 16pt, weight: "bold")[A teoria por trás do artigo]
  #v(0.2em)
  #text(size: 11pt)[
    O modelo de líder de Stackelberg num aeroporto congestionado da monografia
    _Efeitos da entrada de uma empresa aérea de baixo custo na internalização das
    externalidades do congestionamento_ (USP/ESALQ, Piracicaba, 2013), seção 4,
    segundo Brueckner e Van Dender (2008), derivado e verificado; e as cinco
    figuras da sua seção 2, redesenhadas.
  ]
  #v(0.4em)
  #text(size: 9pt, fill: luma(35%))[
    #model.meta.n_identities identidades verificadas com sympy #model.meta.sympy ·
    #figs.figures.len() figuras · equações numeradas como na monografia, (1) a (12)
  ]
]

#v(0.6em)

#block(fill: luma(96%), inset: 8pt, radius: 3pt, width: 100%)[
  *Nada aqui é estimado em dados.* O sympy verifica que a álgebra segue dos
  pressupostos declarados; não diz se as empresas se comportam como o modelo supõe.
  Cada afirmação carrega a sua origem: da monografia, de Brueckner e Van Dender
  (reenunciada) ou deste repositório (o que a derivação acrescenta). Todos os
  números vêm de `reports/theory/model.json` e `figures.json`, escritos por
  `uv run python -m theory.run`.
]

= 1. O modelo e os seus pressupostos

Duas empresas aéreas, 1 e 2, servem um aeroporto congestionado no período de pico
e escolhem volumes de voo $f_1$ e $f_2$. Os passageiros pagam um preço total fixo
$p$ (demanda perfeitamente elástica no caso-base); cada voo tem $s$ assentos,
todos vendidos, ao custo $tau$ por assento. O congestionamento acrescenta um custo
de tempo por passageiro $t(F)$ e um custo operacional por voo $g(F)$, ambos
funções do tráfego total $F = f_1 + f_2$:

$ R_i = [p - t(f_1 + f_2)] s f_i, quad i = 1, 2 #h(2em) (1) $
$ pi_i = [p - t(f_1 + f_2)] s f_i - [tau s + g(f_1 + f_2)] f_i #h(2em) (2) $
$ pi_i = (p - tau) s f_i - c(f_1 + f_2) f_i, quad c(F) equiv s t(F) + g(F), quad c' > 0, quad c'' >= 0 #h(2em) (3)–(5) $

#table(
  columns: (auto, 1fr, auto),
  align: (left, left, left),
  [id], [pressuposto], [status],
  ..model.assumptions.map(a => (a.id, a.statement, a.status)).flatten(),
)

= 2. Ótimo social, seguidor e líder

Com demanda perfeitamente elástica o excedente do consumidor é zero e o ótimo
maximiza o lucro conjunto; a condição de primeira ordem, por assento, é

$ p - tau - [F c'(F) + c(F)] / s = 0 #h(2em) (6) $

O seguidor toma $f_1$ como dado e satisfaz

$ p - tau - [f_2 c' + c] / s = 0 #h(2em) (7) $

Diferenciando (7) totalmente,

$ (partial f_2) / (partial f_1) = - (f_2 c'' + c') / (f_2 c'' + 2 c') equiv - lambda, quad 1/2 <= lambda < 1 #h(2em) (8) $

com $lambda = 1/2$ exatamente quando $c'' = 0$ (`reaction_slope`: $lambda - 1/2 = #raw(model.reaction_slope.lambda_minus_half)$
e $1 - lambda = #raw(model.reaction_slope.one_minus_lambda)$, com $x = f_2 c'' slash c'$). O líder antecipa a reação:

$ p - tau - 1/s [f_1 c' (1 + (partial f_2) / (partial f_1)) + c] = 0 #h(2em) (9) $

Comparando (7) e (9) no mesmo ponto, este repositório obtém
$f_1 = #raw(model.leader_follower.f1)$ — o líder opera pelo menos o dobro dos voos do
seguidor, e exatamente o dobro sob custo linear.

#table(
  columns: (auto, auto, auto, auto, 1fr),
  align: (left, left, left, center, left),
  [id], [equação], [origem], [fecha], [afirmação],
  ..model.identities.map(i => (raw(i.id), i.equation, rot_origem(i.origin), nf(i.holds), i.statement)).flatten(),
)

= 3. Pedágios: a Proposição 1

A diferença entre a condição social (6) e a do líder (9) é a tarifa por voo que
restaura o ótimo:

$ T_1 = (f_2 - f_1 (partial f_2) / (partial f_1)) c' = ((f_2 + lambda f_1) dot "MCD") / (f_1 + f_2), quad "MCD" equiv (f_1 + f_2) c' #h(2em) (10) $
$ T_1^* = 1/2 (1 + lambda^*) "MCD"^* #h(2em) (11) $

#table(
  columns: (1fr, auto),
  align: (left, right),
  [estrutura], [tarifa / MCD\*],
  [monopólio], [#nf(model.tolls.monopoly_over_MCD, d: 2)],
  [duopolista de Cournot, e o seguidor de Stackelberg], [#nf(model.tolls.follower_over_MCD, d: 2)],
  [líder de Stackelberg], [#raw(model.tolls.leader_symmetric_share); #nf(model.tolls.leader_over_MCD_linear, d: 2) (= #model.tolls.leader_over_MCD_linear_exact) sob custo linear],
  [atomística], [#nf(model.tolls.atomistic_over_MCD, d: 2)],
)

Sob custo linear a tarifa do líder fica *a meio caminho* entre a de Cournot e a
atomística — o que a monografia escreve como "entre a metade da tarifa de Cournot e
a tarifa atomística", tradução truncada de _halfway between_.

= 4. Exemplos numéricos

#let exemplo(nome, ex) = {
  let st = ex.stackelberg
  let opt = ex.social_optimum
  let tl = ex.tolls_at_symmetric_optimum
  let custo = ex.cost.pairs().filter(p => p.at(0) != "family").map(p => p.at(0) + " = " + nf(p.at(1), d: 3)).join(", ")
  let demanda = if ex.demand == none { "perfeitamente elástica" } else { ex.demand.pairs().filter(p => p.at(0) != "family").map(p => p.at(0) + " = " + nf(p.at(1), d: 3)).join(", ") }
  heading(level: 2, nome)
  [Primitivas $p = #nf(ex.primitives.p, d: 0)$, $tau = #nf(ex.primitives.tau, d: 0)$, $s = #nf(ex.primitives.s, d: 0)$; custo #ex.cost.family (#custo); demanda #demanda.]
  table(
    columns: (1fr, auto),
    align: (left, right),
    [grandeza], [valor],
    [F\* (total eficiente), W\*], [#nf(opt.F_star, d: 3), #miles(opt.welfare_star)],
    [$lambda^*$, $T_1^* slash "MCD"^*$, $T_1^*$, $T_2^*$], [#nf(tl.lambda_star), #nf(tl.T1_star_over_MCD), #nf(tl.T1_star, d: 1), #nf(tl.T2_star, d: 1)],
    [Stackelberg $f_1$, $f_2$, $F$], [#nf(st.f1, d: 3), #nf(st.f2, d: 3), #nf(st.F, d: 3)],
    [Stackelberg $lambda$, $f_1 slash f_2$, $T_1 slash "MCD"$], [#nf(st.lam), #nf(st.f1 / st.f2, d: 3), #nf(st.T1_over_MCD)],
    [Stackelberg $pi_1$, $pi_2$, $W$, perda / W\*], [#miles(st.profit1), #miles(st.profit2), #miles(st.welfare), #nf(st.loss_share)],
    [Cournot $f$, $F$, perda / W\*], [#nf(ex.cournot.f1, d: 3), #nf(ex.cournot.F, d: 3), #nf(ex.cournot.loss_share)],
    [atomística $F$; monopólio $F$], [#nf(ex.atomistic.F, d: 3); #nf(ex.monopoly.F, d: 3)],
  )
}

#exemplo("Custo linear, demanda perfeitamente elástica", model.examples.linear)
#exemplo("Custo quadrático, demanda perfeitamente elástica", model.examples.quadratic)
#exemplo("Custo linear, demanda inelástica linear", model.examples.inelastic_linear_demand)

= 5. Demanda inelástica e a "Pressuposição 2"

Com $p = d(s F)$, $d' < 0$, a condição do líder passa a ser

$ d + s f_1 d' (1 + (partial f_2) / (partial f_1)) - tau - 1/s [f_1 c' (1 + (partial f_2) / (partial f_1)) + c] = 0 #h(2em) (12) $

Se $partial f_2 slash partial f_1 = -1$, (12) reduz-se a $#raw(model.inelastic.limit_slope_minus_one) = 0$: o líder
não exerce poder de mercado e não internaliza nada. Se $partial f_2 slash partial f_1 = -1/2$,
exerce metade do poder de mercado (termo $#raw(model.inelastic.market_power_term_at_minus_half)$) e ainda
deixa de internalizar $#raw(model.inelastic.uninternalised_term_at_minus_half)$. A "Pressuposição 2" da monografia
lê o líder entre esses dois extremos. Este repositório mostra que os limites
$-1 < partial f_2 slash partial f_1 <= -1/2$ valem sob demanda inelástica *se e só se*
$#raw(model.inelastic.slope_bounds_condition)$ — automático para demanda linear ou côncava,
não garantido para demanda convexa.

#let ex12 = model.examples.inelastic_linear_demand.equation_12_terms_at_stackelberg
No exemplo linear-linear, no ponto de Stackelberg: termo de poder de mercado
#nf(ex12.market_power_term, d: 2), termo não internalizado #nf(ex12.uninternalised_term, d: 2),
tarifa atomística por assento #nf(ex12.atomistic_toll_per_seat, d: 2); o tráfego excede o
ótimo em #nf(ex12.F_exceeds_optimum_by, d: 3) voos.

#table(
  columns: (auto, auto, auto, auto, auto, auto, auto, auto),
  align: (right, right, right, right, right, right, right, right),
  [$d d$], [$f_1$], [$f_2$], [$F$], [$F^*$], [preço], [poder de mercado], [não internalizado],
  ..model.comparative_statics.demand_slope.map(r => (nf(r.dd, d: 3), nf(r.f1, d: 2), nf(r.f2, d: 2), nf(r.F, d: 2), nf(r.F_star, d: 2), nf(r.price, d: 2), nf(r.market_power_term, d: 2), nf(r.uninternalised_term, d: 2))).flatten(),
)

Quando a demanda é suficientemente inclinada, o tráfego de Stackelberg cai *abaixo*
do ótimo: as duas distorções de (12) puxam em sentidos opostos.

= 6. Extensão deste repositório: uma entrante de baixo custo

#let lcc = model.extension_lcc
Não é da monografia. Num jogo de Cournot com custo linear, duas incumbentes a
$tau = #nf(lcc.incumbent_tau, d: 0)$ e uma entrante a $tau = #nf(lcc.entrant_tau, d: 0)$: tráfego total
#nf(lcc.triopoly.F, d: 1) (duopólio de Cournot: #nf(lcc.duopoly_cournot.F, d: 1); Stackelberg:
#nf(lcc.stackelberg_duopoly_F, d: 1)); voos #nf(lcc.triopoly.flights.at(0), d: 1), #nf(lcc.triopoly.flights.at(1), d: 1),
#nf(lcc.triopoly.flights.at(2), d: 1); parcela internalizada do dano marginal
#nf(lcc.triopoly.internalised_share.at(0), d: 2) para a entrante contra
#nf(lcc.triopoly.internalised_share.at(1), d: 2) para cada incumbente. É o termo que Guo, Jiang e
Wan (2018) levam às tarifas.

= 7. Ponte com a Tabela 3 do artigo de 2016

#let rotulos_pt = (:)
#for row in model.bridge.rows { rotulos_pt.insert(row.variable, row.theory_object_pt) }
#let t3 = model.bridge.tables.table3.variables
#let t6 = model.bridge.tables.table6.variables
#table(
  columns: (auto, 1fr, auto, auto, auto),
  align: (left, left, center, right, right),
  [variável], [objeto teórico], [esperado], [Tab. 3 (2)], [Tab. 6 (2)],
  ..t3.pairs().map(p => {
    let v = p.at(0)
    let info = p.at(1)
    let c3 = info.columns.at("2")
    let c6 = t6.at(v).columns.at("2")
    (raw(v), rotulos_pt.at(v), if info.expected_sign == none { "—" } else { info.expected_sign },
     nf(c3.b) + " " + (if c3.stars == none { "" } else { c3.stars }),
     nf(c6.b) + " " + (if c6.stars == none { "" } else { c6.stars }))
  }).flatten(),
)

Os coeficientes publicados vêm de `replication/published.json`; a coluna (2) da
Tabela 3 é o 2SGMM com as dummies de LCC, a da Tabela 6 o OLS correspondente.

= 8. As cinco figuras

#for (key, info) in figs.figures [
  #figure(image("theory/" + info.file, width: 78%), caption: info.title)
  #table(
    columns: (1fr, auto),
    align: (left, right),
    [grandeza], [valor],
    ..info.quantities.pairs().map(p => (raw(p.at(0)), nf(p.at(1), d: 2))).flatten(),
  )
  #text(size: 9pt)[#info.note]
]
