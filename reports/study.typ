// O congestionamento aeroportuário, o jogo e o artigo — o estudo completo no padrão SAPIANS (relatório).
//
// Português (exceção deliberada ao inglês do repositório: CLAUDE.md, ADR-0006).
// NENHUM número deste relatório é digitado à mão: tudo vem de
// `reports/theory/model.json` e `reports/theory/figures.json` (`airline-delays theory`, `just theory`),
// de `reports/summary.json` (`airline-delays summary`) e de
// `reports/replication/{summary,results,sensitivity}.json` (`airline-delays estimate`, `just estimate`).
// As transcrições do artigo entram por `reports/summary.json` (bloco `published`) e pela ponte `bridge`
// de `model.json`, e são marcadas "(artigo, Tabela N)". As figuras são os SVG de `reports/theory/figures/`,
// desenhados por `src/airline_delays/theory/figures.py`. O pacote de design é `reports/sapians/`
// (cópia MIT de sapians-latex, v0.1.0).
//
// Compilar:  uv run airline-delays report --only study   ->   reports/pdf/study.pdf
//            (equivale a: typst compile --root . reports/study.typ reports/pdf/study.pdf)

#import "sapians/lib.typ": *

#let m = json("theory/model.json")
#let figs = json("theory/figures.json")
#let s = json("summary.json")
#let rep = json("replication/summary.json")
#let res = json("replication/results.json")
#let grid_ = json("replication/sensitivity.json")

// ---------------------------------------------------------------- utilitários
// Convenção numérica pt-BR: vírgula decimal, ponto de milhar.
#let nf(x, d: 2) = if x == none { "—" } else if type(x) == bool { if x { "sim" } else { "não" } } else { str(calc.round(x, digits: d)).replace(".", ",") }
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
#let sgn(x, d: 4) = if x == none { "—" } else if x >= 0 { "+" + nf(x, d: d) } else { nf(x, d: d) }
// número grande com casas decimais: ponto de milhar na parte inteira, vírgula decimal
#let numd(x, d: 2) = if x == none { "—" } else {
  let r = calc.round(x, digits: d)
  let a = calc.abs(r)
  let ip = calc.floor(a)
  let frac = calc.round(a - ip, digits: d)
  let fs = if frac == 0 { "" } else { "," + str(frac).slice(2) }
  (if r < 0 { "−" } else { "" }) + miles(ip) + fs
}
#let pct(x, d: 1) = if x == none { "—" } else { nf(x * 100, d: d) + "%" }
#let estrelas(x) = if x == none { "" } else { x }
// coeficiente publicado: sinal, erro-padrão entre parênteses, estrelas
#let coef(c, d: 4) = sgn(c.b, d: d) + " (" + nf(c.se, d: 3) + ")" + (if estrelas(c.stars) == "" { "" } else { " " + c.stars })
#let origem = (monograph: "monografia", BVD: "Brueckner e Van Dender (2008)", here: "este repositório")
#let rot(o) = origem.at(o, default: o)

// equação numerada como na monografia, (1) a (12)
#let numbered(n, body) = grid(
  columns: (1fr, auto),
  align: (center + horizon, right + horizon),
  body,
  text(size: 8pt, fill: sapians-muted-dark)[(#n)],
)
// caixas
// Os cards não quebram entre páginas: um título de card órfão no pé da página
// é o erro de layout mais visível num relatório.
#let intuicao(title, body) = block(breakable: false, light-card(kicker-title: title)[#set text(size: 8.6pt); #set par(justify: false); #body])
#let resultado(title, body) = block(breakable: false, accent-card(title: title)[#set text(size: 8.6pt); #set par(justify: false); #body])
#let chave(title, body) = block(breakable: false, dark-card(kicker-title: title)[#set text(size: 8.6pt); #set par(justify: false); #body])
#let tag(t) = text(fill: sapians-terracotta, weight: "bold", size: 7.5pt)[[#t]]
// figuras
#let fig(key, caption, w: 94%) = {
  let f = figs.figures.at(key)
  figure(
    image("theory/" + f.file, width: w),
    numbering: none,
    caption: text(size: 7.6pt, fill: sapians-muted-dark)[*#f.title.* #caption],
  )
}
#let tab(cols, aligns, ..rows) = table(
  columns: cols,
  align: aligns,
  stroke: stroke-light,
  fill: (_, row) => if row == 0 { sapians-code-bg } else { none },
  inset: (x: 2.4mm, y: 1.8mm),
  ..rows,
)
#show table.cell.where(y: 0): set text(weight: "bold", size: 7.8pt)
#show table.cell: set text(size: 7.8pt)
#show heading.where(level: 3): set text(size: 9.6pt)
#set figure(gap: 1.8mm)
#show figure.caption: set align(left)

// A data impressa é a data de lançamento em CITATION.cff — a mesma que
// `airline-delays report` grava nos metadados do PDF; assim uma recompilação
// sobre a árvore inalterada produz bytes idênticos.
#let release-date = {
  let m = read("../CITATION.cff").match(regex("date-released: '(\\d{4})-(\\d{2})-(\\d{2})'"))
  let meses = ("janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro")
  str(int(m.captures.at(2))) + " de " + meses.at(int(m.captures.at(1)) - 1) + " de " + m.captures.at(0)
}

#show: sapians-report.with(
  title: "O congestionamento aeroportuário, o jogo e o artigo",
  subtitle: "Da economia do congestionamento ao modelo de Stackelberg e ao artigo de 2016 — o estudo completo, derivado e verificado",
  author: "William Eduardo Bendinelli",
  date: release-date,
  version: "1.0",
)

// ------------------------------------------------------------ atalhos de dados
#let lin = m.examples.linear
#let qd = m.examples.quadratic
#let inel = m.examples.at("inelastic_linear_demand")
#let lcc = m.extension_lcc
#let pr = m.primer
#let tt = pr.two_by_two
#let pub3 = s.published.table3.col2
#let pub6 = s.published.table6.col2
#let tot = s.estimation.totals
#let hhi = s.estimation.hhi
#let rec = s.reconstruction
#let ap = s.article_panel
#let est = s.estimation
#let amostra = est.sample

// a especificação do artigo: listas de nomes (identificadores, não medições);
// as contagens em prosa saem de .len(), nunca digitadas
#let exog = ("dailyflcong", "dailyflncong", "prwheather", "princident", "pr_connc", "maxprdel", "cshare", "lcc", "maxalccfu")
#let endog = ("rthhi", "maxcthhi")
#let lcc_terms = ("lcc", "maxalccfu")
#let instr_odds = ("h3_maxcthhi", "lnh1_maxcthhi", "l1h1_maxcthhi", "l1h2_maxcthhi", "h2_rthhi")
#let instr_mins = ("h1_maxcthhi", "h2_maxcthhi", "h3_maxcthhi")
#let instr_all = (instr_odds + instr_mins).dedup()
#let regressandos_arr = ("fsc_oddsarr", "fsc_minsarr", "fsc_minsp15arr")
#let regressandos_dep = ("fsc_oddsdep", "fsc_minsdep", "fsc_minsp15dep")
#let rotulo_var = (
  dailyflcong: "voos por dia nas horas congestionadas",
  dailyflncong: "voos por dia nas horas não congestionadas",
  prwheather: "prop. de voos com mau tempo ou restrição de aeroporto",
  princident: "prop. de voos com incidentes",
  pr_connc: "prop. de voos retidos por rotação de aeronave",
  maxprdel: "máx. prop. de voos atrasados na cidade-extremo",
  cshare: "acordo de codeshare",
  rthhi: "HHI da rota",
  maxcthhi: "HHI máx. das cidades-extremo",
  lcc: "LCC presente na rota",
  maxalccfu: "LCC presente numa cidade-extremo",
  fsc_oddsarr: "ODDS (regressando)",
  fsc_minsarr: "MINS (regressando)",
)
#let nome_var(v) = rotulo_var.at(v, default: v)

= Sumário executivo

Um aeroporto cheio é uma externalidade em funcionamento: cada voo a mais que uma empresa programa no pico atrasa os voos das outras, e quem o programa não paga esse atraso. A pergunta que este estudo percorre é se uma empresa com poder de mercado — a que domina um aeroporto — já embute nas próprias decisões o congestionamento que causa, e o que a entrada de uma empresa de baixo custo muda nisso. O contexto é o mercado doméstico brasileiro de 2000 a 2013: os voos programados do universo de replicação passaram de #miles(rec.flights_scheduled_first_year) por ano a #miles(rec.flights_scheduled_last_year), alta de #nf(rec.flights_growth_pct, d: 1)% (`reconstruction.flights_scheduled_first_year`, `flights_scheduled_last_year`, `flights_growth_pct`)\; a Gol entrou em 2001 e a Azul em 2008; a crise de 2006–2007 fez do congestionamento dos aeroportos um problema de política pública. A resposta publicada é Bendinelli, Bettini & Oliveira (2016), _Airline delays, congestion internalization and non-price spillover effects of low cost carrier entry_, *Transportation Research Part A* 85, 39-52, doi 10.1016/j.tra.2016.01.001 — daqui em diante, "o artigo". Este estudo junta, num só documento, a microeconomia do congestionamento (Parte I), a teoria dos jogos de que o modelo precisa e o modelo derivado passo a passo (Parte II) e o artigo — as hipóteses, os dados, a especificação, os resultados, a replicação feita neste repositório e a recepção (Parte III).

*O que o modelo prevê.* Com um líder de Stackelberg e uma seguidora, a seguidora internaliza a própria parcela do dano marginal de congestionamento e a líder internaliza menos, porque antecipa que a rival ocupará parte do espaço que ela liberar. A tarifa que levaria cada uma ao ótimo é a fração do dano que ela deixa de considerar: #nf(m.tolls.monopoly_over_MCD) para o monopolista, que internaliza tudo; #nf(m.tolls.cournot_over_MCD) para um duopolista de Cournot e para a seguidora; $(1 + lambda^*) slash 2$ para a líder — #nf(m.tolls.leader_over_MCD_linear) sob custo linear —; e #nf(m.tolls.atomistic_over_MCD) para a empresa atomística, o dano inteiro (`tolls`). Concentração no aeroporto deve, portanto, vir com menos atraso; concentração na rota tem sinal ambíguo, porque o poder de mercado retém tráfego e o dano não internalizado o excede; a entrante de baixo custo redistribui as parcelas de todas.

*O que o artigo encontrou.* Na especificação de base — a coluna (2) da Tabela 3, 2SGMM sobre a razão de chances de uma chegada das empresas de serviço completo atrasar mais de quinze minutos, com #miles(pub3.n_obs) rota-meses — a concentração da cidade-extremo mais concentrada reduz o atraso (`maxcthhi` #coef(pub3.maxcthhi)), a concentração da própria rota o aumenta (`rthhi` #coef(pub3.rthhi)), a presença de uma empresa de baixo custo numa das cidades-extremo o reduz (`maxalccfu` #coef(pub3.maxalccfu)) e a presença na rota em si não é significante (`lcc` #coef(pub3.lcc)) (artigo, Tabela 3). Por OLS, sem instrumento, as duas concentrações trocam de sinal — `rthhi` #coef(pub6.rthhi) e `maxcthhi` #coef(pub6.maxcthhi) (artigo, Tabela 6) —, e essa inversão é o argumento identificador do artigo.

*O que a replicação mostra.* As Tabelas 2–7 são reestimadas sobre o painel de estimação do artigo, publicado neste repositório (ADR-0020): dos #tot.coefficients coeficientes das cinco tabelas de regressão, #tot.sign_agreement têm o sinal publicado e #tot.within_half_se (#nf(tot.within_half_se_pct, d: 1)%) ficam a menos de meio erro-padrão publicado do valor publicado; o maior desvio isolado é #nf(tot.max_difference_in_se, d: 2) erro-padrão (`estimation.totals`). Das #hhi.n_comparisons comparações OLS × 2SGMM dos dois índices de concentração, as #hhi.n_inverted_published inversões publicadas reaparecem na reestimação (#hhi.n_inversion_replicates de #hhi.n_inverted_published) e o padrão — haver ou não inversão — coincide em #hhi.n_pattern_agrees das #hhi.n_comparisons (`estimation.hhi`).

#chave("O que a derivação acrescenta à monografia")[
  A teoria do artigo foi trabalhada na monografia de graduação do autor (USP, 2013), segundo Brueckner e Van Dender (2008)\; este estudo a deriva do início ao fim, e três afinamentos, rotulados #tag("aqui") ao longo do texto, são desta derivação. *Primeiro:* das condições da seguidora e da líder segue $f_1 = f_2 slash (1 - lambda) >= 2 f_2$ — a líder voa pelo menos o dobro da seguidora, e exatamente o dobro sob custo linear; a monografia dizia só $f_1 > f_2$. *Segundo:* sob custo linear a tarifa da líder no ótimo simétrico é exatamente #nf(m.tolls.leader_over_MCD_linear) do dano marginal, _a meio caminho_ entre a tarifa de Cournot (#nf(m.tolls.cournot_over_MCD)) e a atomística (#nf(m.tolls.atomistic_over_MCD))\; a frase da monografia "entre a metade da tarifa de Cournot e a tarifa atomística" é tradução truncada de _halfway between_. *Terceiro:* sob demanda inelástica os limites $-1 < partial f_2 slash partial f_1 <= -1/2$ valem se e só se $c'' slash s >= s^2 d''$ — automático para demanda linear ou côncava, não garantido para demanda convexa — condição que nem a monografia nem a fonte enunciam.
]

#v(2mm)
Três rótulos separam de quem é cada afirmação: #tag("BVD") um resultado de Brueckner e Van Dender (2008) reenunciado; #tag("monografia") a afirmação da monografia de graduação do autor (USP, 2013), citada literalmente e como documento externo; #tag("aqui") o que este repositório acrescenta. Duas marcas acompanham as transcrições: "(artigo, Tabela N)" para um número copiado das tabelas publicadas e "(monografia — documento externo)" para o que só existe na monografia. Nenhum número deste documento é digitado: cada um é lido de `reports/theory/model.json`, `reports/theory/figures.json`, `reports/summary.json` ou `reports/replication/`, e a frase ou a tabela que o traz nomeia a chave. Os dois painéis são "o painel de estimação do artigo" — o painel sobre o qual os autores estimaram as Tabelas 2–7, publicado aqui — e "o painel reconstruído", construído a partir dos arquivos da ANAC; o que os liga são as mesmas definições de universo, mapa de nós, conjuntos de empresas e regras de atraso.

#tab((auto, auto, 1fr, 1fr), (left, left, left, left),
  [parte], [seções], [o que entrega], [números-manchete, com a chave em `reports/summary.json`],
  [I], [1–7], [a economia do congestionamento aeroportuário, com as Figuras 1–5 redesenhadas], [—],
  [II], [8–21], [os fundamentos de teoria dos jogos e o modelo de Stackelberg derivado, verificado e ilustrado, Figuras 6–10], [#m.meta.n_identities identidades, #s.theory.n_holding valem; #s.theory.n_figures figuras (`theory.n_identities`, `theory.n_holding`, `theory.n_figures`)],
  [III], [22–26], [o artigo: hipóteses, dados, especificação, resultados e replicação, recepção; Figura 11], [#miles(ap.rows) × #ap.columns no painel de estimação do artigo; #tot.coefficients coeficientes comparados, #tot.sign_agreement com o sinal publicado (`article_panel.rows`, `article_panel.columns`, `estimation.totals`)],
  [Apêndices], [A, B], [as identidades verificadas; como reproduzir cada número], [—],
)

= Parte I — A economia do congestionamento

== 1. Congestionamento como externalidade negativa

Uma empresa aérea que acrescenta um voo num aeroporto cheio paga o próprio custo do voo, mas não paga o tempo que impõe aos voos das outras — nem aos passageiros delas. O custo social de um voo é o custo privado mais esse custo forçado a terceiros; como a diferença não aparece em nenhum preço, a decisão de voar mais é tomada olhando só para o custo privado. É a definição de externalidade negativa, e o congestionamento aeroportuário é o seu exemplo de manual. A monografia a enuncia assim: #quote(block: false)[os custos sociais (ou seja, os custos privados mais os custos forçados a terceiros) excedem os custos privados] (monografia, seção 2.1 — documento externo).

Escreva $Q$ para o número de voos programados no pico, $"CMgP"(Q)$ para o custo marginal privado de um voo e $"CMgE"(Q)$ para o custo marginal externo, o atraso que esse voo impõe aos demais. O custo marginal social é a soma, $"CMgS"(Q) = "CMgP"(Q) + "CMgE"(Q)$, e tudo o que segue decorre de $"CMgE"(Q) > 0$ acima de certo tráfego: abaixo do limiar de capacidade um voo a mais não atrasa ninguém; acima dele, cada voo adicional atrasa todos os que já disputam a pista. #tag("aqui") O mesmo objeto reaparece na Parte II com outro nome: lá o tráfego é $F$ voos, $c(F)$ é o custo de congestionamento por voo, e o custo externo marginal de um voo é o que ele acrescenta ao custo de todos os outros, $F c'(F)$ — o dano marginal de congestionamento, MCD. Este capítulo fala em CMgE; o modelo, em MCD; é a mesma quantidade.

#intuicao("A ideia em uma frase")[
  Quem decide o número de voos não enfrenta o custo inteiro da decisão; por isso o mercado, deixado a si, voa demais — e "demais" é medido contra um nível eficiente que não é zero.
]

== 2. O nível eficiente de congestionamento e a tarifa pigouviana (Figura 1)

#fig("fig1", [Custo marginal privado (CMgP), social (CMgS) e benefício marginal (BMg)\; A é o equilíbrio privado, C o ótimo social, ABC a perda de bem-estar. Redesenhada a partir de curvas paramétricas; adaptada de Cohen, Coughlin e Ott (2009), não copiada. Coordenadas em `reports/theory/figures.json`, chave `fig1`.])

#let f1 = figs.figures.fig1.quantities
Até $Q_c = #nf(f1.Q_c, d: 0)$ voos não há congestionamento: os custos marginais privado e social coincidem. Além dele, cada voo a mais impõe tempo aos outros e a curva social sobe acima da privada. O benefício marginal de um voo — a receita que ele traz — cai à medida que os voos aumentam. O mercado sem regulação para onde o benefício iguala o custo _privado_: o ponto A, com $Q_P = #nf(f1.Q_P, d: 0)$ voos. O ótimo está onde o benefício iguala o custo _social_: o ponto C, com $Q_S = #nf(f1.Q_S, d: 0)$. Entre os dois, cada voo custa à sociedade mais do que rende; a perda acumulada é o triângulo ABC, de área #nf(f1.triangle_ABC_area, d: 0) nas unidades da figura.

Note que o congestionamento eficiente não é zero: em $Q_S$ ainda há fila, porque os voos entre $Q_c$ e $Q_S$ valem mais do que custam — #quote(block: false)[o nível eficiente de congestionamento não é zero, mas sim uma certa quantidade positiva] (monografia, seção 2.2 — documento externo). A pergunta de política não é "como eliminar o atraso", mas "como levar o mercado de $Q_P$ a $Q_S$".

*Duas rotas para o ótimo.* Pela quantidade: fixar em $Q_S$ o número de pousos e decolagens (os _slots_) e decidir quem os usa — por antiguidade (_grandfathering_), que protege quem já está e não gera receita, ou por leilão, que revela quanto cada empresa valoriza o slot e captura esse valor para financiar capacidade (a "captura de valor" de Cohen, Coughlin e Ott 2009; Brueckner 2009 mostra que um leilão de slots pode reproduzir o resultado da tarifa, e Oliveira 2012 leva a discussão ao caso brasileiro). Pelo preço: uma tarifa por voo que suba a curva privada até ela cruzar o benefício em C. A tarifa correta é a distância vertical entre as duas curvas de custo em $Q_S$ — a tarifa pigouviana, $t^* = "CMgS"(Q_S) - "CMgP"(Q_S)$, #nf(f1.toll_pigou_at_QS, d: 0) na figura. No Brasil o instrumento que chegou aos aeroportos saturados foi o de quantidade: a coordenação de horários de Guarulhos e Santos Dumont a partir de 2009 (`data/external/slots.csv`).

#intuicao("Uma nota sobre o segmento AD")[
  O texto da monografia diz que a tarifa é "AD (ou a diferença entre $P_S$ e $P_P$)", que na figura mede #nf(f1.toll_AD_equals_PS_minus_PP, d: 0). As duas coincidem só quando o custo privado é plano entre $Q_S$ e $Q_P$; com a curva privada inclinada, como o próprio texto a descreve, a tarifa que leva o mercado a C é a pigouviana, #nf(f1.toll_pigou_at_QS, d: 0). A figura imprime as duas para que a diferença fique visível (observação deste repositório).
]

