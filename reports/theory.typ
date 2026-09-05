// A teoria por trás do artigo — estudo completo no padrão SAPIANS (relatório).
//
// Português (exceção deliberada ao inglês do repositório: CLAUDE.md, ADR-0006).
// NENHUM número deste relatório é digitado à mão: tudo vem de
// `reports/theory/model.json` e `reports/theory/figures.json`, escritos por
// `uv run python -m theory.run` (`just theory`); as figuras são os SVG de
// `reports/theory/figures/`, desenhados por `theory/figures.py` no estilo SAPIANS.
// O pacote de design é `reports/sapians/` (cópia MIT de sapians-latex, v0.1.0).
//
// Compilar:  typst compile --root . reports/theory.typ reports/build/theory.pdf

#import "sapians/lib.typ": *

#let m = json("theory/model.json")
#let figs = json("theory/figures.json")

// ---------------------------------------------------------------- utilitários
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
#let intuicao(title, body) = light-card(kicker-title: title)[#set text(size: 8.6pt); #set par(justify: false); #body]
#let resultado(title, body) = accent-card(title: title)[#set text(size: 8.6pt); #set par(justify: false); #body]
#let chave(title, body) = dark-card(kicker-title: title)[#set text(size: 8.6pt); #set par(justify: false); #body]
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
#set figure(gap: 1.8mm)
#show figure.caption: set align(left)

#show: sapians-report.with(
  title: "A teoria por trás do artigo",
  subtitle: "Da economia do congestionamento ao jogo de Stackelberg e ao artigo de 2016 — um estudo derivado e verificado",
  author: "William Eduardo Bendinelli",
  date: "5 de setembro de 2026",
  version: "1.0",
)

#let lin = m.examples.linear
#let qd = m.examples.quadratic
#let inel = m.examples.at("inelastic_linear_demand")
#let lcc = m.extension_lcc

= Sumário executivo

O artigo que este repositório replica — Bendinelli, Bettini e Oliveira (2016), _Airline delays, congestion internalization and non-price spillover effects of low cost carrier entry_, *Transportation Research Part A* 85, 39–52 — apoia-se numa teoria que ele não deriva: empresas aéreas com poder de mercado internalizam parte do congestionamento que causam, e um líder de Stackelberg internaliza menos que um duopolista de Cournot. Essa teoria foi trabalhada na monografia de graduação _Efeitos da entrada de uma empresa aérea de baixo custo na internalização das externalidades do congestionamento_ (USP/ESALQ, Piracicaba, 2013), segundo Brueckner e Van Dender (2008). Este estudo a reconstrói do início ao fim: a economia do congestionamento com as suas cinco figuras redesenhadas (Parte I), o jogo formulado e derivado passo a passo, com cada identidade verificada por `sympy` e cada número lido de `reports/theory/model.json` (Parte II), a ponte para os regressores e os sinais publicados do artigo (Parte III) e o que o campo levou (Parte IV).

#chave("O que a derivação acrescenta à monografia")[
  Três afinamentos, rotulados #tag("aqui") ao longo do texto. *Primeiro:* das condições da seguidora e da líder segue $f_1 = f_2 slash (1 - lambda) >= 2 f_2$ — a líder voa pelo menos o dobro da seguidora, e exatamente o dobro sob custo linear; a monografia dizia só $f_1 > f_2$. *Segundo:* sob custo linear a tarifa da líder no ótimo simétrico é exatamente #nf(m.tolls.leader_over_MCD_linear) do dano marginal, _a meio caminho_ entre a tarifa de Cournot (#nf(m.tolls.cournot_over_MCD)) e a atomística (#nf(m.tolls.atomistic_over_MCD)); a frase da monografia "entre a metade da tarifa de Cournot e a tarifa atomística" é tradução truncada de _halfway between_. *Terceiro:* sob demanda inelástica os limites $-1 < partial f_2 slash partial f_1 <= -1/2$ valem se e só se $c'' slash s >= s^2 d''$ — automático para demanda linear ou côncava, não garantido para demanda convexa — condição que nem a monografia nem a fonte enunciam.
]

#v(2mm)
Três rótulos separam de quem é cada afirmação: #tag("BVD") um resultado de Brueckner e Van Dender (2008) reenunciado; #tag("monografia") a afirmação da própria monografia, citada literalmente; #tag("aqui") o que esta derivação acrescenta. Nada é estimado em dados: o `sympy` verifica que a álgebra segue dos pressupostos declarados, não que os pressupostos valem. As #m.meta.n_identities identidades verificadas estão no Apêndice A.

= Parte I — A economia do congestionamento

== 1. Congestionamento como externalidade negativa

Uma empresa aérea que acrescenta um voo num aeroporto cheio paga o próprio custo do voo, mas não paga o tempo que impõe aos voos das outras — nem aos passageiros delas. O custo social de um voo é o custo privado mais esse custo forçado a terceiros; como a diferença não aparece em nenhum preço, a decisão de voar mais é tomada olhando só para o custo privado. É a definição de externalidade negativa, e o congestionamento aeroportuário é o seu exemplo de manual.

#intuicao("A ideia em uma frase")[
  Quem decide o número de voos não enfrenta o custo inteiro da decisão; por isso o mercado, deixado a si, voa demais — e "demais" é medido contra um nível eficiente que não é zero.
]

== 2. O nível eficiente de congestionamento (Figura 1)

#fig("fig1", [Custo marginal privado (CMgP), social (CMgS) e benefício marginal (BMg); A é o equilíbrio privado, C o ótimo social, ABC a perda de bem-estar. Redesenhada a partir de curvas paramétricas; adaptada de Cohen, Coughlin e Ott (2009), não copiada. Coordenadas em `reports/theory/figures.json`.])

#let f1 = figs.figures.fig1.quantities
Até $Q_c = #nf(f1.Q_c, d: 0)$ voos não há congestionamento: os custos marginais privado e social coincidem. Além dele, cada voo a mais impõe tempo aos outros e a curva social sobe acima da privada. O benefício marginal de um voo — a receita que ele traz — cai à medida que os voos aumentam. O mercado sem regulação para onde o benefício iguala o custo _privado_: o ponto A, com $Q_P = #nf(f1.Q_P, d: 0)$ voos. O ótimo está onde o benefício iguala o custo _social_: o ponto C, com $Q_S = #nf(f1.Q_S, d: 0)$. Entre os dois, cada voo custa à sociedade mais do que rende; a perda acumulada é o triângulo ABC, de área #nf(f1.triangle_ABC_area, d: 0) nas unidades da figura.

