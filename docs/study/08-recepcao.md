# A recepção: o que o campo levou e o que continua em aberto

Português (ADR-0006).

Este capítulo fecha a Parte III. Ao terminá-lo, o leitor sabe o que a
literatura levou de Bendinelli, Bettini & Oliveira (2016, *Transportation
Research Part A* 85, 39-52, doi 10.1016/j.tra.2016.01.001) — três coisas, na
ordem em que os capítulos anteriores as construíram —; conhece o trabalho que
tomou a formulação do artigo e a levou às tarifas, Guo, Jiang e Wan (2018), e
o que ele muda na leitura da entrada de baixo custo; e sabe quais perguntas
continuam em aberto e onde, neste repositório, cada uma tem o seu ponto de
partida. Daqui em diante, "o artigo". Este capítulo não mede nem transcreve
números: os coeficientes de 2018 estão no capítulo 3, marcados como documento
externo, e a recepção contada (quantos trabalhos citam o artigo e por qual
achado) é objeto de um projeto à parte, não deste repositório.

## 1. O que o campo levou

O artigo deixou três coisas na literatura, e as três têm um capítulo atrás de
si neste estudo.

**A separação entre concentração da rota e concentração do aeroporto.** O
artigo testa, numa só equação, o poder de mercado onde a empresa vende
(`rthhi`) e a internalização onde ela congestiona (`maxcthhi`), com sinais
esperados distintos e um desenho de identificação para os dois (capítulos 4 e
6). É a peça que os trabalhos posteriores mais reaproveitam, porque converte
a pergunta do debate da internalização que o capítulo 1 revisa — quem
internaliza, e quanto — em algo estimável com dados de operação.

**A internalização medida no atraso.** O coeficiente negativo e significante
de `maxcthhi` no 2SGMM (capítulo 7,
[07-resultados-e-replicacao.md](07-resultados-e-replicacao.md)) é a
Proposição 1 do capítulo 3 vista nos dados: a empresa dominante do aeroporto
sofre a maior parte do congestionamento que causa e programa com mais cuidado.
É o achado pelo qual o artigo entra no debate da internalização ao lado dos
trabalhos que medem o mesmo objeto no atraso, entre eles Ater (2012).

**O derrame não-preço da entrada de baixo custo.** A presença de uma empresa
de baixo custo numa cidade-extremo reduz o atraso das incumbentes em rotas em
que a entrante não voa (`maxalccfu`). É o título do artigo e a Pressuposição 3
da monografia de graduação do autor (USP, 2013) tornada regressor. Dos três, é
o achado de mecanismo menos fechado — o capítulo 3 mostra que "internalizar"
tem mais de uma margem —, e é o que a seção 3 deixa em aberto.

