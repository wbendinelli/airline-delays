// Relatório de replicação — Tabelas 2 a 7 de Bendinelli, Bettini e Oliveira (2016).
//
// Português (exceção deliberada ao inglês do repositório: CLAUDE.md, ADR-0006).
// NENHUM número deste relatório é digitado à mão: tudo vem de
// `reports/replication/{results,summary,sensitivity}.json`, escritos por
// `airline-delays estimate`. Os valores publicados vêm de
// `src/airline_delays/estimation/published.json`, extraídos do texto do artigo por
// `src/airline_delays/estimation/published.py`.
//
// Compilar:  typst compile --root . reports/replication.typ reports/build/replication.pdf

#let results = json("replication/results.json")
#let summary = json("replication/summary.json")
#let grid_ = json("replication/sensitivity.json")
#let meta = results.at("meta")

#set document(
  title: "Replicação das Tabelas 2–7 — Bendinelli, Bettini e Oliveira (2016)",
  author: "William Eduardo Bendinelli",
)
#set page(paper: "a4", margin: (x: 2.2cm, y: 2.4cm), numbering: "1")
#set text(font: ("Libertinus Serif", "New Computer Modern", "Times New Roman"), size: 10pt, lang: "pt")
#set par(justify: true, leading: 0.62em)
#show heading: set block(above: 1.3em, below: 0.7em)
#set table(stroke: 0.4pt + luma(60%), inset: 4pt)
#show table.cell.where(y: 0): strong

// ---------------------------------------------------------------- utilitários
// Convenção numérica pt-BR: vírgula decimal, ponto de milhar.
#let nf(x, d: 4) = if x == none { "—" } else { str(calc.round(x, digits: d)).replace(".", ",") }
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
#let pct(x, d: 1) = if x == none { "—" } else { nf(x * 100, d: d) + "%" }

#let rotulos = (
  dailyflcong: "Voos em horas congestionadas",
  dailyflncong: "Voos em horas não congestionadas",
  prwheather: "Prop. de voos com mau tempo",
  princident: "Prop. de voos com incidentes",
  pr_connc: "Prop. de voos retidos por conexão",
  maxprdel: "Máx. prop. de voos atrasados na cidade",
  cshare: "Acordo de codeshare",
  rthhi: "HHI da rota",
  maxcthhi: "HHI máx. das cidades-extremo",
  lcc: "Presença de LCC na rota",
  maxalccfu: "Presença de LCC nas cidades-extremo",
)
#let titulos = (
  table3: [Tabela 3 — resultados de estimação (2SGMM)],
  table4: [Tabela 4 — verificações de robustez (2SGMM)],
  table5: [Tabela 5 — resultados de estimação (LIML)],
  table6: [Tabela 6 — resultados de estimação (OLS)],
  table7: [Tabela 7 — resultados de estimação (partidas)],
)
#let rotulos_stat = (
  n_obs: "Nº de observações",
  adj_r2: "R² ajustado",
  rmse: "RMSE",
  j_stat: "J de Hansen",
  j_p: "p-valor do J",
  kp_lm: "KP (rk LM)",
  weak_kp_f: "Weak KP (rk Wald F)",
  weak_cd_f: "Weak CD (Cragg–Donald F)",
  f_stat: "Estatística F",
)
#let tabelas_reg = ("table3", "table4", "table5", "table6", "table7")
#let ordem = (
  "dailyflcong", "dailyflncong", "prwheather", "princident", "pr_connc",
  "maxprdel", "cshare", "rthhi", "maxcthhi", "lcc", "maxalccfu",
)

