# A economia do congestionamento aeroportuário

Português (ADR-0006).

Este capítulo abre a Parte I e monta, do zero, a microeconomia de que o
resto do estudo depende. Quem o lê sai sabendo por que o congestionamento
aeroportuário é uma externalidade negativa, por que o nível eficiente de
congestionamento não é zero, como uma tarifa por voo e uma cota de slots
chegam ao mesmo ponto e quando cada uma erra, o que uma pista nova faz e o
que ela não faz, por que a rede *hub-and-spoke* puxa na direção oposta, e
como a literatura chegou à pergunta que Bendinelli, Bettini & Oliveira
(2016, *Transportation Research Part A* 85, 39-52, doi
10.1016/j.tra.2016.01.001) levaram aos dados: se a empresa que domina um
aeroporto já embute nas próprias decisões o atraso que provoca. O texto
segue as seções 2 e 3 da monografia de graduação do autor (USP, 2013),
citada como documento externo. As cinco figuras são redesenhos paramétricos
feitos por `src/airline_delays/theory/figures.py`, adaptados de Cohen e
Coughlin (2003) e de Cohen, Coughlin e Ott (2009), não copiados: todo
número em prosa é uma coordenada de `reports/theory/figures.json`, com a
chave nomeada, ou uma transcrição marcada "(monografia — documento
externo)". Nada aqui é estimado.

## 1. Congestionamento como externalidade negativa

Uma externalidade negativa é um custo que a decisão de um agente impõe a
terceiros sem passar por um preço. No aeroporto cheio, o voo a mais que uma
empresa programa no pico atrasa os voos das outras. Quem o programa paga
combustível, tripulação e tarifa de pouso — o custo privado — e não paga o
atraso alheio, que fica com terceiros:

> os custos sociais (ou seja, os custos privados mais os custos forçados a
> terceiros) excedem os custos privados.
>
> (monografia, seção 2.1 — documento externo)

Escreva $`Q`$ para o número de voos programados no período de pico,
$`\mathrm{CMgP}(Q)`$ para o custo marginal privado de um voo e
$`\mathrm{CMgE}(Q)`$ para o custo marginal externo, o atraso que esse voo
impõe aos demais. O custo marginal social é a soma:

```math
\mathrm{CMgS}(Q) = \mathrm{CMgP}(Q) + \mathrm{CMgE}(Q) \tag{1.1}
```

Tudo o que segue decorre de $`\mathrm{CMgE}(Q) > 0`$ acima de certo tráfego.
Abaixo do limiar de capacidade um voo a mais não atrasa ninguém; acima dele,
cada voo adicional atrasa todos os que já disputam a pista, e o atraso cresce
com a fila. O limiar é um número físico: em Congonhas, 33 movimentos por
hora para a aviação comercial depois de 2007 (`data/external/capacity.csv`).
A monografia mede a escala do problema com dois números da ANAC: 33,6% dos
voos atrasados em 2007 e 12,9% em 2012 (monografia, introdução — documento
externo), nenhum recalculado aqui.

**[aqui]** O mesmo objeto reaparece na Parte II com outro nome. Lá o tráfego
é $`F`$ voos e $`c(F)`$ é o custo de congestionamento por voo; o custo
externo marginal de um voo é o que ele acrescenta ao custo de todos os
outros, $`F\,c'(F)`$, que o capítulo 3 chama de dano marginal de
congestionamento, $`\mathrm{MCD}`$. Este capítulo fala em
$`\mathrm{CMgE}`$; o modelo, em $`\mathrm{MCD}`$; é a mesma quantidade.

## 2. O nível eficiente de congestionamento e a tarifa pigouviana (Figura 1)

![Figura 1 — O nível eficiente de congestionamento](../../reports/theory/figures/fig1_nivel_eficiente.svg)

*O que ver: o mercado para em A, onde o benefício marginal cruza o custo
privado; o ótimo está em C, onde ele cruza o custo social; o triângulo ABC é
o desperdício. Curvas e coordenadas em `reports/theory/figures.json`, chave
`fig1`.*