== 3. Preço ou quantidade sob incerteza (Figura 2)

#fig("fig2", [O regulador conhece os custos mas não o benefício marginal, e fixa a tarifa $t$ ou a cota $Q_Q$ sobre o benefício esperado; o realizado é maior. ABC é a perda da cota, CEF a da tarifa. Adaptada de Cohen, Coughlin e Ott (2009).])

#let f2 = figs.figures.fig2.quantities
Na seção anterior o regulador conhecia as curvas. Suponha agora que conhece os custos mas erra o benefício: fixa a tarifa $t = #nf(f2.toll_set_on_expectations, d: 0)$ ou a cota $Q_Q = #nf(f2.Q_Q_quota, d: 0)$ sobre a curva _esperada_, e a curva _realizada_ fica acima. Com a tarifa, as empresas veem o custo privado mais $t$ e param onde essa curva cruza o benefício realizado: $Q_T = #nf(f2.Q_T_under_the_toll, d: 0)$ voos, além do novo ótimo $Q_S = #nf(f2.Q_S_efficient_under_BMgR, d: 0)$. Com a cota, o mercado fica preso em $Q_Q = #nf(f2.Q_Q_quota, d: 0)$, aquém do ótimo. As duas erram; a pergunta é qual erra menos. Na figura, a perda da cota (ABC, área #nf(f2.triangle_ABC_area_quantity_regulation, d: 0)) é maior que a da tarifa (CEF, área #nf(f2.triangle_CEF_area_price_regulation, d: 0)): o preço vence, e é a conclusão da monografia (seção 2.3 — documento externo).

A regra geral é de Weitzman (1974), que a monografia usa sem nomear: o preço é o instrumento melhor quando o custo marginal é mais inclinado que o benefício marginal — o caso da figura — e a quantidade quando é o contrário. Se a incerteza estiver nos custos, e não no benefício, os dois instrumentos dão o mesmo resultado. Slots distribuídos de graça e negociados entre as empresas chegam ao resultado eficiente se os custos de transação forem baixos — argumento coasiano que defende o direito adquirido quanto à eficiência, nunca quanto à entrada. E há uma complicação própria da aviação: aeroportos são complementares (decolar de um é pousar noutro), e Czerny (2006) mostra que essa complementaridade propaga a incerteza de uma tarifa de aeroporto em aeroporto, enquanto a restrição de slots a interrompe — o único argumento da seção a favor da quantidade.

== 4. Expandir o aeroporto (Figura 3)

#fig("fig3", [Antes e depois de uma expansão: as duas curvas de custo deslocam-se para a direita e o limiar de congestionamento passa de $Q_T$ a $Q_(T X)$. Com demanda elástica o equilíbrio vai de E a E′; com demanda inelástica, de I a I′. Adaptada de Cohen e Coughlin (2003).])

#let f3 = figs.figures.fig3.quantities
A terceira opção é construir. Uma pista nova desloca as curvas de custo para a direita: o congestionamento passa a começar em $Q_(T X) = #nf(f3.Q_TX, d: 0)$ em vez de $Q_T = #nf(f3.Q_T, d: 0)$. Se o congestionamento persiste depende da demanda. Com demanda elástica, o custo menor atrai voos e o equilíbrio vai de $Q_E = #nf(f3.Q_E_before, d: 0)$ para #nf(f3.Q_E_after, d: 0) — ainda além do novo limiar: a expansão foi absorvida por tráfego novo. Com demanda inelástica, fixa em $Q_I = #nf(f3.Q_I, d: 0)$, o novo limiar fica acima do tráfego e o congestionamento desaparece; o preço cai de #nf(f3.P_I_before, d: 0) para #nf(f3.P_I_after, d: 0). Capacidade nova compra mais viagem, não menos fila, sempre que a demanda responde — e a pergunta que a figura não responde é se os benefícios superam o custo da pista, que Cohen e Coughlin (2003) pesam contra congestionamento evitado, viagens novas e economia operacional.

== 5. Externalidades de rede (Figuras 4 e 5)

#fig("fig4", [Benefício marginal local contra social num aeroporto-spoke: a rede acrescenta o valor das conexões que o voo alimenta. Adaptada de Cohen e Coughlin (2003).])

#let f4 = figs.figures.fig4.quantities
O foco num único aeroporto esconde uma característica do transporte aéreo: a rede. Um voo a mais num aeroporto _spoke_ vale, para quem conecta no _hub_, mais do que o benefício local mede. O aeroporto que decide pelo benefício local para em $Q_0 = #nf(f4.Q_0, d: 0)$; o benefício social justifica $Q_1 = #nf(f4.Q_1, d: 0)$, e a diferença entre as duas curvas em $Q_1$ — #nf(f4.subsidy_at_Q_1, d: 0) na figura — é o subsídio que levaria o aeroporto lá: a tarifa da seção 2 com o sinal trocado.

#fig("fig5", [Congestionamento e rede juntos: o custo social acima do privado por um lado, o benefício social acima do local pelo outro. Desenhada, como a monografia descreve a sua Figura 5, para que os dois efeitos se cancelem exatamente.])

#let f5 = figs.figures.fig5.quantities
Com as duas externalidades ao mesmo tempo a prescrição fica ambígua. O congestionamento pede uma tarifa; a rede pede um subsídio. Na Figura 5 os dois efeitos se compensam exatamente — o ótimo com as duas externalidades, $Q^* = #nf(f5.Q_star, d: 0)$, coincide com o equilíbrio de mercado $Q_0 = #nf(f5.Q_0, d: 0)$ — e nenhuma intervenção é necessária. É um caso especial: só o congestionamento levaria o ótimo a #nf(f5.Q_S_congestion_only, d: 0)\; só a rede, a #nf(f5.Q_N_network_only, d: 4). Fora dele, #quote(block: false)[a prescrição política é ambígua, a menos que se saibam os tamanhos dos efeitos] (monografia, seção 2.4 — documento externo). Saber qual é o caso é uma pergunta empírica — a pergunta do artigo.

== 6. O debate da internalização

Se o aeroporto é dominado por uma empresa, o custo extra que um voo dela impõe aos outros voos _dela_ é interno à empresa. Ela o internaliza sozinha, e a tarifa eficiente deveria cobrar só a parte que ela impõe às outras. Essa é a intuição de Brueckner (2002), que abre o debate levando ao aéreo o modelo do transporte de superfície: um monopolista internaliza tudo; duopolistas de Cournot internalizam a própria parcela; a tarifa eficiente é a parcela _não_ internalizada, menor quanto maior a empresa. Mayer e Sinai (2003) separam dois efeitos que a concentração mistura — o _hub_ aumenta atrasos, porque a empresa concentra voos na mesma janela para maximizar conexões, e a dominância os reduz, porque a dominante internaliza — e concluem que nem todo atraso é um mal. O contra-argumento é de Daniel (1995) e Daniel e Harback (2008): se a dominante reduz voos para aliviar o pico, as rivais preenchem o espaço, o incentivo evapora e a tarifa deve tratar todo atraso como externo. Pels e Verhoef (2004) somam a distorção de poder de mercado; Morrison e Winston (2007) encontram internalização só parcial; Rupp (2009) leva a pergunta ao teste direto com dados de voo dos Estados Unidos e encontra evidência mista; Ater (2012) mostra que empresas concentradas escolhem intervalos mais longos entre os voos — internalizar é reprogramar, não só voar menos.

Brueckner e Van Dender (2008) amarram as duas visões e trocam a pergunta: o que decide não é a concentração, é a _estrutura_ do jogo. Com um líder de Stackelberg diante de uma franja competitiva, o líder prevê que cada voo cortado será ocupado pela franja, e a tarifa eficiente volta ao nível atomístico — o mundo de Daniel. Com um líder e um seguidor, o líder internaliza parte, o seguidor internaliza como em Cournot, e a tarifa do líder fica entre a de Cournot e a atomística. É esse o modelo que a Parte II deriva.

#tab((auto, 1fr, 1fr, auto), (left, left, left, left),
  [obra], [estrutura de mercado], [quem internaliza], [tarifa eficiente],
  [Brueckner (2002)], [monopólio; Cournot], [tudo; a própria parcela], [zero; parcial],
  [Mayer e Sinai (2003)], [hubs, com rede], [em parte; a rede eleva atrasos], [pequena],
  [Daniel (1995)\; Daniel e Harback (2008)], [dominante com franja competitiva], [ninguém], [atomística],
  [Pels e Verhoef (2004)], [Cournot com poder de mercado], [a própria parcela], [reduzida pela parcela e pela correção de poder de mercado],
  [Morrison e Winston (2007)], [oligopólio com dominância], [as dominantes, em parte], [entre a atomística e zero],
  [Brueckner e Van Dender (2008)], [líder de Stackelberg com seguidora], [a seguidora, à Cournot; a líder, menos], [entre Cournot e atomística],
  [Ater (2012)], [aeroportos concentrados], [as dominantes, reprogramando horários], [limitada aos picos],
)

== 7. O modelo de negócios de baixo custo e a entrante

A seção 4.5 da monografia sai da regulação e entra na firma. O modelo de baixo custo produziu vocabulário próprio: o _efeito Southwest_ é a queda de tarifas quando uma empresa desse tipo passa a servir um aeroporto que não tinha nenhuma (Pitfield 2008), e o método é consenso mesmo sem definição única — tarifas baixas por estratégias que ora removem elementos da função de produção, ora reduzem os que restam. O preço menor gera tráfego novo mais do que o transfere; Dresner, Lin e Windle (1996) e Morrison (2001) medem, nos Estados Unidos, os transbordamentos do serviço da Southwest sobre rotas concorrentes e adjacentes, e Button (2012) pergunta se o modelo se sustenta. Para manter custos baixos, essas empresas usam aeroportos secundários ou terminais dedicados — e é por isso que Gudmundsson, Paleari e Redondi (2014) as encontram onde o congestionamento não está. No Brasil, a Azul seguiu a estratégia de criar mercado novo em aeroportos secundários — Viracopos, em Campinas, é o caso concreto — e a Gol, entre 2001 e 2005, a de disputar mercados existentes com preço, em duas fases que Oliveira (2009) separa: "baixo custo, tarifa baixa" e, depois da re-regulação de 2003–2004, apenas "baixo custo".

*Por que a entrante muda os incentivos.* A literatura da seção 6 trata de empresas com posição dada; a entrante muda a posição de todas, e em termos de jogo três coisas acontecem ao mesmo tempo. Muda o número de jogadores: com $n$ empresas em Cournot, cada uma internaliza a sua parcela $f_i slash F$ do dano marginal, a soma das parcelas é sempre um, e a entrante toma parcela das incumbentes. Muda quem tem tamanho: a empresa de custo menor voa mais e, por isso, internaliza mais. Muda a estrutura: um líder que antecipava um único seguidor perde a previsibilidade de que o modelo de Stackelberg depende. Este é o terreno da "Pressuposição 3" da monografia, enunciada na seção 20, e da extensão numérica que este repositório lhe dá ali: no triopólio de Cournot com uma entrante de custo por assento #nf(lcc.entrant_tau, d: 0) contra #nf(lcc.incumbent_tau, d: 0), a entrante voa #nf(lcc.triopoly.flights.at(0), d: 0) dos #nf(lcc.triopoly.F, d: 0) voos e internaliza #nf(lcc.triopoly.internalised_share.at(0)) do dano marginal contra #nf(lcc.triopoly.internalised_share.at(1)) de cada incumbente (`extension_lcc`). Os dois movimentos — a entrante na rota e no aeroporto, e o que a presença dela faz ao atraso de todos — são o que o artigo procura nos dados.

= Parte II — O jogo

== 8. Fundamentos: como se lê e como se resolve um jogo

Antes das equações, as ferramentas — e nenhuma a mais do que as seções seguintes usam. Um *jogo* é uma situação em que o resultado de cada um depende das escolhas de todos, e descrevê-lo exige cinco peças: quem joga (os *jogadores*), o que cada um pode escolher (as *estratégias*), o que cada um recebe em cada combinação de escolhas (os *pagamentos*), quem escolhe quando (a *ordem dos lances*) e o que cada um sabe na hora de escolher (a *informação*). Um mercado com poucas empresas é um jogo porque o lucro de cada uma depende do que as outras fazem — é o que separa o oligopólio da concorrência perfeita, em que ninguém é grande o bastante para afetar os demais. No aeroporto congestionado os jogadores são duas empresas, 1 e 2; a estratégia de cada uma é quantos voos programar no pico, $f_1$ e $f_2$, com tráfego total $F = f_1 + f_2$; o pagamento é o lucro; a informação é completa. O que liga os jogadores é o custo: cada voo rende $(p - tau) s$ antes do congestionamento — o preço total $p$ pago pelo passageiro menos o custo $tau$ de um assento, vezes os $s$ assentos — e custa $c(F)$ de congestionamento, com $c' > 0$, de modo que o custo de um voo _meu_ depende de quantos voos _você_ programa. O lucro da empresa $i$ é $pi_i = (p - tau) s f_i - c(F) f_i$, as equações (3) e (4) da seção 10.

Todo número desta seção sai do bloco `primer` de `reports/theory/model.json`, recortado do exemplo linear que percorre a Parte II: $p = #nf(lin.primitives.p, d: 0)$, $tau = #nf(lin.primitives.tau, d: 0)$, $s = #nf(lin.primitives.s, d: 0)$ e $c(F) = #nf(lin.cost.a, d: 0) + #nf(lin.cost.b, d: 0) F$ (`examples.linear.primitives`, `.cost`). A receita líquida por voo antes do congestionamento é $(p - tau) s = #miles(pr.primitives.A)$ e, descontada a parte fixa do custo, $D = (p - tau) s - a = #miles(pr.primitives.D)$ (`primer.primitives`). Os valores são estilizados, escolhidos para que os equilíbrios saiam em números redondos; nada aqui foi calibrado a dado brasileiro.

#let vol(k) = nf(tt.strategies.at(k).volume, d: if k == "low" { 1 } else { 0 })
#let cel(k) = miles(tt.cells.at(k).profit1) + ", " + miles(tt.cells.at(k).profit2)
#let ponto(k) = "(" + nf(tt.cells.at(k).f1, d: 1) + "; " + nf(tt.cells.at(k).f2, d: 1) + ")"

=== O dilema dos voos de pico: estratégia dominante e equilíbrio de Nash

Reduza as opções de cada empresa a duas: programar #vol("low") voos no pico — o volume por empresa que um planejador escolheria, $f^* = D slash 4b$ — ou programar #vol("high"), o volume $D slash 3b$ que cada uma escolhe sozinha no equilíbrio de Cournot (`primer.two_by_two.strategies`). Os lucros das quatro combinações saem da função de lucro: a margem por voo, $(p - tau) s - c(F)$, vezes os voos próprios. As células são `primer.two_by_two.cells`, a primeira posição da chave sendo a estratégia da empresa 1.