Note que o congestionamento eficiente não é zero: em $Q_S$ ainda há congestionamento, porque os voos entre $Q_c$ e $Q_S$ valem mais do que custam. A pergunta de política não é "como eliminar o atraso", mas "como levar o mercado de $Q_P$ a $Q_S$".

*Duas rotas para o ótimo.* Pela quantidade: fixar em $Q_S$ o número de pousos e decolagens (os _slots_), e decidir quem os usa — por antiguidade (_grandfathering_), que protege quem já está e não gera receita, ou por leilão, que revela quanto cada empresa valoriza o slot e captura esse valor para financiar capacidade (a "captura de valor" de Cohen, Coughlin e Ott 2009). Pelo preço: uma tarifa por voo que suba a curva privada até ela cruzar o benefício em C. A tarifa correta é a distância vertical entre as duas curvas de custo em $Q_S$ — a tarifa pigouviana, #nf(f1.toll_pigou_at_QS, d: 0) na figura.

#intuicao("Uma nota honesta sobre o segmento AD")[
  O texto da monografia diz que a tarifa é "AD (ou a diferença entre $P_S$ e $P_P$)", que na figura mede #nf(f1.toll_AD_equals_PS_minus_PP, d: 0). As duas coincidem só quando o custo privado é plano entre $Q_S$ e $Q_P$; com a curva privada inclinada, como o próprio texto a descreve, a tarifa que leva o mercado a C é a pigouviana, #nf(f1.toll_pigou_at_QS, d: 0). A figura imprime as duas para que a diferença fique visível (observação deste repositório).
]

== 3. Preço ou quantidade sob incerteza (Figura 2)

#fig("fig2", [O regulador conhece os custos mas não o benefício marginal, e fixa a tarifa $t$ ou a cota $Q_Q$ sobre o benefício esperado; o realizado é maior. ABC é a perda da cota, CEF a da tarifa. Adaptada de Cohen, Coughlin e Ott (2009).])

#let f2 = figs.figures.fig2.quantities
Na seção anterior o regulador conhecia as curvas. Suponha agora que conhece os custos mas erra o benefício: fixa a tarifa $t = #nf(f2.toll_set_on_expectations, d: 0)$ ou a cota $Q_Q = #nf(f2.Q_Q_quota, d: 0)$ sobre a curva _esperada_, e a curva _realizada_ fica acima. Com a tarifa, as empresas veem o custo privado mais $t$ e param onde essa curva cruza o benefício realizado: $Q_T = #nf(f2.Q_T_under_the_toll, d: 0)$ voos, além do novo ótimo $Q_S = #nf(f2.Q_S_efficient_under_BMgR, d: 0)$. Com a cota, o mercado fica preso em $Q_Q = #nf(f2.Q_Q_quota, d: 0)$, aquém do ótimo. As duas erram; a pergunta é qual erra menos. Na figura, a perda da cota (ABC, área #nf(f2.triangle_ABC_area_quantity_regulation, d: 0)) é maior que a da tarifa (CEF, área #nf(f2.triangle_CEF_area_price_regulation, d: 0)): o preço vence.

A regra geral é de Weitzman (1974), que a monografia usa sem nomear: o preço é o instrumento melhor quando o custo marginal é mais inclinado que o benefício marginal, e a quantidade quando é o contrário. Se a incerteza estiver nos custos, e não no benefício, os dois instrumentos dão o mesmo resultado. E há uma complicação própria da aviação: aeroportos são complementares (decolar de um é pousar noutro), e Czerny (2006) mostra que essa complementaridade propaga a incerteza de uma tarifa de aeroporto em aeroporto — o que favorece as cotas.

== 4. Expandir o aeroporto (Figura 3)

#fig("fig3", [Antes e depois de uma expansão: as duas curvas de custo deslocam-se para a direita e o limiar de congestionamento passa de $Q_T$ a $Q_(T X)$. Com demanda elástica o equilíbrio vai de E a E′; com demanda inelástica, de I a I′. Adaptada de Cohen e Coughlin (2003).])

#let f3 = figs.figures.fig3.quantities
A terceira opção é construir. Uma pista nova desloca as curvas de custo para a direita: o congestionamento passa a começar em $Q_(T X) = #nf(f3.Q_TX, d: 0)$ em vez de $Q_T = #nf(f3.Q_T, d: 0)$. Se o congestionamento persiste depende da demanda. Com demanda elástica, o custo menor atrai voos e o equilíbrio vai de $Q_E = #nf(f3.Q_E_before, d: 0)$ para $#nf(f3.Q_E_after, d: 0)$ — ainda além do novo limiar: a expansão foi absorvida por tráfego novo. Com demanda inelástica, fixa em $Q_I = #nf(f3.Q_I, d: 0)$, o novo limiar fica acima do tráfego e o congestionamento desaparece; o preço cai de #nf(f3.P_I_before, d: 0) para #nf(f3.P_I_after, d: 0). A expansão beneficia mais quem não responde ao preço — e a pergunta que a figura não responde é se os benefícios superam o custo da pista.

== 5. Externalidades de rede (Figuras 4 e 5)

#fig("fig4", [Benefício marginal local contra social num aeroporto-spoke: a rede acrescenta o valor das conexões que o voo alimenta. Adaptada de Cohen e Coughlin (2003).])

#let f4 = figs.figures.fig4.quantities
O foco num único aeroporto esconde uma característica do transporte aéreo: a rede. Um voo a mais num aeroporto _spoke_ vale, para quem conecta no _hub_, mais do que o benefício local mede. O aeroporto que decide pelo benefício local para em $Q_0 = #nf(f4.Q_0, d: 0)$; o benefício social justifica $Q_1 = #nf(f4.Q_1, d: 0)$, e a diferença entre as duas curvas em $Q_1$ — #nf(f4.subsidy_at_Q_1, d: 0) na figura — é o subsídio que levaria o aeroporto lá.