O custo marginal privado é plano enquanto o aeroporto está folgado e sobe a
partir do limiar de congestionamento $`Q_c`$. O custo marginal social
coincide com ele abaixo de $`Q_c`$ e descola acima, porque soma o atraso
imposto às demais. O benefício marginal $`\mathrm{BMg}`$ decresce com o
volume. A empresa que decide sozinha programa até o benefício marginal
igualar o **seu** custo, o ponto A; o planejador para onde o benefício
marginal iguala o custo **social**, o ponto C:

```math
\mathrm{BMg}(Q_P) = \mathrm{CMgP}(Q_P), \qquad \mathrm{BMg}(Q_S) = \mathrm{CMgS}(Q_S) \tag{1.2}
```

| grandeza | valor | chave em `figures.fig1` |
|---|---|---|
| limiar de congestionamento $`Q_c`$ | 40 | `quantities.Q_c` |
| inclinações acima de $`Q_c`$: $`\mathrm{CMgP}`$, $`\mathrm{CMgS}`$, $`\mathrm{BMg}`$ | 0,5; 1,5; −1 | `curves` |
| equilíbrio privado, ponto A: $`Q_P`$, $`P_P`$ | 60, 40 | `quantities.Q_P`, `quantities.P_P` |
| ótimo social, ponto C: $`Q_S`$, $`P_S`$ | 52, 48 | `quantities.Q_S`, `quantities.P_S` |
| área do triângulo ABC | 80 | `quantities.triangle_ABC_area` |
| tarifa pigouviana em $`Q_S`$ | 12 | `quantities.toll_pigou_at_QS` |
| segmento AD, $`P_S - P_P`$ | 8 | `quantities.toll_AD_equals_PS_minus_PP` |

Repare no que a figura **não** diz:

> o nível eficiente de congestionamento não é zero, mas sim uma certa
> quantidade positiva.
>
> (monografia, seção 2.2 — documento externo)

Entre $`Q_c`$ e $`Q_S`$ há fila, e ela compensa: cada um desses voos vale
mais do que custa à sociedade inteira. O desperdício está entre $`Q_S`$ e
$`Q_P`$, os voos cujo custo social supera o benefício, e mede a área do
triângulo ABC.

**A tarifa pigouviana.** O remédio clássico para uma externalidade é cobrar
de quem a causa exatamente o custo que ela impõe aos outros. Uma tarifa por
voo igual ao custo externo marginal no ótimo,

```math
t^{*} = \mathrm{CMgS}(Q_S) - \mathrm{CMgP}(Q_S) = \mathrm{CMgE}(Q_S) \tag{1.3}
```

desloca o custo privado para cima em $`t^{*}`$ e faz a empresa parar em C
por conta própria. No redesenho, $`t^{*}`$ vale 12. **[aqui]** O texto da
monografia identifica a tarifa com o segmento AD, "a diferença entre
$`P_S`$ e $`P_P`$", que mede 8. As duas grandezas coincidem só quando o
custo privado é plano entre $`Q_S`$ e $`Q_P`$; com $`\mathrm{CMgP}`$ já
inclinado nesse trecho, $`P_S - P_P`$ subestima a tarifa necessária. É a
tarifa de (1.3) que a Parte II generaliza para empresas com poder de
mercado.

**Preço ou quantidade.** A tarifa é o instrumento de preço. O instrumento de
quantidade é limitar pousos e decolagens por janela de tempo — o conceito de
slot — e fixar a oferta em $`Q_S`$. Os dois levam ao mesmo ponto, mas a
quantidade traz uma pergunta que o preço não traz: quem fica com os slots. O
direito adquirido (*grandfathering*) protege o incumbente e pode deixar
horários valiosos com quem menos os valoriza. O leilão, com revenda
secundária, induz lances que revelam o valor verdadeiro e deixa a receita
com o poder público — a "captura de valor" de Cohen, Coughlin e Ott (2009),
que poderia financiar aeroportos menos eficientes. Brueckner (2009)
formaliza a comparação com empresas dotadas de poder de mercado e mostra que
um leilão de slots pode reproduzir o resultado da tarifa de congestionamento.
Oliveira (2012) leva a discussão ao caso brasileiro: o direito adquirido
contra a regulação realocativa de uma infraestrutura escassa. As datas em
que Guarulhos e Santos Dumont passaram a ter horários coordenados, em 2009,
estão em `data/external/slots.csv`.

