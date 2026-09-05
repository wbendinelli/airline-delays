# Apresentação: a pergunta, a tese e o mapa do estudo

Português (ADR-0006).

Esta página abre o estudo. Ao terminá-la, o leitor sabe qual é a pergunta
econômica, o que Bendinelli, Bettini & Oliveira (2016, *Transportation
Research Part A* 85, 39-52, doi 10.1016/j.tra.2016.01.001) responderam, como
as três partes e os quatro apêndices se encadeiam, quais convenções valem em
todos os capítulos e por onde entrar conforme o que procura. "O artigo",
daqui em diante, é esse.

## A pergunta

Entre 2000 e 2013 o mercado aéreo doméstico brasileiro cresceu depressa e se
concentrou em poucos aeroportos. Os voos programados do universo de
replicação — tipos de linha N, R e E, DI 0, todos os aeroportos — passaram
de 659.301 em 2000 a 984.956 em 2013, alta de 49,4% (`reports/summary.json`,
chaves `reconstruction.flights_scheduled_first_year`,
`flights_scheduled_last_year` e `flights_growth_pct`). No mesmo período duas
empresas de baixo custo redesenharam o mapa competitivo: a Gol, a partir de
2001, e a Azul, a partir de 2008. A crise de 2006-2007 — dois acidentes
fatais e o apagão aéreo — fez do congestionamento dos aeroportos um problema
de política pública (`data/external/events.csv`).

A pergunta é a do artigo: **uma empresa aérea com poder de mercado
internaliza o congestionamento que causa?** Quando a empresa dominante de um
aeroporto sofre a maior parte do atraso que os seus próprios voos impõem uns
aos outros, ela tem razão para programar menos voos no pico, e a concentração
reduz o atraso. Quando a rivalidade disciplina a pontualidade melhor que a
dominância, a concentração aumenta o atraso. As duas hipóteses levam a
recomendações opostas sobre alocação de slots, precificação do aeroporto e
análise de fusões. A segunda pergunta é o que **a entrada de uma empresa de
baixo custo** muda nesse equilíbrio: a entrante altera a estrutura do jogo no
aeroporto e a pontualidade das incumbentes, inclusive em rotas em que ela não
voa.

## A tese do artigo, em três frases

Primeira: **instrumentada a concentração, mais concentração na cidade-extremo
mais concentrada da rota vem com menos atraso das empresas de serviço
completo** — a dominante internaliza o congestionamento que impõe a si
mesma. Segunda: **mais concentração na própria rota vem com mais atraso** —
na rota, o canal é a qualidade da concorrência, não a internalização.
Terceira: **uma empresa de baixo custo em uma das cidades-extremo reduz o
atraso das incumbentes**, o "spillover não-preço" do título, enquanto a sua
presença na rota em si não é significante para as chances de atraso.

| Regressor | 2SGMM (artigo, Tabela 3, coluna 2) | OLS (artigo, Tabela 6, coluna 2) |
|---|---|---|
| `rthhi`, HHI da rota | +0,8192** (0,410) | −0,3126*** (0,068) |
| `maxcthhi`, HHI da cidade-extremo mais concentrada | −1,5144*** (0,527) | +0,1057 (0,196) |
| `lcc`, baixo custo na rota | −0,0412 (0,072) | −0,1636*** (0,033) |
| `maxalccfu`, baixo custo em uma cidade-extremo | −0,4234** (0,179) | −0,1793 (0,137) |
| N | 19.419 | 19.590 |

Erros-padrão entre parênteses; as estrelas são os níveis de significância do
artigo. A variável dependente é `ODDS`, o logaritmo da razão de chances de uma
chegada das empresas de serviço completo (TAM, grupo Varig, Transbrasil,
Vasp) atrasar mais de quinze minutos na rota-mês. A inversão de sinal dos dois
HHI entre OLS e 2SGMM é o argumento identificador do artigo; o capítulo 7
mostra que ela se reproduz.

## As três partes e os apêndices

**Parte I — a economia.** O capítulo 1,
[`01-economia-do-congestionamento.md`](01-economia-do-congestionamento.md),
trata o congestionamento como externalidade: o nível eficiente, preço contra
quantidade sob incerteza, a expansão do aeroporto, as externalidades de rede,
a literatura da internalização e o modelo de negócio de baixo custo, com as
Figuras 1 a 5.