#fig("fig5", [Congestionamento e rede juntos: o custo social acima do privado por um lado, o benefício social acima do local pelo outro. Desenhada, como a monografia descreve a sua Figura 5, para que os dois efeitos se cancelem exatamente.])

#let f5 = figs.figures.fig5.quantities
Com as duas externalidades ao mesmo tempo a prescrição fica ambígua. O congestionamento pede uma tarifa; a rede pede um subsídio. Na Figura 5 os dois efeitos se compensam exatamente — o ótimo com as duas externalidades, $Q^* = #nf(f5.Q_star, d: 0)$, coincide com o equilíbrio de mercado $Q_0 = #nf(f5.Q_0, d: 0)$ — e nenhuma intervenção é necessária. É um caso especial: só o congestionamento levaria o ótimo a #nf(f5.Q_S_congestion_only, d: 0); só a rede, a #nf(f5.Q_N_network_only, d: 1). Fora do caso especial, a política depende de qual efeito é maior, e saber isso é um problema empírico — o que motiva a Parte III.

== 6. O debate da internalização

Se o aeroporto é dominado por uma empresa, o custo extra que um voo dela impõe aos outros voos _dela_ é interno à empresa. Ela o internaliza sozinha, e a tarifa eficiente deveria cobrar só a parte que ela impõe às outras. Essa é a intuição de Brueckner (2002): um monopolista discriminador de preços internaliza tudo; duopolistas de Cournot internalizam a própria parcela. O contra-argumento é de Daniel (1995) e Daniel e Harback (2008): se a dominante reduz voos para aliviar o pico, as rivais preenchem o espaço — a dominante não tem incentivo a internalizar, e a tarifa deve tratar todo atraso como externo. Mayer e Sinai (2003) medem os dois lados nos _hubs_ americanos e encontram o efeito da rede dominando o do congestionamento; Morrison e Winston (2007) encontram internalização só parcial; Ater (2012) mostra que empresas concentradas escolhem intervalos mais longos entre os voos, o que reduz o atraso sem tarifa nenhuma. Brueckner e Van Dender (2008) tentam unificar: o que decide é a estrutura do mercado — quem lidera, quem segue, se há franja competitiva — e não a concentração em si. É esse o modelo que a Parte II deriva.

#tab((auto, 1fr, 1fr, auto), (left, left, left, left),
  [obra], [estrutura de mercado], [quem internaliza], [tarifa eficiente],
  [Brueckner (2002)], [monopólio; Cournot], [tudo; a própria parcela], [zero; parcial],
  [Daniel (1995); Daniel e Harback (2008)], [dominante com franja competitiva], [ninguém], [atomística],
  [Mayer e Sinai (2003)], [hubs, com rede], [em parte; a rede domina], [pequena],
  [Brueckner e Van Dender (2008)], [líder de Stackelberg com seguidora], [a seguidora, à Cournot; a líder, menos], [entre Cournot e atomística],
  [Ater (2012)], [aeroportos concentrados], [reprogramando horários], [limitada],
)

= Parte II — O jogo

== 7. Os jogadores, as estratégias e o tempo

Antes das equações, o jogo. Há duas empresas aéreas, $i in {1, 2}$, servindo um aeroporto congestionado no período de pico. A *estratégia* de cada uma é o seu volume de voos, $f_i >= 0$; o *resultado* é o tráfego total $F = f_1 + f_2$, que determina o congestionamento. O *pagamento* é o lucro $pi_i (f_1, f_2)$ da seção 8. A *informação* é completa: as duas conhecem custos, demanda e a regra do jogo. O que muda entre os casos é o *tempo*:

#step-item(1, "Jogo simultâneo (Cournot).", description: [as duas escolhem $f_i$ ao mesmo tempo; o conceito de solução é o equilíbrio de Nash: cada uma responde otimamente ao volume da outra.])
#v(1mm)
#step-item(2, "Jogo sequencial (Stackelberg).", description: [a empresa 1 escolhe primeiro e a 2 observa antes de escolher; o conceito de solução é o equilíbrio perfeito em subjogos, obtido por indução retroativa — primeiro a melhor resposta da seguidora, depois a escolha da líder que a antecipa.])
#v(1mm)
#step-item(3, "Pontos de referência.", description: [o comportamento atomístico (cada empresa ignora o efeito do próprio volume sobre o congestionamento) e o monopólio (uma empresa só) delimitam os extremos entre os quais Cournot e Stackelberg se situam.])

#v(2mm)
#tab((auto, 1fr, auto), (left, left, left),
  [símbolo], [o que é], [nome em `theory/model.py`],
  [$f_1, f_2, F$], [voos da empresa 1, da 2, e o total $F = f_1 + f_2$], [`f1`, `f2`, `F`],
  [$p$], [preço total que o passageiro paga (demanda horizontal no caso-base)], [`p`],
  [$s$], [assentos por voo, todos vendidos], [`s`],
  [$tau$], [custo por assento sem congestionamento], [`tau`],
  [$t(F)$], [custo de tempo por passageiro causado pelo congestionamento], [dentro de `c`],
  [$g(F)$], [custo operacional extra por voo causado pelo congestionamento], [dentro de `c`],
  [$c(F)$], [$s t(F) + g(F)$: o custo do congestionamento por voo, $c' > 0$, $c'' >= 0$], [`c`, `c0`, `c1`, `c2`],
  [$lambda$], [$-partial f_2 slash partial f_1$: quantos voos a seguidora corta por voo extra da líder], [`lam`],
  [$x$], [$f_2 c'' slash c'$: a única razão de que todo limite de $lambda$ depende], [`x`],
  [$d(Q)$], [demanda inversa sobre o total de assentos $Q = s F$, $d' < 0$ (seção 17)], [`d`, `d0`, `d1`, `d2`],
)

#v(2mm)
Os pressupostos, com o status que a verificação lhes dá:

#tab((auto, 1fr, auto), (left, left, left),
  [id], [pressuposto], [status],
  ..m.assumptions.map(a => (a.id, a.statement, a.status)).flatten(),
)

== 8. A função de lucro, termo a termo

O passageiro está disposto a pagar um preço total $p$ pela viagem no aeroporto congestionado. Como o congestionamento lhe impõe um custo de tempo $t(F)$, a tarifa que a empresa consegue cobrar é o preço total menos esse custo. Com $s$ assentos vendidos por voo, a receita da empresa $i$ é

#numbered(1)[$ R_i = [p - t(f_1 + f_2)] s f_i, quad i = 1, 2 $]

Do lado do custo, cada assento custa $tau$, e o congestionamento acrescenta $g(F)$ por voo. O lucro é

#numbered(2)[$ pi_i = [p - t(f_1 + f_2)] s f_i - [tau s + g(f_1 + f_2)] f_i $]

Os dois custos do congestionamento — o do passageiro, $s t(F)$ por voo, e o da empresa, $g(F)$ — entram no lucro do mesmo jeito, subtraindo por voo. A monografia os junta numa só função,

#numbered(5)[$ c(F) equiv s t(F) + g(F), quad c' > 0, quad c'' >= 0, $]

e o lucro fica na forma que se usa daqui em diante:

#numbered(3)[$ pi_1 = (p - tau) s f_1 - c(f_1 + f_2) f_1 $]
#numbered(4)[$ pi_2 = (p - tau) s f_2 - c(f_1 + f_2) f_2 $]

#intuicao("Por que a curvatura de c importa")[
  $c' > 0$ diz que cada voo a mais torna o congestionamento mais caro; $c'' >= 0$ diz que esse encarecimento não desacelera. Tudo o que vem depois — quanto a seguidora reage, quanto a líder internaliza, quanto vale a tarifa — depende dessas duas derivadas, e de nada mais. Por isso a verificação simbólica trabalha com $c$ genérica e os exemplos numéricos com $c$ linear ($c'' = 0$) e quadrática ($c'' > 0$).
]