A recepção medida — quantos trabalhos citam o artigo, por qual dos três
achados e com que fidelidade — é objeto de um projeto irmão do autor,
`citation-audit` (https://github.com/wbendinelli/citation-audit), com método e
números próprios. Eles são atualizados lá e não são impressos por nenhum
artefato deste repositório; por isso este capítulo não os transcreve.

## 2. O artigo que levou a formulação aos preços

Guo, Jiang e Wan (2018, *Transportation Research Part A* 118, 648–661)
constroem explicitamente sobre a separação da seção 1 e mudam o teste de
lugar: do atraso para a tarifa. O modelo deles na notação deste estudo, os
dados norte-americanos de 2014–2015 e os coeficientes publicados estão no
capítulo 3, seção 13
([03-o-jogo-do-congestionamento.md](03-o-jogo-do-congestionamento.md)); o que
importa aqui é o que encontraram e o que criticaram. Encontraram a interação
entre o atraso do aeroporto e o tráfego próprio — a parcela própria do dano
marginal escrita em passageiros — positiva e significante na tarifa das
empresas de serviço completo e não significante na das de baixo custo, e a
explicação que oferecem não é comportamental: as de baixo custo escolhem
aeroportos menos congestionados (Gudmundsson, Paleari e Redondi 2014). A
crítica ao artigo recai sobre o desenho, não sobre o achado: controlar por
tráfego no nível do aeroporto remove, junto com o efeito residual de mercado,
a parte da internalização que opera por redução de tráfego via preço maior; o
que sobra medido no atraso é a reprogramação de horários.

Lido ao lado do artigo, o resultado obriga a reler a Pressuposição 3. O artigo
mediu a internalização no atraso, controlando por tráfego do aeroporto; 2018 a
mediu no preço. O capítulo 3, seção 12, propõe — como leitura deste
repositório, marcada **[aqui]** — que "internalizar" tem pelo menos três
margens: reprogramar horários sem mudar o número de voos (Ater 2012), reduzir
tráfego via preço (Guo, Jiang e Wan 2018) e escolher o aeroporto
(Gudmundsson, Paleari e Redondi 2014). Sob essa leitura, "a entrante de baixo
custo internaliza" e "as de baixo custo não internalizam via preço" deixam de
ser contraditórios: a primeira afirma incentivo, a segunda mede uma margem
específica, e quem internaliza pela terceira margem não aparece numa regressão
de preços. A leitura é hipótese, não resultado: testá-la exige separar as três
margens no mesmo painel, e isso pede tarifas.

## 3. O que continua em aberto

Cada pergunta em aberto tem, no
[apendice-d-extensoes.md](apendice-d-extensoes.md), o que já existe para
construí-la e o que falta.

| Pergunta | O que falta | Ponto de partida neste repositório | Apêndice D |
|---|---|---|---|
| a internalização nos preços, e as três margens | os microdados tarifários da ANAC (`docs/data-availability.md`, fonte 4) | as chaves `route` e `ym` do painel reconstruído, prontas para uma junção por rota-mês | seção 5 |
| o HHI ponderado por passageiros, e os sete instrumentos, no painel reconstruído | os dados estatísticos da ANAC (fonte 3) | `passenger_weighted_hhi()` com a assinatura certa; `rthhi_flights` e `maxcthhi_flights` ao lado | seção 2 |
| o clima medido, e não inferido do código de justificativa | METAR da REDEMET/DECEA (fonte 9) | a chave estação × hora já existe nas etapas de voo | seção 4 |
| desenhos no nível do aeroporto, com Viracopos separado de São Paulo | uma agregação por `origin_icao` e `dest_icao`, não por nó | as duas colunas estão em toda etapa de voo de `data/staged/` | seção 7 |
| curto e longo prazo do efeito de baixo custo | um par de regressores que separe entrada recente de presença consolidada | `is_entry`, `entry_lcc` e as datas de `data/external/groups.csv` | seção 1 |
| a pergunta da monografia de 2013, no seu grão | a binária da Azul no próprio aeroporto, assentos, clima mensal, conexões | a tabela-fato no grão empresa × rota × mês, `arr_delayed_gt30`, `rthhi_flights` | seção 9 |

Nenhuma dessas extensões foi implementada nesta Parte III; descrever o caminho
não é percorrê-lo. O passo de maior alcance é a fonte 3: com ela a
especificação do capítulo 6
([06-especificacao-e-identificacao.md](06-especificacao-e-identificacao.md))
passa a poder rodar sobre os dois painéis, e a comparação entre eles deixa de
ser uma comparação de definições para ser uma comparação de estimativas.

## Escopo e próximos passos

Este capítulo descreve a recepção do artigo, não a deste repositório, que é
novo. Ele não conta citações e não reestima nada; o que afirma sobre o campo é
o que os capítulos anteriores permitem afirmar sobre o que o artigo deixou, e
o que afirma sobre 2018 é o que está publicado, marcado como documento
externo. O passo seguinte é o Apêndice D, na ordem da tabela da seção 3 — e,
antes dele, o Apêndice B
([apendice-b-como-reproduzir.md](apendice-b-como-reproduzir.md)), que diz de
qual artefato e de qual comando sai cada número do estudo.

## Onde conferir

- Nenhum número neste capítulo. Os coeficientes de Guo, Jiang e Wan (2018)
  estão no capítulo 3, seção 13, transcritos da Tabela 4 daquele artigo e
  marcados como documento externo.
- `reports/theory/model.json`, `extension_lcc` — a extensão de baixo custo do
  capítulo 3 de que a leitura por margens parte.
- `src/airline_delays/estimation/published.json` e `reports/summary.json`
  (`published`, `estimation`) — os coeficientes do artigo e a sua replicação,
  que a seção 1 resume.
- `docs/data-availability.md`, fontes 3, 4 e 9 — as fontes que cada pergunta
  em aberto exige.

Referências completas em [bibliografia.md](bibliografia.md).