## 3. Preço ou quantidade sob incerteza (Figura 2)

A seção anterior supõe o regulador onisciente. A Figura 2 mantém os custos
conhecidos e retira o conhecimento dos benefícios: o regulador age sobre um
benefício marginal esperado, $`\mathrm{BMgE}`$, e o mundo entrega um
realizado, $`\mathrm{BMgR}`$, mais alto.

![Figura 2 — Benefício marginal em condições de incerteza](../../reports/theory/figures/fig2_incerteza.svg)

*O que ver: com o benefício realizado acima do esperado, a cota deixa voos
de menos (triângulo ABC) e a tarifa deixa voos demais (triângulo CEF); o
menor dos dois triângulos aponta o instrumento que erra menos. Coordenadas
em `reports/theory/figures.json`, chave `fig2`.*

Calibrado na expectativa, o regulador escolhe uma tarifa por voo ou uma cota
de voos, e as duas estão certas para $`\mathrm{BMgE}`$. Quando o benefício
realizado surpreende para cima, cada instrumento erra a seu modo: sob a
tarifa, a empresa vê o custo privado deslocado e programa voos demais; sob a
cota, fica presa no volume antigo, voos de menos.

| grandeza | valor | chave em `figures.fig2.quantities` |
|---|---|---|
| tarifa fixada na expectativa | 12 | `toll_set_on_expectations` |
| cota fixada na expectativa | 52 | `Q_Q_quota` |
| voos sob a tarifa quando o benefício surpreende | 62 | `Q_T_under_the_toll` |
| volume eficiente sob $`\mathrm{BMgR}`$, ponto C: $`Q_S`$, $`P_S`$ | 58, 57 | `Q_S_efficient_under_BMgR`, `P_S` |
| perda da cota, triângulo ABC | 45 | `triangle_ABC_area_quantity_regulation` |
| perda da tarifa, triângulo CEF | 20 | `triangle_CEF_area_price_regulation` |

> Conforme a Figura 2, a área do triângulo CEF é menor que a área do
> triângulo ABC. Portanto, a regulação via preços seria preferível à de
> quantidade.
>
> (monografia, seção 2.3 — documento externo)

**[aqui]** Não é acaso do desenho. O custo marginal social é mais inclinado
que o benefício marginal — $`\lvert \mathrm{CMgS}' \rvert = 1{,}5`$ contra
$`\lvert \mathrm{BMg}' \rvert = 1`$ (`figures.fig2.note`) — e a regra geral
tem nome: Weitzman (1974). Benefício marginal mais inclinado que o custo
favorece a quantidade; mais plano, favorece o preço. A monografia chega à
conclusão pela geometria, sem citar a regra, e uma frase da sua seção 2.3 a
enuncia com o sinal trocado; vale a figura, não a frase.

Quatro desdobramentos completam a seção 2.3 da monografia. **Incerteza de
custo.** Se a dúvida estiver em $`\mathrm{CMgS}`$, e não em
$`\mathrm{BMg}`$, preço e quantidade dão o mesmo resultado. **Tarifas por
empresa.** A empresa grande já sofre parte da fila que provoca; com duas
empresas, a maior paga tarifa **menor** que a menor — resultado que o
capítulo 3 deriva como Proposição 1. **Quantidade com negociação.** Slots
distribuídos de graça e negociados entre as empresas chegam ao resultado
eficiente se os custos de transação forem baixos, argumento coasiano que
defende o direito adquirido quanto à eficiência, nunca quanto à entrada.
**Aeroportos não são ilhas.** Vizinhos são substitutos pelos passageiros e
complementares pela rede, e Czerny (2006) mostra que, sob tarifa, a
incerteza de demanda se propaga entre aeroportos, enquanto a restrição de
slots a interrompe — o único argumento da seção a favor da quantidade.

## 4. Expandir o aeroporto (Figura 3)