== 9. O ótimo social

Com demanda horizontal o excedente do consumidor é zero: o passageiro paga exatamente o que a viagem vale para ele. O bem-estar é então o lucro conjunto, $W = pi_1 + pi_2 = (p - tau) s F - c(F) F$. Derivando em relação a $F$ e dividindo por $s$ para ler a condição por assento,

#numbered(6)[$ p - tau - [F c'(F) + c(F)] / s = 0 $]

Leia o termo entre colchetes. $c(F)$ é o custo de congestionamento do próprio voo; $F c'(F)$ é o custo que esse voo impõe a _todos_ os $F$ voos do aeroporto — cada um deles fica $c'$ mais caro. Esse segundo termo tem nome:

#resultado("Definição: dano marginal de congestionamento")[
  $"MCD" equiv F c'(F)$ é o custo que um voo a mais impõe ao conjunto dos voos já existentes. É o que uma tarifa eficiente deve cobrar de quem não o considera — e a fração de MCD que cada estrutura de mercado deixa de considerar é a medida da sua falha em internalizar.
]

== 10. Ponto de referência: Cournot

No jogo simultâneo cada empresa maximiza o próprio lucro tomando o volume da outra como dado. Da equação (3), $partial pi_1 slash partial f_1 = (p - tau) s - c(F) - f_1 c'(F) = 0$, ou, por assento,

$ p - tau - [f_1 c' + c] / s = 0, quad "e simetricamente" quad p - tau - [f_2 c' + c] / s = 0. $

Compare com (6): a empresa 1 internaliza $f_1 c'$ — o dano que impõe aos próprios voos — mas não $f_2 c'$, o que impõe aos voos da rival. Cada uma internaliza a _própria parcela_ do dano marginal. A tarifa que fecha a diferença é $f_2 c'$ para a empresa 1 e $f_1 c'$ para a 2; no ponto simétrico, metade de MCD. Este é o resultado de Brueckner (2002) que a monografia toma como referência, e é a origem do termo de internalização que Guo, Jiang e Wan (2018) levam aos preços (seção 19).

#fig("fig6", [As funções de reação do exemplo linear: a da seguidora, $f_2 (f_1) = (D - b f_1) slash 2b$, e a da empresa 1 no jogo simultâneo. Cournot é o cruzamento das duas; Stackelberg é o ponto da reação da seguidora que a líder escolhe; o ótimo simétrico fica abaixo dos dois.])

== 11. Pontos de referência: atomístico e monopólio

A empresa *atomística* ignora que os seus voos congestionam: a sua condição é $p - tau - c slash s = 0$, sem termo $c'$ nenhum, e a tarifa que a corrige é o dano marginal inteiro, MCD. O *monopolista* faz o contrário: maximiza $(p - tau) s F - c(F) F$ e a sua condição coincide com (6) — internaliza tudo, e a tarifa é zero. A tabela abaixo, lida de `model.json` (`tolls`), resume os pontos de referência que as seções seguintes usam:

#tab((1fr, auto, auto), (left, left, right),
  [estrutura], [o que internaliza], [tarifa ÷ MCD\*],
  [monopólio], [todo o dano marginal], [#nf(m.tolls.monopoly_over_MCD)],
  [duopólio de Cournot, e a seguidora de Stackelberg], [a própria parcela, $f_i slash F$], [#nf(m.tolls.follower_over_MCD)],
  [líder de Stackelberg], [menos que a própria parcela], [$(1 + lambda^*) slash 2$; #nf(m.tolls.leader_over_MCD_linear) sob custo linear],
  [atomística], [nada], [#nf(m.tolls.atomistic_over_MCD)],
)

== 12. Stackelberg, passo 1: a seguidora

Na indução retroativa começa-se pelo fim: a seguidora, empresa 2, observa $f_1$ e escolhe $f_2$. A sua condição é a de Cournot,

#numbered(7)[$ p - tau - [f_2 c' + c] / s = 0 $]

O que muda é o que fazemos com ela. A condição (7) define $f_2$ como função de $f_1$ — a _função de reação_ — e a pergunta central do modelo é quanto $f_2$ cai quando $f_1$ sobe. Diferenciando (7) totalmente: como $c$ e $c'$ dependem de $F = f_1 + f_2$, um aumento de $f_1$ move o lado esquerdo por $-(c' + f_2 c'') slash s$ (o $c$ sobe $c'$, e $f_2 c'$ sobe $f_2 c''$), e um aumento de $f_2$ o move por $-(2 c' + f_2 c'') slash s$ (os mesmos dois efeitos, mais o $c'$ do próprio $f_2$ a multiplicar). Para (7) continuar valendo, a razão entre os dois é

#numbered(8)[$ (partial f_2) / (partial f_1) = - (f_2 c'' + c') / (f_2 c'' + 2 c') equiv - lambda $]

#resultado("[aqui] Os limites de λ, derivados")[
  Toda a informação de (8) cabe numa razão: com $x = f_2 c'' slash c' >= 0$, $lambda = (1 + x) slash (2 + x)$ (`reaction_slope.lambda_of_x`). Daí $lambda - 1 slash 2 = x slash (2(2 + x)) >= 0$ e $1 - lambda = 1 slash (2 + x) > 0$, portanto $1 slash 2 <= lambda < 1$, com $lambda = 1 slash 2$ exatamente quando $c'' = 0$ (`reaction_slope.lambda_minus_half`, `one_minus_lambda`). Em palavras: a seguidora corta entre metade e a totalidade de cada voo extra da líder — metade sob custo linear, mais que metade quando o custo marginal do congestionamento acelera.
]

#intuicao("Por que a seguidora corta")[
  Um voo a mais da líder encarece o congestionamento para todos. A seguidora, que só olha para a própria parcela, vê o seu custo marginal subir e recua — mas não recua voo por voo, porque ao recuar alivia o congestionamento e parte do incentivo desaparece. Fica no meio: $lambda$ entre ½ e 1.
]

