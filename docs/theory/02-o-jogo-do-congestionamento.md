# O jogo do congestionamento — um líder de Stackelberg, derivado

Este é o capítulo 2 de quatro. Ele deriva, passo a passo, o modelo de teoria
dos jogos da seção 4 da monografia de graduação do autor — *Efeitos da
entrada de uma empresa aérea de baixo custo na internalização das
externalidades do congestionamento* (USP/ESALQ, Piracicaba, 2013) —, que
segue Brueckner e Van Dender (2008, *Journal of Urban Economics* 64,
288–295). Daqui em diante, "a monografia". Três rótulos dizem de quem é cada
afirmação: **[BVD]**, Brueckner e Van Dender (2008) reenunciados;
**[monografia]**, o que a monografia afirma; **[aqui]**, o que esta
derivação acrescenta. Toda identidade é conferida por `tests/test_theory.py`
contra `src/airline_delays/theory/model.py`, e todo número sai de `reports/theory/model.json`,
com a chave nomeada na mesma frase. O capítulo termina em Guo, Jiang e Wan
(2018), onde a formulação foi levada aos preços.

## 1. Pressupostos e notação

Duas empresas aéreas, 1 e 2, servem um aeroporto congestionado no pico e
escolhem volumes de voos $f_1$ e $f_2$; o tráfego total é $F = f_1 + f_2$.
Para isolar o congestionamento do poder de mercado, o caso básico supõe
demanda perfeitamente elástica: paga-se um preço total fixo $p$ e a tarifa é
$p - t(F)$, com $t(F)$ o custo de tempo por passageiro, $t' > 0$ e
$t'' \ge 0$. Cada aeronave tem $s$ assentos, todos vendidos, e a empresa $i$
vende $s\,f_i$ deles: sua receita é

$$ [\,p - t(F)\,]\; s\, f_i, \qquad i = 1, 2 \tag{1} $$

Sem congestionamento o custo por assento é $\tau$, e o congestionamento
acrescenta $g(F)$ por voo, com $g \ge 0$, $g' > 0$, $g'' \ge 0$:

$$ \pi_i = [\,p - t(F)\,] s\, f_i - [\,\tau s + g(F)\,] f_i \tag{2} $$

Abrindo o colchete da receita e agrupando os custos que dependem de $F$:

$$ \pi_1 = (p - \tau)\, s\, f_1 - c(F)\, f_1 \tag{3} $$

$$ \pi_2 = (p - \tau)\, s\, f_2 - c(F)\, f_2 \tag{4} $$

$$ c(F) \equiv s\, t(F) + g(F), \quad c' > 0, \quad c'' \ge 0 \tag{5} $$

A equação (5) junta os dois custos, que entram na função-lucro da mesma
forma; os sinais de $c'$ e $c''$ vêm de $t$ e $g$ e são o pressuposto A3,
base das cotas sobre $\lambda$.

| símbolo | nome em `src/airline_delays/theory/model.py` | o que é |
|---|---|---|
| $f_1$, $f_2$ | `f1`, `f2` | voos do líder e do seguidor |
| $F$ | `F` | tráfego total, $f_1 + f_2$ |
| $p$ | `p` | preço total pago pelo passageiro |
| $\tau$ | `tau` | custo por assento sem congestionamento |
| $s$ | `s` | assentos por aeronave, todos vendidos |
| $c$, $c'$, $c''$ | `c0`, `c1`, `c2` | custo do congestionamento por voo |
| $\lambda$ | `lam` | quanto o seguidor corta por voo extra do líder |
| $x$ | `x` | a razão $f_2 c''/c'$, de que dependem as cotas |
| $\partial f_2/\partial f_1$ | `slope` | a reação do seguidor, deixada livre |
| $d$, $d'$, $d''$ | `d0`, `d1`, `d2` | demanda inversa e derivadas (seção 7) |

O que é suposto, e não provado, está em `assumptions` — oito itens da
monografia:

| # | pressuposto | status |
|---|---|---|
| A1 | demanda perfeitamente elástica em (1)–(11); excedente do consumidor zero e bem-estar igual ao lucro conjunto | suposto |
| A2 | todo assento é vendido; $s$ é exógeno e igual nas duas empresas | suposto |
| A3 | $c' > 0$ e $c'' \ge 0$, a equação (5) | suposto |
| A4 | a empresa 1 lidera e a 2 segue por hipótese; $f_1 > f_2$ decorre de quem lidera, não de tamanho | suposto |
| A5 | as tarifas de (10)–(11) são constantes por voo avaliadas na alocação eficiente e não alteram a reação do seguidor | suposto |
| A6 | a "Pressuposição 2" precisa de $-1 < \partial f_2/\partial f_1 \le -\tfrac12$ | vale se e somente se $c''/s \ge s^2 d''$ — condição desta derivação (seção 7) |
| A7 | a "Pressuposição 3" | verbal na monografia; ilustrada pela extensão deste repositório (seção 8) |
| A8 | existência e unicidade de um equilíbrio interior | verificada numericamente só para os parâmetros escolhidos |