Tarifa e slot movem a demanda ao longo das curvas. Expandir o aeroporto
desloca $`\mathrm{CMgP}`$ e $`\mathrm{CMgS}`$ para a direita e empurra o
limiar de congestionamento.

![Figura 3 — Custo marginal social e privado antes e depois de uma expansão](../../reports/theory/figures/fig3_expansao.svg)

*O que ver: as mesmas curvas de custo antes e depois de o limiar saltar. Com
demanda elástica o equilíbrio acompanha a capacidade e continua
congestionado; com demanda inelástica ele fica parado e a fila desaparece.
Coordenadas em `reports/theory/figures.json`, chave `fig3`.*

O que decide o resultado é quem responde ao preço. Com demanda elástica, o
volume cresce até quase ocupar a capacidade nova: o equilíbrio migra para
além do novo limiar e o congestionamento sobrevive à obra. Com demanda
inelástica, o volume não muda, o preço cai e a fila acaba. Capacidade nova
compra mais viagem, não menos fila, sempre que a demanda responde.

| grandeza | valor | chave em `figures.fig3.quantities` |
|---|---|---|
| limiar antes e depois da expansão, $`Q_T`$ e $`Q_{TX}`$ | 40, 64 | `Q_T`, `Q_TX` |
| equilíbrio com demanda elástica, antes e depois | 60, 68 | `Q_E_before`, `Q_E_after` |
| congestionado depois da expansão, demanda elástica | sim | `elastic_still_congested_after` |
| volume com demanda inelástica | 50 | `Q_I` |
| preço com demanda inelástica, antes e depois | 35, 30 | `P_I_before`, `P_I_after` |
| congestionado depois da expansão, demanda inelástica | não | `inelastic_uncongested_after` |

Resta o que a comparação esconde: se a expansão vale o que custa. Cohen e
Coughlin (2003) pesam-na contra três benefícios — congestionamento evitado,
viagens novas e economia operacional — e nenhum dos três é automático. No
repositório, `data/external/capacity.csv` guarda a capacidade horária
declarada de que há registro, e `DECISIONS.md` ADR-0007 registra que a
medida de congestionamento por capacidade declarada espera a coleta das
declarações sazonais da ANAC; o painel de estimação do artigo carrega as
contagens de voos no pico e fora do pico feitas pelos próprios autores.

## 5. Externalidades de rede (Figuras 4 e 5)

Até aqui, um aeroporto sozinho. O sistema é uma rede *hub-and-spoke*: quem
embarca em um *spoke* beneficia quem conecta no *hub*, e esse benefício não
entra na conta do planejador local. É uma externalidade **positiva**, e ela
pede o remédio simétrico ao da seção 2.

![Figura 4 — Expansão do aeroporto levando em conta as externalidades de rede](../../reports/theory/figures/fig4_externalidade_de_rede.svg)

*O que ver: o benefício marginal local para em $`Q_0`$; o benefício social,
que inclui a rede, justifica $`Q_1`$; a distância vertical entre as duas
curvas em $`Q_1`$ é o subsídio. Coordenadas em `reports/theory/figures.json`,
chave `fig4`.*

O planejador que iguala o benefício marginal **local** ao custo marginal
para em $`Q_0`$; o benefício marginal **social**, que inclui a rede, está
acima, e o volume eficiente é $`Q_1`$. A diferença entre as curvas em
$`Q_1`$ é o subsídio — ou a transferência intergovernamental — que leva de
$`Q_0`$ a $`Q_1`$: a tarifa da seção 2 com o sinal trocado.

Juntas, as duas externalidades apontam para lados opostos, e a Figura 5 as
põe no mesmo gráfico.

![Figura 5 — Congestionamento e externalidades de rede](../../reports/theory/figures/fig5_congestionamento_e_rede.svg)

*O que ver: corrigir só o congestionamento reduziria o volume; corrigir só
a rede o aumentaria; corrigindo as duas, o ótimo cai sobre o volume de
mercado, porque a figura foi calibrada para os efeitos se cancelarem.
Coordenadas em `reports/theory/figures.json`, chave `fig5`.*