== 13. Stackelberg, passo 2: a líder

A líder sabe que $f_2 = f_2 (f_1)$ e maximiza $pi_1 = (p - tau) s f_1 - c(f_1 + f_2 (f_1)) f_1$. Pela regra da cadeia, $partial c slash partial f_1 = c' (1 + partial f_2 slash partial f_1)$, e a condição de primeira ordem, por assento, é

#numbered(9)[$ p - tau - 1 / s [f_1 c' (1 + (partial f_2) / (partial f_1)) + c] = 0 $]

O fator $(1 + partial f_2 slash partial f_1) = 1 - lambda$ é o coração do modelo. Comparado com Cournot, onde esse fator é 1, a líder internaliza _menos_: ela antecipa que, se cortar voos para aliviar o pico, a seguidora ocupará parte do espaço — é o mecanismo de compensação que Daniel e Harback (2008) descrevem — e por isso o seu incentivo a conter o congestionamento encolhe na proporção $1 - lambda$.

#resultado("[aqui] A líder voa pelo menos o dobro da seguidora")[
  De (7), $p - tau - c slash s = f_2 c' slash s$; de (9), $p - tau - c slash s = f_1 c' (1 - lambda) slash s$. No mesmo ponto, $f_2 c' = f_1 c' (1 - lambda)$, logo $f_1 = f_2 slash (1 - lambda)$ (`leader_follower.f1`). Com $lambda = (1 + x) slash (2 + x)$ isso é $f_1 = f_2 (2 + x)$, ou $f_1 - 2 f_2 = f_2 x >= 0$: a líder voa pelo menos o dobro da seguidora, e exatamente o dobro sob custo linear — mais forte que o "$f_1 > f_2$" da monografia. No exemplo quadrático a razão é #nf(qd.stackelberg.f1 / qd.stackelberg.f2, d: 3) (`examples.quadratic.stackelberg`).
]

== 14. As tarifas que restauram o ótimo

A tarifa por voo que leva a líder ao ótimo é a diferença entre a condição social (6) e a dela (9): o dano marginal que ela deixa de considerar. Subtraindo,

#numbered(10)[$ T_1 = (f_2 - f_1 (partial f_2) / (partial f_1)) c' = ((f_2 + lambda f_1) dot "MCD") / (f_1 + f_2) $]

— a primeira forma diz de onde vem a tarifa (o dano aos voos da seguidora, $f_2 c'$, mais o dano que a líder deixa de considerar por causa da reação, $lambda f_1 c'$); a segunda a expressa como fração de MCD. A seguidora, que se comporta à Cournot, paga $T_2 = F c' - f_2 c' = f_1 c'$. Avaliando no ótimo simétrico, $f_1 = f_2 = f^*$:

#numbered(11)[$ T_1^* = 1/2 (1 + lambda^*) "MCD"^*, quad T_2^* = 1/2 "MCD"^* $]

#resultado("Proposição 1 [BVD]")[
  #quote(block: false)[Com um líder de Stackelberg e um seguidor, do seguidor é cobrada tarifa de congestionamento ao estilo Cournot. Do líder é cobrada uma tarifa que fica entre o valor de Cournot e da tarifa atomística (o que equivale a 100 por cento do dado do congestionamento marginal de um voo extra).] — monografia, seção 4.3, reenunciando Brueckner e Van Dender (2008). O comportamento do líder empurra a tarifa em direção à estrutura atomística sem chegar a ela: $1 slash 2 <= (1 + lambda^*) slash 2 < 1$.
]

#resultado("[aqui] Três quartos, a meio caminho")[
  Sob custo linear $lambda^* = 1 slash 2$ e (11) vira um número: $T_1^* = #nf(m.tolls.leader_over_MCD_linear) "MCD"^*$ (`tolls.leader_over_MCD_linear`), exatamente a meio caminho entre a tarifa de Cournot (#nf(m.tolls.cournot_over_MCD)) e a atomística (#nf(m.tolls.atomistic_over_MCD)). A monografia escreve que a tarifa "situa-se entre a metade da tarifa de Cournot e a tarifa atomística" — tradução truncada de _halfway between_. Quando $c'' > 0$, $lambda^* > 1 slash 2$ e a tarifa da líder sobe acima de três quartos: #nf(qd.tolls_at_symmetric_optimum.T1_star_over_MCD, d: 4) no exemplo quadrático (Figura 7). E há uma coincidência útil: em qualquer equilíbrio de Stackelberg $f_2 = (1 - lambda) f_1$, logo $T_1 = T_2 = f_1 c'$ — as duas empresas precisam da mesma tarifa por voo, por razões diferentes (identidade `T1_equals_T2_at_stackelberg`).
]

#fig("fig7", [As tarifas de (11) por estrutura de mercado, como fração do dano marginal no ótimo simétrico. Lidas de `model.json` (`examples.linear` e `examples.quadratic`, `tolls_at_symmetric_optimum`).])