#tab((1fr, 1fr, 1fr), (left, center, center),
  [(lucro da 1, lucro da 2)], [empresa 2 voa #vol("low")], [empresa 2 voa #vol("high")],
  [*empresa 1 voa #vol("low")*], cel("low_low"), cel("low_high"),
  [*empresa 1 voa #vol("high")*], cel("high_low"), cel("high_high"),
)

#v(1mm)
O que muda de uma célula para outra é o tráfego total e, com ele, o custo de _cada_ voo:

#tab((1fr, auto, auto, auto), (left, right, right, right),
  [célula], [$F$], [$c(F)$], [lucro total],
  [as duas voam #vol("low")], nf(tt.cells.low_low.F, d: 1), miles(tt.cells.low_low.c), miles(tt.cells.low_low.total_profit),
  [uma voa #vol("high"), a outra #vol("low")], nf(tt.cells.high_low.F, d: 1), miles(tt.cells.high_low.c), miles(tt.cells.high_low.total_profit),
  [as duas voam #vol("high")], nf(tt.cells.high_high.F, d: 1), miles(tt.cells.high_high.c), miles(tt.cells.high_high.total_profit),
)

#v(1mm)
Três definições, e o jogo se resolve sozinho. A *resposta ótima* de um jogador a uma estratégia do rival é a estratégia que maximiza o seu pagamento dada aquela do rival. Uma *estratégia dominante* é uma resposta ótima a _toda_ estratégia do rival: escolhe-se sem precisar adivinhar o que o outro fará. Um *equilíbrio de Nash* é uma combinação de estratégias em que cada uma é resposta ótima à outra — ninguém ganha desviando sozinho:

$ pi_1 (f_1^N, f_2^N) >= pi_1 (f_1, f_2^N) quad "para todo" f_1 , \
  pi_2 (f_1^N, f_2^N) >= pi_2 (f_1^N, f_2) quad "para todo" f_2 . $

Leia a matriz pela linha da empresa 1. Se a empresa 2 voa #vol("low"), a 1 compara #miles(tt.cells.low_low.profit1) (voar #vol("low")) com #miles(tt.cells.high_low.profit1) (voar #vol("high")) e escolhe #vol(tt.best_response_of_airline_1.to_low). Se a empresa 2 voa #vol("high"), a 1 compara #miles(tt.cells.low_high.profit1) com #miles(tt.cells.high_high.profit1) e escolhe #vol(tt.best_response_of_airline_1.to_high) de novo (`best_response_of_airline_1`). Voar #vol(tt.dominant_strategy) é dominante (`dominant_strategy`)\; o jogo é simétrico, e a empresa 2 raciocina igual. A única célula em que as duas dão resposta ótima uma à outra é #ponto(tt.nash), o equilíbrio de Nash (`nash`), com #miles(tt.cells.at(tt.nash).profit1) para cada uma. A célula cooperativa #ponto(tt.cooperative) daria #miles(tt.cells.at(tt.cooperative).profit1) a cada uma (`cooperative`), e o lucro total ali, #miles(tt.cells.at(tt.cooperative).total_profit), é exatamente o bem-estar do ótimo social da seção 11 (`cooperative_total_equals_welfare_star` vale #nf(tt.cooperative_total_equals_welfare_star)). As duas preferem a cooperação ao equilíbrio, e nenhuma consegue chegar lá sozinha.

#resultado("O dilema dos prisioneiros, em voos")[
  Os quatro pagamentos de um jogador ordenam-se como tentação, recompensa, punição e prejuízo de quem coopera sozinho — #miles(tt.ordering.temptation) acima de #miles(tt.ordering.reward), acima de #miles(tt.ordering.punishment), acima de #miles(tt.ordering.sucker) (`ordering`; `is_prisoners_dilemma` vale #nf(tt.is_prisoners_dilemma)). A externalidade está numa linha de contas: quando uma empresa passa de #vol("low") a #vol("high") voos com a rival parada, acrescenta #nf(tt.deviation_from_cooperation.extra_flights, d: 1) voos ao pico e eleva o custo de _cada_ voo em #miles(tt.deviation_from_cooperation.extra_cost_per_flight)\; os #vol("low") voos da rival carregam #miles(tt.deviation_from_cooperation.loss_to_rival) desse custo, e é isso que a rival perde; a desviante ganha #miles(tt.deviation_from_cooperation.gain_to_deviator) e o total cai #miles(-tt.deviation_from_cooperation.change_in_total_profit) (`deviation_from_cooperation`). A desviante conta o ganho e não conta a perda, porque a perda é dos voos da outra. Congestionamento é um dilema social: o voo a mais compensa para quem o programa e não compensa para o conjunto.
]

_O que isso significa para o artigo._ O dilema é o mecanismo por trás do atraso: cada empresa acrescenta ao pico voos que pagam para ela e custam a todas. O coeficiente positivo dos voos no período congestionado sobre o atraso — `dailyflcong` no artigo — é o $c' > 0$ desta matriz; a pergunta do artigo é se a estrutura do mercado leva as empresas da célula de Nash em direção à célula cooperativa.

=== Da matriz à função de reação: Cournot

Agora cada empresa escolhe qualquer número de voos. A resposta ótima da empresa $i$ a um $f_j$ dado é o $f_i$ que maximiza o lucro; a derivada igualada a zero e dividida por $s$ dá $p - tau - [f_i c'(F) + c(F)] slash s = 0$ — a equação (7) da seção 14, ali escrita para a seguidora. Cada termo tem um nome: $p - tau$ é o que um assento rende; $c(F) slash s$ é o custo de congestionamento por assento do voo novo; $f_i c'(F) slash s$ é o que o voo novo acrescenta ao custo dos _outros voos da própria empresa_. A empresa conta este último termo e não conta $f_j c'$, o que o voo novo acrescenta aos voos da rival — a assimetria do dilema, agora em derivadas. Resolvida em $f_i$, a condição é uma *função de reação*: para cada volume da rival, o volume que a empresa escolhe. Sob custo linear ela é a reta

$ f_2 = (D - b f_1) / (2 b) , $

com intercepto $D slash 2b = #nf(pr.reaction_function.intercept, d: 0)$ — o que a empresa 2 voaria sozinha — e inclinação #nf(pr.reaction_function.slope, d: 1): a cada voo a mais da rival, a empresa corta meio voo (`primer.reaction_function`).

#let leitura_ponto = (
  "0": [a empresa 2 sozinha: o volume de monopólio, `examples.linear.monopoly.F`],
  "22.5": [a resposta ao volume eficiente por empresa],
  "30": [a resposta ao volume de Cournot: ele responde a si mesmo],
  "45": [a resposta ao volume da líder de Stackelberg],
  "60": [a resposta ao dobro do volume de Cournot],
  "90": [a empresa 2 sai do pico: o tráfego atomístico, `examples.linear.atomistic.F`],
)
#tab((auto, auto, 1fr), (right, right, left),
  [voos da empresa 1, $f_1$], [resposta ótima da empresa 2, $f_2$], [o que é esse ponto],
  ..pr.reaction_function.points.map(p => (nf(p.f1, d: 1), nf(p.f2, d: 2), leitura_ponto.at(str(p.f1), default: ""))).flatten(),
)

#v(1mm)
A tabela mostra o que a matriz escondia: no jogo de duas opções, #vol("high") era dominante porque é a melhor das duas respostas a qualquer escolha da rival; no jogo contínuo, #vol("high") é a resposta ótima exata a #vol("high"), e só a ela. O *equilíbrio de Cournot* é o equilíbrio de Nash do jogo contínuo com lances simultâneos: o par em que cada empresa está sobre a sua função de reação. Como as duas reações são simétricas, ele está na diagonal, $f = D slash 3b$ (`linear_closed_forms.f_cournot`): #nf(lin.cournot.f1, d: 0) voos cada, #nf(lin.cournot.F, d: 0) no total, com #miles(lin.cournot.profit1) de lucro para cada uma (`examples.linear.cournot`) — a célula de Nash da matriz, reencontrada. A inclinação da reação é o objeto central do modelo: a seção 14 a deriva para um custo qualquer, equação (8), e chama de $lambda$ quantos voos a seguidora corta por voo extra da líder — exatamente #nf(m.reaction_slope.lambda_linear_cost, d: 1) sob custo linear (`reaction_slope.lambda_linear_cost`). A Figura 6, na seção 12, desenha a reta e os pontos que as seções seguintes derivam.

=== Mover primeiro: indução retroativa e Stackelberg

Num *jogo sequencial* uma empresa escolhe primeiro, a *líder*, e a outra observa a escolha e responde, a *seguidora*. Resolve-se um jogo assim de trás para a frente — *indução retroativa*: primeiro o que a seguidora fará para _cada_ escolha possível da líder, que é a função de reação; depois o que a líder escolhe sabendo disso. A líder não escolhe um ponto; escolhe um ponto _sobre a reação da rival_. Sob custo linear o seu lucro ao longo da reação é $pi_1 (f_1) = f_1 (D - b f_1) slash 2$, uma parábola com máximo em $f_1 = D slash 2b$ (`primer.leader_profit_along_reaction`):

#tab((auto, auto, auto, auto, auto), (right, right, right, right, right),
  [voos da líder, $f_1$], [reação da seguidora, $f_2$], [tráfego $F$], [lucro da líder], [lucro da seguidora],
  ..pr.leader_profit_along_reaction.map(r => (nf(r.f1, d: 1), nf(r.f2, d: 2), nf(r.F, d: 2), numd(r.profit1, d: 2), numd(r.profit2, d: 2))).flatten(),
)

#v(1mm)
A líder que voa #nf(lin.cournot.f1, d: 0), o volume de Cournot, ganha #miles(lin.cournot.profit1)\; a que voa #nf(lin.stackelberg.f1, d: 0) ganha #miles(lin.stackelberg.profit1), porque sabe que a seguidora recuará para #nf(lin.stackelberg.f2, d: 1). O *equilíbrio de Stackelberg* é esse ponto — $f_1 = #nf(lin.stackelberg.f1, d: 0)$, $f_2 = #nf(lin.stackelberg.f2, d: 1)$, $F = #nf(lin.stackelberg.F, d: 1)$, lucros #miles(lin.stackelberg.profit1) e #miles(lin.stackelberg.profit2) (`examples.linear.stackelberg`) —, e a *vantagem de quem move primeiro* é a diferença entre as duas linhas: a líder ganha mais que sob Cournot, a seguidora menos. O que a líder faz de diferente é contar só a fração $1 - lambda$ do congestionamento que impõe aos próprios voos, porque prevê que cada voo que cortasse seria em parte reposto; a seção 15 escreve isso como a equação (9) e dela tira $f_1 = f_2 slash (1 - lambda) >= 2 f_2$ (`leader_follower.statement`) — #nf(lin.stackelberg.f1, d: 0) contra #nf(lin.stackelberg.f2, d: 1). O bem-estar ordena as estruturas (`examples.linear`):

#tab((1fr, auto, auto, auto), (left, right, right, right),
  [estrutura], [$F$], [bem-estar], [fração de $W^*$ perdida],
  [ótimo social (`social_optimum`)], nf(lin.social_optimum.F_star, d: 0), miles(lin.social_optimum.welfare_star), "0",
  [Cournot (`cournot`)], nf(lin.cournot.F, d: 0), miles(lin.cournot.welfare), nf(lin.cournot.loss_share, d: 4),
  [Stackelberg (`stackelberg`)], nf(lin.stackelberg.F, d: 1), miles(lin.stackelberg.welfare), nf(lin.stackelberg.loss_share, d: 2),
  [atomístico (`atomistic`)], nf(lin.atomistic.F, d: 0), miles(lin.atomistic.welfare), nf(lin.atomistic.loss_share, d: 0),
)

#v(1mm)
Repare na ordem: Stackelberg perde _mais_ bem-estar que Cournot, porque o fator $1 - lambda$ corrói o incentivo da líder a conter voos. Quem move primeiro ganha para si e piora o conjunto. _O que isso significa para o artigo:_ a empresa dominante de um aeroporto é a candidata natural a líder, e o modelo diz que a liderança enfraquece, sem anular, a internalização — a concentração no aeroporto deve reduzir o atraso, mas menos do que reduziria sob Cournot. Essa gradação é o que a Proposição 1 da seção 16 formaliza.

=== Internalizar uma externalidade, em termos de jogo

Internalizar uma externalidade é _contar, na própria decisão, um custo que se impõe a outros_. Em termos de jogo a definição vira uma comparação de condições de primeira ordem: quanto do dano total que um voo a mais provoca entra na conta de quem decide. O dano total é o dano marginal de congestionamento, $"MCD" equiv F c'(F)$ (`tolls.MCD`) — o que um voo a mais acrescenta ao custo de _todos_ os $F$ voos, o dele próprio incluído; é o CMgE da seção 1 escrito nas variáveis do modelo. Cada estrutura conta uma fração dele (`primer.internalised_share_of_MCD`):

#let quota = pr.internalised_share_of_MCD
#tab((1fr, auto, auto, auto), (left, left, left, right),
  [quem decide], [o que conta em $c'$], [fração do MCD internalizada], [no exemplo linear],
  [planejador social, e o monopolista], [$F$], [1], nf(quota.monopoly, d: 0),
  [empresa de Cournot, na simetria], [$f_i$], [$f_i slash F$], nf(quota.cournot_symmetric, d: 1),
  [seguidora, no equilíbrio de Stackelberg], [$f_2$], [$f_2 slash F$], nf(quota.stackelberg_follower_at_equilibrium, d: 4),
  [líder, no equilíbrio de Stackelberg], [$f_1 (1 - lambda)$], [$(1 - lambda) f_1 slash F$], nf(quota.stackelberg_leader_at_equilibrium, d: 4),
  [empresa atomística], [nada], [0], nf(quota.atomistic, d: 0),
)

#v(1mm)
Duas coisas na tabela merecem pausa. A fração _não_ internalizada é o que uma tarifa terá de cobrir, e ela já está em `model.json` como fração do MCD: #nf(lin.cournot.T1_over_MCD, d: 1) para Cournot (`examples.linear.cournot.T1_over_MCD`) e #nf(lin.stackelberg.T1_over_MCD, d: 4) para a líder e para a seguidora no equilíbrio de Stackelberg (`.stackelberg.T1_over_MCD`, `.T2_over_MCD`). E no ponto de Stackelberg líder e seguidora internalizam a _mesma_ fração, por razões opostas: a líder voa o dobro e desconta a metade; a seguidora voa a metade e não desconta nada — a identidade `T1_equals_T2_at_stackelberg` da seção 16. _O que isso significa para o artigo:_ a participação da maior empresa no aeroporto, `maxcthhi`, é a contrapartida empírica de $f_i slash F$, a fração internalizada por construção do modelo; é por isso que o artigo espera dela sinal negativo sobre o atraso, e não porque concentração seja boa em si.

=== O planejador e a tarifa pigouviana como mecanismo

A *referência cooperativa* de um jogo é o que os jogadores fariam se pudessem decidir juntos e cumprir o combinado. Aqui é o planejador social, que maximiza o lucro conjunto $W = pi_1 + pi_2$ — sob demanda perfeitamente elástica o excedente do consumidor é zero e o bem-estar é o lucro das duas empresas. Onde a empresa carrega $f_i c'$, o planejador carrega $F c'$, o MCD inteiro; é a equação (6) da seção 11, e sob custo linear o tráfego eficiente é $F^* = D slash 2b = #nf(lin.social_optimum.F_star, d: 0)$, #nf(lin.social_optimum.f_star, d: 1) por empresa, com bem-estar #miles(lin.social_optimum.welfare_star) (`examples.linear.social_optimum`) — a célula cooperativa da matriz e o ponto #ponto(tt.cooperative) da Figura 6, que não está sobre a reação de ninguém e por isso nenhuma empresa o alcança sozinha.

A *tarifa pigouviana* é o mecanismo que faz a célula cooperativa virar o equilíbrio: cobra-se de cada empresa, por voo, exatamente a fração do MCD que ela não conta, avaliada no ótimo. Para uma empresa que conta a própria parcela, como a de Cournot ou a seguidora, a tarifa é o que falta, $T_2 = F c' - f_2 c' = f_1 c'$, os voos da _rival_ vezes $c'$ (`tolls.follower`)\; para a líder, que conta menos, a tarifa é maior — as equações (10) e (11) da seção 16. Veja o mecanismo funcionar na matriz. Cobre de cada voo a tarifa de Cournot no ótimo, #miles(tt.with_toll.toll_per_flight) (`primer.two_by_two.with_toll.toll_per_flight`, o $f^* c'$ de `examples.linear.tolls_at_symmetric_optimum.T2_star`), e recalcule as quatro células:

#let celt(k) = miles(tt.with_toll.cells.at(k).profit1) + ", " + miles(tt.with_toll.cells.at(k).profit2)
#tab((1fr, 1fr, 1fr), (left, center, center),
  [com a tarifa: (lucro da 1, lucro da 2)], [empresa 2 voa #vol("low")], [empresa 2 voa #vol("high")],
  [*empresa 1 voa #vol("low")*], celt("low_low"), celt("low_high"),
  [*empresa 1 voa #vol("high")*], celt("high_low"), celt("high_high"),
)

#v(1mm)
Agora, se a rival voa #vol("low"), voar #vol("low") rende #miles(tt.with_toll.cells.low_low.profit1) contra #miles(tt.with_toll.cells.high_low.profit1)\; se a rival voa #vol("high"), voar #vol("low") rende #miles(tt.with_toll.cells.low_high.profit1) contra #miles(tt.with_toll.cells.high_high.profit1). Voar #vol(tt.with_toll.dominant_strategy) passou a ser a estratégia dominante (`with_toll.dominant_strategy`), e a célula de Nash é a cooperativa, #ponto(tt.with_toll.nash) (`with_toll.nash`). A tarifa não destruiu valor: em cada célula, os lucros mais a receita da tarifa somam o lucro total da célula sem tarifa — em #ponto(tt.with_toll.nash), #miles(tt.with_toll.cells.low_low.total_profit) de lucro e #miles(tt.with_toll.cells.low_low.toll_revenue) de receita (`with_toll.cells.low_low`) refazem os #miles(lin.social_optimum.welfare_star) do ótimo. A tarifa é uma transferência que muda os incentivos, e `tests/test_theory.py` confere as duas coisas: a célula de Nash que muda e a soma que não muda.

#chave("O que isso significa para o artigo")[
  No Brasil de 2000–2013 não havia tarifa de congestionamento; o instrumento que chegou aos aeroportos saturados foi o de quantidade, a coordenação de horários de Guarulhos e Santos Dumont a partir de 2009 (`data/external/slots.csv`). Sem o mecanismo de preço, o que pode mover as empresas da célula de Nash em direção à cooperativa é a estrutura do mercado — e é isso que o artigo testa. Três objetos bastam para acompanhar o resto da Parte II: $lambda$, a inclinação da reação com o sinal trocado, porque tudo o que a líder faz de diferente da seguidora passa pelo fator $1 - lambda$; $"MCD" = F c'$, a unidade em que toda tarifa é medida; e a _fração_ do MCD que cada estrutura conta, porque é dela que saem a Proposição 1, a Figura 7 e os regressores de estrutura de mercado do artigo.
]

== 9. Os jogadores, as estratégias e o tempo

O modelo é o da seção 4 da monografia de graduação do autor (USP, 2013), citada como documento externo; ele segue Brueckner e Van Dender (2008) e, nos casos de referência, Brueckner (2002). Há duas empresas aéreas, $i in {1, 2}$, servindo um aeroporto congestionado no período de pico. A *estratégia* de cada uma é o seu volume de voos, $f_i >= 0$; o *resultado* é o tráfego total $F = f_1 + f_2$, que determina o congestionamento; o *pagamento* é o lucro $pi_i (f_1, f_2)$ da seção 10; a *informação* é completa. O que muda entre os casos é o *tempo*: em Cournot as duas escolhem ao mesmo tempo e o conceito de solução é o equilíbrio de Nash; em Stackelberg a empresa 1 escolhe primeiro e a 2 observa antes de escolher, e o conceito de solução é o equilíbrio perfeito em subjogos, obtido por indução retroativa — primeiro a resposta ótima da seguidora, depois a escolha da líder que a antecipa. O comportamento atomístico e o monopólio delimitam os extremos entre os quais Cournot e Stackelberg se situam. Os símbolos, com o nome que cada um tem em `src/airline_delays/theory/model.py`:

#tab((auto, 1fr, auto), (left, left, left),
  [símbolo], [o que é], [nome no código],
  [$f_1, f_2, F$], [voos da empresa 1, da 2, e o total $F = f_1 + f_2$], [`f1`, `f2`, `F`],
  [$p$], [preço total que o passageiro paga (demanda horizontal no caso-base)], [`p`],
  [$s$], [assentos por voo, todos vendidos], [`s`],
  [$tau$], [custo por assento sem congestionamento], [`tau`],
  [$t(F)$], [custo de tempo por passageiro causado pelo congestionamento], [dentro de `c`],
  [$g(F)$], [custo operacional extra por voo causado pelo congestionamento], [dentro de `c`],
  [$c(F)$], [$s t(F) + g(F)$: o custo do congestionamento por voo, $c' > 0$, $c'' >= 0$], [`c`, `c0`, `c1`, `c2`],
  [$lambda$], [$-partial f_2 slash partial f_1$: quantos voos a seguidora corta por voo extra da líder], [`lam`],
  [$x$], [$f_2 c'' slash c'$: a única razão de que todo limite de $lambda$ depende], [`x`],
  [$d(Q)$], [demanda inversa sobre o total de assentos $Q = s F$, $d' < 0$ (seção 19)], [`d`, `d0`, `d1`, `d2`],
  [$a$, $b$, $d d$], [o custo linear $a + b F$ e a inclinação da demanda linear $d_0 - d d dot Q$ dos exemplos], [`a`, `b`, `dd`],
)

#v(2mm)
O que é suposto, e não provado, está na lista `assumptions` de `model.json`, com o status que a derivação lhe dá:

#let pressuposto_pt = (
  A1: [demanda perfeitamente elástica ao preço $p$ em (1)–(11)\; excedente do consumidor zero e bem-estar igual ao lucro conjunto],
  A2: [todo assento é vendido; $s$ é exógeno e igual nas duas empresas],
  A3: [$c' > 0$ e $c'' >= 0$ (equação 5)\; todo limite de $lambda$ é condicional a isso],
  A4: [a empresa 1 lidera e a 2 segue por hipótese; $f_1 > f_2$ decorre de quem lidera, não de tamanho],
  A5: [as tarifas de (10)–(11) são constantes por voo avaliadas na alocação eficiente e não alteram a reação da seguidora],
  A6: [a "Pressuposição 2" (a líder sob demanda inelástica fica entre as duas leituras extremas de (12)) precisa de $-1 < partial f_2 slash partial f_1 <= -1 slash 2$],
  A7: [a "Pressuposição 3": a entrada de uma empresa de baixo custo quebra a estrutura de Stackelberg e a entrante tem incentivo a internalizar o próprio congestionamento],
  A8: [existência e unicidade de um equilíbrio interior],
)
#let status_pt = (
  A1: "suposto", A2: "suposto", A3: "suposto", A4: "suposto", A5: "suposto",
  A6: "vale se e somente se c''/s ≥ s² d''; conferida simbolicamente para d'' = 0 e numericamente para demanda linear (seção 19)",
  A7: "verbal na monografia; ilustrada pela extensão de Cournot deste repositório (seção 20)",
  A8: "verificada numericamente só para os parâmetros escolhidos",
)
#tab((auto, 1fr, 0.6fr), (left, left, left),
  [id], [pressuposto], [status],
  ..m.assumptions.map(a => (a.id, pressuposto_pt.at(a.id, default: a.statement), status_pt.at(a.id, default: a.status))).flatten(),
)

#v(1mm)
_O que isso significa para o artigo._ A1 e A4 são o que o artigo relaxa na prática — os preços variam por rota e nenhuma empresa é declarada líder; o que sobrevive é a estrutura de incentivos, e é ela que os regressores medem.

== 10. A função de lucro, termo a termo

O passageiro está disposto a pagar um preço total $p$ pela viagem no aeroporto congestionado. Como o congestionamento lhe impõe um custo de tempo $t(F)$, a tarifa que a empresa consegue cobrar é o preço total menos esse custo. Com $s$ assentos vendidos por voo, a receita da empresa $i$ é

#numbered(1)[$ R_i = [p - t(f_1 + f_2)] s f_i, quad i = 1, 2 $]

#tag("monografia") A receita cai quando o tráfego total sobe, mesmo com $p$ fixo: o passageiro desconta da tarifa o tempo que perde. Do lado do custo, cada assento custa $tau$, e o congestionamento acrescenta $g(F)$ por voo. O lucro é

#numbered(2)[$ pi_i = [p - t(f_1 + f_2)] s f_i - [tau s + g(f_1 + f_2)] f_i $]

Os dois custos do congestionamento — o do passageiro, $s t(F)$ por voo, e o da empresa, $g(F)$ — entram no lucro do mesmo jeito, subtraindo por voo. A monografia os junta numa só função, a sua equação (5) — a ordem em que ela apresenta as equações explica a numeração —,

#numbered(5)[$ c(F) equiv s t(F) + g(F), quad c' > 0, quad c'' >= 0, $]

e o lucro fica na forma que se usa daqui em diante:

#numbered(3)[$ pi_1 = (p - tau) s f_1 - c(f_1 + f_2) f_1 $]
#numbered(4)[$ pi_2 = (p - tau) s f_2 - c(f_1 + f_2) f_2 $]

O primeiro termo é a receita líquida por voo sem congestionamento, $(p - tau) s$, vezes os voos; o segundo é o custo do congestionamento por voo vezes os voos. O que liga as duas empresas é só $c(F)$: o lucro de cada uma depende do que a outra faz apenas através do tráfego total.

#intuicao("Por que a curvatura de c importa")[
  $c' > 0$ diz que cada voo a mais torna o congestionamento mais caro; $c'' >= 0$ diz que esse encarecimento não desacelera. Tudo o que vem depois — quanto a seguidora reage, quanto a líder internaliza, quanto vale a tarifa — depende dessas duas derivadas, e de nada mais. Por isso a verificação simbólica trabalha com $c$ genérica e os exemplos numéricos com $c$ linear ($c'' = 0$) e quadrática ($c'' > 0$).
]