// ------------------------------------------------------------------- abertura
#align(center)[
  #text(size: 16pt, weight: "bold")[Replicação das Tabelas 2–7]
  #v(0.2em)
  #text(size: 11pt)[
    Bendinelli, Bettini e Oliveira (2016), _Airline delays, congestion
    internalization and non-price spillover effects of low cost carrier entry_,
    *Transportation Research Part A* 85, 39–52,
    #link("https://doi.org/10.1016/j.tra.2016.01.001")[`10.1016/j.tra.2016.01.001`]
  ]
  #v(0.4em)
  #text(size: 9pt, fill: luma(35%))[
    painel de estimação do artigo: *#meta.panel.path* · #miles(meta.sample.n_after_singleton_cut)
    observações · #meta.sample.routes rotas · #meta.sample.months meses ·
    execução em #nf(meta.seconds, d: 1) s
  ]
]

#v(0.6em)

#block(fill: luma(96%), inset: 8pt, radius: 3pt, width: 100%)[
  *Nada foi ajustado para bater com o publicado.* Toda divergência é medida e
  declarada — aqui, em `docs/declared-differences.md` e em
  `docs/notes/replication.md`. Todos os números deste relatório são lidos de
  `reports/replication/*.json`, escritos por `uv run python -m replication.run`;
  os valores publicados vêm de `replication/published.json`, extraídos do texto
  do artigo por `replication/published.py`.
]

= 1. Placar: publicado × replicado

A coluna que decide é `dif/e.p.` — a diferença entre o coeficiente replicado e o
publicado, medida em *erros-padrão publicados*. Acima de cerca de 2 as estimativas
seriam materialmente diferentes; o máximo observado em todo o conjunto é
#nf(calc.max(..tabelas_reg.map(t => summary.at(t).max_difference_in_se)), d: 2).

#table(
  columns: (auto, auto, auto, auto, auto, auto, auto),
  align: (left, right, right, right, right, right, right),
  [Tabela], [coef.], [sinais iguais], [a menos de ½ e.p.], [mediana dif/e.p.],
  [máx. dif/e.p.], [mediana da razão de e.p.],
  ..tabelas_reg.map(t => {
    let s = summary.at(t)
    (
      titulos.at(t),
      str(s.n_coefficients),
      str(s.sign_agreement) + "/" + str(s.n_coefficients),
      str(s.within_half_se) + "/" + str(s.n_coefficients) + " (" + pct(s.within_half_se_share, d: 0) + ")",
      nf(s.median_difference_in_se, d: 3),
      nf(s.max_difference_in_se, d: 3),
      nf(s.median_se_ratio, d: 3),
    )
  }).flatten(),
)

A razão mediana de erros-padrão abaixo de 1 em todas as tabelas diz que os
erros-padrão replicados são sistematicamente *menores* que os publicados — o que
é coerente com uma amostra #pct(meta.sample.n_after_singleton_cut / 19590 - 1)
maior (ver §5).

= 2. Amostra e decisões de implementação