== 15. Exemplo numérico completo

Com $p = #nf(lin.primitives.p, d: 0)$, $tau = #nf(lin.primitives.tau, d: 0)$, $s = #nf(lin.primitives.s, d: 0)$ e custo linear $c(F) = #nf(lin.cost.a, d: 0) + #nf(lin.cost.b, d: 0) F$, tudo tem forma fechada em $D = (p - tau) s - a$ e $b$ (`linear_closed_forms`): o ótimo $F^* = D slash 2b$; Cournot $D slash 3b$ por empresa; Stackelberg $D slash 2b$ para a líder e $D slash 4b$ para a seguidora; o total atomístico $D slash b$. As perdas de bem-estar são frações fixas de $W^*$: $1 slash 9$ sob Cournot, $1 slash 4$ sob Stackelberg, tudo sob comportamento atomístico. A tabela põe os números lado a lado:

#tab((1fr, auto, auto, auto, auto), (left, right, right, right, right),
  [estrutura], [$f_1$], [$f_2$], [$F$], [perda ÷ $W^*$],
  [ótimo social ($W^* = #miles(lin.social_optimum.welfare_star)$)], [#nf(lin.social_optimum.f_star, d: 1)], [#nf(lin.social_optimum.f_star, d: 1)], [#nf(lin.social_optimum.F_star, d: 0)], [0],
  [monopólio], [—], [—], [#nf(lin.monopoly.F, d: 0)], [#nf(lin.monopoly.loss_share, d: 2)],
  [Cournot], [#nf(lin.cournot.f1, d: 0)], [#nf(lin.cournot.f2, d: 0)], [#nf(lin.cournot.F, d: 0)], [#nf(lin.cournot.loss_share, d: 4)],
  [Stackelberg], [#nf(lin.stackelberg.f1, d: 0)], [#nf(lin.stackelberg.f2, d: 1)], [#nf(lin.stackelberg.F, d: 1)], [#nf(lin.stackelberg.loss_share, d: 2)],
  [atomística], [—], [—], [#nf(lin.atomistic.F, d: 0)], [#nf(lin.atomistic.loss_share, d: 0)],
)

#v(1.5mm)
No ponto de Stackelberg o dano marginal é MCD = #miles(lin.stackelberg.MCD), a líder deve #miles(lin.stackelberg.T1) por voo e a seguidora #miles(lin.stackelberg.T2) — iguais, como a seção 14 antecipa —, e a tarifa da líder é #nf(lin.stackelberg.T1_over_MCD, d: 4) do dano marginal, abaixo dos #nf(lin.tolls_at_symmetric_optimum.T1_star_over_MCD) do ótimo simétrico porque o equilíbrio não é o ótimo. Os lucros são #miles(lin.stackelberg.profit1) e #miles(lin.stackelberg.profit2) (`examples.linear.stackelberg`).

== 16. Estática comparativa: a curvatura do custo

#fig("fig8", [$lambda^*$ e $T_1^* slash "MCD"^*$ no ótimo simétrico para $c(F) = 1000 + 50 F + q F^2$, $q$ de 0 a 4 (`comparative_statics.cost_curvature`).])

#tab((auto, auto, auto, auto, auto, auto), (right, right, right, right, right, right),
  [$q$], [$F^*$], [$lambda^*$], [$T_1^* slash "MCD"^*$], [$f_1 slash f_2$ (Stackelberg)], [perda ÷ $W^*$],
  ..m.comparative_statics.cost_curvature.map(r => (nf(r.q, d: 2), nf(r.F_star, d: 2), nf(r.lambda_star, d: 4), nf(r.T1_star_over_MCD, d: 4), nf(r.f1_over_f2, d: 3), nf(r.loss_share, d: 4))).flatten(),
)

#v(1.5mm)
Quanto mais curvo o custo, mais a seguidora recua ($lambda^*$ sobe), menos a líder internaliza, e mais a sua tarifa se aproxima da atomística — mas a perda de bem-estar de Stackelberg _cai_ em fração de $W^*$, porque o ótimo também encolhe. A leitura para a política: a diferença entre a tarifa de Cournot e a da líder é maior justamente onde o congestionamento acelera mais depressa.

== 17. Demanda inelástica e a "Pressuposição 2"

Até aqui as empresas não tinham poder de mercado: o preço era dado. A monografia relaxa isso na seção 4.4, com $p = d(s F)$, $d' < 0$ — o preço cai com o total de assentos, e cada empresa sabe que os seus voos o derrubam. O lucro da líder passa a ser $pi_1 = d(s (f_1 + f_2 (f_1))) s f_1 - tau s f_1 - c f_1$, e a condição de primeira ordem, por assento,

#numbered(12)[$ d + s f_1 d' (1 + (partial f_2) / (partial f_1)) - tau - 1 / s [f_1 c' (1 + (partial f_2) / (partial f_1)) + c] = 0 $]

enquanto a condição eficiente é $d - tau - [F c' + c] slash s = 0$ (`inelastic.social_foc`). Há agora duas distorções, de sinais opostos: o termo $s f_1 d' (1 - lambda) < 0$ é o poder de mercado exercido (retém tráfego), e o termo $f_1 c' (1 - lambda) slash s$ é o dano que a líder deixa de internalizar (excede tráfego). A monografia lê os dois extremos: se $partial f_2 slash partial f_1 = -1$, (12) reduz-se a $d - tau - c slash s = 0$ — nem poder de mercado, nem internalização, e só uma tarifa atomística corrige; se $partial f_2 slash partial f_1 = -1 slash 2$, a líder exerce metade do poder de mercado e ainda deixa de internalizar $f_1 c' slash 2 s$.

#resultado("Pressuposição 2 [monografia]")[
  #quote(block: false)[O líder Stackelberg, quando enfrenta uma demanda inelástica, maximiza seu lucro no intervalo que apresenta como limite inferior o caso em que não explora seu poder de mercado mas falha na internalização do congestionamento e, como limite superior, o caso em que exerce metade do seu poder de mercado sendo incapaz também de internalizar o congestionamento.] — monografia, seção 4.4. É uma leitura dos extremos de (12), condicional a $-1 < partial f_2 slash partial f_1 <= -1 slash 2$ continuar valendo sob demanda inelástica — o que a monografia supõe sem derivar.
]

#resultado("[aqui] A condição para os limites valerem")[
  Derivando a reação da seguidora sob $p = d(s F)$, $partial f_2 slash partial f_1 = -A slash B$ com $A = (c' + f_2 c'') slash s - s d' - s^2 f_2 d''$ e $B = A + c' slash s - s d'$ (`inelastic.slope_A`, `slope_B`), e $-partial f_2 slash partial f_1 - 1 slash 2 = f_2 (c'' slash s - s^2 d'') slash 2 B$. O limite vale, portanto, se e só se $c'' slash s >= s^2 d''$ (`inelastic.slope_bounds_condition`): automático para demanda linear ou côncava, não garantido para demanda convexa. Com $d'' = 0$ a reação é $-(k + f_2 c'') slash (2k + f_2 c'')$, $k = c' - s^2 d' > 0$, e os limites do caso elástico se repetem (identidade `lambda_linear_demand`).
]

#fig("fig9", [Demanda linear $d(Q) = 400 - d d dot Q$ e custo linear: o total de Stackelberg contra o eficiente à medida que a demanda inclina (`comparative_statics.demand_slope`).])

No exemplo linear-linear com $d d = #nf(inel.demand.dd, d: 3)$, o ponto de Stackelberg é $f_1 = #nf(inel.stackelberg.f1, d: 0)$, $f_2 = #nf(inel.stackelberg.f2, d: 0)$, preço #nf(inel.stackelberg.price, d: 1), total #nf(inel.stackelberg.F, d: 0) contra um ótimo de #nf(inel.social_optimum.F_star, d: 2); os dois termos de (12) valem #nf(inel.equation_12_terms_at_stackelberg.market_power_term, d: 1) e #nf(inel.equation_12_terms_at_stackelberg.uninternalised_term, d: 0). A tabela mostra o que a Figura 9 desenha: quando a demanda inclina o bastante, a distorção do poder de mercado vence e o tráfego cai _abaixo_ do ótimo — uma consequência que a monografia não explora (observação deste repositório).

#tab((auto, auto, auto, auto, auto, auto, auto), (right, right, right, right, right, right, right),
  [$d d$], [$f_1$], [$f_2$], [$F$], [$F^*$], [poder de mercado], [não internalizado],
  ..m.comparative_statics.demand_slope.map(r => (nf(r.dd, d: 3), nf(r.f1, d: 2), nf(r.f2, d: 2), nf(r.F, d: 2), nf(r.F_star, d: 2), nf(r.market_power_term, d: 2), nf(r.uninternalised_term, d: 2))).flatten(),
)

== 18. A entrada de uma empresa de baixo custo

#resultado("Pressuposição 3 [monografia]")[
  #quote(block: false)[A entrada de uma empresa aérea de baixo custo no mercado quebra a estrutura do jogo em Stackelberg. Devido à estrutura do modelo de negócios de uma empresa aérea de baixo custo, é coerente pressupor que tais empresas procurem internalizar os custos do congestionamento, uma vez que tais custos podem afetar o planejamento estratégico de longo prazo da empresa que busca o crescimento de sua participação de mercado.] — monografia, seção 4.5. Não há equação por trás: é o pressuposto que assina as dummies de Gol e Azul da estimação de 2013 (status A7).
]

#resultado("[aqui] Uma extensão, rotulada como tal")[
  O que a frase pode significar dentro do modelo: com a entrante o jogo deixa de ter uma líder e passa a ser um Cournot de três, e a entrante custa menos por assento. Sob custo linear a condição de cada empresa $i$ é $D_i - b F - b f_i = 0$ com $D_i = (p - tau_i) s - a$, de onde $F = sum D_i slash 4 b$ e $f_i = D_i slash b - F$. Com duas incumbentes a $tau = #nf(lcc.incumbent_tau, d: 0)$ e uma entrante a $tau = #nf(lcc.entrant_tau, d: 0)$: total #nf(lcc.triopoly.F, d: 0) (contra #nf(lcc.duopoly_cournot.F, d: 0) no duopólio de Cournot e #nf(lcc.stackelberg_duopoly_F, d: 1) em Stackelberg), voos #nf(lcc.triopoly.flights.at(0), d: 0), #nf(lcc.triopoly.flights.at(1), d: 0) e #nf(lcc.triopoly.flights.at(2), d: 0), e parcela internalizada do dano marginal #nf(lcc.triopoly.internalised_share.at(0)) para a entrante contra #nf(lcc.triopoly.internalised_share.at(1)) para cada incumbente (`extension_lcc`). A entrante internaliza mais porque voa mais, e voa mais porque custa menos. A extensão não diz nada sobre tempo, escolha de aeroporto ou preços — as três coisas que a seção 19 mostra importarem.
]

#fig("fig10", [Parcelas internalizadas do dano marginal, $f_i slash F$, no duopólio de Cournot e no triopólio com a entrante (`extension_lcc`).])

== 19. Do jogo às tarifas: Guo, Jiang e Wan (2018)

A formulação foi completada onde a monografia não tinha dado: nos preços. Guo, Jiang e Wan (2018, *Transportation Research Part A* 118, 648–661, DOI `10.1016/j.tra.2018.10.012`) partem do mesmo termo de Cournot da seção 10 — a própria parcela do dano marginal — e o levam à tarifa. Na nossa notação, uma empresa com tráfego $q_(i A)$ no aeroporto A, enfrentando o atraso marginal $D'_A$ que o seu tráfego provoca, fixa o preço $p = c + beta D_A - p' q + k beta D'_A q_(i A)$: o último termo é o _markup de internalização_, e existe ($k = 1$) só se a empresa internaliza. Daí uma hipótese testável sem medir atraso nenhum como variável dependente: se as empresas internalizam, a tarifa sobe com a interação entre os passageiros próprios no aeroporto e o atraso do aeroporto. Com dados americanos de 2014–2015 (DB1B, T-100, AOTP), a interação é positiva e significante para o conjunto das empresas; separando por tipo, as de serviço completo internalizam e as de baixo custo não (números externos, Guo, Jiang e Wan 2018, Tabela 4).

O artigo constrói explicitamente sobre o de 2016 — a separação entre concentração de mercado e de aeroporto — e o critica num ponto preciso: controlar por tráfego do aeroporto remove o canal de internalização que age _reduzindo tráfego via preço_, deixando visível só o canal de _reprogramação_. É uma crítica ao desenho, não ao achado.

#chave("As três margens de internalização (síntese deste repositório)")[
  Uma empresa pode internalizar o próprio congestionamento *reprogramando horários* (Ater 2012), *reduzindo tráfego via preço* (Guo, Jiang e Wan 2018) ou *escolhendo o aeroporto* (Gudmundsson, Paleari e Redondi 2014; a Azul em Viracopos na monografia). Lidas por margem, a Pressuposição 3 e "as LCC não internalizam via preço" deixam de ser contraditórias: a LCC brasileira de 2013 internalizou pela margem do aeroporto próprio, não pela tarifa. É a hipótese que este estudo deixa formulada e a Parte IV lista como aberta.
]