| grandeza | valor | chave |
|---|---|---|
| volume de mercado $`Q_0`$ (Figura 4) | 70 | `figures.fig4.quantities.Q_0` |
| volume eficiente com a rede $`Q_1`$ (Figura 4) | 85 | `figures.fig4.quantities.Q_1` |
| subsídio em $`Q_1`$ (Figura 4) | 15 | `figures.fig4.quantities.subsidy_at_Q_1` |
| volume de mercado $`Q_0`$ (Figura 5) | 60 | `figures.fig5.quantities.Q_0` |
| corrigindo só o congestionamento (Figura 5) | 52 | `figures.fig5.quantities.Q_S_congestion_only` |
| corrigindo só a rede (Figura 5) | 73,3333 | `figures.fig5.quantities.Q_N_network_only` |
| corrigindo as duas: $`Q^{*}`$, $`P^{*}`$ (Figura 5) | 60, 60 | `figures.fig5.quantities.Q_star`, `.P_star` |
| $`Q^{*} = Q_0`$ (Figura 5) | sim | `figures.fig5.quantities.Q_star_equals_Q_0` |

Na Figura 5 a política ótima é não fazer nada, e a monografia não vende isso
como regra geral:

> quando representados os dois tipos de externalidades, a prescrição
> política é ambígua, a menos que se saibam os tamanhos dos efeitos.
>
> (monografia, seção 2.4 — documento externo)

Se o congestionamento pesa mais, cabe tarifa; se a rede pesa mais, subsídio;
se empatam, silêncio. Qual é o caso é uma pergunta empírica, e é a pergunta
do artigo.

## 6. O debate da internalização, em ordem

A demanda cresce mais depressa que a capacidade dos aeroportos (Czerny e
Zhang 2011), e a resposta óbvia — elevar a tarifa até o nível eficiente da
Figura 1 — esbarra em três traços do setor. A **estrutura vertical**:
aeroportos a montante, empresas a jusante, cada um com seu preço. O
**oligopólio**: poucas empresas, cada uma com uma fatia visível do tráfego.
A **heterogeneidade dos passageiros**: quem viaja a negócios valoriza mais o
tempo. O ponto de discórdia é a **internalização**. A empresa grande sofre
parte da fila que provoca; se ela já embute esse custo nas próprias
decisões, a tarifa eficiente cai abaixo do nível atomístico — o de empresas
sem poder de mercado, que tratam todo atraso como externo — e cobrar a
tarifa atomística de uma empresa dominante seria cobrar duas vezes.

**Brueckner (2002)** abre o debate levando ao aéreo o modelo do transporte
de superfície. O monopolista internaliza integralmente, porque todo voo
atrasado é dele; sob Cournot, cada empresa internaliza só o congestionamento
que impõe aos próprios voos, a sua parcela do tráfego; e a tarifa eficiente
é a parcela **não** internalizada, menor quanto maior a empresa. O artigo
traz também evidência: aeroportos mais concentrados têm menos atraso. Como
observa Oliveira (2012), o resultado é elucidativo sobre o papel do
regulador. **Mayer e Sinai (2003)** separam dois efeitos que a concentração
mistura: o *hub* aumenta atrasos, porque a empresa concentra voos na mesma
janela para maximizar conexões, e a concentração os reduz, porque a
dominante internaliza. Nem todo atraso é um mal — o atraso do *hub* é o
preço de uma rede. **Daniel (1995)**, com um modelo de gargalo e filas
estocásticas para o *hub* de Minneapolis, conclui pela negativa: se a
dominante corta voos, concorrentes sem barreiras ocupam a lacuna, e o
incentivo evapora; a dominante comporta-se como atomística. **Daniel e
Harback (2008)** testam a hipótese nos grandes *hubs* norte-americanos,
rejeitam-na e propõem tratar todos os atrasos como externos.