## 2. O ótimo social

Sob demanda perfeitamente elástica o excedente do consumidor é zero, e o
bem-estar é o lucro conjunto $W = (p - \tau)\,s\,F - c(F)\,F$. As derivadas
em $f_1$ e $f_2$ são idênticas, porque as empresas entram em $W$ só via $F$;
por assento:

$$ p - \tau - \frac{F\,c'(F) + c(F)}{s} = 0 \tag{6} $$

**[monografia]** O volume é eficiente quando o preço total iguala o custo
marginal social de um assento. O mecanismo é aditivo: um voo extra da
empresa 1 eleva $c(F) f_1$ em $c + f_1 c'$ e $c(F) f_2$ em $f_2 c'$, e a
soma dividida por $s$ é $[F c' + c]/s$. Dê nome ao pedaço isolado:
$\mathrm{MCD} \equiv F\,c'(F)$ (`tolls.MCD`) é o dano marginal do
congestionamento, o custo que um voo extra impõe a **todos** os voos, o dele
próprio incluído. Por assento vale $\mathrm{MCD}/s$, e é como fração de
$\mathrm{MCD}$ que toda tarifa será medida.

## 3. O seguidor

A empresa 2 escolhe $f_2$ tomando $f_1$ como dado. Maximizar (4) em $f_2$ e
dividir por $s$ dá

$$ p - \tau - \frac{f_2\,c' + c}{s} = 0 \tag{7} $$

Compare com (6): onde o ótimo social carrega $F c'$, o seguidor carrega só
$f_2 c'$ — internaliza o dano que impõe aos próprios voos e ignora o que
impõe aos do rival, a raiz de tudo o que vem depois. Para saber como $f_2$
responde a $f_1$, diferencie (7) totalmente: escrita antes da divisão por
$s$ como $\Phi(f_1, f_2) = (p - \tau)s - c(F) - f_2\,c'(F)$, ela tem
parciais

$$ \frac{\partial \Phi}{\partial f_1} = -\,c' - f_2\,c'' , \qquad \frac{\partial \Phi}{\partial f_2} = -\,2c' - f_2\,c'' $$

A segunda tem dois $c'$ porque $f_2$ move $F$ e é também o multiplicador de
$f_2 c'$. O teorema da função implícita dá então

$$ \frac{\partial f_2}{\partial f_1} = -\,\frac{\partial \Phi/\partial f_1}{\partial \Phi/\partial f_2} = -\,\frac{c' + f_2\,c''}{2c' + f_2\,c''} \;\equiv\; -\lambda \;<\; 0 \tag{8} $$

(`reaction_slope.expression`): a seguidora reduz voos quando a líder aumenta
os dela. **[aqui]** Toda a informação de (8) cabe em uma razão. Com
$x \equiv f_2 c''/c' \ge 0$, dividir numerador e denominador por $c'$ dá
$\lambda = (1 + x)/(2 + x)$ (`reaction_slope.lambda_of_x`), e as duas cotas
da monografia viram uma linha de álgebra cada:
$\lambda - \tfrac12 = x/[2(2 + x)] \ge 0$ e $1 - \lambda = 1/(2 + x) > 0$
(`reaction_slope.lambda_minus_half` e `reaction_slope.one_minus_lambda`).
Logo $\tfrac12 \le \lambda < 1$ — `reaction_slope.lambda_lower` vale 0,5 e
`reaction_slope.lambda_upper_exclusive` vale 1 —, com $\lambda = \tfrac12$
se e somente se $c'' = 0$ (`reaction_slope.lambda_linear_cost`, 0,5).
**[monografia]** A seguidora corta entre metade e a totalidade de cada voo
extra da líder: metade exata sob custo marginal constante, e mais quanto
mais crescente esse custo.

## 4. O líder

A líder conhece a reação da seguidora e escolhe $f_1$ sabendo que $f_2$
responderá. Substitua $f_2 = f_2(f_1)$ em (3) e derive pela regra da cadeia:
$F$ move-se em $1 + \partial f_2/\partial f_1$ por voo extra da líder, e não
em 1. Dividindo por $s$,

$$ p - \tau - \frac{1}{s}\left[\,f_1\,c'\!\left(1 + \frac{\partial f_2}{\partial f_1}\right) + c\,\right] = 0 \tag{9} $$

**[monografia]** O fator $(1 + \partial f_2/\partial f_1) = 1 - \lambda$ é o
coração do resultado: menor que 1, encolhe a internalização da líder, que
prevê que cada voo cortado será parcialmente compensado por um voo a mais da
seguidora — o mecanismo de compensação de Daniel e Harback (2008). Como
$\tfrac12 \le \lambda < 1$, o fator fica entre 0 e $\tfrac12$: a líder
internaliza, no máximo, metade do que internalizaria se a rival não
reagisse.

**[aqui]** A monografia conclui daí que $f_1 > f_2$; dá para dizer mais. Em
(7) e (9) aparece a mesma receita líquida por assento $p - \tau - c/s$: a
primeira a iguala a $f_2 c'/s$, a segunda a $f_1 c'(1 - \lambda)/s$. Onde
ambas valem, $f_2 c' = f_1 c'(1 - \lambda)$, ou seja
$f_1 = f_2/(1 - \lambda)$ (`leader_follower.f1`). Como
$1 - \lambda = 1/(2+x)$, vem $f_1 = f_2\,(2 + x)$ e portanto
$f_1 - 2 f_2 = f_2\,x \ge 0$ (`leader_follower.f1_minus_2_f2`): a líder
opera **pelo menos o dobro** dos voos da seguidora, e exatamente o dobro sob
custo linear — a desigualdade da monografia com a constante que faltava. No
exemplo quadrático a razão é 2,2161 (`comparative_statics.cost_curvature`,
linha $q = 1$, chave `f1_over_f2`).

## 5. As tarifas que restauram o ótimo

![Figura 7 — Tarifas no ótimo simétrico por estrutura de mercado](../../reports/theory/figures/fig7_tarifas_por_estrutura.svg)

A Figura 7 põe as tarifas de (11) lado a lado, como fração do dano marginal, para monopólio, Cournot, a líder de Stackelberg sob custo linear e quadrático, e o comportamento atomístico (`reports/theory/figures.json`, `fig7`).

Líder e seguidora erram por motivos diferentes, e as tarifas que as levariam
ao ótimo diferem. A da líder tem de eliminar a diferença entre o termo
$f_1 c'(1 - \lambda)$ de (9) e o termo $F c'$ de (6):

$$ T_1 = F\,c' - f_1\,c'\,(1 - \lambda) = \left(f_2 - f_1\,\frac{\partial f_2}{\partial f_1}\right) c' = \frac{(f_2 + \lambda f_1)\,\mathrm{MCD}}{f_1 + f_2} \tag{10} $$

com $\mathrm{MCD} = (f_1 + f_2)\,c'$; as duas formas coincidem
(`tolls.leader_difference_form` e `tolls.leader_share_form`; identidade
`eq10_two_forms`). A de participação diz o que a líder paga: os voos que
ignora, mais a parcela $\lambda$ dos próprios. Para a seguidora, o mesmo
cálculo com (7) no lugar de (9) dá $T_2 = F\,c' - f_2\,c' = f_1\,c'$
(`tolls.follower`): a tarifa de Cournot pura, os voos do **rival** vezes o
custo marginal. Na alocação eficiente, simétrica, $f_1 = f_2 = f^*$, tem-se
$\mathrm{MCD}^* = 2f^*c'$ e $T_1^* = f^*(1 + \lambda^*)c'$:

$$ T_1^{*} = \tfrac12\,(1 + \lambda^{*})\,\mathrm{MCD}^{*} \tag{11} $$

(`tolls.leader_symmetric_share`). No mesmo ponto
$T_2^* = f^* c' = \tfrac12\,\mathrm{MCD}^*$ (`tolls.follower_over_MCD`,
0,5). **[BVD]** É o resultado que a monografia enuncia:

> Proposição 1: Com um líder de Stackelberg e um seguidor, do seguidor é
> cobrada tarifa de congestionamento ao estilo Cournot. Do líder é cobrada uma
> tarifa que fica entre o valor de Cournot e da tarifa atomística (o que
> equivale a 100 por cento do dado do congestionamento marginal de um voo
> extra).
>
> (monografia, seção 4.3)

**[aqui]** Sob custo linear $\lambda^* = \tfrac12$, e (11) vira um número:
$T_1^{*} = \tfrac34\,\mathrm{MCD}^{*}$, com `tolls.leader_over_MCD_linear`
valendo 0,75 — **exatamente o ponto médio** entre a tarifa de Cournot
($\tfrac12$) e a atomística (1). A monografia escreve:

> situa-se entre a metade da tarifa de Cournot e a tarifa atomística
>
> (monografia, seção 4.3)

A frase é tradução truncada de *halfway between*, "a meio caminho entre", e
não "a metade da tarifa de Cournot": esta seria $\tfrac14\,\mathrm{MCD}^*$,
abaixo da tarifa da seguidora, contradizendo a Proposição 1 da mesma página.
O valor é $\tfrac34$, o que a identidade `eq11_linear_3_4` verifica. Com
$c'' > 0$ o ponto médio deixa de valer: em
`comparative_statics.cost_curvature`, com $c(F) = 1000 + 50F + qF^2$, para
$q = 0$ a chave `lambda_star` é 0,5 e `T1_star_over_MCD` é 0,75; para
$q = 4$, 0,5825 e 0,7912 — a tarifa vai na direção da atomística sem
alcançá-la, porque $\lambda < 1$.

**[aqui]** As tarifas (10) e (11) valem no ótimo. No **próprio equilíbrio de
Stackelberg**, onde $f_2 = (1 - \lambda) f_1$ pela seção 4, a forma de
participação colapsa:
$T_1 = (f_2 + \lambda f_1)c' = [(1-\lambda) f_1 + \lambda f_1]c' = f_1 c' = T_2$
(identidade `T1_equals_T2_at_stackelberg`). Ali as duas precisam da
**mesma** tarifa por voo, por razões diferentes — a seguidora porque ignora
os voos da líder, a líder porque antecipa a compensação. No exemplo linear
ambas valem 4.500 (`examples.linear.stackelberg.T1` e `.T2`), ou 0,6667 do
dano marginal (`.T1_over_MCD`), entre 0,5 e 0,75 porque o equilíbrio não é o
ótimo.

## 6. Os pontos de referência: Cournot, atomístico, monopólio

![Figura 6 — A função de reação da seguidora e os equilíbrios (exemplo linear)](../../reports/theory/figures/fig6_funcao_de_reacao.svg)

A Figura 6 desenha, no exemplo linear, a reação da seguidora e os pontos de Cournot, de Stackelberg e do ótimo simétrico (`reports/theory/figures.json`, `fig6`).

Três estruturas calibram a escala. Sob **Cournot**,
$p - \tau - (f_i\,c' + c)/s = 0$ (`benchmarks.cournot`): cada empresa
internaliza a própria parcela do dano, e a tarifa é os voos da rival vezes
$c'$, na simetria $\tfrac12\,\mathrm{MCD}$ (identidade
`cournot_toll_half_at_symmetry`, Brueckner 2002). Sob comportamento
**atomístico**, $p - \tau - c/s = 0$ (`benchmarks.atomistic`): nada é
internalizado e a tarifa é o dano marginal inteiro. Sob **monopólio**, a
condição coincide com (6) (identidade `monopoly_foc_is_social`, Brueckner
2002) e a tarifa é zero — internalização não é virtude, é consequência de
tamanho.

**[aqui]** Com custo linear $c(F) = a + bF$ e $D \equiv (p - \tau)s - a$
tudo tem forma fechada (`linear_closed_forms`): $F^* = D/2b$; cada
duopolista de Cournot voa $D/3b$; a líder voa $D/2b$ e a seguidora $D/4b$;
as atomísticas voam $D/b$, o dobro do eficiente. As perdas são frações
exatas de $W^*$: $1/9$ sob Cournot, $1/4$ sob Stackelberg e a totalidade sob
atomismo (chaves `loss_share_cournot`, `loss_share_stackelberg` e
`loss_share_atomistic`; identidade `linear_welfare_losses`). O exemplo usa
$p = 300$, $\tau = 200$, $s = 100$ e $c(F) = 1000 + 100F$, com $D = 9.000$ e
$b = 100$ (`examples.linear.primitives` e `.cost`):

| estrutura | forma fechada | exemplo linear | chave em `examples.linear` | fração de $W^*$ perdida |
|---|---|---|---|---|
| ótimo social | $D/2b$ | 45 | `social_optimum.F_star` | 0 |
| monopólio | $D/2b$ | 45 | `monopoly.F` | 0 |
| Cournot | $2D/3b$ | 60, sendo 30 de cada | `cournot.F` e `cournot.f1` | 0,1111 |
| Stackelberg | $3D/4b$ | 67,5, sendo 45 e 22,5 | `stackelberg.F`, `.f1` e `.f2` | 0,25 |
| atomístico | $D/b$ | 90 | `atomistic.F` | 1 |

A última coluna é a chave `loss_share` de cada bloco; o bem-estar no ótimo é
$W^* = 202.500$ (`examples.linear.social_optimum.welfare_star`) e, no ótimo
simétrico, $\mathrm{MCD}^* = 4.500$, $T_1^* = 3.375$ e $T_2^* = 2.250$
(`examples.linear.tolls_at_symmetric_optimum.MCD_star`, `.T1_star` e
`.T2_star`) — a razão entre 3.375 e 4.500 é os três quartos da seção 5. Note
a ordem: Stackelberg perde **mais** que Cournot (0,25 contra 0,1111), porque
o $1 - \lambda$ de (9) corrói o incentivo de conter voos.

## 7. Demanda inelástica e a "Pressuposição 2"

![Figura 9 — Demanda inelástica: o total de Stackelberg contra o ótimo](../../reports/theory/figures/fig9_demanda_inelastica.svg)

A Figura 9 mostra o total de Stackelberg contra o eficiente à medida que a demanda inclina (`reports/theory/figures.json`, `fig9`).

A demanda perfeitamente elástica é simplificação forte num mercado com
milhagem e passageiros corporativos. Relaxe-a: $p = d(sF)$, $d' < 0$. A
líder maximiza
$\pi_1 = d\big(s(f_1 + f_2(f_1))\big)\,s f_1 - \tau s f_1 - c(f_1 + f_2(f_1))\,f_1$
em $f_1$; agora a cadeia atinge dois lugares — preço e custo — e cada um
carrega o fator $1 + \partial f_2/\partial f_1$. Dividindo por $s$:

$$ d + s\,f_1\,d'\!\left(1 + \frac{\partial f_2}{\partial f_1}\right) - \tau - \frac{1}{s}\left[\,f_1\,c'\!\left(1 + \frac{\partial f_2}{\partial f_1}\right) + c\,\right] = 0 \tag{12} $$

(`inelastic.leader_foc`). A condição eficiente sai de maximizar o excedente
total $\int_0^{sF} d(q)\,dq - \tau s F - c(F)F$ e é (6) com $d$ no lugar de
$p$: $d - \tau - [F c' + c]/s = 0$ (`inelastic.social_foc`).
**[monografia]** Comparar (12) com ela revela **duas** distorções de sinais
opostos, separadas pelos extremos da reação do seguidor. Se
$\partial f_2/\partial f_1 = -1$, os termos com o fator somem e (12) colapsa
em $d - \tau - c/s = 0$ (`inelastic.limit_slope_minus_one`), a condição
atomística: a líder não internaliza nada **e** não explora poder de mercado
nenhum, e só a parte não internalizada precisa de correção, pela tarifa
atomística inteira. Se $\partial f_2/\partial f_1 = -\tfrac12$, sobra metade
de cada, $d + s f_1 d'/2 - \tau - (f_1 c'/2 + c)/s = 0$
(`inelastic.limit_slope_minus_half`): metade do poder de mercado, pelo termo
$s f_1 d'/2 < 0$ (`inelastic.market_power_term_at_minus_half`), e nenhuma
internalização, pelo termo $f_1 c'/2s > 0$
(`inelastic.uninternalised_term_at_minus_half`). Daí o enunciado:

> Pressuposição 2: O líder Stackelberg, quando enfrenta uma demanda inelástica,
> maximiza seu lucro no intervalo que apresenta como limite inferior o caso em
> que não explora seu poder de mercado mas falha na internalização do
> congestionamento e, como limite superior, o caso em que exerce metade do seu
> poder de mercado sendo incapaz também de internalizar o congestionamento.
>
> (monografia, seção 4.4)

A Pressuposição 2 não é teorema novo: é a leitura dos extremos de (12),
condicional a que $-1 < \partial f_2/\partial f_1 \le -\tfrac12$ valha sob
demanda inelástica — cota que a monografia toma emprestada do caso elástico,
provada em (8), sem reprová-la. É o pressuposto A6.

**[aqui]** A cota pode ser derivada, e não vale sempre. Repetindo para a
seguidora sob $p = d(sF)$ o que a seção 3 fez sob preço fixo,
$\partial f_2/\partial f_1 = -A/B$ com

$$ A = \frac{c' + f_2 c''}{s} - s\,d' - s^2 f_2\,d'' , \qquad B = A + \frac{c'}{s} - s\,d' $$

(`inelastic.slope_A` e `inelastic.slope_B`), e a distância até a cota é uma
linha:

$$ -\frac{\partial f_2}{\partial f_1} - \tfrac12 = \frac{f_2\left(c''/s - s^2 d''\right)}{2B} $$

de modo que $\partial f_2/\partial f_1 \le -\tfrac12$ vale se e somente se
$c''/s \ge s^2 d''$ (`inelastic.slope_bounds_condition`; identidade
`lambda_inelastic_general`) — automático para demanda linear ou côncava, e
**não** garantido para demanda convexa. Com $d'' = 0$ a inclinação vira
$-(k + f_2 c'')/(2k + f_2 c'')$, com $k = c' - s^2 d' > 0$
(`inelastic.slope_linear_demand`; identidade `lambda_linear_demand`): a
estrutura de (8) com $k$ no lugar de $c'$.

O exemplo linear-linear ($c = 1000 + 100F$, $d(Q) = 400 - 0{,}015\,Q$) dá
$f_1 = 38$, $f_2 = 19$, preço 314,5 e tráfego 57
(`examples.inelastic_linear_demand.stackelberg.f1`, `.f2`, `.price` e `.F`),
contra $F^* \approx 54{,}29$ (`.social_optimum.F_star` do mesmo bloco). Os
dois termos de (12) nesse ponto valem $-28{,}5$ (poder de mercado) e $19$
(parte não internalizada), com tarifa atomística por assento de 57
(`examples.inelastic_linear_demand.equation_12_terms_at_stackelberg.market_power_term`,
`.uninternalised_term` e `.atomistic_toll_per_seat`).

**Observação deste repositório.** Os dois termos puxam em direções opostas e
qual vence depende da inclinação da demanda. Em
`comparative_statics.demand_slope`, com o mesmo custo linear: para $dd = 0$
o total de Stackelberg é 67,5 contra $F^* = 45$; para $dd = 0{,}015$, 57
contra 54,29; e para $dd = 0{,}03$ o total cai a **35,625, abaixo** de
$F^* = 38$ — demanda íngreme o bastante faz o poder de mercado dominar, e o
líder voa de menos. A Pressuposição 2 descreve o intervalo dos dois termos;
não diz que a soma tenha sinal fixo.

## 8. A entrada de uma LCC e a "Pressuposição 3"

![Figura 10 — A entrante de baixo custo e a parcela internalizada](../../reports/theory/figures/fig10_entrante_lcc.svg)

A Figura 10 compara as parcelas internalizadas do dano marginal no duopólio e no triopólio com a entrante (`reports/theory/figures.json`, `fig10`).

A última peça da seção 4 motiva as dummies de empresa do artigo de 2016:

> Pressuposição 3: A entrada de uma empresa aérea de baixo custo no mercado
> quebra a estrutura do jogo em Stackelberg. Devido à estrutura do modelo de
> negócios de uma empresa aérea de baixo custo, é coerente pressupor que tais
> empresas procurem internalizar os custos do congestionamento, uma vez que
> tais custos podem afetar o planejamento estratégico de longo prazo da empresa
> que busca o crescimento de sua participação de mercado.
>
> (monografia, seção 4.5)

**[monografia]** A Pressuposição 3 é verbal: não há equação por trás dela, e
é o status A7 em `assumptions`. É também a hipótese que assina as dummies de
2013 — a razão para esperar sinais diferentes de uma incumbente e de uma
entrante. O terreno verbal está no capítulo 01, seção 7
([01-economia-do-congestionamento.md](01-economia-do-congestionamento.md)).

**[aqui]** Este repositório a converte em algo imprimível; o que segue é
**extensão deste repositório, não da monografia** (`extension_lcc.label`). É
um triopólio de Cournot com custo linear e uma entrante de custo por assento
menor ($\tau = 170$ contra 200 das incumbentes): com
$D_i = (p - \tau_i)s - a$, o equilíbrio é $F = \sum_i D_i/\big((n+1)b\big)$
e $f_i = D_i/b - F$, e $f_i/F$ é a parcela do dano marginal que $i$
internaliza. Em `extension_lcc.triopoly`, o tráfego total é 75 (chave `F`),
contra 60 no duopólio de Cournot (`extension_lcc.duopoly_cournot.F`) e 67,5
no de Stackelberg (`extension_lcc.stackelberg_duopoly_F`); os voos se
repartem em 45 para a entrante e 15 para cada incumbente (`.flights`); e as
parcelas internalizadas são 0,60 contra 0,20 (`.internalised_share`).

A entrante internaliza mais **porque voa mais**, e voa mais porque seu custo
é menor. Esse é o sentido preciso — e o único — em que "uma empresa de baixo
custo tem incentivos a internalizar o próprio congestionamento" vale neste
modelo: internalização é função da participação, e participação é função do
custo; é argumento de tamanho, não de modelo de negócios. O que a extensão
**não** mostra: não há sequência temporal, e a quebra do jogo é imposta, não
deduzida; nem aeroporto a escolher, nem preço.

## 9. A formulação levada aos preços: Guo, Jiang e Wan (2018)

O termo de auto-internalização de Cournot — a parcela própria do dano
marginal, o $f_i c'$ da seção 6 — pode ser lido dentro da tarifa aérea. É o
que fazem Guo, Jiang e Wan (2018, *Transportation Research Part A* 118,
648–661, DOI `10.1016/j.tra.2018.10.012`).

**O modelo, na nossa notação.** Uma empresa $i$ opera em vários mercados a
partir de um aeroporto A, com tráfego próprio $q_{iA}$ ali e atraso de
congestionamento $D_A$, valorado a $\beta$ por unidade de tempo. Maximizando
a soma sobre mercados de $(p - c - \beta D_A)\,q$ em cada quantidade, a
condição de primeira ordem é

$$ p = c + \beta D_A - p'\,q + \beta\,D'_A\,q_{iA} $$

Os três primeiros termos são um Cournot comum; o quarto,
$\beta\,D'_A\,q_{iA}$, é o markup de auto-internalização: é o $f_i c'$ da
seção 6 escrito em passageiros no lugar de voos, o atraso marginal do
aeroporto vezes o tráfego próprio da empresa **naquele aeroporto**. Quem não
internaliza não tem esse termo, e os autores sintetizam os dois casos com um
indicador que o multiplica, 1 com internalização e 0 sem. Daí a hipótese
testável: a regressão é de log-tarifa contra log-atraso, log-passageiros da
empresa no aeroporto e a **interação** dos dois, com coeficiente positivo
sob internalização.

**Dados e desenho.** Tarifas do DB1B, tráfego do T-100 e atraso NAS do AOTP,
trimestrais para 2014–2015, sem os aeroportos controlados por slots (JFK,
LGA, DCA) e com efeitos fixos de empresa, mercado e trimestre. Contra a
causalidade reversa — tarifa alta reduz tráfego, que reduz atraso — usam
defasagem de um ano e um instrumento do AIR-21.

**O achado.** A interação é positiva e significante no agregado; por tipo, é
positiva e significante para as empresas de serviço completo (0,0436 a
0,0564) e não significante para as de baixo custo (entre $-0{,}0190$ e
$0{,}00833$) — Guo, Jiang e Wan 2018, Tabela 4, documento externo. A
conclusão, na frase deles: "FSCs internalize airport congestion externality
while LCCs do not" (Guo, Jiang e Wan 2018 — documento externo). A explicação
que oferecem não é comportamental: as de baixo custo escolhem aeroportos
menos congestionados (Gudmundsson et al. 2014).

**A crítica ao artigo de 2016.** É precisa: controlar por tráfego no nível
do aeroporto remove o efeito de mercado residual, mas remove **junto** o
canal que opera por redução de tráfego via preço maior; o que sobra medido é
a reprogramação, não o preço.

**Observação deste repositório.** A Pressuposição 3 e o "as LCCs não
internalizam via preço" parecem contraditórios e não são, porque falam de
margens distintas. Há pelo menos três: **reprogramação**, deslocar partidas
para fora do pico sem mudar o número de voos (Ater 2012), o canal medido em
2016 e o que sobra quando se controla por tráfego no aeroporto; **redução de
tráfego via preço**, o markup $\beta D'_A q_{iA}$ acima (Guo, Jiang e Wan
2018), o canal que esse controle apaga; e **escolha de aeroporto**, operar
onde o congestionamento não existe (Gudmundsson et al. 2014) — a estratégia
de aeroportos secundários e regionais que a monografia atribui à Azul, de
que Viracopos é o caso concreto brasileiro. Quem internaliza pela terceira
margem não precisa da segunda e não aparece naquela regressão: a
Pressuposição 3 afirma incentivo a internalizar, Guo, Jiang e Wan (2018)
medem uma margem específica, e as duas afirmações podem ser verdadeiras ao
mesmo tempo. A ponte para os regressores de 2016 está no capítulo 03
([03-do-modelo-ao-artigo.md](03-do-modelo-ao-artigo.md)); a recepção do
artigo, no capítulo 04 ([04-impacto.md](04-impacto.md)).

## 10. Verificação numérica e simulação

![Figura 8 — Estática comparativa na curvatura do custo de congestionamento](../../reports/theory/figures/fig8_estatica_curvatura.svg)

A Figura 8 acompanha λ* e a tarifa da líder ao longo da curvatura do custo (`reports/theory/figures.json`, `fig8`).

A álgebra é simbólica; os números saem de `src/airline_delays/theory/equilibrium.py`. O
seguidor vem de busca de raiz em intervalo delimitado: para um $f_1$ dado, o
intervalo é dobrado até (7) trocar de sinal e a raiz sai de `brentq` com
tolerância $10^{-12}$. O líder é resolvido **por cima** disso: para cada
$f_1$ candidato resolve-se o seguidor, calcula-se a inclinação da reação,
avalia-se (9) e busca-se a raiz em $f_1$ — sem ponto de partida, logo sem
sensibilidade a ele.

O exemplo quadrático ($c = 1000 + 50F + F^2$) exercita o que o linear
esconde, porque nele $c'' > 0$. Em `examples.quadratic`: o ótimo é
$F^* = 40{,}585$ (`social_optimum.F_star`); no ótimo simétrico
$\lambda^* = 0{,}5670$ e a tarifa da líder é 0,7835 do dano marginal
(`tolls_at_symmetric_optimum.lambda_star` e `.T1_star_over_MCD`), acima dos
três quartos do caso linear. No equilíbrio, $f_1 = 39{,}261$ e
$f_2 = 17{,}716$ (`stackelberg.f1` e `.f2`), razão 2,2161
(`comparative_statics.cost_curvature`, $q = 1$, `f1_over_f2`), igual a
$1/(1 - \lambda)$; a perda é 0,2340 de $W^*$ (`stackelberg.loss_share`).

Quatro testes de `tests/test_theory.py` prendem os resultados centrais:

| teste | o que ele prende |
|---|---|
| `test_reaction_slope_is_minus_one_half_under_linear_cost` | a equação (8) com $c'' = 0$, seção 3 |
| `test_leader_toll_at_symmetric_optimum_is_three_quarters_of_mcd_under_linear_cost` | os três quartos de (11), seção 5 |
| `test_follower_toll_has_the_cournot_form` | a forma de Cournot da tarifa do seguidor, seção 5 |
| `test_inelastic_slope_bounds_hold_under_linear_demand` | a condição de A6 sob demanda linear, seção 7 |

Há ainda dois testes de outra natureza: o primeiro resolve o caso quadrático
de novo com `sympy.nsolve` e compara com `brentq`, porque dois métodos
independentes devem coincidir; o segundo reconstrói
`reports/theory/model.json` em memória e falha se a cópia versionada
divergir — uma edição em `src/airline_delays/theory/` sem regerar o relatório deixa a suíte
vermelha, que é o correto. `meta.n_identities` registra 29 identidades
verificadas, cada uma com sua origem na lista `identities`, e todas valem.

## 11. Limites declarados

Nada do que segue é defeito de implementação: são limites do modelo, vários
declarados pela própria monografia. **Um líder e um seguidor** — o jogo tem
duas empresas com papéis fixos, e a monografia avisa:

> Ressalta-se que o modelo tal como está não se aplica diretamente ao caso
> brasileiro, onde a presença de dois possíveis líderes pode alterar os
> resultados do modelo econômico.
>
> (monografia, seção 4)

No período do artigo de 2016, TAM e Gol eram ambas grandes; com dois agentes
antecipando reações mútuas, a noção de função de reação muda e nenhuma cota
da seção 3 sobrevive sem reprova. **Sem franja competitiva** — Daniel (1995)
modela líder dominante mais franja atomística e chega a resultados
diferentes: é outro jogo. **A simetria de (11)** — a equação supõe simétrico
o nível eficiente, o que vale porque as duas empresas têm o mesmo custo e o
mesmo $s$ (A2 e A4); com custos diferentes, como na seção 8, o ótimo é
assimétrico e (11) não se aplica. **A cota emprestada da Pressuposição 2** —
a condição sob a qual ela de fato vale, $c''/s \ge s^2 d''$, é desta
derivação, e é violável por demanda convexa. **A Pressuposição 3 é verbal, e
a extensão é ilustrativa** — a seção 8 não deriva a quebra do jogo de
Stackelberg, não tem escolha de aeroporto e não tem preço. **Sem
financiamento de capacidade e sem variável de preço** — o modelo cobra
tarifas e não pergunta o que se faz com a receita, e o preço é dado, nunca
escolha estratégica; ausências que a própria monografia declara em sua seção
final. **Nada aqui é estimado, e sympy prova álgebra, não economia** — os
parâmetros são estilizados, escolhidos em `src/airline_delays/theory/families.py` para que o
caso linear tenha equilíbrios inteiros; a econometria de referência é a do
artigo de 2016. Uma identidade "valer" significa que a afirmação decorre dos
pressupostos em `assumptions`, e nada diz sobre se as empresas se comportam
como o modelo supõe — como a seção 9 mostra, essa é a pergunta empírica de
fato aberta.

## 12. Como reproduzir

```bash
just theory
uv run pytest tests/test_theory.py -q
```

O primeiro comando roda `src/airline_delays/theory/run.py`, é offline e determinístico, leva
cerca de um segundo e reescreve `reports/theory/model.json`,
`reports/theory/results.md` e as figuras, imprimindo as 29 identidades e o
resultado de cada uma. O segundo roda a suíte de teoria inteira, que deve
passar sem falhas. Uma segunda execução não altera nada em
`reports/theory/`: o relatório é função pura do código, sem carimbo de data
ou commit, e é por isso que o teste de defasagem detecta uma cópia
desatualizada.

Referências completas em [bibliografia.md](bibliografia.md).