_O que isso significa para o artigo._ $c' > 0$ é a razão para esperar sinal positivo nos voos do pico (`dailyflcong`) e no estado de congestionamento do aeroporto (`maxprdel`): mais tráfego no horário congestionado, mais atraso para todos.

== 11. O ótimo social

Com demanda horizontal o excedente do consumidor é zero: o passageiro paga exatamente o que a viagem vale para ele. O bem-estar é então o lucro conjunto, $W = pi_1 + pi_2 = (p - tau) s F - c(F) F$. Derivando em relação a $F$ e dividindo por $s$ para ler a condição por assento,

#numbered(6)[$ p - tau - [F c'(F) + c(F)] / s = 0 $]

#tag("monografia") O volume é eficiente quando o preço total iguala o custo marginal social de um assento. Leia o termo entre colchetes. $c(F)$ é o custo de congestionamento do próprio voo; $F c'(F)$ é o custo que esse voo impõe a _todos_ os $F$ voos do aeroporto — cada um deles fica $c'$ mais caro. Esse segundo termo tem nome:

#resultado("Definição: dano marginal de congestionamento")[
  $"MCD" equiv F c'(F)$ é o custo que um voo a mais impõe ao conjunto dos voos já existentes (`tolls.MCD`). É o que uma tarifa eficiente deve cobrar de quem não o considera — e a fração de MCD que cada estrutura de mercado deixa de considerar é a medida da sua falha em internalizar. No exemplo linear o ótimo é $F^* = #nf(lin.social_optimum.F_star, d: 0)$, com $"MCD"^* = #miles(lin.tolls_at_symmetric_optimum.MCD_star)$ (`examples.linear.social_optimum.F_star`, `tolls_at_symmetric_optimum.MCD_star`).
]

_O que isso significa para o artigo._ O ótimo social é a régua: o que o artigo mede nos atrasos é a distância entre o comportamento observado das empresas e essa régua, estrutura de mercado por estrutura de mercado.

== 12. Ponto de referência: Cournot

No jogo simultâneo cada empresa maximiza o próprio lucro tomando o volume da outra como dado. Da equação (3), $partial pi_1 slash partial f_1 = (p - tau) s - c(F) - f_1 c'(F) = 0$, ou, por assento,

$ p - tau - [f_1 c' + c] / s = 0, quad "e simetricamente" quad p - tau - [f_2 c' + c] / s = 0. $

Compare com (6): a empresa 1 internaliza $f_1 c'$ — o dano que impõe aos próprios voos — mas não $f_2 c'$, o que impõe aos voos da rival. Cada uma internaliza a _própria parcela_ do dano marginal. A tarifa que fecha a diferença é $f_2 c'$ para a empresa 1 e $f_1 c'$ para a 2; no ponto simétrico, metade de MCD (identidade `cournot_toll_half_at_symmetry`). Este é o resultado de Brueckner (2002) que a monografia toma como referência, e é a origem do termo de internalização que Guo, Jiang e Wan (2018) levam aos preços (seção 21).

#fig("fig6", [As funções de reação do exemplo linear: a da seguidora, $f_2 (f_1) = (D - b f_1) slash 2b$, e a da empresa 1 no jogo simultâneo. Cournot é o cruzamento das duas; Stackelberg é o ponto da reação da seguidora que a líder escolhe; o ótimo simétrico fica abaixo dos dois.])

_O que isso significa para o artigo._ A separação entre "a própria parcela" e "o dano inteiro" é a distância que o regressor de concentração no aeroporto mede: quanto maior a parcela de uma empresa, maior a fração do dano que ela já paga por conta própria.

== 13. Pontos de referência: atomístico e monopólio

A empresa *atomística* ignora que os seus voos congestionam: a sua condição é $p - tau - c slash s = 0$, sem termo $c'$ nenhum, e a tarifa que a corrige é o dano marginal inteiro, MCD. O *monopolista* faz o contrário: maximiza $(p - tau) s F - c(F) F$ e a sua condição coincide com (6) — internaliza tudo, e a tarifa é zero (identidade `monopoly_foc_is_social`). Internalização não é virtude, é consequência de ser dono de todos os voos. A tabela, lida de `model.json` (`tolls`), resume os pontos de referência que as seções seguintes usam:

#tab((1fr, auto, auto), (left, left, right),
  [estrutura], [o que internaliza], [tarifa ÷ MCD\*],
  [monopólio], [todo o dano marginal], [#nf(m.tolls.monopoly_over_MCD)],
  [duopólio de Cournot, e a seguidora de Stackelberg], [a própria parcela, $f_i slash F$], [#nf(m.tolls.follower_over_MCD)],
  [líder de Stackelberg], [menos que a própria parcela], [$(1 + lambda^*) slash 2$; #nf(m.tolls.leader_over_MCD_linear) sob custo linear],
  [atomística], [nada], [#nf(m.tolls.atomistic_over_MCD)],
)

#v(1mm)
_O que isso significa para o artigo._ Os casos de referência dizem que o efeito da concentração sobre o atraso não é monotônico em geral — quem lidera internaliza menos que um duopolista simétrico —, e é por isso que o artigo separa a concentração na rota da concentração no aeroporto.

== 14. Stackelberg, passo 1: a seguidora

Na indução retroativa começa-se pelo fim: a seguidora, empresa 2, observa $f_1$ e escolhe $f_2$. A sua condição é a de Cournot,

#numbered(7)[$ p - tau - [f_2 c' + c] / s = 0 $]

O que muda é o que fazemos com ela. A condição (7) define $f_2$ como função de $f_1$ — a _função de reação_ — e a pergunta central do modelo é quanto $f_2$ cai quando $f_1$ sobe. Diferenciando (7) totalmente: como $c$ e $c'$ dependem de $F = f_1 + f_2$, um aumento de $f_1$ move o lado esquerdo por $-(c' + f_2 c'') slash s$ (o $c$ sobe $c'$, e $f_2 c'$ sobe $f_2 c''$), e um aumento de $f_2$ o move por $-(2 c' + f_2 c'') slash s$ (os mesmos dois efeitos, mais o $c'$ do próprio $f_2$ a multiplicar). Para (7) continuar valendo, a razão entre os dois é

#numbered(8)[$ (partial f_2) / (partial f_1) = - (f_2 c'' + c') / (f_2 c'' + 2 c') equiv - lambda $]

#resultado("[aqui] Os limites de λ, derivados")[
  Toda a informação de (8) cabe numa razão: com $x = f_2 c'' slash c' >= 0$, $lambda = (1 + x) slash (2 + x)$ (`reaction_slope.lambda_of_x`). Daí $lambda - 1 slash 2 = x slash (2(2 + x)) >= 0$ e $1 - lambda = 1 slash (2 + x) > 0$, portanto $1 slash 2 <= lambda < 1$, com $lambda = 1 slash 2$ exatamente quando $c'' = 0$ (`reaction_slope.lambda_minus_half`, `one_minus_lambda`; `lambda_lower` vale #nf(m.reaction_slope.lambda_lower, d: 1) e `lambda_upper_exclusive` vale #nf(m.reaction_slope.lambda_upper_exclusive, d: 0)). Em palavras: a seguidora corta entre metade e a totalidade de cada voo extra da líder — metade sob custo linear, mais que metade quando o custo marginal do congestionamento acelera. No exemplo quadrático, $c(F) = #nf(qd.cost.a, d: 0) + #nf(qd.cost.b, d: 0) F + F^2$, ela corta $lambda = #nf(qd.stackelberg.lam, d: 4)$ voo por voo extra da líder no equilíbrio (`examples.quadratic.stackelberg.lam`).
]

#intuicao("Por que a seguidora corta")[
  Um voo a mais da líder encarece o congestionamento para todos. A seguidora, que só olha para a própria parcela, vê o seu custo marginal subir e recua — mas não recua voo por voo, porque ao recuar alivia o congestionamento e parte do incentivo desaparece. Fica no meio: $lambda$ entre ½ e 1.
]

_O que isso significa para o artigo._ A função de reação é a forma teórica do mecanismo de compensação que Daniel e Harback (2008) descrevem: o espaço que uma empresa libera no pico é parcialmente ocupado pela outra, e é por ele que a concentração do aeroporto pode reduzir os atrasos menos do que a internalização própria sugeriria.

== 15. Stackelberg, passo 2: a líder

A líder sabe que $f_2 = f_2 (f_1)$ e maximiza $pi_1 = (p - tau) s f_1 - c(f_1 + f_2 (f_1)) f_1$. Pela regra da cadeia, $partial c slash partial f_1 = c' (1 + partial f_2 slash partial f_1)$, e a condição de primeira ordem, por assento, é

#numbered(9)[$ p - tau - 1 / s [f_1 c' (1 + (partial f_2) / (partial f_1)) + c] = 0 $]

#tag("monografia") O fator $(1 + partial f_2 slash partial f_1) = 1 - lambda$ é o coração do modelo. Comparado com Cournot, onde esse fator é 1, a líder internaliza _menos_: ela antecipa que, se cortar voos para aliviar o pico, a seguidora ocupará parte do espaço — é o mecanismo de compensação que Daniel e Harback (2008) descrevem — e por isso o seu incentivo a conter o congestionamento encolhe na proporção $1 - lambda$. Como $1 slash 2 <= lambda < 1$, o fator fica entre 0 e ½: um duopolista de Cournot conta $f_i c'$, o dano que os seus voos sofrem; a líder conta $f_1 c' (1 - lambda)$, o mesmo dano só na fração do voo extra que sobrevive à reação da seguidora.

#resultado("[aqui] A líder voa pelo menos o dobro da seguidora")[
  De (7), $p - tau - c slash s = f_2 c' slash s$; de (9), $p - tau - c slash s = f_1 c' (1 - lambda) slash s$. No mesmo ponto, $f_2 c' = f_1 c' (1 - lambda)$, logo $f_1 = f_2 slash (1 - lambda)$ (`leader_follower.f1`). Com $lambda = (1 + x) slash (2 + x)$ isso é $f_1 = f_2 (2 + x)$, ou $f_1 - 2 f_2 = f_2 x >= 0$ (`leader_follower.f1_minus_2_f2`): a líder voa pelo menos o dobro da seguidora, e exatamente o dobro sob custo linear — mais forte que o "$f_1 > f_2$" da monografia. No exemplo linear a razão é #nf(lin.stackelberg.f1 / lin.stackelberg.f2, d: 0)\; no quadrático, #nf(qd.stackelberg.f1 / qd.stackelberg.f2, d: 4), igual a $1 slash (1 - lambda)$ com o $lambda$ de #nf(qd.stackelberg.lam, d: 4) da seção 14 (`examples.quadratic.stackelberg`).
]

#intuicao("A vantagem de mover primeiro")[
  A líder não é maior porque é mais eficiente — as duas têm o mesmo custo (A2). Ela é maior porque escolhe antes e sabe que cada voo seu afasta meio voo da rival. O mesmo conhecimento que a faz grande a faz internalizar menos: quem sabe que a rival preenche o espaço tem menos razão para deixá-lo vazio.
]

_O que isso significa para o artigo._ O fator $1 - lambda$ é a razão teórica para esperar que a empresa dominante de um aeroporto internalize, mas menos do que a sua participação sugeriria; é o objeto por trás do regressor de concentração no aeroporto (`maxcthhi`) e do sinal negativo que a seção 22 espera dele.

== 16. As tarifas que restauram o ótimo

A tarifa por voo que leva a líder ao ótimo é a diferença entre a condição social (6) e a dela (9): o dano marginal que ela deixa de considerar. Subtraindo,

#numbered(10)[$ T_1 = F c' - f_1 c' (1 - lambda) = (f_2 - f_1 (partial f_2) / (partial f_1)) c' = ((f_2 + lambda f_1) dot "MCD") / (f_1 + f_2) $]

— a forma de diferença diz de onde vem a tarifa (o dano aos voos da seguidora, $f_2 c'$, mais o dano que a líder deixa de considerar por causa da reação, $lambda f_1 c'$)\; a forma de participação a expressa como fração de MCD (identidade `eq10_two_forms`). A seguidora, que se comporta à Cournot, paga $T_2 = F c' - f_2 c' = f_1 c'$ (`tolls.follower`). Avaliando no ótimo simétrico, $f_1 = f_2 = f^*$:

#numbered(11)[$ T_1^* = 1/2 (1 + lambda^*) "MCD"^*, quad T_2^* = 1/2 "MCD"^* $]

#resultado("Proposição 1 [BVD]")[
  #quote(block: false)[Com um líder de Stackelberg e um seguidor, do seguidor é cobrada tarifa de congestionamento ao estilo Cournot. Do líder é cobrada uma tarifa que fica entre o valor de Cournot e da tarifa atomística (o que equivale a 100 por cento do dado do congestionamento marginal de um voo extra).] — monografia, seção 4.3 (documento externo), reenunciando Brueckner e Van Dender (2008). O comportamento do líder empurra a tarifa em direção à estrutura atomística sem chegar a ela: $1 slash 2 <= (1 + lambda^*) slash 2 < 1$.
]

#resultado("[aqui] Três quartos, a meio caminho")[
  Sob custo linear $lambda^* = 1 slash 2$ e (11) vira um número: $T_1^* = #nf(m.tolls.leader_over_MCD_linear) "MCD"^*$ (`tolls.leader_over_MCD_linear`), exatamente a meio caminho entre a tarifa de Cournot (#nf(m.tolls.cournot_over_MCD)) e a atomística (#nf(m.tolls.atomistic_over_MCD)). A monografia escreve que a tarifa "situa-se entre a metade da tarifa de Cournot e a tarifa atomística" — tradução truncada de _halfway between_, "a meio caminho entre", e não "a metade da tarifa de Cournot", que seria um quarto de MCD e contradiria a Proposição 1 da mesma página (identidade `eq11_linear_3_4`). Quando $c'' > 0$, $lambda^* > 1 slash 2$ e a tarifa da líder sobe acima de três quartos: #nf(qd.tolls_at_symmetric_optimum.T1_star_over_MCD, d: 4) no exemplo quadrático (Figura 7). E há uma coincidência útil: em qualquer equilíbrio de Stackelberg $f_2 = (1 - lambda) f_1$, logo $T_1 = T_2 = f_1 c'$ — as duas empresas precisam da mesma tarifa por voo, por razões diferentes (identidade `T1_equals_T2_at_stackelberg`). No exemplo linear, $"MCD"^* = #miles(lin.tolls_at_symmetric_optimum.MCD_star)$, $T_1^* = #miles(lin.tolls_at_symmetric_optimum.T1_star)$ e $T_2^* = #miles(lin.tolls_at_symmetric_optimum.T2_star)$ (`examples.linear.tolls_at_symmetric_optimum`).
]

#fig("fig7", [As tarifas de (11) por estrutura de mercado, como fração do dano marginal no ótimo simétrico. Lidas de `model.json` (`examples.linear` e `examples.quadratic`, `tolls_at_symmetric_optimum`).])

_O que isso significa para o artigo._ A Proposição 1 ordena as estruturas de mercado pela fração do dano que deixam de considerar; é essa ordem que o artigo procura nos dados — menos atraso onde o aeroporto é mais concentrado, com a ressalva de que uma líder internaliza menos do que a sua participação.

== 17. Exemplo numérico completo

Com $p = #nf(lin.primitives.p, d: 0)$, $tau = #nf(lin.primitives.tau, d: 0)$, $s = #nf(lin.primitives.s, d: 0)$ e custo linear $c(F) = #nf(lin.cost.a, d: 0) + #nf(lin.cost.b, d: 0) F$, tudo tem forma fechada em $D = (p - tau) s - a$ e $b$ (`linear_closed_forms`): o ótimo $F^* = D slash 2b$; Cournot $D slash 3b$ por empresa; Stackelberg $D slash 2b$ para a líder e $D slash 4b$ para a seguidora; o total atomístico $D slash b$, o dobro do eficiente. As perdas de bem-estar são frações fixas de $W^*$: $1 slash 9$ sob Cournot, $1 slash 4$ sob Stackelberg, tudo sob comportamento atomístico (identidade `linear_welfare_losses`). A tabela põe os números lado a lado (`examples.linear`):

#tab((1fr, auto, auto, auto, auto, auto, auto), (left, right, right, right, right, right, right),
  [estrutura], [$f_1$], [$f_2$], [$F$], [lucro 1], [lucro 2], [perda ÷ $W^*$],
  [ótimo social ($W^* = #miles(lin.social_optimum.welfare_star)$)], nf(lin.social_optimum.f_star, d: 1), nf(lin.social_optimum.f_star, d: 1), nf(lin.social_optimum.F_star, d: 0), "—", "—", "0",
  [monopólio], "—", "—", nf(lin.monopoly.F, d: 0), "—", "—", nf(lin.monopoly.loss_share, d: 2),
  [Cournot], nf(lin.cournot.f1, d: 0), nf(lin.cournot.f2, d: 0), nf(lin.cournot.F, d: 0), miles(lin.cournot.profit1), miles(lin.cournot.profit2), nf(lin.cournot.loss_share, d: 4),
  [Stackelberg], nf(lin.stackelberg.f1, d: 0), nf(lin.stackelberg.f2, d: 1), nf(lin.stackelberg.F, d: 1), miles(lin.stackelberg.profit1), miles(lin.stackelberg.profit2), nf(lin.stackelberg.loss_share, d: 2),
  [atomística], "—", "—", nf(lin.atomistic.F, d: 0), "—", "—", nf(lin.atomistic.loss_share, d: 0),
)

#v(1.5mm)
No ponto de Stackelberg o dano marginal é MCD = #miles(lin.stackelberg.MCD), a líder deve #miles(lin.stackelberg.T1) por voo e a seguidora #miles(lin.stackelberg.T2) — iguais, como a seção 16 antecipa —, e a tarifa da líder é #nf(lin.stackelberg.T1_over_MCD, d: 4) do dano marginal, abaixo dos #nf(lin.tolls_at_symmetric_optimum.T1_star_over_MCD) do ótimo simétrico porque o equilíbrio não é o ótimo (`examples.linear.stackelberg`). O mesmo quadro sob custo quadrático, $c(F) = #nf(qd.cost.a, d: 0) + #nf(qd.cost.b, d: 0) F + F^2$, onde $c'' > 0$ e nada é inteiro (`examples.quadratic`):

#tab((1fr, auto, auto, auto, auto, auto, auto), (left, right, right, right, right, right, right),
  [estrutura], [$f_1$], [$f_2$], [$F$], [lucro 1], [lucro 2], [perda ÷ $W^*$],
  [ótimo social ($W^* = #numd(qd.social_optimum.welfare_star, d: 2)$)], nf(qd.social_optimum.f_star, d: 4), nf(qd.social_optimum.f_star, d: 4), nf(qd.social_optimum.F_star, d: 4), "—", "—", "0",
  [monopólio], "—", "—", nf(qd.monopoly.F, d: 4), "—", "—", nf(qd.monopoly.loss_share, d: 2),
  [Cournot], nf(qd.cournot.f1, d: 4), nf(qd.cournot.f2, d: 4), nf(qd.cournot.F, d: 4), numd(qd.cournot.profit1, d: 2), numd(qd.cournot.profit2, d: 2), nf(qd.cournot.loss_share, d: 4),
  [Stackelberg], nf(qd.stackelberg.f1, d: 4), nf(qd.stackelberg.f2, d: 4), nf(qd.stackelberg.F, d: 4), numd(qd.stackelberg.profit1, d: 2), numd(qd.stackelberg.profit2, d: 2), nf(qd.stackelberg.loss_share, d: 4),
  [atomística], "—", "—", nf(qd.atomistic.F, d: 4), "—", "—", nf(qd.atomistic.loss_share, d: 0),
)

#v(1.5mm)
#intuicao("Leia a tabela linear de baixo para cima")[
  As atomísticas voam #nf(lin.atomistic.F, d: 0) e dissipam tudo; a líder e a seguidora voam #nf(lin.stackelberg.F, d: 1) e perdem um quarto; os duopolistas de Cournot voam #nf(lin.cournot.F, d: 0) e perdem um nono; o monopolista voa #nf(lin.monopoly.F, d: 0) e nada perde. Cada degrau é uma fração a mais do dano marginal levada em conta.
]

_O que isso significa para o artigo._ Os números são estilizados — escolhidos em `src/airline_delays/theory/families.py` para que o caso linear tenha equilíbrios inteiros — e não calibrados a nenhum aeroporto; o que o artigo leva deles é a ordem das estruturas, não as magnitudes.

== 18. Estática comparativa: a curvatura do custo

#tag("aqui") O que muda quando o custo marginal do congestionamento acelera? O bloco `comparative_statics.cost_curvature` varia $q$ em $c(F) = a + b F + q F^2$, com o $a = #nf(qd.cost.a, d: 0)$ e o $b = #nf(qd.cost.b, d: 0)$ do exemplo quadrático (`examples.quadratic.cost`), demanda perfeitamente elástica e os mesmos primitivos; como aqui $b$ é o do exemplo quadrático, o caso $q = 0$ tem um ótimo diferente do exemplo linear da seção 17.

#fig("fig8", [$lambda^*$ e $T_1^* slash "MCD"^*$ no ótimo simétrico para $c(F) = a + b F + q F^2$, $q$ de #nf(m.comparative_statics.cost_curvature.first().q, d: 0) a #nf(m.comparative_statics.cost_curvature.last().q, d: 0) (`comparative_statics.cost_curvature`).])

#tab((auto, auto, auto, auto, auto, auto, auto), (right, right, right, right, right, right, right),
  [$q$], [$F^*$], [$lambda^*$], [$T_1^* slash "MCD"^*$], [$lambda$ em Stackelberg], [$f_1 slash f_2$], [perda ÷ $W^*$],
  ..m.comparative_statics.cost_curvature.map(r => (nf(r.q, d: 2), nf(r.F_star, d: 2), nf(r.lambda_star, d: 4), nf(r.T1_star_over_MCD, d: 4), nf(r.stackelberg_lambda, d: 4), nf(r.f1_over_f2, d: 3), nf(r.loss_share, d: 4))).flatten(),
)