**Parte II — a teoria dos jogos.** O capítulo 2,
[`02-teoria-dos-jogos-fundamentos.md`](02-teoria-dos-jogos-fundamentos.md),
dá os fundamentos de que o modelo precisa — jogadores, estratégias, ordem
dos lances, resposta ótima, equilíbrio de Nash, Cournot e Stackelberg —
com um jogo discreto de duas empresas impresso em `reports/theory/model.json`
(bloco `primer`). O capítulo 3,
[`03-o-jogo-do-congestionamento.md`](03-o-jogo-do-congestionamento.md),
deriva passo a passo o jogo do congestionamento com uma líder de Stackelberg
e uma seguidora, equações (1)–(12): a função de reação da seguidora e os seus
limites, a relação $`f_1 = f_2/(1-\lambda) \ge 2 f_2`$ entre os voos das duas,
a tarifa ótima da líder como fração $`(1+\lambda)/2`$ do dano marginal de
congestionamento — 0,75 sob custo linear, entre a de Cournot (0,5) e a
atomística (1) —, a demanda inelástica e a entrante de baixo custo, com as
Figuras 6 a 10. As 29 identidades do modelo valem sob `sympy`
(`reports/summary.json`, `theory.n_identities`, `theory.n_holding`,
`theory.leader_toll_share_linear`, `theory.cournot_toll_share`,
`theory.atomistic_toll_share`).

**Parte III — o artigo.** O capítulo 4,
[`04-do-modelo-as-hipoteses.md`](04-do-modelo-as-hipoteses.md), liga cada
objeto do modelo a um regressor do artigo e ao seu sinal esperado, e explica
por que a concentração precisa ser instrumentada (Figura 11). O capítulo 5,
[`05-os-dados.md`](05-os-dados.md), vai do registro de voo da ANAC ao painel
rota × mês: as 13.652.322 etapas de voo (`reconstruction.staged.rows`), a
tabela-fato e os dois painéis. O capítulo 6,
[`06-especificacao-e-identificacao.md`](06-especificacao-e-identificacao.md),
escreve a especificação: 2SGMM, os sete instrumentos, os erros-padrão HAC e
a estatística de Kleibergen–Paap, implementada do zero neste repositório. O
capítulo 7, [`07-resultados-e-replicacao.md`](07-resultados-e-replicacao.md),
lê os resultados publicados e a replicação das Tabelas 2–7 sobre o painel de
estimação do artigo. O capítulo 8, [`08-recepcao.md`](08-recepcao.md), diz o
que o campo levou do artigo e o que continua em aberto.

**Apêndices.** [`apendice-a-previsao-de-atrasos.md`](apendice-a-previsao-de-atrasos.md)
vai além do artigo, com o preditor de atrasos por voo;
[`apendice-b-como-reproduzir.md`](apendice-b-como-reproduzir.md) dá os
comandos que reproduzem cada número;
[`apendice-c-direitos-e-licencas.md`](apendice-c-direitos-e-licencas.md) diz
quem detém o quê e sob qual licença;
[`apendice-d-extensoes.md`](apendice-d-extensoes.md) lista as extensões que o
código já sustenta; [`bibliografia.md`](bibliografia.md) é a lista única da
literatura citada.

| Parte | O que entrega | Números-manchete e sua chave em `reports/summary.json` |
|---|---|---|
| I | a economia do congestionamento, com as figuras redesenhadas | — |
| II | o modelo derivado e verificado | 29 identidades, 11 figuras (`theory.n_identities`, `theory.n_figures`) |
| III | o artigo e a sua replicação | 306 coeficientes comparados, 302 com o sinal publicado, 259 a menos de meio erro-padrão publicado, 84,6% (`estimation.totals.coefficients`, `sign_agreement`, `within_half_se`, `within_half_se_pct`) |
| Apêndice A | o preditor por voo | AUC de 0,715–0,741 na véspera e de 0,757–0,824 no portão (`prediction.rolling.horizons.D-1`, `.H-1`) |

## Convenções

- **Três rótulos.** **[BVD]** marca um resultado de Brueckner e Van Dender
  (2008) reenunciado; **[monografia]** marca um enunciado da monografia de
  graduação do autor (USP, 2013), citada como documento externo e única
  origem admitida da teoria antes do artigo; **[aqui]** marca o que a
  derivação deste repositório acrescenta.
