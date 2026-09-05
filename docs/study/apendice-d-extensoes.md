# Apêndice D — Extensões que o repositório já sustenta

Português (ADR-0006).

Este apêndice lista as extensões que o desenho de Bendinelli, Bettini &
Oliveira (2016, *Transportation Research Part A* 85, 39-52, doi
10.1016/j.tra.2016.01.001) sugere e que este repositório ainda não fecha, e
diz, para cada uma, o que já existe para construí-la, o que falta e qual é o
próximo passo concreto. "A arquitetura já sustenta" não é o mesmo que "já
está pronto", e cada seção diz qual dos dois é o caso. Ao terminá-lo, o
leitor sabe por onde começar a estender o artigo sem reextrair os arquivos da
ANAC.

## 1. Curto e longo prazo do efeito de baixo custo

**O que falta.** Um par de regressores que separe a entrada recente de uma
empresa de baixo custo da sua presença consolidada não existe em
`src/airline_delays/schema/columns.py`; as duas binárias do artigo, `lcc` e
`maxalccfu`, medem presença, não idade da presença.

**O que já existe.** `data/external/groups.csv` traz `start` e `end` datados
ao mês por empresa e grupo (ADR-0003); a tabela-fato marca a entrada e a saída
de um grupo na rota (`is_entry`, `is_exit`, `entry_lcc`); a camada de previsão
já carrega, por voo, `months_on_route` e `is_new_on_route`
(`docs/dictionary.md`). O próximo passo é uma função em
`src/airline_delays/fact/build.py` que, dado um corte — a data de entrada do
grupo na rota, não uma data fixa de calendário —, particione `sh_flights_lcc`
em dois regressores.

## 2. HHI ponderado por passageiros

**O que já existe.** `passenger_weighted_hhi()`, em
`src/airline_delays/definitions/concentration.py`, tem a assinatura certa e
devolve nulo até a fonte existir; as colunas `rthhi`, `maxcthhi` e `gmchhi`
existem no painel reconstruído, inteiramente nulas e documentadas como tal, e
as versões por participação em voos vão ao lado sob nome próprio,
`rthhi_flights` e `maxcthhi_flights` (`docs/dictionary.md`). O painel de
estimação do artigo carrega os valores dos autores.

**O que falta.** Os dados estatísticos da ANAC — passageiros pagos por
empresa-rota-mês (`docs/data-availability.md`, fonte 3) —, não coletados. O
próximo passo é um comando de coleta dessa fonte e um `join` por `route`,
`ym` e `group`, as três chaves que o painel reconstruído já usa. Com ela
entram também os sete instrumentos do artigo, hoje só no painel de estimação
(`reports/summary.json`, `reconstruction.article_columns_missing`).

## 3. O limiar de 30 minutos

**Já implementado.** `fsc_prdelarr1530` e `fsc_prdelarr30m` — e as variantes
`fscc_`, `all_`, `lccfu_` e `lccclass_` — existem no painel reconstruído
(`docs/dictionary.md`). A linhagem é longa: 30 minutos é o corte da Resolução
ANAC 218, sobre o qual a ANAC apura os seus próprios percentuais de atraso, e
é o corte da variável dependente da monografia de graduação do autor (USP,
2013), medida sobre outro conjunto de empresas e outro denominador
(monografia — documento externo); o corte de quinze minutos do artigo é a
convenção norte-americana. `fsc_prdelarr30m` é o que mais se aproxima da
medida de 2013.

## 4. Meteorologia (METAR)

**O que falta.** Nenhuma coluna de METAR existe aqui; o sinal de clima do
repositório vem inteiramente dos códigos de justificativa do próprio VRA
(ADR-0005), como no artigo.

**O que já existe.** A REDEMET/DECEA publica hoje as observações
(`docs/data-availability.md`, fonte 9), e `flight_date`, `dep_hour`,
`origin_icao` e `dest_icao` já dão a chave de junção — estação × hora — que
um METAR pede. O próximo passo é um coletor paralelo a
`src/airline_delays/ingest/download.py` e uma nova família de variáveis em
`src/airline_delays/prediction/dataset.py`, não na tabela-fato: o METAR varia
por hora, não por mês. É a extensão de maior retorno esperado para o preditor
do [`apendice-a-previsao-de-atrasos.md`](apendice-a-previsao-de-atrasos.md).

## 5. A pergunta de preços

**O que falta.** Nenhuma coluna de tarifa: os microdados tarifários da ANAC
(`docs/data-availability.md`, fonte 4) não são coletados aqui, e deles só
viajam, dentro do painel de estimação do artigo, as binárias de presença de
baixo custo. A pergunta — o que a internalização faz com as tarifas — foi
levada adiante por Guo, Jiang e Wan (2018), que construíram sobre o artigo
([`08-recepcao.md`](08-recepcao.md)); a leitura de apoio sobre o elo entre
atraso e preço é Forbes (2008), que mede o efeito dos atrasos sobre as tarifas
nos Estados Unidos.

**O que já existe.** As chaves `route` e `ym` do painel reconstruído tornam
direta uma junção com microdados tarifários agregados por rota-mês, sem
reextrair o VRA.

## 6. Atraso de baixo custo como variável de resposta