#v(1.5mm)
Quanto mais curvo o custo, mais a seguidora recua ($lambda^*$ sobe), porque um voo da líder eleva também $c'$ e com ele o termo próprio que a seguidora já conta; menos a líder internaliza, e mais a sua tarifa se aproxima da atomística — sem alcançá-la, porque $lambda < 1$; a razão $f_1 slash f_2$ sobe de 2 na direção de $1 slash (1 - lambda)$; e a perda de bem-estar de Stackelberg _cai_ em fração de $W^*$, porque o ótimo também encolhe. _O que isso significa para o artigo:_ a diferença entre a tarifa de Cournot e a da líder é maior justamente onde o congestionamento acelera mais depressa — os aeroportos saturados —, e é ali que a distinção entre internalizar a própria parcela e internalizar menos que ela tem mais consequência empírica.

== 19. Demanda inelástica e a "Pressuposição 2"

Até aqui as empresas não tinham poder de mercado: o preço era dado. A monografia relaxa isso na seção 4.4, com $p = d(s F)$, $d' < 0$ — o preço cai com o total de assentos, e cada empresa sabe que os seus voos o derrubam. O lucro da líder passa a ser $pi_1 = d(s (f_1 + f_2 (f_1))) s f_1 - tau s f_1 - c f_1$; a regra da cadeia atinge dois lugares, o preço e o custo, e a condição de primeira ordem, por assento, é

#numbered(12)[$ d + s f_1 d' (1 + (partial f_2) / (partial f_1)) - tau - 1 / s [f_1 c' (1 + (partial f_2) / (partial f_1)) + c] = 0 $]

enquanto a condição eficiente é $d - tau - [F c' + c] slash s = 0$ (`inelastic.social_foc`). #tag("monografia") Há agora duas distorções, de sinais opostos: o termo $s f_1 d' (1 - lambda) < 0$ é o poder de mercado exercido (retém tráfego), e o termo $f_1 c' (1 - lambda) slash s > 0$ é o dano que a líder deixa de internalizar (excede tráfego). A monografia lê os dois extremos: se $partial f_2 slash partial f_1 = -1$, (12) reduz-se a $d - tau - c slash s = 0$ (`inelastic.limit_slope_minus_one`) — nem poder de mercado, nem internalização, e só uma tarifa atomística corrige; se $partial f_2 slash partial f_1 = -1 slash 2$, a líder exerce metade do poder de mercado e ainda deixa de internalizar $f_1 c' slash 2 s$ (`inelastic.limit_slope_minus_half`).

#resultado("Pressuposição 2 [monografia]")[
  #quote(block: false)[O líder Stackelberg, quando enfrenta uma demanda inelástica, maximiza seu lucro no intervalo que apresenta como limite inferior o caso em que não explora seu poder de mercado mas falha na internalização do congestionamento e, como limite superior, o caso em que exerce metade do seu poder de mercado sendo incapaz também de internalizar o congestionamento.] — monografia, seção 4.4 (documento externo). É uma leitura dos extremos de (12), condicional a $-1 < partial f_2 slash partial f_1 <= -1 slash 2$ continuar valendo sob demanda inelástica — limite que a monografia toma emprestado do caso elástico, provado em (8), sem o reprovar (pressuposto A6).
]

#resultado("[aqui] A condição para os limites valerem")[
  Derivando a reação da seguidora sob $p = d(s F)$, $partial f_2 slash partial f_1 = -A slash B$ com $A = (c' + f_2 c'') slash s - s d' - s^2 f_2 d''$ e $B = A + c' slash s - s d'$ (`inelastic.slope_A`, `slope_B`), e $-partial f_2 slash partial f_1 - 1 slash 2 = f_2 (c'' slash s - s^2 d'') slash 2 B$. O limite vale, portanto, se e só se $c'' slash s >= s^2 d''$ (`inelastic.slope_bounds_condition`; identidade `lambda_inelastic_general`): automático para demanda linear ou côncava, não garantido para demanda convexa. Com $d'' = 0$ a reação é $-(k + f_2 c'') slash (2k + f_2 c'')$, $k = c' - s^2 d' > 0$, e os limites do caso elástico se repetem (identidade `lambda_linear_demand`). Com custo linear e demanda linear $d(Q) = d_0 - d d dot Q$ tudo volta a ter forma fechada, em $D_p = s d_0 - s tau - a$ e $m = b + d d dot s^2$: $f_1 = D_p slash 2m$, $f_2 = D_p slash 4m$, $F^* = D_p slash (2b + d d dot s^2)$ (identidade `inelastic_linear_closed_forms`).
]

#fig("fig9", [Demanda linear $d(Q) = #nf(inel.demand.d0, d: 0) - d d dot Q$ e custo linear: o total de Stackelberg contra o eficiente à medida que a demanda inclina (`comparative_statics.demand_slope`).])

No exemplo linear-linear com $d_0 = #nf(inel.demand.d0, d: 0)$ e $d d = #nf(inel.demand.dd, d: 3)$ (`examples.inelastic_linear_demand`), o ponto de Stackelberg é $f_1 = #nf(inel.stackelberg.f1, d: 0)$, $f_2 = #nf(inel.stackelberg.f2, d: 0)$, preço #nf(inel.stackelberg.price, d: 1), total #nf(inel.stackelberg.F, d: 0) contra um ótimo de #nf(inel.social_optimum.F_star, d: 4)\; os dois termos de (12) valem #nf(inel.equation_12_terms_at_stackelberg.market_power_term, d: 1) (poder de mercado) e #nf(inel.equation_12_terms_at_stackelberg.uninternalised_term, d: 0) (parcela não internalizada), e o total excede o ótimo em #nf(inel.equation_12_terms_at_stackelberg.F_exceeds_optimum_by, d: 4) voos. Com poder de mercado o monopolista deixa de coincidir com o ótimo: voa #nf(inel.monopoly.F, d: 0) e perde #nf(inel.monopoly.loss_share, d: 2) de $W^*$, porque retém tráfego para sustentar o preço. A tabela mostra o que a Figura 9 desenha (`comparative_statics.demand_slope`):

#tab((auto, auto, auto, auto, auto, auto, auto, auto), (right, right, right, right, right, right, right, right),
  [$d d$], [$f_1$], [$f_2$], [$F$], [$F^*$], [preço], [poder de mercado], [não internalizado],
  ..m.comparative_statics.demand_slope.map(r => (nf(r.dd, d: 3), nf(r.f1, d: 2), nf(r.f2, d: 2), nf(r.F, d: 2), nf(r.F_star, d: 2), nf(r.price, d: 2), nf(r.market_power_term, d: 2), nf(r.uninternalised_term, d: 2))).flatten(),
)

#v(1.5mm)
#tag("aqui") Quando a demanda inclina o bastante, a distorção do poder de mercado vence e o tráfego cai _abaixo_ do ótimo — a última linha da tabela —, uma consequência que a monografia não explora. A Pressuposição 2 descreve o intervalo dos dois termos; não diz que a soma tenha sinal fixo, e é por isso que a distorção líquida é uma pergunta empírica. _O que isso significa para o artigo:_ é por isso que o sinal da concentração na rota (`rthhi`) é ambíguo na teoria — $d' < 0$ reduz voos, e o dano não internalizado os aumenta —, e a seção 22 mostra como o artigo lê esse regressor.

== 20. A entrada de uma empresa de baixo custo

#resultado("Pressuposição 3 [monografia]")[
  #quote(block: false)[A entrada de uma empresa aérea de baixo custo no mercado quebra a estrutura do jogo em Stackelberg. Devido à estrutura do modelo de negócios de uma empresa aérea de baixo custo, é coerente pressupor que tais empresas procurem internalizar os custos do congestionamento, uma vez que tais custos podem afetar o planejamento estratégico de longo prazo da empresa que busca o crescimento de sua participação de mercado.] — monografia, seção 4.5 (documento externo). Não há equação por trás: é o pressuposto A7, verbal, e o terreno econômico do modelo de negócios de baixo custo é a seção 7.
]

#resultado("[aqui] Uma extensão, rotulada como tal")[
  O que a frase pode significar dentro do modelo — extensão deste repositório, não da monografia (`extension_lcc.label`): com a entrante o jogo deixa de ter uma líder e passa a ser um Cournot de três, e a entrante custa menos por assento. Sob custo linear a condição de cada empresa $i$ é $D_i - b F - b f_i = 0$ com $D_i = (p - tau_i) s - a$, de onde $F = sum_i D_i slash (n + 1) b$ e $f_i = D_i slash b - F$, e $f_i slash F$ é a parcela do dano marginal que $i$ internaliza — a lógica de Cournot da seção 12 com participações desiguais. Com duas incumbentes a $tau = #nf(lcc.incumbent_tau, d: 0)$ e uma entrante a $tau = #nf(lcc.entrant_tau, d: 0)$: receita líquida por voo #miles(lcc.triopoly.D.at(0)) para a entrante e #miles(lcc.triopoly.D.at(1)) para cada incumbente; total #nf(lcc.triopoly.F, d: 0) (contra #nf(lcc.duopoly_cournot.F, d: 0) no duopólio de Cournot e #nf(lcc.stackelberg_duopoly_F, d: 1) em Stackelberg)\; voos #nf(lcc.triopoly.flights.at(0), d: 0), #nf(lcc.triopoly.flights.at(1), d: 0) e #nf(lcc.triopoly.flights.at(2), d: 0)\; parcela internalizada do dano marginal #nf(lcc.triopoly.internalised_share.at(0)) para a entrante contra #nf(lcc.triopoly.internalised_share.at(1)) para cada incumbente, que passam de #nf(lcc.duopoly_cournot.internalised_share.at(0)) a #nf(lcc.triopoly.internalised_share.at(1)) cada (`extension_lcc`). A entrante internaliza mais porque voa mais, e voa mais porque custa menos: é argumento de tamanho, não de modelo de negócios. A extensão não diz nada sobre tempo, escolha de aeroporto ou preços — as três coisas que a seção 21 mostra importarem.
]

#fig("fig10", [Parcelas internalizadas do dano marginal, $f_i slash F$, no duopólio de Cournot e no triopólio com a entrante (`extension_lcc`).])

#tag("aqui") A leitura que este repositório propõe é que "internalizar" tem pelo menos _três margens_, e a Pressuposição 3 não diz por qual delas a entrante opera: a *reprogramação* — deslocar partidas para fora do pico sem mudar o número de voos (Ater 2012)\; a *redução de tráfego via preço* — cobrar mais e voar menos, o canal que a seção 21 mede; e a *escolha do aeroporto* — operar onde o congestionamento não existe (Gudmundsson, Paleari e Redondi 2014), a estratégia de aeroportos secundários que a seção 7 atribui à entrante brasileira do período. Quem internaliza pela terceira margem não precisa da segunda, e não aparece numa regressão de preços. _O que isso significa para o artigo:_ as duas variáveis de baixo custo do artigo — na rota (`lcc`) e em uma das cidades-extremo (`maxalccfu`) — são a forma empírica da Pressuposição 3, e o sinal negativo esperado para ambas vem daqui.

== 21. Do jogo às tarifas: Guo, Jiang e Wan (2018)

A formulação foi completada onde a monografia não tinha dado: nos preços. Guo, Jiang e Wan (2018, *Transportation Research Part A* 118, 648–661, doi 10.1016/j.tra.2018.10.012) partem do mesmo termo de Cournot da seção 12 — a própria parcela do dano marginal — e o levam à tarifa. Na nossa notação, uma empresa $i$ com tráfego $q_(i A)$ no aeroporto A, enfrentando o atraso $D_A$ valorado a $beta$ por unidade de tempo, fixa em cada mercado o preço $p = c + beta D_A - p' q + beta D'_A q_(i A)$: os três primeiros termos são um Cournot comum — custo, atraso e o _markup_ de poder de mercado —, e o quarto é o _markup de internalização própria_, o $f_i c'$ da seção 12 escrito em passageiros no lugar de voos, que existe só se a empresa internaliza. Daí uma hipótese testável sem medir atraso nenhum como variável dependente: se as empresas internalizam, a tarifa sobe com a interação entre os passageiros próprios no aeroporto e o atraso do aeroporto. Com dados americanos de 2014–2015 (DB1B, T-100, AOTP), a interação é positiva e significante para as empresas de serviço completo e não significante para as de baixo custo (Guo, Jiang e Wan 2018, Tabela 4 — documento externo)\; a explicação dos autores não é comportamental: as de baixo custo escolhem aeroportos menos congestionados.

O artigo de 2018 constrói explicitamente sobre o de 2016 — a separação entre concentração de mercado e de aeroporto — e o critica num ponto preciso: controlar por tráfego do aeroporto remove o canal de internalização que age _reduzindo tráfego via preço_, deixando visível só o canal de _reprogramação_. É uma crítica ao desenho, não ao achado.

#chave("As três margens de internalização (síntese deste repositório)")[
  Lidas por margem, a Pressuposição 3 e "as empresas de baixo custo não internalizam via preço" deixam de ser contraditórias: a primeira afirma incentivo a internalizar, a segunda mede uma margem específica, e as duas podem ser verdadeiras ao mesmo tempo se a entrante brasileira do período tiver internalizado pela margem do aeroporto próprio, não pela tarifa. É a hipótese que este estudo deixa formulada e a seção 26 lista como aberta; testá-la exige separar as três margens no mesmo painel, e isso pede tarifas. _O que isso significa para o artigo:_ 2016 mediu a internalização no atraso, controlando por tráfego do aeroporto; 2018 a mediu no preço. São margens diferentes do mesmo objeto teórico.
]

= Parte III — O artigo

== 22. Do modelo às hipóteses

O artigo não estima o jogo; estima a sua consequência observável. Cada objeto do modelo tem um regressor, cada regressor um sinal esperado, e a regra de proveniência é uma só: todo coeficiente publicado vem de `src/airline_delays/estimation/published.json`, lido pela ponte `bridge` de `reports/theory/model.json` ou pelo bloco `published` de `reports/summary.json`, e é marcado "(artigo, Tabela N)"; nada é reestimado nesta seção — a replicação é a seção 25. Três peças do jogo têm contraparte empírica, e cada uma vira uma hipótese com um regressor, um sinal esperado e um mecanismo.

*H1 — internalização no aeroporto.* Uma empresa que opera $f_i$ dos $F$ voos sente, do dano marginal $F c'$, só a fatia $f_i c'$ que recai sobre os próprios voos; é essa fatia que ela internaliza, e a Proposição 1 mede o que falta cobrar — $(1 + lambda) slash 2$ do dano para a líder, #nf(m.tolls.leader_over_MCD_linear) sob custo linear (`tolls.leader_over_MCD_linear`). Quanto maior a parcela de uma empresa no aeroporto, maior a fração do dano que ela já paga por conta própria. A hipótese: onde uma empresa domina o aeroporto, os atrasos são menores do que o volume de voos faria prever, tudo o mais constante. O regressor é a concentração de passageiros na cidade-extremo mais concentrada da rota, `maxcthhi`, e o sinal esperado é negativo (`bridge.rows`).

*H2 — poder de mercado na rota.* Com demanda inversa $d(s F)$ e $d' < 0$, a equação (12) carrega dois termos de sinais opostos — o poder de mercado, que leva a voar de menos, e o dano não internalizado, que leva a voar de mais (seção 19). Para o atraso, o poder de mercado na _rota_ tem por isso dois canais: menos concorrência significa menos voos e menos pressão sobre a pista (menos atraso), e uma empresa sem rival na rota tem menos a perder com um horário mal cumprido — o canal concorrência–qualidade (mais atraso). O modelo não escolhe entre eles; a monografia esperava "−, +" para os índices de concentração, e o artigo lê o coeficiente positivo que encontra como o canal concorrência–qualidade. O regressor é a concentração de passageiros na rota, `rthhi`, e o sinal esperado é ambíguo. A separação entre `rthhi` e `maxcthhi` é a decisão que permite testar as duas coisas ao mesmo tempo — poder de mercado onde a empresa vende, internalização onde ela congestiona.

*H3 — a entrante de baixo custo.* A Pressuposição 3 é verbal; a extensão da seção 20 lhe dá tamanho — a entrante internaliza #nf(lcc.triopoly.internalised_share.at(0)) do dano marginal contra #nf(lcc.triopoly.internalised_share.at(1)) de cada incumbente, porque voa mais, e voa mais porque custa menos (`extension_lcc`). A hipótese do artigo não é sobre o atraso da entrante, e sim sobre o das incumbentes: a presença de uma empresa de baixo custo reduz o atraso das empresas de serviço completo, na rota em que entra e na cidade em que opera. São dois regressores binários, `lcc` (Gol ou Azul vendendo bilhetes na rota no mês) e `maxalccfu` (Gol ou Azul presente numa das cidades-extremo), ambos com sinal esperado negativo; o segundo é o _spillover_ não-preço do título do artigo, um efeito que a entrante exerce sobre rotas em que nem sequer voa. O restante da especificação são controles: volumes no pico e fora dele, três parcelas de causa não estratégica (ADR-0005), o estado do aeroporto e o codeshare. A tabela resume, na ordem das hipóteses; os objetos e os sinais são as linhas de `bridge.rows`.

#let hip = (
  maxcthhi: ("H1 — aeroporto", [quem enfrenta o próprio congestionamento contém voos; Proposição 1]),
  rthhi: ("H2 — rota", [menos voos (−) contra menos incentivo a cumprir horário (+)\; equação (12)]),
  lcc: ("H3 — LCC na rota", [a entrante internaliza; a rota com LCC atrasa menos; Pressuposição 3]),
  maxalccfu: ("H3 — LCC na cidade", [o derrame não-preço do título, pela cidade]),
  dailyflcong: ("controle", [$f_1 + f_2$ com $c' > 0$: mais voo na hora cheia, mais atraso]),
  dailyflncong: ("controle", [sem previsão do modelo; o artigo acha o mesmo sinal do pico]),
  prwheather: ("controle", [atraso não estratégico, fora do jogo (ADR-0005)]),
  princident: ("controle", [atraso não estratégico, fora do jogo (ADR-0005)]),
  pr_connc: ("controle", [atraso não estratégico, fora do jogo (ADR-0005)]),
  maxprdel: ("controle", [$c(F)$ é de todos: o atraso de todas as empresas na ponta mais movimentada]),
  cshare: ("controle", [cooperação fora do modelo]),
)
#let ordem_h = ("maxcthhi", "rthhi", "lcc", "maxalccfu", "dailyflcong", "dailyflncong", "prwheather", "princident", "pr_connc", "maxprdel", "cshare")
#let linha_de(v) = m.bridge.rows.find(r => r.variable == v)
#let sinal_esperado(v, e) = if e == "-" { "−" } else if e != none { e } else if v == "rthhi" { "ambíguo" } else { "sem previsão" }
#tab((auto, 1.3fr, auto, auto, 1fr), (left, left, left, center, left),
  [hipótese], [objeto teórico], [regressor], [sinal esperado], [mecanismo],
  ..ordem_h.filter(v => linha_de(v) != none).map(v => {
    let r = linha_de(v)
    let h = hip.at(v, default: ("—", []))
    (h.at(0), r.theory_object_pt, raw(v), sinal_esperado(v, r.expected_sign), h.at(1))
  }).flatten(),
)