#table(
  columns: (auto, 1fr),
  align: (left, left),
  [Etapa], [Efeito],
  [painel de estimação do artigo, #raw(meta.panel.path)], [#miles(meta.sample.n_raw) obs., #meta.sample.routes_raw rotas],
  [#raw("drop if " + meta.sample.filter_regressand + " == .")], [#miles(meta.sample.n_after_missing_regressand) obs.],
  [#raw("drop if _count_k <= " + str(meta.sample.singleton_cutoff))], [#miles(meta.sample.n_after_singleton_cut) obs., #meta.sample.routes rotas],
)

#v(0.4em)

#table(
  columns: (auto, 1fr),
  align: (left, left),
  [Questão], [Decisão e base],
  [Kernel HAC],
  [Bartlett, largura de banda #str(meta.bandwidth) na convenção do `linearmodels`
   (pesos $1 - j slash (b w + 1)$) — equivale a `bw(5)` do `ivreg2`, que é o
   $T^(1 slash 3)$ com $T = 144$ que o artigo declara.],
  [Correção de amostra finita],
  [#if meta.debiased [ligada] else [desligada] — o `ivreg2` só imprime a
   estatística F, que aparece nas tabelas publicadas, com a opção `small`.],
  [Dummies sazonais `sz_*`],
  [#if meta.with_seasonality [entram] else [não entram] — o `dummymonthreg` as
   cria e o `gregcontrols` não as menciona; o `.ado` que decidiria não foi
   entregue. O artigo fala em _seasonality controls_, e a §4 mede as duas
   variantes.],
  [Efeitos fixos],
  [Dummies de rota e de mês entram *explicitamente* (o do-file não usa
   `partial()` nem `xtivreg2`); uma dummy de rota é omitida contra a constante e
   as colunas exatamente colineares caem por QR.],
  [Endógenas],
  [Apenas `rthhi` e `maxcthhi`. As dummies de LCC são exógenas — o código é
   inequívoco, ainda que a introdução do artigo diga o contrário.],
)

= 3. Tabela 2 — estatísticas descritivas

#let t2 = results.at("table2")
#let comp2 = t2.comparison

O triângulo de correlações fecha: #comp2.n_correlations células comparadas,
diferença absoluta mediana #nf(comp2.median_abs_correlation_difference, d: 3),
máxima #nf(comp2.max_abs_correlation_difference, d: 3). Os mínimos e máximos
coincidem até a quarta casa — é isso que *prova* a identificação de cada
variável do código com a coluna do artigo, em vez de supô-la.

#table(
  columns: (1fr, auto, auto, auto, auto, auto, auto, auto, auto),
  align: (left, right, right, right, right, right, right, right, right),
  [Variável], [média pub.], [média rep.], [d.p. pub.], [d.p. rep.],
  [mín. pub.], [mín. rep.], [máx. pub.], [máx. rep.],
  ..t2.published.variables.map(v => {
    let nome = if v in rotulos { rotulos.at(v) } else if v == "fsc_oddsarr" { "ODDS" } else { "MINS" }
    (
      nome,
      nf(comp2.univariate.mean.at(v).published, d: 2),
      nf(comp2.univariate.mean.at(v).replicated, d: 4),
      nf(comp2.univariate.sd.at(v).published, d: 2),
      nf(comp2.univariate.sd.at(v).replicated, d: 4),
      nf(comp2.univariate.min.at(v).published, d: 2),
      nf(comp2.univariate.min.at(v).replicated, d: 4),
      nf(comp2.univariate.max.at(v).published, d: 2),
      nf(comp2.univariate.max.at(v).replicated, d: 4),
    )
  }).flatten(),
)

= 4. Tabelas 3 a 7 — coeficientes e estatísticas

Cada tabela ocupa uma página em paisagem: são até 21 colunas (publicado,
replicado e diferença em erros-padrão, por coluna do artigo), e comprimi-las em
retrato as tornaria ilegíveis.