= Parte III — Do modelo ao artigo

== 20. Objeto teórico, regressor, sinal publicado

O artigo de 2016 não estima o jogo; estima a sua consequência observável. Cada objeto do modelo tem um regressor, e cada regressor um sinal esperado e um sinal publicado. A tabela junta os três, com os coeficientes lidos de `replication/published.json` através de `model.json` (`bridge`): a coluna (2) da Tabela 3, o 2SGMM com as dummies de LCC, e a coluna (2) da Tabela 6, o OLS correspondente.

#let rotulos = (:)
#for row in m.bridge.rows { rotulos.insert(row.variable, row.theory_object_pt) }
#let t3 = m.bridge.tables.table3.variables
#let t6 = m.bridge.tables.table6.variables
#tab((auto, 1fr, auto, auto, auto), (left, left, center, right, right),
  [variável], [objeto teórico], [esperado], [Tab. 3 (2), 2SGMM], [Tab. 6 (2), OLS],
  ..t3.pairs().map(p => {
    let v = p.at(0)
    let info = p.at(1)
    let c3 = info.columns.at("2")
    let c6 = t6.at(v).columns.at("2")
    (raw(v), rotulos.at(v), if info.expected_sign == none { "—" } else { info.expected_sign },
     sgn(c3.b) + " " + (if c3.stars == none { "" } else { c3.stars }),
     sgn(c6.b) + " " + (if c6.stars == none { "" } else { c6.stars }))
  }).flatten(),
)