=== A tabela-ponte: cada hipótese e o que saiu publicado

A tabela tem uma linha por objeto teórico, na ordem de `bridge.rows`. As duas colunas de resultados são o coeficiente publicado com as estrelas, lidos de `bridge.tables.table3` e `bridge.tables.table6`: a coluna (2) da Tabela 3 é o 2SGMM com as binárias de LCC, o modelo de base do artigo; a coluna (2) da Tabela 6 é a mesma especificação por OLS, sem instrumento (artigo, Tabelas 3 e 6). Estrelas: \*\*\* 1%, \*\* 5%, \* 10%.

#let objeto_pt = (:)
#for row in m.bridge.rows { objeto_pt.insert(row.variable, row.theory_object_pt) }
#let t3 = m.bridge.tables.table3.variables
#let t6 = m.bridge.tables.table6.variables
#let st3 = res.table3.comparison
#let st6 = res.table6.comparison
#tab((auto, 1.5fr, auto, 1fr, 0.8fr), (left, left, center, right, right),
  [variável], [objeto teórico], [esperado], [Tab. 3 (2), 2SGMM], [Tab. 6 (2), OLS],
  ..t3.pairs().map(p => {
    let v = p.at(0)
    let info = p.at(1)
    let c3 = info.columns.at("2")
    let c6 = t6.at(v).columns.at("2")
    (raw(v), objeto_pt.at(v, default: v), sinal_esperado(v, info.expected_sign),
     sgn(c3.b) + " " + estrelas(c3.stars),
     sgn(c6.b) + " " + estrelas(c6.stars))
  }).flatten(),
  [—], [a reação da seguidora, $partial f_2 slash partial f_1 = -lambda$: nenhuma variável, é a endogeneidade], [—],
  [$N$ = #miles(st3.at("2").stats.n_obs.published)\; KP LM #nf(st3.at("2").stats.kp_lm.published, d: 4)\; $J$ = #nf(st3.at("2").stats.j_stat.published, d: 4) ($p$ = #nf(st3.at("2").stats.j_p.published, d: 4))],
  [$N$ = #miles(st6.at("2").stats.n_obs.published)\; sem instrumento],
)

#v(1mm)
As estatísticas da última linha são as publicadas para as colunas (2) das Tabelas 3 e 6 (artigo)\; a coluna (1) da Tabela 3, sem as binárias de LCC, tem o mesmo $N$ = #miles(st3.at("1").stats.n_obs.published), KP LM #nf(st3.at("1").stats.kp_lm.published, d: 4) e $J$ = #nf(st3.at("1").stats.j_stat.published, d: 4) ($p$ = #nf(st3.at("1").stats.j_p.published, d: 4)) (artigo, Tabela 3).

#fig("fig11", [Os quatro regressores de estrutura de mercado: OLS (cinza) contra 2SGMM (colorido), coeficientes publicados da coluna (2) das Tabelas 6 e 3, com as estrelas publicadas. Valores em `figures.json` (`fig11.quantities`)\; nada é reestimado.], w: 84%)

*Três leituras.* _(a) As duas concentrações contam duas histórias, e o par OLS/2SGMM é a demonstração._ No OLS, `rthhi` sai #sgn(t6.rthhi.columns.at("2").b) a 1% e `maxcthhi` #sgn(t6.maxcthhi.columns.at("2").b) sem estrela; no 2SGMM os dois invertem: `rthhi` #sgn(t3.rthhi.columns.at("2").b) a 5%, `maxcthhi` #sgn(t3.maxcthhi.columns.at("2").b) a 1% (artigo, Tabelas 3 e 6). Concentração na rota associada a mais atraso é o canal concorrência–qualidade; concentração no aeroporto associada a menos atraso é internalização. A inversão não é anedota de uma célula: ela ocorre nas duas colunas ODDS de cada tabela e em nenhuma coluna MINS, onde OLS e 2SGMM já têm o mesmo sinal e só a magnitude muda — o padrão completo, e a sua replicação, estão na seção 25. _(b) A LCC age pela cidade, não pela rota._ Na coluna (2) da Tabela 3, `lcc` é #sgn(t3.lcc.columns.at("2").b) sem estrela e `maxalccfu` é #sgn(t3.maxalccfu.columns.at("2").b) a 5%; no OLS a ordem se inverte: `lcc` #sgn(t6.lcc.columns.at("2").b) a 1% e `maxalccfu` #sgn(t6.maxalccfu.columns.at("2").b) sem estrela. Instrumentar as concentrações desloca o efeito da rota para a cidade — e é o efeito de cidade, o derrame sobre rotas em que a entrante não voa, que dá título ao artigo. Nas colunas em minutos, `lcc` muda de sinal e sai positivo a 10% (#sgn(t3.lcc.columns.at("4").b) e #sgn(t3.lcc.columns.at("6").b) nas colunas (4) e (6)), enquanto `maxalccfu` segue negativo e sem estrela (artigo, Tabela 3; `bridge.tables.table3.variables.lcc.pattern`). _(c) Os controles são estáveis._ Clima, incidentes, rotação e estado do aeroporto saem positivos a 1% com magnitudes quase iguais nos dois estimadores; os volumes saem positivos nos dois, com estrela só no 2SGMM. É o que se espera de variáveis que não estão no jogo: a endogeneidade da concentração não as contamina.

=== A lógica da identificação, em uma página

*Por que a concentração é endógena ao atraso.* No jogo, cada empresa escolhe voos olhando o congestionamento que os outros voos causam — a seguidora reage a $f_1$ com $partial f_2 slash partial f_1 = -lambda$. Voos determinam participações, e participações determinam o HHI. Logo o HHI de uma rota-mês e o atraso dessa rota-mês são decididos no _mesmo_ equilíbrio: uma rota que atrasa muito pode perder o rival marginal e ficar mais concentrada, e uma rota concentrada pode ser mais ou menos pontual pelos dois canais de H2. Um efeito fixo de rota não resolve isso: remove o que é constante na rota — distância, tamanho das cidades, geografia —, não a simultaneidade dentro de cada mês. Um coeficiente OLS de `rthhi` ou `maxcthhi` mistura o efeito da concentração sobre o atraso com o efeito do atraso sobre a concentração, e a Tabela 6 mostra o resultado dessa mistura.

*Por que instrumentos, e quais.* Um instrumento precisa mover a concentração desta rota-mês sem passar pelo atraso desta rota-mês. A escolha do artigo é do tipo Hausman: a concentração de _outras_ cidades e rotas, em faixas de vizinhança e com defasagem — #instr_all.len() colunas do painel de estimação do artigo, #instr_all.map(raw).join(", "), construção espacial dos autores. A hipótese de exclusão é que choques de estratégia e de custo de uma empresa se refletem na sua concentração em várias cidades ao mesmo tempo, enquanto o atraso de uma rota-mês específica não muda a concentração das vizinhas. As endógenas são só #endog.map(raw).join(" e ")\; as binárias de LCC entram como exógenas. As listas por bloco, os estimadores e a estatística que testa a força dos instrumentos são a seção 24.

*Por que a inversão de sinal é o argumento do artigo.* A Tabela 6 existe para ser comparada com a Tabela 3: é a mesma especificação sem instrumentar. Se a endogeneidade fosse inócua, os dois estimadores dariam o mesmo sinal; eles dão sinais opostos para as duas concentrações, exatamente nas colunas em que o regressando é a proporção de atrasos (Figura 11). A direção do viés é a que a simultaneidade prevê: no OLS a concentração da rota parece reduzir o atraso e a do aeroporto parece aumentá-lo. O 2SGMM devolve os sinais que a teoria espera, e o teste de sobreidentificação não rejeita os instrumentos ($J$ = #nf(st3.at("2").stats.j_stat.published, d: 4), $p$ = #nf(st3.at("2").stats.j_p.published, d: 4) na coluna (2)\; artigo, Tabela 3). É por isso que a replicação da seção 25 trata a inversão como a afirmação mais afiada do artigo e a mais barata de conferir.

== 23. Os dados

// Meses no formato AAAA-MM do guia de estilo (200001 -> 2000-01).
#let ym(v) = { let t = str(v); t.slice(0, 4) + "-" + t.slice(4) }
*Do registro de voo ao painel.* A fonte primária é o Voo Regular Ativo (VRA) da ANAC, via dados.gov.br — o registro operacional que junta o horário aprovado e os Boletins de Alteração de Voo da IAC 1504, uma linha por etapa de voo: #rec.raw.files arquivos CSV mensais de #rec.raw.years.at(0) a #rec.raw.years.at(1), #nf(rec.raw.gigabytes, d: 2) GB, baixados em #nf(rec.raw.fetch_minutes, d: 1) minutos e registrados por sha256 em `data/raw/manifest.json` (`reconstruction.raw`). Os arquivos têm dois layouts — o antigo, até 2009, com o código de justificativa em duas letras, e o novo, de 2010 em diante, com a descrição por extenso, que o staging remapeia aos códigos da IAC 1504 (`data/external/cause_codes.csv`) —, e o staging os traz para um só esquema de #s.registry.columns_by_layer.staged colunas: #miles(rec.staged.rows) etapas de voo em #rec.staged.partitions partições anuais (`reconstruction.staged`). Nos arquivos antigos um voo realizado sem ocorrência vem com o horário realizado vazio; o painel reconstruído o lê como voo pontual, a convenção sobre a qual as tabelas do artigo se apoiam (ADR-0012). O universo é o do artigo (ADR-0002): voos programados dos tipos de linha N, R e E com DI 0, realizados e cancelados; extras e voos de retorno ficam fora. Os aeroportos são agrupados em #rec.panel.nodes nós metropolitanos (ADR-0001): as capitais de um aeroporto só e três nós compostos — São Paulo com Congonhas, Guarulhos e Viracopos; Rio de Janeiro com Galeão e Santos Dumont; Belo Horizonte com Pampulha e Confins —, porque o `f` do artigo é uma contagem metropolitana. O atraso é a diferença entre o horário realizado e o previsto, com sinal — uma chegada adiantada é um atraso negativo —, e o voo conta como atrasado acima de quinze minutos, como no artigo; o limiar de _outlier_ de #nf(rec.fact.outlier_threshold_min, d: 2) minutos aplica-se ao valor absoluto do atraso (ADR-0008, ADR-0015). As empresas viram grupos econômicos datados ao mês por `data/external/groups.csv` (ADR-0003); as três colunas de causa (`prwheather`, `princident`, `pr_connc`) seguem a taxonomia IAC 1504 exatamente como o artigo as define (ADR-0005), e o conjunto de empresas de serviço completo é o do artigo — o grupo TAM, o grupo Varig até 2007-03, Transbrasil e Vasp (ADR-0013). O que o VRA não traz — HHI de passageiros, instrumentos, contagens no pico por capacidade declarada — o painel reconstruído declara sob nome próprio ou deixa nulo (ADR-0007).

#tab((auto, 1fr, auto, auto), (left, left, right, right),
  [camada], [o que é], [linhas × colunas], [tempo medido],
  [`data/raw/`], [os CSV mensais da ANAC, #rec.raw.files arquivos, #nf(rec.raw.gigabytes, d: 2) GB], [—], [#nf(rec.raw.fetch_minutes, d: 1) min],
  [`data/staged/`], [etapas de voo, uma partição por ano], [#miles(rec.staged.rows) × #s.registry.columns_by_layer.staged], [um ano por vez],
  [tabela-fato], [grupo × rota × mês; #miles(rec.fact.route_months) rota-meses; #miles(rec.fact.node_day_hours) nó-dia-horas para a medida de pico; limiar de _outlier_ #nf(rec.fact.outlier_threshold_min, d: 2) min (ADR-0008)], [#miles(rec.fact.rows) × #rec.fact.columns], [#nf(rec.fact.seconds, d: 2) s],
  [painel reconstruído], [rota × mês, #rec.panel.routes rotas, #rec.panel.months meses, #ym(rec.panel.ym_range.at(0)) a #ym(rec.panel.ym_range.at(1))\; projeções cidade × mês (#miles(rec.city_month.rows) × #rec.city_month.columns) e empresa × cidade × mês (#miles(rec.airline_city_month.rows) × #rec.airline_city_month.columns)], [#miles(rec.panel.rows) × #rec.panel.columns], [#nf(rec.panel.seconds, d: 2) s],
  [painel de estimação do artigo], [rota × mês, #ap.routes rotas, #ap.months meses, #ym(ap.ym_range.at(0)) a #ym(ap.ym_range.at(1))\; curado uma vez da base final dos autores, #miles(ap.variables_in_source) variáveis com carimbo de cabeçalho #ap.source_header_timestamp (ADR-0020)], [#miles(ap.rows) × #ap.columns], [—],
)

#v(1mm)
Os números são `reconstruction.*` e `article_panel.*` de `reports/summary.json`, escritos por `airline-delays summary` a partir dos manifestos de `data/analysis/`. A tabela-fato é a única tabela de fatos; o painel e as duas projeções de cidade são agregações testadas dela, nunca uma segunda fonte de verdade.

*O crescimento do período.* Os voos programados do universo por ano civil, realizados e programados (`reconstruction.flights_by_year`)\; a alta de #rec.raw.years.at(0) a #rec.raw.years.at(1) é #nf(rec.flights_growth_pct, d: 1)% (`flights_growth_pct`):

#let fy = rec.flights_by_year.pairs()
#let metade = calc.ceil(fy.len() / 2)
#tab((auto, auto, auto, auto, auto, auto), (left, right, right, left, right, right),
  [ano], [programados], [realizados], [ano], [programados], [realizados],
  ..range(metade).map(i => {
    let e = fy.at(i)
    let esq = (e.at(0), miles(e.at(1).scheduled), miles(e.at(1).realised))
    let dir = if i + metade < fy.len() { let d = fy.at(i + metade); (d.at(0), miles(d.at(1).scheduled), miles(d.at(1).realised)) } else { ("", "", "") }
    esq + dir
  }).flatten(),
)

#v(1mm)
*O painel de estimação do artigo.* É o painel sobre o qual os autores estimaram as Tabelas 2–7, publicado neste repositório em `data/analysis/article_panel_route_month.parquet` sob CC BY 4.0 (ADR-0020): #miles(ap.rows) rota-meses × #ap.columns colunas, todas declaradas na camada `article_panel` de `src/airline_delays/schema/columns.py`. As famílias de colunas: as chaves e a geografia; as contagens de voos sobre as quais toda participação é construída; os #(regressandos_arr.len() + regressandos_dep.len()) regressandos — #regressandos_arr.map(raw).join(", ") e as três variantes de partida; os #exog.len() regressores exógenos — #exog.map(raw).join(", ")\; os #endog.len() termos de concentração endógenos, #endog.map(raw).join(" e "), com o termo alternativo de cidade `gmchhi`; os #instr_all.len() instrumentos; e os componentes das duas binárias de baixo custo (`pres_glo`, `pres_azu`, `olccfu`, `dlccfu`). O que não entra: as dummies de rota, tempo e sazonalidade, que `src/airline_delays/estimation/loader.py` reconstrói exatamente; toda variável de fonte não aberta; e a contabilidade interna da base. `data/analysis/article_panel_manifest.json` registra o sha256 da base de origem e dos dois arquivos publicados e a contagem de nulos por coluna — nunca um caminho.

*O que o painel reconstruído não carrega.* As mesmas definições valem nos dois painéis — universo, mapa de nós, conjuntos de empresas, regras de atraso —, e o que difere é a fonte: os HHI de passageiros e os instrumentos esperam os dados estatísticos da ANAC, as contagens no pico esperam as declarações de capacidade (`docs/data-availability.md`). As colunas do painel de estimação do artigo que o painel reconstruído não traz com valor são, por `reconstruction.article_columns_missing`: #rec.article_columns_missing.map(raw).join(", ") — #rec.article_columns_missing.len() colunas. Cada objeto do modelo tem um endereço no registro, renderizado em `docs/dictionary.md`:

#tab((1fr, auto, 1fr), (left, left, left),
  [objeto do modelo], [no painel de estimação do artigo], [no painel reconstruído],
  [tráfego $F = f_1 + f_2$], [`f`, `dailyfl`], [mesmos nomes e definições],
  [tráfego no pico e fora dele], [`dailyflcong`, `dailyflncong`], [não carregados; o proxy interno p90 tem outro nome (ADR-0007)],
  [o atraso $t(F)$ das incumbentes], [`fsc_oddsarr`, `fsc_minsarr`, `fsc_minsp15arr` e as três de partida], [mesmos nomes e definições (ADR-0013)],
  [o estado do aeroporto, $c(F)$], [`maxprdel`], [`maxprdel_proxy`, sob outro nome],
  [a parcela própria do dano marginal], [`maxcthhi` (e `gmchhi`)], [existe e é nulo; `maxcthhi_flights` é a versão sobre voos],
  [poder de mercado na rota, $d' < 0$], [`rthhi`], [existe e é nulo; `rthhi_flights` é a versão sobre voos],
  [a entrante de baixo custo], [`lcc`, `maxalccfu`], [mesmos nomes, lidos da operação no VRA e não da venda de bilhetes],
  [a reação da seguidora, $-lambda$], [os #instr_all.len() instrumentos], [não carregados: derivam dos HHI de passageiros],
)

#v(1mm)
O registro de colunas `src/airline_delays/schema/columns.py` é a única origem de toda coluna: #s.registry.columns_total colunas em #s.registry.layers camadas (`registry`), e nenhuma existe sem uma entrada nele.

#let camada_pt = (
  staged: "etapas de voo (staged)",
  fact: "tabela-fato grupo × rota × mês",
  city: "projeção cidade × mês",
  airline_city: "projeção empresa × cidade × mês",
  panel: "painel reconstruído rota × mês",
  article_panel: "painel de estimação do artigo",
  ml: "tabela por voo do preditor",
)
#tab((auto, 1fr, auto), (left, left, right),
  [camada], [o que é], [colunas],
  ..s.registry.columns_by_layer.pairs().map(p => (raw(p.at(0)), camada_pt.at(p.at(0), default: p.at(0)), str(p.at(1)))).flatten(),
)

== 24. Especificação e identificação

A unidade de observação é a rota-mês, $r t$, e a equação estimada nas Tabelas 3–7 é, para cada regressando $y$,

$ y_(r t) = x'_(r t) beta + gamma_1 "rthhi"_(r t) + gamma_2 "maxcthhi"_(r t) + delta_1 "lcc"_(r t) + delta_2 "maxalccfu"_(r t) + alpha_r + theta_t + phi_(g(r), m(t)) + epsilon_(r t) , $

com $x_(r t)$ os #(exog.len() - lcc_terms.len()) controles exógenos, $alpha_r$ o efeito fixo de rota, $theta_t$ o de mês-calendário, $phi_(g(r), m(t))$ a sazonalidade região × mês do ano — uma dummy por região tocada pela rota e por mês do ano — e `rthhi` e `maxcthhi` instrumentadas. Os *regressandos* são três medidas do atraso de chegada das empresas de serviço completo — #regressandos_arr.map(raw).join(", "): ODDS, o logaritmo da razão de chances $ln [p slash (1 - p)]$ da proporção $p$ de chegadas com mais de quinze minutos de atraso, que não existe quando $p$ é 0 ou 1 — e é por isso que o filtro de amostra morde por ela; MINS, os minutos médios de atraso; MINS > 15, os minutos além de quinze — e as três medidas de partida correspondentes, #regressandos_dep.map(raw).join(", "), usadas na Tabela 7. Os *regressores exógenos* são #exog.len(): #exog.map(v => raw(v) + " (" + nome_var(v) + ")").join(", "). As *endógenas* são #endog.len(): #endog.map(raw).join(" e "). Os *instrumentos excluídos* são #instr_all.len() colunas do tipo Hausman, em duas listas que os do-files não unificam: o bloco ODDS usa #instr_odds.len() — #instr_odds.map(raw).join(", ") —, e o bloco MINS usa #instr_mins.len() — #instr_mins.map(raw).join(", "). Com #endog.len() endógenas, o $J$ de Hansen tem #(instr_odds.len() - endog.len()) graus de liberdade no bloco ODDS e #(instr_mins.len() - endog.len()) no bloco MINS; invertendo os pares ($J$, $p$) publicados, os graus de liberdade implícitos batem com as duas listas — a evidência mais forte de que os do-files que geraram as tabelas são os que a especificação reproduz. As constantes vivem em `src/airline_delays/estimation/specification.py`.

*Estimadores.* 2SGMM — GMM em dois estágios com matriz de ponderação ótima robusta a heterocedasticidade e autocorrelação — nas Tabelas 3, 4 e 7; LIML na Tabela 5, mesma amostra e mesmos regressores; OLS na Tabela 6 e na coluna (4) da Tabela 4, a única coluna sem estatísticas de identificação. Os erros-padrão são HAC com kernel de Bartlett e largura de banda #est.bandwidth na convenção do `linearmodels`, que pesa a defasagem $j$ por $1 - j slash (b w + 1)$ — equivale ao `bw(5)` do `ivreg2`, que é o $T^(1 slash 3)$ com $T = #amostra.months$ meses que o artigo declara (`estimation.bandwidth`, `estimation.sample.months`). A correção de amostra finita está #if res.meta.debiased [ligada] else [desligada], porque o `ivreg2` só imprime a estatística F das tabelas publicadas com a opção `small`; as dummies sazonais #if res.meta.with_seasonality [entram] else [não entram], porque o artigo fala em _seasonality controls_ e incluí-las aproxima mensuravelmente os coeficientes — a escolha fica exposta e medida nos dois sentidos na seção 25. Os efeitos fixos entram explicitamente, como nos do-files: dummies de rota (uma omitida contra a constante) e de mês, com as colunas exatamente colineares removidas por QR revelador de posto.

*A amostra, na ordem exata dos do-files* (`estimation.sample`):

#tab((auto, 1fr, auto, auto), (left, left, right, right),
  [passo], [o que faz], [observações], [rotas],
  [painel de estimação do artigo], [#ym(ap.ym_range.at(0)) a #ym(ap.ym_range.at(1)), todas as rotas], miles(amostra.n_raw), str(amostra.routes_raw),
  [#raw("drop if " + res.meta.sample.filter_regressand + " == .")], [remove a rota-mês sem o regressando das colunas (1) e (2), para que as seis colunas de uma tabela rodem sobre a mesma amostra], miles(amostra.n_after_missing_regressand), "—",
  [#raw("drop if _count_k <= " + str(res.meta.sample.singleton_cutoff))], [remove a rota com #res.meta.sample.singleton_cutoff ou menos observações; as dummies de rota e de tempo são recriadas depois do corte], miles(amostra.n_after_singleton_cut), str(amostra.routes),
)

#v(1mm)
A Tabela 7 troca o filtro por `fsc_oddsdep`, e é por isso que o seu $N$ publicado é #miles(rep.table7.n_obs.at("1").published) e #miles(rep.table7.n_obs.at("3").published), e não #miles(rep.table3.n_obs.at("1").published) e #miles(rep.table3.n_obs.at("3").published) (artigo, Tabelas 3 e 7). As colunas (1) e (2) perdem ainda as rota-meses em que os instrumentos defasados não existem — o primeiro mês de cada rota no painel —, e por isso o seu $N$ reestimado é #miles(rep.table3.n_obs.at("1").replicated), contra #miles(rep.table3.n_obs.at("3").replicated) nas colunas em minutos (`reports/replication/summary.json`, `table3.n_obs`); a coluna (4) da Tabela 4, OLS sem concentrações, não precisa dos instrumentos e é a única da tabela com a amostra maior. As dummies de tempo e as sazonais região × mês são reconstruídas a partir de `ym`, `o_region` e `d_region` em `src/airline_delays/estimation/loader.py`, em vez de lidas do painel; na coluna (1) da Tabela 3 o desenho tem #grid_.cells.find(c => c.column == 1 and c.with_seasonality).stats.n_params parâmetros com as sazonais e #grid_.cells.find(c => c.column == 1 and not c.with_seasonality).stats.n_params sem elas (`reports/replication/sensitivity.json`).

*Kleibergen–Paap.* Nenhum pacote Python implementa a estatística `rk` de Kleibergen e Paap (2006), a que as tabelas publicadas chamam _KP statistic_; `src/airline_delays/estimation/kp.py` a escreve a partir do artigo. A validação não depende de outra implementação da mesma coisa: com a covariância dos coeficientes da forma reduzida na forma i.i.d., a matriz de ponderação do meio da forma quadrática vira a identidade e, na hipótese de subidentificação $q = k_2 - 1$, a versão _Wald_ tem de colapsar na estatística de Cragg–Donald $N lambda slash (1 - lambda)$ e a versão _LM_ na estatística de correlação canônica de Anderson $N lambda$, com $lambda$ a menor correlação canônica ao quadrado. As duas identidades valem até a precisão de máquina (`tests/test_estimation_kp.py`) contra uma implementação que não compartilha código com a primeira. Contra os valores publicados, nas colunas ODDS a implementação acerta o nível e a estrutura interna; nas colunas MINS, com #instr_mins.len() instrumentos e #endog.len() endógenas, o sistema é quase exatamente identificado e a estatística fica muito mais sensível ao tamanho da amostra. A Tabela 3, coluna a coluna (`reports/replication/results.json`):

#tab((auto, auto, auto, auto, auto, auto, auto), (left, left, right, right, right, right, right),
  [col.], [regressando], [KP LM pub.], [KP LM rep.], [Weak KP F pub. / rep.], [$J$ pub. / rep.], [$p$ do $J$ pub. / rep.],
  ..st3.pairs().map(p => {
    let c = p.at(1)
    let stt = c.stats
    ("(" + p.at(0) + ")", c.published_regressand,
     nf(stt.kp_lm.published, d: 2), nf(stt.kp_lm.replicated, d: 2),
     nf(stt.weak_kp_f.published, d: 2) + " / " + nf(stt.weak_kp_f.replicated, d: 2),
     nf(stt.j_stat.published, d: 3) + " / " + nf(stt.j_stat.replicated, d: 3),
     nf(stt.j_p.published, d: 3) + " / " + nf(stt.j_p.replicated, d: 3))
  }).flatten(),
)

== 25. Resultados e replicação

*A leitura econômica.* A especificação de base é a coluna (2) da Tabela 3: 2SGMM, regressando ODDS, com as binárias de baixo custo. Lida ao lado da coluna (2) da Tabela 6 — a mesma especificação por OLS —, ela contém o argumento inteiro do artigo (`published.table3.col2`, `published.table6.col2`):

#let pub_vars = ("rthhi", "maxcthhi", "lcc", "maxalccfu")
#tab((1fr, auto, auto), (left, right, right),
  [regressor], [2SGMM (artigo, Tabela 3, col. 2)], [OLS (artigo, Tabela 6, col. 2)],
  ..pub_vars.map(v => ([`#v`, #nome_var(v)], coef(pub3.at(v)), coef(pub6.at(v)))).flatten(),
  [$N$], miles(pub3.n_obs), miles(pub6.n_obs),
)

#v(1mm)
Erros-padrão entre parênteses; as estrelas são os níveis de significância do artigo. Instrumentada a concentração, mais concentração na cidade-extremo mais concentrada da rota vem com menos atraso das empresas de serviço completo — a dominante internaliza o congestionamento que impõe a si mesma (H1)\; mais concentração na própria rota vem com mais atraso — na rota, o canal é a qualidade da concorrência (H2)\; uma empresa de baixo custo numa das cidades-extremo reduz o atraso das incumbentes, o _spillover_ não-preço do título, enquanto a sua presença na rota em si não é significante para as chances de atraso (H3). A inversão de sinal dos dois HHI entre OLS e 2SGMM é o argumento identificador do artigo, e é a primeira coisa que a replicação confere.

*O que "replicar" significa aqui, e o placar.* As Tabelas 2–7 são reestimadas sobre o mesmo painel em que os autores estimaram — o painel de estimação do artigo —, com os filtros de amostra na ordem do código dos autores e a especificação da seção 24 portada do Stata para Python, por `airline-delays estimate`, e comparadas célula a célula com as tabelas publicadas. A régua é uma só: a diferença entre o coeficiente reestimado e o publicado, medida em erros-padrão publicados. Acima de cerca de dois erros-padrão duas estimativas seriam materialmente diferentes; a menos de meio, contam a mesma história. "Acompanha de perto" quer dizer exatamente isso — o mesmo sinal e a mesma ordem de grandeza em quase todas as células, e nenhuma célula a mais de um erro-padrão publicado —, e não "reproduz exatamente": a amostra reestimada é maior que a publicada, o kernel HAC e a correção de amostra finita seguem convenções de software que se traduzem, não se copiam, e a decisão sobre as dummies sazonais teve de ser tomada e medida (`estimation.tables`, `reports/replication/summary.json`).

#let tabelas_reg = ("table3", "table4", "table5", "table6", "table7")
#let titulos = (
  table3: [Tabela 3 — 2SGMM, chegadas],
  table4: [Tabela 4 — robustez, 2SGMM],
  table5: [Tabela 5 — LIML],
  table6: [Tabela 6 — OLS],
  table7: [Tabela 7 — 2SGMM, partidas],
)
#let j_cols = tabelas_reg.map(t => res.at(t).comparison.values().filter(c =>
  "j_p" in c.stats and c.stats.j_p.at("published", default: none) != none
  and c.stats.j_p.at("replicated", default: none) != none
)).flatten()
#let j_cols_len = j_cols.len()
#let j_same = j_cols.filter(c => (c.stats.j_p.published < 0.05) == (c.stats.j_p.replicated < 0.05)).len()
#let j_rej = j_cols.filter(c => c.stats.j_p.published < 0.05).len()
#tab((auto, auto, auto, auto, auto, auto, auto), (left, right, right, right, right, right, right),
  [tabela], [coef.], [sinais iguais], [a menos de ½ e.p.], [mediana dif/e.p.], [máx. dif/e.p.], [mediana da razão de e.p.],
  ..tabelas_reg.map(t => {
    let e = est.tables.at(t)
    let r = rep.at(t)
    (
      titulos.at(t),
      str(e.n_coefficients),
      str(e.sign_agreement) + "/" + str(e.n_coefficients),
      str(e.within_half_se) + "/" + str(e.n_coefficients) + " (" + pct(r.within_half_se_share, d: 0) + ")",
      nf(e.median_difference_in_se, d: 3),
      nf(e.max_difference_in_se, d: 3),
      nf(e.median_se_ratio, d: 3),
    )
  }).flatten(),
)

#v(1mm)
#chave("O que bate")[
  Dos #tot.coefficients coeficientes das cinco tabelas de regressão, #tot.sign_agreement têm o sinal publicado e #tot.within_half_se (#nf(tot.within_half_se_pct, d: 1)%) ficam a menos de meio erro-padrão publicado; o maior desvio isolado é #nf(tot.max_difference_in_se, d: 2) erro-padrão (`estimation.totals`). A razão mediana de erros-padrão abaixo de 1 em todas as tabelas diz que os erros-padrão reestimados são sistematicamente _menores_ que os publicados. Nas #j_cols_len colunas que reportam o $J$ de Hansen, o veredito a 5% é o mesmo no publicado e no reestimado em #j_same delas: #j_rej rejeitam ortogonalidade nos dois casos, e as demais não rejeitam nos dois (`reports/replication/results.json`).
]

*Célula a célula, onde importa.* As células que sustentam a leitura econômica, publicadas e reestimadas, com a diferença em erros-padrão publicados (`reports/replication/results.json`):

#let rotulo_tab = (table3: "Tabela 3", table4: "Tabela 4", table5: "Tabela 5", table6: "Tabela 6", table7: "Tabela 7")
#let estimador_pt = (gmm2s: "2SGMM", liml: "LIML", ols: "OLS")
#let celulas_chave = (("table3", "2"), ("table3", "4"), ("table6", "2"))
#tab((auto, auto, auto, auto, auto), (left, left, right, right, right),
  [tabela, coluna], [regressor], [publicado \[e.p.\]], [reestimado \[e.p.\]], [dif/e.p.],
  ..celulas_chave.map(tc => {
    let comp = res.at(tc.at(0)).comparison.at(tc.at(1))
    pub_vars.filter(v => v in comp.coefficients).map(v => {
      let e = comp.coefficients.at(v)
      (rotulo_tab.at(tc.at(0)) + ", (" + tc.at(1) + ") " + comp.published_regressand + ", " + estimador_pt.at(comp.estimator, default: comp.estimator),
       raw(v),
       sgn(e.published_b) + " [" + nf(e.published_se, d: 3) + "]",
       sgn(e.replicated_b) + " [" + nf(e.replicated_se, d: 4) + "]",
       nf(e.difference_in_se, d: 2))
    })
  }).flatten(),
)

#let discordantes = ()
#let maxcel = none
#for t in tabelas_reg {
  for (c, comp) in res.at(t).comparison.pairs() {
    for (v, e) in comp.coefficients.pairs() {
      if e.at("sign_agrees", default: true) == false { discordantes.push((t: t, c: c, v: v, e: e)) }
      let d = e.at("difference_in_se", default: none)
      if d != none and (maxcel == none or d > maxcel.d) { maxcel = (t: t, c: c, v: v, d: d, e: e) }
    }
  }
}
#v(1mm)
Os quatro coeficientes de estrutura de mercado da coluna de base saem com o sinal publicado; nas colunas em minutos os coeficientes reestimados das duas concentrações são menores em valor absoluto que os publicados, com o mesmo sinal. A maior diferença isolada em todo o conjunto é #nf(maxcel.d, d: 2) erro-padrão publicado: #raw(maxcel.v) na coluna (#maxcel.c) da #rotulo_tab.at(maxcel.t), #sgn(maxcel.e.published_b) (#nf(maxcel.e.published_se, d: 3)) publicado contra #sgn(maxcel.e.replicated_b) reestimado. Dos #tot.coefficients coeficientes, #discordantes.len() saem com sinal diferente do publicado (`estimation.totals.sign_agreement` vale #tot.sign_agreement); os #discordantes.len() são coeficientes muito menores que o seu próprio erro-padrão publicado, sem estrela no artigo, e nenhum é um regressor de estrutura de mercado com estrela — um coeficiente que vale uma fração pequena do seu erro-padrão não tem sinal no sentido estatístico:

#tab((auto, auto, auto, auto, auto), (left, left, right, right, right),
  [tabela, coluna], [regressor], [publicado \[e.p.\]], [reestimado], [dif/e.p.],
  ..discordantes.map(x => (
    rotulo_tab.at(x.t) + ", (" + x.c + ")", raw(x.v),
    sgn(x.e.published_b) + " [" + nf(x.e.published_se, d: 3) + "]",
    sgn(x.e.replicated_b), nf(x.e.difference_in_se, d: 2),
  )).flatten(),
)

#v(1mm)
*A inversão de sinal dos HHI.* O padrão da Figura 11 é conferido nas #hhi.n_comparisons comparações OLS × 2SGMM dos dois índices — #hhi.n_comparisons células, dois índices vezes seis colunas. Na tabela publicada a inversão ocorre nas #hhi.n_inverted_published células das colunas (#hhi.columns_with_inversion.join(") e (")), regressando ODDS, e em nenhuma coluna MINS, onde OLS e 2SGMM já saem com o mesmo sinal e só a magnitude muda; na reestimação as #hhi.n_inversion_replicates inversões reaparecem e o padrão — haver ou não inversão — coincide em #hhi.n_pattern_agrees das #hhi.n_comparisons (`estimation.hhi`; `reports/replication/summary.json`, `hhi_sign_inversions`):

#tab((auto, auto, auto, auto, auto, auto, auto, auto), (left, left, left, right, right, right, right, center),
  [col.], [regressando], [variável], [OLS pub.], [2SGMM pub.], [OLS rep.], [2SGMM rep.], [inversão pub. / rep.],
  ..rep.hhi_sign_inversions.detail.map(d => (
    "(" + d.column + ")", d.regressand, raw(d.variable),
    sgn(d.published.ols), sgn(d.published.gmm), sgn(d.replicated.ols), sgn(d.replicated.gmm),
    nf(d.published.inverted) + " / " + nf(d.replicated.inverted),
  )).flatten(),
)

#v(1mm)
*A Tabela 2.* As estatísticas descritivas das #est.table2.n_variables variáveis são o que prova a identificação de cada variável do código com a coluna do artigo, em vez de supô-la: os mínimos e máximos coincidem até a quarta casa, e o triângulo de #est.table2.n_correlations correlações fecha com diferença absoluta mediana #nf(est.table2.median_abs_correlation_difference, d: 3) e máxima #nf(est.table2.max_abs_correlation_difference, d: 3) (`estimation.table2`). Publicado e reestimado, sobre a amostra filtrada (artigo, Tabela 2; `reports/replication/results.json`):

#let t2 = res.table2
#let comp2 = t2.comparison
#tab((2.6fr,) + (1fr,) * 8, (left, right, right, right, right, right, right, right, right),
  [variável], [média pub.], [média rep.], [d.p. pub.], [d.p. rep.], [mín. pub.], [mín. rep.], [máx. pub.], [máx. rep.],
  ..t2.published.variables.map(v => (
    nome_var(v),
    nf(comp2.univariate.mean.at(v).published, d: 2), nf(comp2.univariate.mean.at(v).replicated, d: 4),
    nf(comp2.univariate.sd.at(v).published, d: 2), nf(comp2.univariate.sd.at(v).replicated, d: 4),
    nf(comp2.univariate.min.at(v).published, d: 2), nf(comp2.univariate.min.at(v).replicated, d: 4),
    nf(comp2.univariate.max.at(v).published, d: 2), nf(comp2.univariate.max.at(v).replicated, d: 4),
  )).flatten(),
)

#v(1mm)
*Nota sobre a amostra.* As tabelas publicadas reportam entre #miles(est.n_obs_published_range.at(0)) e #miles(est.n_obs_published_range.at(1)) observações; a reestimação sobre o painel de estimação do artigo, com os filtros da seção 24, dá entre #miles(est.n_obs_replicated_range.at(0)) e #miles(est.n_obs_replicated_range.at(1)), #nf(est.n_obs_excess_pct, d: 1)% a mais (`estimation.n_obs_published_range`, `n_obs_replicated_range`, `n_obs_excess_pct`). Os dois valores ficam registrados lado a lado em cada coluna de `reports/replication/tables.md`, e nenhum filtro é reconstruído para aproximá-los (ADR-0020). A estatística F das tabelas publicadas não é reproduzida: o F do `ivreg2` é o Wald conjunto de todos os regressores, dummies incluídas, sob convenção própria, e o análogo do `linearmodels` não mede a mesma coisa — a célula fica vazia de propósito. O $J$ de Hansen, o $R^2$ ajustado e o RMSE de cada coluna estão em `reports/replication/tables.md`, publicado e reestimado lado a lado; o relatório técnico completo, com as cinco tabelas célula a célula, é `reports/pdf/replication.pdf`.

*Sensibilidade.* Um eixo: as dummies sazonais região × mês, interruptor puro de especificação, nas colunas (1) e (2) da Tabela 3 (`reports/replication/sensitivity.json`). Nenhum sinal muda. O limiar de _outlier_ do atraso (ADR-0008) não varia aqui: ele age no nível do voo, antes de agregar, e o painel de estimação do artigo chega agregado.

#tab((auto, auto, auto, auto, auto, auto, auto), (right, center, right, right, right, right, right),
  [col.], [sazonais], [$N$], [`rthhi`], [`maxcthhi`], [$R^2$ aj.], [$J$],
  ..grid_.cells.map(c => (
    "(" + str(c.column) + ")",
    nf(c.with_seasonality),
    miles(c.stats.n_obs),
    sgn(c.b.at("rthhi", default: none)) + " [" + nf(c.se.at("rthhi", default: none), d: 4) + "]",
    sgn(c.b.at("maxcthhi", default: none)) + " [" + nf(c.se.at("maxcthhi", default: none), d: 4) + "]",
    nf(c.stats.adj_r2, d: 4), nf(c.stats.j_stat, d: 4),
  )).flatten(),
)