#let bloco(nome) = {
  let comp = results.at(nome).comparison
  let cols = comp.keys()
  heading(level: 2, titulos.at(nome))
  set text(size: 7pt)
  set table(inset: 2.6pt)
  table(
    columns: (1.7fr,) + (1fr,) * (3 * cols.len()),
    align: (left,) + (right,) * (3 * cols.len()),
    [Variável],
    ..cols.map(c => ([(#c) pub.], [(#c) rep.], [(#c) dif/e.p.])).flatten(),
    ..ordem.filter(v => cols.any(c => v in comp.at(c).coefficients)).map(v => {
      (rotulos.at(v),) + cols.map(c => {
        let e = comp.at(c).coefficients.at(v, default: (:))
        let pb = e.at("published_b", default: none)
        let rb = e.at("replicated_b", default: none)
        (
          if pb == none { "—" } else { sgn(pb) + " [" + nf(e.at("published_se", default: none), d: 3) + "]" },
          if rb == none { "—" } else { sgn(rb) + " [" + nf(e.at("replicated_se", default: none), d: 4) + "]" },
          nf(e.at("difference_in_se", default: none), d: 2),
        )
      }).flatten()
    }).flatten(),
  )
  v(0.3em)
  table(
    columns: (1.7fr,) + (1fr,) * (2 * cols.len()),
    align: (left,) + (right,) * (2 * cols.len()),
    [Estatística], ..cols.map(c => ([(#c) pub.], [(#c) rep.])).flatten(),
    ..rotulos_stat.keys().filter(k => cols.any(c => k in comp.at(c).stats)).map(k => {
      (rotulos_stat.at(k),) + cols.map(c => {
        let e = comp.at(c).stats.at(k, default: (:))
        let d = if k == "n_obs" { 0 } else { 4 }
        if k == "n_obs" {
          (miles(e.at("published", default: none)), miles(e.at("replicated", default: none)))
        } else {
          (nf(e.at("published", default: none), d: d), nf(e.at("replicated", default: none), d: d))
        }
      }).flatten()
    }).flatten(),
  )
}

#for nome in tabelas_reg {
  page(flipped: true, margin: (x: 1.4cm, y: 1.6cm), bloco(nome))
}

= 5. Sensibilidade: dummies sazonais

Coeficientes principais das colunas (1) e (2) da Tabela 3 com e sem as 60
dummies sazonais região × mês. O limiar de _outlier_ do atraso no nível do voo
(ADR-0008) é fixo num painel que chega agregado e por isso não varia aqui; esse
parâmetro vive no pipeline de reconstrução.

#table(
  columns: (auto, auto, auto, auto, auto, auto, auto),
  align: (right, center, right, right, right, right, right),
  [Col.], [sazonais], [N], [HHI da rota], [HHI máx. cidades], [R² aj.], [J],
  ..grid_.cells.map(c => (
    "(" + str(c.column) + ")",
    if c.with_seasonality { "sim" } else { "não" },
    miles(c.stats.n_obs),
    sgn(c.b.at("rthhi", default: none)) + " [" + nf(c.se.at("rthhi", default: none)) + "]",
    sgn(c.b.at("maxcthhi", default: none)) + " [" + nf(c.se.at("maxcthhi", default: none)) + "]",
    nf(c.stats.adj_r2), nf(c.stats.j_stat),
  )).flatten(),
)

= 6. Kleibergen–Paap

Nenhum pacote Python implementa a estatística `rk` de Kleibergen e Paap (2006);
`replication/kp.py` a escreve a partir do artigo. A validação não depende de
outra implementação da mesma coisa: com a covariância dos coeficientes da forma
reduzida na forma i.i.d., a matriz de ponderação do meio da forma quadrática
vira a identidade e, na hipótese de subidentificação $q = k_2 - 1$, a versão
*Wald* tem de colapsar na estatística de Cragg–Donald $N lambda slash (1 - lambda)$
e a versão *LM* na estatística de correlação canônica de Anderson $N lambda$.
As duas identidades valem até a precisão de máquina
(`tests/test_replication_kp.py`), contra uma implementação que não compartilha
código com a primeira.

Contra os valores publicados, nas colunas ODDS a implementação acerta o nível
_e_ a estrutura interna; nas colunas MINS, com 3 instrumentos e 2 endógenas, o
sistema é quase exatamente identificado e a estatística fica muito mais sensível
ao tamanho da amostra. Os números estão nas tabelas da §4.

= 7. Divergências declaradas

A lista completa, com causas, está em `docs/declared-differences.md`; o raciocínio
em português está em `docs/notes/replication.md`. As quatro que dominam:

+ *N* — a amostra replicada é #pct(meta.sample.n_after_singleton_cut / 19590 - 1)
  maior que a publicada, em todas as tabelas e nos dois lados (chegadas e
  partidas). Nenhum filtro visível nos do-files produz os números publicados. É
  a causa dominante de tudo o que segue.
+ *J de Hansen* — muda de tamanho porque é uma forma quadrática com 1 ou 3 graus
  de liberdade; em nenhuma coluna a *conclusão* muda.
+ *R² e RMSE nas colunas MINS* — a réplica ajusta melhor, o que aponta para uma
  amostra publicada com mais linhas difíceis.
+ *Estatística F* — não reproduzida: o F do `ivreg2` é o Wald conjunto de ~340
  regressores com convenção própria; comparar contra o análogo do `linearmodels`
  seria comparar coisas diferentes.