**Já implementado.** `lccfu_prdelarr` — o conjunto de empresas do artigo,
Gol e Azul — e `lccclass_prdelarr` — a classe de baixo custo, incluindo a
Webjet enquanto independente — existem no painel reconstruído
(`docs/dictionary.md`). Tratar o atraso das empresas de baixo custo como
resposta em vez de regressor é uma escolha de especificação sobre colunas que
já existem, não uma extensão de dado.

## 7. Desenhos no nível do aeroporto

**O que já existe.** `origin_icao` e `dest_icao` ficam ao lado dos nós
metropolitanos em cada etapa de voo de `data/staged/`, não no painel
rota-mês, onde um nó metropolitano — `MRSP`, `MRRJ`, `MRBH` — reúne
aeroportos por desenho (ADR-0001). Um desenho por aeroporto não precisa
reprocessar o VRA bruto: agrupa `data/staged/` por `origin_icao` e
`dest_icao` em vez de por `origin_node` e `dest_node`, reusando toda a
limpeza já feita no staging.

**O que falta.** Nenhuma tabela agregada por aeroporto, em vez de por nó,
existe hoje; só a tabela por voo carrega a chave certa.

## 8. Previsão de atraso por voo

**Feita.** O desenho — o voo programado como unidade, os dois horizontes, a
avaliação por origem rolante de 2006 a 2013, as nove checagens de vazamento
— está fixado na ADR-0009 e descrito no
[`apendice-a-previsao-de-atrasos.md`](apendice-a-previsao-de-atrasos.md). Os
números-manchete (`reports/summary.json`, bloco `prediction.rolling`): AUC de
0,715 a 0,741 na véspera e de 0,757 a 0,824 no portão nos oito folds, contra
0,608 a 0,673 da prevalência da rota no mês anterior; no subconjunto com
etapa anterior ligada, o portão chega a 0,869–0,934.

**O que falta.** Meteorologia (seção 4), capacidade declarada por aeroporto
— `data/external/capacity.csv` tem uma linha (`external.capacity`), e uma
linha não sustenta um painel nacional — e a auditoria dos trechos de
code-share da não operadora, candidata a ADR-0018.

## 9. A pergunta da monografia de 2013

**O que já existe.** A unidade da monografia de graduação do autor (USP,
2013) — empresa × rota × mês, com atrasos acima de 30 minutos — é o grão da
tabela-fato deste repositório: `arr_delayed_gt30` e `dep_delayed_gt30`
(`docs/dictionary.md`). O HHI da rota sobre voos planejados que ela regrediu é
`rthhi_flights`; o tempo de voo médio é `sched_block_mean_min`; a presença da
Gol e da Azul na rota é `pres_glo` e `pres_azu`; a entrada de um grupo na rota
é `is_entry`. Os seus 38 aeroportos (`external.monograph_airports`) cobrem os
27 nós da ADR-0001 — 31 deles estão em `data/external/nodes.csv`, e os 7
ausentes não são capitais (`scripts/monograph_airports.py`). A ponte entre o
modelo e os regressores, variável a variável, está no
[`04-do-modelo-as-hipoteses.md`](04-do-modelo-as-hipoteses.md); o modelo, no
[`03-o-jogo-do-congestionamento.md`](03-o-jogo-do-congestionamento.md).

**O que falta.** A binária da Azul no seu próprio aeroporto exige o grão
par-de-aeroportos (seção 7; a ADR-0001 dobra Viracopos em `MRSP`); o CR2 do
aeroporto, computável a partir da tabela-fato; os assentos por aeronave
(HOTRAN, não coletado); o clima mensal (seção 4); e os passageiros em conexão
da Infraero (`docs/data-availability.md`, fonte 13), com
`src/airline_delays/definitions/hubs.py` como substituto estrutural. A
regressão da monografia — N = 87.237 (monografia — documento externo) —
não é reestimada aqui (`docs/notes/monografia-2013.md`); refazê-la é uma
decisão própria, uma ADR, não uma edição.

## Escopo e próximos passos

Das nove extensões, três já têm número publicado hoje — o limiar de 30
minutos, o atraso de baixo custo como resposta e a previsão por voo; as
outras seis precisam de uma fonte ainda não coletada ou de uma função ainda
não escrita, e nenhuma delas foi implementada neste apêndice: descrever o
caminho não é percorrê-lo. O passo de maior alcance é a fonte 3 de
`docs/data-availability.md`: com ela entram no painel reconstruído os HHI de
passageiros (seção 2) e, deles, os sete instrumentos do artigo, e a
especificação do [`06-especificacao-e-identificacao.md`](06-especificacao-e-identificacao.md)
passa a poder rodar sobre os dois painéis.

## Onde conferir

- `docs/dictionary.md` — toda coluna citada acima, com tipo, unidade, regra de
  agregação e definição; gerado de `src/airline_delays/schema/columns.py`.
- `reports/summary.json` — `reconstruction.article_columns_missing`,
  `external.capacity`, `external.slots`, `external.monograph_airports`,
  `prediction.rolling`.
- `docs/data-availability.md` — as fontes 3, 4, 6, 9 e 13, com titular,
  forma de obtenção e o que depende de cada uma.
- `ROADMAP.md`, "Open items" — o estado de cada item em aberto.
- `scripts/monograph_airports.py` — imprime as contagens de aeroportos da
  monografia contra o mapa de nós.