#v(1mm)
*O que 2013 estimou e o que 2016 estimou.* A monografia de graduação do autor (USP, 2013) — documento externo, citado e não redistribuído — estimou a mesma pergunta em outro desenho: um painel empresa × rota × mês, com a parcela de voos atrasados acima de trinta minutos como dependente, um HHI de rota sobre voos planejados e uma razão de concentração das duas maiores no aeroporto; encontrou coeficientes positivos e significantes para as duas medidas de concentração, um efeito ambíguo para a presença da Gol e um efeito negativo para a Azul no seu próprio aeroporto, e leu as concentrações como uma "tragédia dos comuns" (monografia, seções 5 a 7 — documento externo). O artigo estimou um painel rota × mês, com o atraso das empresas de serviço completo acima de quinze minutos, HHI de passageiros, 2SGMM com instrumentos e erros-padrão HAC. Os coeficientes não se comparam — unidade de observação, base do HHI, estimador, regressando e limiar de atraso diferem —, e por isso a regressão da monografia não é reestimada aqui nem o seu sinal de concentração é posto ao lado do do artigo como se fosse a mesma grandeza (`docs/notes/monografia-2013.md`). O que se compara é a pergunta, e ela é a mesma; o que o painel reconstruído oferece de comparável é a construção — `rthhi_flights`, o HHI de rota sobre voos programados, e `fsc_prdelarr30m`, o corte de trinta minutos.

== 26. A recepção: o que o campo levou e o que continua em aberto

O artigo deixou três coisas na literatura, e as três têm uma seção atrás de si neste estudo. *A separação entre concentração da rota e concentração do aeroporto.* O artigo testa, numa só equação, o poder de mercado onde a empresa vende (`rthhi`) e a internalização onde ela congestiona (`maxcthhi`), com sinais esperados distintos e um desenho de identificação para os dois (seções 22 e 24). É a peça que os trabalhos posteriores mais reaproveitam, porque converte a pergunta do debate da seção 6 — quem internaliza, e quanto — em algo estimável com dados de operação. *A internalização medida no atraso.* O coeficiente negativo e significante de `maxcthhi` no 2SGMM (seção 25) é a Proposição 1 da seção 16 vista nos dados: a empresa dominante do aeroporto sofre a maior parte do congestionamento que causa e programa com mais cuidado. É o achado pelo qual o artigo entra no debate da internalização ao lado dos trabalhos que medem o mesmo objeto no atraso, entre eles Ater (2012). *O derrame não-preço da entrada de baixo custo.* A presença de uma empresa de baixo custo numa cidade-extremo reduz o atraso das incumbentes em rotas em que a entrante não voa (`maxalccfu`). É o título do artigo e a Pressuposição 3 da monografia tornada regressor; dos três, é o achado de mecanismo menos fechado — a seção 20 mostra que "internalizar" tem mais de uma margem. A recepção medida — quantos trabalhos citam o artigo, por qual dos três achados e com que fidelidade — é objeto de um projeto irmão do autor, #link("https://github.com/wbendinelli/citation-audit")[`citation-audit`], com método e números próprios; eles são atualizados lá e não são impressos por nenhum artefato deste repositório, e por isso este estudo não os transcreve.

*O artigo que levou a formulação aos preços.* Guo, Jiang e Wan (2018) constroem sobre a separação acima e mudam o teste de lugar, do atraso para a tarifa (seção 21): uma empresa que internaliza carrega na sua tarifa a parcela própria do dano marginal escrita em passageiros, observável como a interação entre atraso e tráfego próprio numa regressão de tarifas. Encontram que as empresas de serviço completo internalizam via preço e as de baixo custo não, e explicam a diferença pela escolha de aeroportos menos congestionados (Gudmundsson, Paleari e Redondi 2014), não por comportamento. A crítica ao artigo recai sobre o desenho, não sobre o achado: controlar por tráfego do aeroporto remove, junto com o efeito residual de mercado, a parte da internalização que opera por redução de tráfego via preço maior; o que sobra medido no atraso é a reprogramação de horários. Lido ao lado do artigo, o resultado obriga a reler a Pressuposição 3 pelas três margens da seção 20 — reprogramar, reduzir tráfego via preço, escolher o aeroporto —, sob as quais "a entrante de baixo custo internaliza" e "as de baixo custo não internalizam via preço" deixam de ser contraditórios. A leitura é hipótese, não resultado: testá-la exige separar as três margens no mesmo painel, e isso pede tarifas.

*O que continua em aberto.* Cada pergunta tem, no Apêndice D da edição em Markdown deste estudo (`docs/study/apendice-d-extensoes.md`), o que já existe para construí-la e o que falta:

#tab((1fr, 1fr, 1fr), (left, left, left),
  [pergunta], [o que falta], [ponto de partida neste repositório],
  [a internalização nos preços, e as três margens], [os microdados tarifários da ANAC (`docs/data-availability.md`)], [as chaves `route` e `ym` do painel reconstruído, prontas para uma junção por rota-mês],
  [o HHI ponderado por passageiros, e os instrumentos, no painel reconstruído], [os dados estatísticos da ANAC], [`passenger_weighted_hhi()` com a assinatura certa; `rthhi_flights` e `maxcthhi_flights` ao lado],
  [o clima medido, e não inferido do código de justificativa], [METAR da REDEMET/DECEA], [a chave estação × hora já existe nas etapas de voo],
  [desenhos no nível do aeroporto, com Viracopos separado de São Paulo], [uma agregação por `origin_icao` e `dest_icao`, não por nó], [as duas colunas estão em toda etapa de voo de `data/staged/`],
  [curto e longo prazo do efeito de baixo custo], [um par de regressores que separe entrada recente de presença consolidada], [`is_entry`, `entry_lcc` e as datas de `data/external/groups.csv`],
  [a pergunta da monografia de 2013, no seu grão], [a binária da Azul no próprio aeroporto, assentos, clima mensal, conexões], [a tabela-fato no grão empresa × rota × mês, `arr_delayed_gt30`, `rthhi_flights`; a nota `docs/notes/monografia-2013.md`],
)

#v(1mm)
Nenhuma dessas extensões foi implementada neste estudo; descrever o caminho não é percorrê-lo. O passo de maior alcance são os dados estatísticos da ANAC: com eles a especificação da seção 24 passa a poder rodar sobre os dois painéis, e a comparação entre eles deixa de ser uma comparação de definições para ser uma comparação de estimativas. Esta seção descreve a recepção do artigo, não a deste repositório, que é novo; ela não conta citações e não reestima nada.

= Apêndice A — As identidades verificadas

#m.meta.n_identities afirmações algébricas, cada uma verificada com `sympy` #m.meta.sympy em `src/airline_delays/theory/model.py` e presa por `tests/test_theory.py`; as #m.meta.n_identities valem (`theory.n_holding` vale #s.theory.n_holding). Uma identidade "valer" significa que a afirmação decorre dos pressupostos da seção 9 — `sympy` prova álgebra, não economia. A coluna "origem" diz de quem é a afirmação; a coluna "fecha" é a chave `holds` de cada uma. Os números da Parte II saem de `src/airline_delays/theory/equilibrium.py` por outro caminho — busca de raiz em intervalo delimitado para a seguidora e, por cima dela, para a líder —, e `tests/test_theory.py` prende os dois caminhos um ao outro e ao relatório versionado: uma edição em `src/airline_delays/theory/` sem regerar `reports/theory/` deixa a suíte vermelha.

#let afirmacao_pt = (
  eq6_social_foc: [a condição eficiente é $p - tau - [F c' + c] slash s = 0$],
  eq7_follower_foc: [a condição da seguidora é $p - tau - [f_2 c' + c] slash s = 0$],
  eq8_reaction_slope: [$partial f_2 slash partial f_1 = -(f_2 c'' + c') slash (f_2 c'' + 2 c')$],
  eq8_lambda_of_x: [$lambda = (1 + x) slash (2 + x)$ com $x = f_2 c'' slash c'$],
  eq8_lambda_minus_half: [$lambda - 1 slash 2 = x slash (2 (2 + x)) >= 0$, logo $lambda >= 1 slash 2$],
  eq8_one_minus_lambda: [$1 - lambda = 1 slash (2 + x) > 0$, logo $lambda < 1$],
  eq8_lambda_half_when_linear: [$lambda = 1 slash 2$ exatamente quando $c'' = 0$],
  eq9_leader_foc: [a condição da líder é $p - tau - [f_1 c' (1 + partial f_2 slash partial f_1) + c] slash s = 0$],
  f1_over_f2: [num mesmo ponto, (7) e (9) dão $f_1 = f_2 slash (1 - lambda)$ e $f_1 - 2 f_2 = f_2 x >= 0$],
  eq10_gap: [$F c' - f_1 c' (1 - lambda) = (f_2 + lambda f_1) c'$],
  eq10_two_forms: [$(f_2 - f_1 partial f_2 slash partial f_1) c' = (f_2 + lambda f_1) "MCD" slash (f_1 + f_2)$ quando $partial f_2 slash partial f_1 = -lambda$],
  eq11_symmetric: [em $f_1 = f_2 = f^*$: $T_1^* = 1/2 (1 + lambda^*) "MCD"^*$],
  eq11_linear_3_4: [com $c'' = 0$ ($lambda^* = 1 slash 2$) a tarifa da líder é $3 slash 4$ de $"MCD"^*$, a meio caminho entre a de Cournot ($1 slash 2$) e a atomística (1)],
  eq11_follower_half: [a tarifa da seguidora, $F c' - f_2 c' = f_1 c'$, é $1/2 "MCD"^*$ no ótimo simétrico],
  monopoly_foc_is_social: [a condição do monopolista coincide com a eficiente (internalização completa)],
  cournot_toll_half_at_symmetry: [a tarifa de um duopolista de Cournot é os voos da rival vezes $c'$: $1/2 "MCD"$ na simetria],
  eq12_leader_foc: [com $p = d(s F)$: $d + s f_1 d' (1 + partial f_2 slash partial f_1) - tau - [f_1 c' (1 + partial f_2 slash partial f_1) + c] slash s = 0$],
  eq12_social_foc: [a condição eficiente sob demanda inelástica é $d - tau - [F c' + c] slash s = 0$],
  eq12_limit_minus_1: [em $partial f_2 slash partial f_1 = -1$ a condição colapsa em $d - tau - c slash s = 0$],
  eq12_limit_minus_half: [em $partial f_2 slash partial f_1 = -1 slash 2$: $d + s f_1 d' slash 2 - tau - (f_1 c' slash 2 + c) slash s = 0$],
  lambda_inelastic_general: [sob $p = d(s F)$, $partial f_2 slash partial f_1 = -A slash B$ com $B = A + c' slash s - s d'$, e $-partial f_2 slash partial f_1 - 1 slash 2 = f_2 (c'' slash s - s^2 d'') slash (2 B)$: o limite vale se e somente se $c'' slash s >= s^2 d''$],
  lambda_linear_demand: [com $d'' = 0$: $partial f_2 slash partial f_1 = -(k + f_2 c'') slash (2 k + f_2 c'')$, $k = c' - s^2 d' > 0$, e os limites do caso elástico valem],
  linear_F_star: [$c = a + b F$: o total eficiente é $D slash (2 b)$],
  linear_cournot: [$c = a + b F$: cada duopolista de Cournot voa $D slash (3 b)$],
  linear_stackelberg: [$c = a + b F$: a líder voa $D slash (2 b)$ e a seguidora $D slash (4 b)$],
  linear_atomistic: [$c = a + b F$: as atomísticas voam $D slash b$ no total, o dobro do eficiente],
  linear_welfare_losses: [$c = a + b F$: a perda é $1 slash 9$ de $W^*$ sob Cournot, $1 slash 4$ sob Stackelberg e tudo sob atomismo],
  inelastic_linear_closed_forms: [$c = a + b F$, $d = d_0 - d d dot Q$: $f_1 = D_p slash (2 m)$, $f_2 = D_p slash (4 m)$, $F^* = D_p slash (s^2 d d + 2 b)$],
  T1_equals_T2_at_stackelberg: [em qualquer equilíbrio de Stackelberg $f_2 = (1 - lambda) f_1$, logo $T_1 = T_2 = f_1 c'$],
)
#let equacao_pt(e) = if e == "benchmark" { "referência" } else { e }
#tab((auto, auto, auto, auto, 1fr), (left, left, left, center, left),
  [id], [equação], [origem], [fecha], [afirmação],
  ..m.identities.map(i => (raw(i.id), equacao_pt(i.equation), rot(i.origin), nf(i.holds), afirmacao_pt.at(i.id, default: i.statement))).flatten(),
)

= Apêndice B — Como reproduzir

O ambiente é Python gerido pelo `uv`, `just` como executor de receitas e `typst` no PATH só para compilar os PDF; a CLI é `airline-delays <etapa>`, e cada receita do `justfile` embrulha um comando dela. Quatro comandos refazem tudo o que este estudo cita, e os tempos são os medidos e gravados em `reports/summary.json`, com a chave ao lado.

#tab((auto, 1fr, auto), (left, left, left),
  [comando], [o que faz], [tempo medido],
  [`just demo`], [a menor reprodução: a cadeia de ponta a ponta sobre a amostra versionada em `tests/fixtures/` — #miles(s.fixture.legs) etapas de voo de #s.fixture.routes rotas nos anos de #s.fixture.years.map(str).join(", ") (`fixture`) —, das etapas staged à tabela-fato, ao painel reconstruído e à Tabela 2, sem rede, escrevendo só sob `data/derived/demo/`], [cerca de um segundo],
  [`just estimate`], [reestima as Tabelas 2–7 sobre o painel de estimação do artigo, compara célula a célula com as tabelas publicadas e escreve `reports/replication/results.json`, `summary.json`, `sensitivity.json` e `tables.md` (seções 24 e 25)], [#nf(est.seconds, d: 1) s (`estimation.seconds`)],
  [`just theory`], [deriva o modelo com `sympy`, confere as #m.meta.n_identities identidades, desenha as #s.theory.n_figures figuras e escreve `reports/theory/model.json`, `figures.json`, `figures/*.svg` e `results.md`, sem carimbo de tempo — uma segunda rodada sobre uma árvore inalterada não muda nada (Partes I e II, seção 22, Apêndice A)], [cerca de um segundo],
  [`just report`], [compila as três fontes Typst de `reports/` — este estudo, `reports/replication.typ` e `reports/prediction.typ` — em `reports/pdf/`, versionado (ADR-0022), com o carimbo de criação tomado do commit da fonte; `uv run airline-delays report --only study` compila só este documento], [segundos],
)

#v(1mm)
`just summary` reescreve `reports/summary.json`, o único lugar de onde as páginas de entrada e este estudo tiram números-manchete; `uv run airline-delays summary --check` falha quando o arquivo versionado difere de uma reconstrução. A cadeia completa, dos arquivos da ANAC aos relatórios, roda numa única máquina de trabalho, um ano por vez, nunca duas varreduras completas de `data/raw/` ao mesmo tempo (`just pipeline-full`; `just pipeline` parte de `data/staged/`):

#tab((auto, auto, 1fr, auto), (left, left, left, right),
  [etapa], [receita], [lê → escreve], [tempo medido (chave)],
  [ingestão], [`just fetch`], [os CSV mensais da ANAC → `data/raw/`, #rec.raw.files arquivos, #nf(rec.raw.gigabytes, d: 2) GB, com o sha256 de cada um em `data/raw/manifest.json`], [#nf(rec.raw.fetch_minutes, d: 1) min (`reconstruction.raw.fetch_minutes`)],
  [staging], [`just stage`], [`data/raw/` → `data/staged/`, #miles(rec.staged.rows) etapas de voo em #rec.staged.partitions partições], [um ano por vez],
  [tabela-fato], [`just fact`], [etapas staged → `data/analysis/fact_group_route_month.parquet` (#miles(rec.fact.rows) × #rec.fact.columns) e as duas projeções de cidade], [#nf(rec.fact.seconds, d: 2) s (`reconstruction.fact.seconds`)],
  [painel], [`just panel`], [tabela-fato → `data/analysis/panel_route_month.parquet` (#miles(rec.panel.rows) × #rec.panel.columns), depois `docs/dictionary.md` e `datapackage.json`], [#nf(rec.panel.seconds, d: 2) s (`reconstruction.panel.seconds`)],
  [painel do artigo], [`just article-panel`], [a base final dos autores → `data/analysis/article_panel_route_month.parquet` (#miles(ap.rows) × #ap.columns), uma vez, na máquina do primeiro autor], [—],
  [estimação], [`just estimate`], [painel de estimação do artigo → `reports/replication/`], [#nf(est.seconds, d: 1) s (`estimation.seconds`)],
  [previsão], [`just predict-dataset`, `just predict`], [etapas staged → `data/derived/ml/` (#miles(s.prediction.rows) voos) → `reports/prediction/`; o preditor por voo é o Apêndice A da edição em Markdown], [#nf(s.prediction.dataset_build_seconds, d: 2) s; #miles(s.prediction.runtime_seconds) s (`prediction.dataset_build_seconds`, `prediction.runtime_seconds`)],
  [teoria], [`just theory`], [`src/airline_delays/theory/` → `reports/theory/`], [cerca de um segundo],
  [relatórios], [`just summary`, `just report`], [os artefatos → `reports/summary.json`; as fontes Typst → `reports/pdf/`], [segundos],
)

#v(1mm)
De onde vem cada número deste estudo, seção a seção:

#tab((auto, 1fr, auto), (left, left, left),
  [seção], [artefato], [comando],
  [Sumário executivo], [`reports/summary.json` (`reconstruction`, `published`, `estimation`, `theory`)\; `reports/theory/model.json` (`tolls`)], [`just summary`, `just estimate`, `just theory`],
  [1–7, Parte I], [`reports/theory/figures.json` e `reports/theory/figures/` (Figuras 1–5)\; `model.json` (`extension_lcc`)], [`just theory`],
  [8, fundamentos], [`reports/theory/model.json`, bloco `primer`, e `examples.linear`], [`just theory`],
  [9–21, o jogo], [`reports/theory/model.json` (`assumptions`, `reaction_slope`, `leader_follower`, `tolls`, `linear_closed_forms`, `inelastic`, `examples`, `comparative_statics`, `extension_lcc`)\; Figuras 6–10], [`just theory`],
  [22, hipóteses], [`model.json`, bloco `bridge`; `reports/replication/results.json` (as estatísticas publicadas por coluna)\; Figura 11], [`just theory`, `just estimate`],
  [23, dados], [`data/analysis/manifest.json`, `panel_manifest.json`, `article_panel_manifest.json`; `reports/summary.json` (`reconstruction`, `article_panel`, `registry`)], [`just fact`, `just panel`, `just summary`],
  [24, especificação], [`src/airline_delays/estimation/specification.py`; `reports/replication/results.json`, `sensitivity.json`; `reports/summary.json` (`estimation.sample`, `estimation.bandwidth`)], [`just estimate`, `just summary`],
  [25, resultados], [`reports/replication/results.json`, `summary.json`, `sensitivity.json`; `reports/summary.json` (`published`, `estimation`)], [`just estimate`, `just summary`],
  [26, recepção], [nenhum número medido aqui; as obras citadas estão em `docs/study/bibliografia.md`], [—],
  [Apêndice A], [`reports/theory/model.json`, lista `identities`], [`just theory`],
)

#v(1mm)
As verificações: `uv run pytest -q` roda a suíte — a amostra versionada, as tabelas de `data/analysis/`, o teste de frescor da replicação, as identidades da teoria, o vocabulário e a paridade dos READMEs; `uv run python scripts/check_docs_paths.py` confere que todo caminho e comando citado existe; `uv run python scripts/check_prose_numbers.py` confere que todo número das páginas de entrada é um valor de `reports/summary.json`; `just check-analysis` reconstrói em memória as tabelas versionadas e falha quando uma delas deixou de corresponder ao código; `just publish` confere que dicionário, datapackage, summary e `.zenodo.json` são reconstruções. Os números marcados "(artigo, Tabela N)" são transcrições das tabelas publicadas, e os marcados "(monografia — documento externo)" só existem na monografia de graduação do autor (USP, 2013)\; nenhum dos dois é medição deste repositório. A bibliografia do estudo é `docs/study/bibliografia.md`.