**Brueckner e Van Dender (2008)** amarram as duas visões e trocam a
pergunta: o que decide não é a concentração, é a **estrutura** do jogo. Com
um líder de Stackelberg diante de uma franja competitiva, o líder prevê que
cada voo cortado será ocupado pela franja, e a tarifa eficiente volta ao
nível atomístico — o mundo de Daniel. Com um líder e um seguidor, o líder
internaliza parte, o seguidor internaliza como em Cournot, e a tarifa do
líder fica entre a de Cournot e a atomística: **[BVD]** a Proposição 1, que
o capítulo 3 deriva. **Rupp (2009)** leva a pergunta ao teste direto com
dados de voo dos Estados Unidos, e a evidência que encontra é mista; a
monografia o cita entre os que encontram internalização (monografia, seção
3 — documento externo). **Ater (2012)** encontra o canal: nos aeroportos
concentrados, a empresa espaça mais seus horários conforme a participação
cresce, o que reduz atrasos e limita o efeito de uma tarifa — internalizar é
reprogramar, não só voar menos.

Em torno desse eixo, a literatura acrescenta peças. **Pels e Verhoef
(2004)** confirmam a internalização de Cournot e somam a distorção de poder
de mercado: a tarifa ótima subtrai do dano marginal tanto a parcela já
internalizada quanto a correção pelo preço acima do custo marginal.
**Morrison e Winston (2007)** ficam no meio: só parte dos atrasos é
internalizada, e a tarifa eficiente fica entre a atomística e zero. **Zhang
e Zhang (2006)** ligam internalização a capacidade: internalizando, a
tarifa cobrável é limitada, e com ela os recursos para investir. **Basso e
Zhang (2008)** mostram que o aeroporto privado cobra mais e reduz bem-estar
— menos congestionamento não é, por si, melhor. **Czerny e Zhang (2011)**
trazem o passageiro: pode valer elevar a taxa para proteger quem tem alto
valor do tempo, efeito capaz de dominar o de mercado.

| obra | estrutura de mercado | quem internaliza | tarifa eficiente relativa à atomística |
|---|---|---|---|
| Brueckner (2002) | monopólio e oligopólio de Cournot | integralmente no monopólio, a própria parcela sob Cournot | nula no monopólio, reduzida sob Cournot |
| Mayer e Sinai (2003) | *hubs* de rede | a dominante, enquanto o efeito de rede eleva atrasos | pequena, com pouco efeito sobre a grade de voos |
| Daniel (1995) | dominante diante de franja com entrada livre | ninguém, na prática | igual à atomística |
| Daniel e Harback (2008) | dominante com franja, teste empírico | hipótese rejeitada nos dados | igual à atomística, com todo atraso tratado como externo |
| Brueckner e Van Dender (2008) | líder de Stackelberg com franja, ou com um seguidor | com franja, não; com um seguidor, em parte | atomística com franja; entre Cournot e atomística com um seguidor |
| Rupp (2009) | aeroportos norte-americanos, teste empírico | evidência mista | sem prescrição única |
| Ater (2012) | aeroportos concentrados | as dominantes, via espaçamento dos horários | positiva apenas nos picos de custo de fila |
| Pels e Verhoef (2004) | oligopólio de Cournot | a própria parcela | reduzida pela parcela e pela correção de poder de mercado |
| Morrison e Winston (2007) | oligopólio com dominância | parcialmente, as dominantes | abaixo da atomística, sem chegar a zero |
| Zhang e Zhang (2006) | oligopólio com poder de mercado e aeroporto investidor | a própria empresa, o que limita a tarifa cobrável | reduzida, ao custo do financiamento da capacidade |
| Basso e Zhang (2008) | aeroporto público comparado ao privado | a questão é o dono do aeroporto, não a aérea | mais alta sob aeroporto privado, com perda de bem-estar |
| Czerny e Zhang (2011) | passageiros heterogêneos, aéreas não atomísticas | as aéreas, mas o efeito passageiro domina | acima do que o poder de mercado sozinho justificaria |

## 7. O modelo de negócios de baixo custo e a entrante

A seção 4.5 da monografia sai da regulação e entra na firma. O modelo de
baixo custo — "sem supérfluos", porque a empresa oferece apenas o serviço
básico — produziu vocabulário próprio. O **efeito Southwest** é a queda de
tarifas quando uma empresa desse tipo passa a servir um aeroporto que não
tinha nenhuma (Pitfield 2008). Não há definição única, mas há consenso sobre
o método: tarifas baixas por estratégias que ora removem elementos da função
de produção, ora reduzem os que restam — cobrar serviços a bordo, encurtar o
tempo de escala, cortar comissões de venda, negociar duro as taxas com
aeroportos e fornecedores.

