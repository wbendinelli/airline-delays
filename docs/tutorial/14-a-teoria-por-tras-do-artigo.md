# M14 — A teoria por trás do artigo: derivada, verificada, e onde culmina

**Objetivo.** Ler a teoria que o artigo replicado pressupõe e não deriva —
a economia do congestionamento e o jogo de um líder de Stackelberg com um
seguidor — verificada por script, e ver onde ela culmina: no artigo de
2016 que este repositório replica, e no artigo de 2018 que levou a mesma
formulação às tarifas. Este módulo é a porta para a discussão temática de
[`../theory/README.md`](../theory/README.md); ela não é cronológica e não
renumera nada nos módulos M1–M13.

## Contexto (fora deste repositório)

A monografia de graduação *Efeitos da entrada de uma empresa aérea de
baixo custo na internalização das externalidades do congestionamento*
(USP/ESALQ, Piracicaba, 2013; orientadores Márcia Azanha Ferraz Dias de
Moraes e Alessandro Vinícius Marques de Oliveira) tem nove seções: a
economia do congestionamento, uma revisão da literatura da internalização,
um modelo de líder de Stackelberg segundo Brueckner e Van Dender (2008), e
uma estimação em painel sobre a base de regressão da própria monografia
(documento externo). O seu resumo fecha assim:

> "a entrada da Gol, apesar do seu efeito ambíguo, ceteris paribus, não foi
> suficiente para fazer com que seus rivais internalizassem os custos do
> congestionamento. Entretanto, como o fato reduziu a participação de
> mercado destes, contribuiu indiretamente para uma redução na quantidade
> de atrasos do sistema, enquanto que a entrada da 'Azul' em um aeroporto
> secundário e próprio internalizou o congestionamento."

Os metadados do arquivo dizem que ele foi criado em 2013-12-18, impresso
pela última vez em 2013-12-19 e revisado até 2014-02-17. A proposta de
mestrado que M1 descreve é de 2013-09-16. Os dois documentos são, portanto,
**contemporâneos**: em 2013 o mesmo autor, sob o mesmo orientador, fazia ao
mesmo tempo a pergunta de preços (M1) e a pergunta de atrasos e
internalização (aqui). Nenhuma data de defesa é afirmada — não foi lida.

A formulação de teoria dos jogos que a monografia começa foi levada às
tarifas por Guo, Jiang e Wan (2018, *Transportation Research Part A* 118,
648–661, DOI `10.1016/j.tra.2018.10.012`), construindo explicitamente sobre
o artigo de 2016 — ver
[`../theory/02-o-jogo-do-congestionamento.md`](../theory/02-o-jogo-do-congestionamento.md),
seção 9.

Esta descrição, incluindo o trecho entre aspas, vem do texto da própria
monografia, lido na íntegra pelo autor deste repositório. A monografia é
documento externo: não está aqui (M12) até que o depósito no Zenodo, em
curso, lhe dê um DOI (`[DOI-MONOGRAFIA]`). O artigo de 2018 é citado por
DOI e nunca redistribuído, como o de 2016.

## Arquivos deste repositório

- [`../theory/README.md`](../theory/README.md) — a ordem de leitura dos
  quatro capítulos e da bibliografia.
- `src/airline_delays/theory/model.py` — o modelo em `sympy`: equações (1)–(12), o declive de
  reação do seguidor e os seus limites, as tarifas da Proposição 1, os
  pontos de referência, a demanda inelástica; `IDENTITIES` e
  `ASSUMPTIONS`.
- `src/airline_delays/theory/equilibrium.py`, `src/airline_delays/theory/figures.py`,
  `src/airline_delays/theory/bridge.py` — os exemplos numéricos, as onze
  figuras (as cinco da monografia redesenhadas e seis sobre o jogo e a ponte),
  a ponte com os sinais publicados do artigo.
- `reports/theory/model.json`, `reports/theory/figures.json`,
  `reports/theory/results.md` e os onze SVG em `reports/theory/figures/`
  — tudo o que os capítulos citam, escrito por `src/airline_delays/theory/run.py`.
- `tests/test_theory.py` — cada identidade, os exemplos contra as formas
  fechadas, as figuras contra as suas curvas, e o relatório commitado contra
  o que o código produz hoje.
- `DECISIONS.md`, ADR-0019 — a decisão que autoriza esta camada.

## Comandos

```bash
just theory
uv run pytest tests/test_theory.py -q
```

**Número esperado.** O primeiro comando imprime uma linha que começa com
`theory: 29 identities hold` e diz que a tarifa do líder sob custo linear é
`0.75 MCD*` e que, no exemplo linear, o líder voa `f1 = 45` e o seguidor
`f2 = 22.5` — os mesmos valores de `reports/theory/model.json`
(`tolls.leader_over_MCD_linear`, `examples.linear.stackelberg`). Rodá-lo
uma segunda vez não muda nenhum arquivo sob `reports/theory/` — o
relatório não tem data nem commit, é função pura do código. O segundo
comando passa inteiro, incluindo
`test_leader_toll_at_symmetric_optimum_is_three_quarters_of_mcd_under_linear_cost`,
que fixa a fração 3/4, e o teste de *staleness*, que falharia se alguém
editasse `src/airline_delays/theory/` sem rodar `just theory`.

## Exercício

Derive à mão, das condições (7) e (9) do capítulo 02, a relação
$f_1 = f_2/(1-\lambda)$ — e conclua por que o líder voa pelo menos o dobro
do seguidor. Depois abra `src/airline_delays/theory/families.py`, troque
localmente o custo quadrático (`QuadraticCost`) por um mais curvo (por exemplo
`q = 4.0`), rode `uv run airline-delays theory --outdir /tmp/teoria` e leia em
`/tmp/teoria/model.json` os valores de `lambda_star` e `T1_star_over_MCD`
do exemplo quadrático. Para que lado a tarifa do líder se move quando o
custo marginal do congestionamento cresce mais depressa, e por quê? Não
commite a mudança: o teste de *staleness* existe para isso.

## Limites e próximos passos

A Proposição 1 é de Brueckner e Van Dender (2008); a monografia a reenuncia,
e este repositório a deriva e a afina — o líder paga exatamente três
quartos do dano marginal sob custo linear, a meio caminho entre Cournot e
a tarifa atomística, o que o texto de 2013 escreve como "entre a metade da
tarifa de Cournot e a tarifa atomística", tradução truncada. O modelo tem um
líder e um seguidor, e a própria monografia diz que dois líderes possíveis
podem mudar os resultados. A "Pressuposição 2" só vale sob uma condição que
nem a monografia nem a fonte enunciam, e que o capítulo 02 deriva. A
"Pressuposição 3" é verbal, e a extensão que a ilustra é deste repositório.
Nada foi estimado: a econometria de referência continua sendo a do artigo
de 2016, e os coeficientes da monografia aparecem em
[`../theory/03-do-modelo-ao-artigo.md`](../theory/03-do-modelo-ao-artigo.md)
como números externos. As cinco figuras são redesenhadas, não copiadas; e a
monografia em si não está aqui até ter DOI.