- **Duas marcas de transcrição.** "(artigo, Tabela N)" acompanha um número
  copiado das tabelas publicadas, parseadas em
  `src/airline_delays/estimation/published.json`; "(monografia — documento
  externo)" acompanha o que só existe na monografia.
- **Nenhum número solto.** Todo número do estudo é um valor de
  `reports/summary.json`, de `reports/theory/model.json`, de
  `reports/replication/` ou de `src/airline_delays/estimation/published.json`,
  ou está marcado como documento externo; a frase ou a tabela que o traz nomeia
  a chave. Anos, DOIs, números de equação, de tabela e de ADR não são medições.
- **Os dois painéis.** "O painel de estimação do artigo" é o painel sobre o
  qual os autores estimaram as Tabelas 2–7, publicado em
  `data/analysis/article_panel_route_month.parquet` (ADR-0020); "o painel
  reconstruído" é o painel aberto construído aqui a partir dos arquivos da
  ANAC, `data/analysis/panel_route_month.parquet`. O que os liga são as mesmas
  definições — universo, mapa de nós, conjuntos de empresas, regras de atraso
  — registradas em `DECISIONS.md`.
- **Uma notação.** As Partes II e III usam a mesma notação, a de
  `src/airline_delays/theory/model.py`: duas empresas, 1 (líder) e 2
  (seguidora), voos $`f_1`$ e $`f_2`$, tráfego total $`F = f_1 + f_2`$, custo
  de congestionamento por voo $`c(F)`$ com $`c' > 0`$, reação da seguidora
  $`\lambda = -\partial f_2/\partial f_1`$. As equações (1)–(12) mantêm a
  numeração de Brueckner e Van Dender (2008) e da monografia.
- **Caminhos e comandos.** Um caminho entre crases existe neste repositório e
  um comando `just` ou `airline-delays` citado existe no `justfile` e na
  CLI; `scripts/check_docs_paths.py` confere ambos, e
  `scripts/check_markdown_math.py` confere que a matemática renderiza no
  GitHub. Cada capítulo fecha com "Onde conferir".
- **Língua.** O estudo é escrito em português por decisão (ADR-0006); nomes
  de coluna, comandos e caminhos ficam em inglês, idênticos aos do código.

## Como ler

| Leitor | Percurso |
|---|---|
| economista com pressa | capítulos 3, 4 e 7: o modelo, o que ele prevê para os regressores, o que o artigo encontrou e o que reproduz |
| estudante | capítulos 1 a 3, na ordem, e depois o 4: da externalidade ao jogo e do jogo às hipóteses |
| replicador | capítulos 5 a 7 e o Apêndice B: os dados, a especificação, a replicação e os comandos que a refazem |
| quem quer estender | Apêndice D, depois o Apêndice A: o que o código já sustenta e o que já foi além do artigo |

## O estudo em PDF

O mesmo estudo compila num único PDF, `reports/pdf/study.pdf`, a partir de
`reports/study.typ` com `just report` (`airline-delays report`), que precisa
do `typst` no PATH. O PDF traz as três partes e dois apêndices — as
identidades verificadas e como reproduzir; os apêndices sobre o preditor, os
direitos e as extensões existem só nesta edição em Markdown. A fonte Typst lê `reports/theory/model.json`,
`reports/theory/figures.json`, `reports/replication/summary.json`,
`reports/replication/results.json` e `reports/summary.json` com `json()`, e
embute as figuras de `reports/theory/figures/`: nenhum número do PDF é
digitado à mão, e o PDF é versionado (ADR-0022).

## Onde conferir

- `reports/summary.json` — `reconstruction.flights_scheduled_first_year`,
  `flights_scheduled_last_year`, `flights_growth_pct`,
  `reconstruction.staged.rows`; `published.table3.col2` e
  `published.table6.col2`; `theory.*`; `estimation.totals.*`;
  `prediction.rolling.horizons.*`.
- `src/airline_delays/estimation/published.json` — as células publicadas das
  Tabelas 2–7, marcadas "(artigo, Tabela N)".
- `reports/theory/model.json` — `leader_follower`, `tolls`, `primer`.
- `data/external/events.csv` — os eventos do período, com fonte e grau de
  confiança em cada linha.