O preço menor gera tráfego novo mais do que o transfere: o volume das
incumbentes muda pouco, mas o resultado financeiro piora. Button (2012)
descreve a mudança estrutural — tarifas caindo, demanda crescendo,
tradicionais perdendo participação — e pergunta se o modelo se sustenta.
Dresner, Lin e Windle (1996) argumentam que o efeito é maior do que se
estimava, pelos transbordamentos do serviço da Southwest sobre rotas
concorrentes adjacentes. Morrison (2001) mede a concorrência efetiva,
adjacente e potencial trazida pela Southwest nas rotas norte-americanas de
1998: os passageiros da própria Southwest ganharam 3,4 bilhões de dólares e
os das demais operadoras, 9,5 bilhões (monografia, seção 4.5 — documento
externo). O modelo mexeu também com os aeroportos: para manter custos
baixos, essas empresas usam aeroportos pequenos, secundários ou terciários,
ou terminais dedicados nos principais — concorrência fora do ambiente
regulado, e a razão pela qual Gudmundsson, Paleari e Redondi (2014)
encontram as empresas de baixo custo onde o congestionamento não está.
Francis, Fidato e Humphreys (2003) questionam a sustentabilidade do arranjo:
o sucesso de muitas veio do crescimento rápido de passageiros nos aeroportos
onde operam, mas muitas fracassaram, e contratos que reflitam o risco de
fracasso ficam mais difíceis à medida que entrantes proliferam.

**Duas estratégias, dois casos brasileiros.** Uma entrante pode criar
mercado novo ou disputar mercado existente. A **Azul** seguiu a primeira,
com aeroportos secundários ou regionais como alvo — Viracopos, em Campinas,
é o caso concreto, que a monografia descreve sem nomear (observação deste
repositório). A **Gol**, entre 2001 e 2005, seguiu a segunda: mercados
grandes já disputados, com preços competitivos. Oliveira (2009) divide seus
primeiros anos em duas fases. Na de "baixo custo, tarifa baixa" o
crescimento foi exponencial, puxado por preços menores, publicidade
agressiva, estímulo de demanda, a saída da Transbrasil e o acesso a
Congonhas no primeiro ano e a Santos Dumont e à Ponte Aérea Rio de
Janeiro–São Paulo no segundo. Na fase seguinte, apenas de "baixo custo", o
crescimento arrefeceu, porém seguiu constante, sob a queda dos preços da
concorrência, a desvalorização cambial de 2002, o *code share* Varig–TAM de
2003 e a re-regulação do Departamento de Aviação Civil, com congelamento de
oferta em 2003 e restrições à precificação agressiva em 2004. Ao fundo está
a desregulamentação do mercado aéreo nacional a partir de 2000, que permitiu
tarifas menores ao aumentar a concorrência. Seja qual for a estratégia, a
tarifa baixa é a vantagem competitiva, e pesa mais onde há concorrentes.

**Por que a entrante muda os incentivos.** A literatura da seção 6 trata de
empresas com posição dada; a entrante muda a posição de todas. Em termos de
jogo, três coisas acontecem ao mesmo tempo. Primeiro, muda o número de
jogadores: com $`n`$ empresas em Cournot, cada uma internaliza a sua parcela
$`f_i/F`$ do dano marginal, e a soma das parcelas é sempre um; a entrante
toma parcela das incumbentes, que passam a internalizar menos. Segundo, muda
quem tem tamanho: a empresa de custo menor voa mais e, por isso, internaliza
mais. Terceiro, muda a estrutura: um líder que antecipava um único seguidor
perde a previsibilidade de que o modelo de Stackelberg depende. Este é o
terreno da **Pressuposição 3** da monografia — **[monografia]** a hipótese
de que a entrada de uma empresa de baixo custo quebra o jogo de Stackelberg
e de que tal empresa tem motivo próprio para internalizar o
congestionamento —, enunciada e discutida no capítulo 3. **[aqui]** A
extensão numérica deste repositório dá tamanho aos dois primeiros efeitos,
com uma entrante de custo por assento menor num triopólio de Cournot com
custo linear (`extension_lcc` em `reports/theory/model.json`):