#fig("fig11", [Os quatro regressores de estrutura de mercado: OLS (cinza) contra 2SGMM (colorido), coeficientes publicados. Nada é reestimado aqui.], w: 84%)

*Como ler.* A concentração da rota (`rthhi`) é o poder de mercado $d' < 0$ da seção 17, e o artigo a lê como canal de concorrência e qualidade; a concentração do aeroporto (`maxcthhi`) é a internalização da seção 14, a parcela própria do dano marginal — e o seu sinal negativo no 2SGMM é a Proposição 1 vista nos dados. As duas concentrações são instrumentadas porque, no jogo, a reação da seguidora torna volumes, concentração e atraso determinados _em conjunto_ — é a razão econômica da instrumentação, e a inversão de sinal do OLS para o 2SGMM nas duas variáveis é o achado central do artigo (`replication/table6.py`). As dummies de LCC (`lcc`, `maxalccfu`) são a Pressuposição 3 tornada regressor: negativas, como a monografia esperava para as suas próprias dummies de Gol e Azul.

== 21. O que 2013 estimou e o que 2016 estimou

A monografia estimou, num painel empresa × rota × mês com atrasos acima de 30 minutos, coeficientes positivos e significantes para o HHI da rota e para a razão de concentração das duas maiores no aeroporto, um efeito ambíguo para a Gol e um efeito negativo para a Azul no seu próprio aeroporto — e leu os dois primeiros como uma "tragédia dos comuns" (monografia, seção 7; números externos, em `docs/theory/03-do-modelo-ao-artigo.md`). O artigo de 2016 estimou, num painel rota × mês com atrasos das FSC acima de 15 minutos, o 2SGMM da tabela acima. Os sinais de concentração não são comparáveis entre os dois: bases do HHI diferentes (voos planejados contra passageiros), unidades, estimadores e regressandos diferentes. O que é comparável é a pergunta, e ela é a mesma.

= Parte IV — O que o campo levou

O artigo acumulou 93 trabalhos citantes, mapeados pelo projeto irmão `citation-audit` (números externos): 18 pela internalização do congestionamento, 8 pelo arcabouço que testa congestionamento e estrutura de mercado numa única equação, 4 pelos _spillovers_ não-preço da entrada de LCC — o achado que dá título ao artigo é o menos citado dos três. Entre os citantes, Guo, Jiang e Wan (2018) é classificado como citação _foundational_ e fiel: o que continua a linha teórica é o artigo que a levou aos preços. Fica aberto o que este estudo formula e não testa: as três margens de internalização, cuja separação exigiria um painel com tarifas que este repositório não tem.

= Apêndice A — As identidades verificadas

#m.meta.n_identities afirmações algébricas, cada uma verificada com `sympy` #m.meta.sympy por `tests/test_theory.py`. A coluna "origem" diz de quem é a afirmação.

#tab((auto, auto, auto, auto, 1fr), (left, left, left, center, left),
  [id], [equação], [origem], [fecha], [afirmação],
  ..m.identities.map(i => (raw(i.id), i.equation, rot(i.origin), nf(i.holds), i.statement)).flatten(),
)

= Apêndice B — Como reproduzir

```bash
just theory
uv run pytest tests/test_theory.py -q
typst compile --root . reports/theory.typ reports/build/theory.pdf
```

O primeiro comando roda `theory/run.py`: verifica as identidades, resolve os exemplos, desenha as onze figuras no estilo SAPIANS e escreve `reports/theory/model.json`, `figures.json` e `results.md` — sem data nem commit, de modo que uma segunda execução não muda nada. O segundo roda os testes, incluindo o que falha quando o relatório commitado está defasado. O terceiro compila este documento com o pacote de design vendorizado em `reports/sapians/` (cópia MIT de `sapians-latex` v0.1.0); a fonte Inter é usada quando instalada, com Helvetica Neue ou Arial como reserva.