| grandeza | duopólio de incumbentes | triopólio com a entrante | chave em `extension_lcc` |
|---|---|---|---|
| custo por assento: entrante, incumbentes | —, 200 | 170, 200 | `entrant_tau`, `incumbent_tau` |
| voos: entrante, incumbentes | —, 30 e 30 | 45, 15 e 15 | `duopoly_cournot.flights`, `triopoly.flights` |
| parcela internalizada do dano marginal | 0,5 e 0,5 | 0,6, 0,2 e 0,2 | `duopoly_cournot.internalised_share`, `triopoly.internalised_share` |
| tráfego total $`F`$ | 60 | 75 | `duopoly_cournot.F`, `triopoly.F` |

A entrante internaliza a maior parcela porque voa mais, e voa mais porque
custa menos; as incumbentes passam de metade a um quinto cada, e o tráfego
total sobe. Os dois movimentos são o que o artigo procura nos dados: uma
empresa de baixo custo na rota e no aeroporto, e o que a presença dela faz
ao atraso de todos.

## 8. Escopo e próximos passos

As figuras são estilizadas: curvas lineares por partes com parâmetros
escolhidos em `src/airline_delays/theory/figures.py`, não calibradas a dado
brasileiro; as áreas e tarifas das seções 2 a 5 são propriedades do desenho,
não do mundo. A revisão da seção 6 cobre a literatura até 2012, que é a da
monografia; o que veio depois — Guo, Jiang e Wan (2018) e a recepção do
artigo — está no capítulo 3
([03-o-jogo-do-congestionamento.md](03-o-jogo-do-congestionamento.md)) e no
capítulo 8 ([08-recepcao.md](08-recepcao.md)). Os percentuais da ANAC da
seção 1 são transcrições da monografia e não se comparam aos números da
replicação sem checar definição e universo. Cinco obras da bibliografia —
Morrison (1987), Schank (2005), Czerny (2010), Santos e Robin (2010) e de
Neufville e Odoni (2013) — são leitura de apoio a este capítulo, sobre
precificação de pistas, gestão do congestionamento, determinantes dos atrasos
e planejamento aeroportuário, e não são discutidas aqui.

O passo seguinte é formal. Este capítulo disse **o que** é internalizar e
**por que** a estrutura de mercado importa; falta dizer **como** uma
empresa decide quantos voos programar quando sabe que a rival vai reagir. O
capítulo 2 ([02-teoria-dos-jogos-fundamentos.md](02-teoria-dos-jogos-fundamentos.md))
ensina, com exemplos de empresas aéreas, as ferramentas de que essa pergunta
precisa — jogos, equilíbrio de Nash, funções de reação, indução retroativa,
a tarifa pigouviana como mecanismo — e o capítulo 3
([03-o-jogo-do-congestionamento.md](03-o-jogo-do-congestionamento.md)) as
usa para derivar o modelo do líder de Stackelberg e a Proposição 1,
transformando o $`\mathrm{CMgE}`$ desta página no
$`\mathrm{MCD} = F\,c'(F)`$ que as tarifas do modelo repartem.

## Onde conferir

- `reports/theory/figures.json` — as curvas, os pontos e as grandezas das
  Figuras 1 a 5, chaves `fig1` a `fig5`; os SVG estão em
  `reports/theory/figures/`.
- `src/airline_delays/theory/figures.py` — o código que desenha as cinco
  figuras e imprime essas grandezas; `tests/test_theory.py` confere que cada
  ponto rotulado está sobre as curvas que o definem.
- `reports/theory/model.json` — o bloco `extension_lcc` da seção 7.
- `data/external/capacity.csv` e `data/external/slots.csv` — a capacidade
  horária de Congonhas e as datas de coordenação de horários.
- `uv run airline-delays theory` (ou `just theory`) reescreve tudo isso em
  cerca de um segundo, offline; uma segunda execução sobre a árvore
  inalterada não muda nada.
- Referências completas em [bibliografia.md](bibliografia.md).
