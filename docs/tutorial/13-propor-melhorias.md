# M13 — Propor melhorias: o que este repositório já sustenta

**Objetivo.** Para cada extensão que o arco original prometeu, abandonou
ou nunca tentou (M1-M10), dizer com precisão o que já existe neste
repositório para construí-la, o que falta, e o próximo passo concreto —
sem confundir "a arquitetura já suporta isto" com "isto já está pronto".
As duas coisas são diferentes, e cada seção abaixo diz qual é qual.

## 1. A decomposição de curto e longo prazo (a promessa removida, M9)

**O que falta.** `lcc_sr`/`lcc_lr` (LCC antes/depois de uma data de corte
por grupo) não existem em `src/airline_delays/schema/columns.py` — confirmável
com `grep -c "lcc_sr\|lcc_lr" src/airline_delays/schema/columns.py` (0 ocorrências).

**O que já existe para construí-la.** `data/external/groups.csv` já traz
`start`/`end` datados ao mês por empresa e grupo (`DECISIONS.md`
ADR-0003), e a tabela-fato já marca entrada e saída de grupo na rota
(`is_entry`/`is_exit`, `docs/dictionary.md`). O próximo passo é uma
função em `src/airline_delays/fact/build.py` que, dado um corte (por exemplo, a data
de entrada do grupo na rota, não uma data fixa de calendário como o
artigo original parece ter usado), particiona `sh_flights_lcc` em dois
regressores — exatamente o par que o artigo prometeu e nunca publicou.

## 2. HHI ponderado por passageiros

**O que já existe.** `src/airline_delays/definitions/concentration.py` já
tem uma função `passenger_weighted_hhi` com a assinatura certa, que devolve
`None` até a fonte existir — as colunas `rthhi`/`maxcthhi` já estão no
painel reconstruído, inteiramente nulas, documentadas como tal
(`docs/dictionary.md`).

**O que falta.** Os dados estatísticos da ANAC por empresa-rota-mês
(`docs/data-availability.md`, fonte 3) — não coletados. O próximo passo é
um comando de coleta desses dados (a construir) e um `join` por
`route`/`ym`/`group` — as mesmas três chaves que o painel reconstruído já usa.

## 3. O limiar de 30 minutos

**Já implementado, não uma proposta.** `fsc_prdelarr1530` e
`fsc_prdelarr30m` (e as variantes `fscc_`/`all_`/`lccfu_`/`lccclass_`)
já existem no painel reconstruído — ver M5, que mostra a mesma ambiguidade
sem resolução no projeto irmão original. A
linhagem é mais longa: 30 minutos é o corte da Resolução ANAC 218 e a
variável dependente da monografia de 2013 (M14,
`docs/notes/monografia-2013.md`); `fsc_prdelarr30m` é o que mais se
aproxima do que o autor mediu em 2013 — sobre outro conjunto de empresas
(todas, por empresa) e outro denominador (voos planejados no do-file de
2013; voos realizados na publicação da ANAC).

## 4. Meteorologia (METAR)

**O que falta.** Nenhuma coluna de METAR existe aqui — o sinal de clima
deste repositório vem inteiramente dos códigos de justificativa do
próprio VRA (`DECISIONS.md` ADR-0005), como já era no artigo original.

**O que já existe.** A REDEMET/DECEA é pública hoje
(`docs/data-availability.md`, fonte 9); `flight_date`, `dep_hour` e
`origin_node`/`dest_node` já dão a chave de junção (estação × hora) que
um METAR precisaria. O próximo passo é um módulo paralelo a
`src/airline_delays/ingest/download.py` (a criar), e uma nova família de
features em `src/airline_delays/prediction/dataset.py` — não na tabela-fato,
porque METAR varia por hora exata, não por mês.

## 5. A pergunta original de preços

**O que falta.** Nenhuma coluna de tarifa (`docs/data-availability.md`,
fonte 4) — ver M1 e M5.

**O que já existe.** As mesmas chaves `route`/`ym` do painel reconstruído
tornam uma junção com microdados tarifários por rota-mês direta, sem
reextrair o VRA.

## 6. Atraso de LCC como variável de resposta

**Já implementado, não uma proposta.** `lccfu_prdelarr` (o conjunto de
empresas do artigo, Gol e Azul) e `lccclass_prdelarr` (a classe LCC,
incluindo a Webjet enquanto independente) já existem no painel
reconstruído (`docs/dictionary.md`). Tratar atraso de LCC como resposta em
vez de regressor é
uma escolha de especificação sobre colunas que já existem — não uma
extensão de dado.

## 7. Desenhos no nível do aeroporto

**O que já existe.** `origin_icao`/`dest_icao` já ficam ao lado dos nós
metropolitanos em **cada etapa de voo** (`data/staged/`,
`src/airline_delays/schema/columns.py`, ADR-0001) — não no painel de rota-mês, onde um nó
metropolitano (`MRSP`, `MRRJ`, `MRBH`) mistura aeroportos por desenho
(ADR-0001). Um desenho a nível de aeroporto não precisa reprocessar o VRA
bruto: agrupa `data/staged/` por `origin_icao`/`dest_icao` em vez de por
`origin_node`/`dest_node`, reusando toda a limpeza já feita no staging.

**O que falta.** Nenhuma tabela agregada por aeroporto (em vez de nó)
existe hoje — só a flight-level já carrega a chave certa.

## 8. Previsão de atraso por voo

**Feita, não uma proposta.** O desenho — universo, dois horizontes
(véspera e no portão), avaliação por origem rolante 2006-2013,
`AUC`/`PR-AUC`/`Brier`/calibração, testes de vazamento — está fixado em
`DECISIONS.md` ADR-0009 e `docs/notes/prediction.md`, e os números estão em
`reports/prediction/results.md`: origem rolante nos oito anos de teste, AUC
de véspera entre 0,715 e 0,741 e AUC de portão entre 0,757 e 0,824, contra
0,61 a 0,67 da prevalência da rota no mês anterior; nos 20% a 35% de voos
com etapa anterior ligada, o portão chega a 0,87–0,93. O alvo anterior a
2010 segue a leitura B da ADR-0017 — horário real vazio em voo realizado de
empresa FSC, LCC ou regional é "sem alteração reportada", atraso 0 — e é um
**piso** de pontualidade, não uma medição; o mesmo arquivo traz as métricas
sob a leitura superada ao lado.

**O que falta.** Meteorologia (METAR do DECEA/REDEMET), capacidade
declarada por aeroporto e a auditoria dos trechos de code-share da não
operadora (candidata a ADR-0018) — as três estão listadas em
`docs/notes/prediction.md`, seção 7.

## 9. A pergunta da monografia de 2013 (M14)

**O que já existe.** A unidade da monografia — empresa × rota × mês, com
atrasos acima de 30 minutos — é o grão da tabela-fato deste repositório:
`arr_delayed_gt30` e `dep_delayed_gt30` (`docs/dictionary.md`). O HHI da
rota sobre voos planejados que ela regrediu é `rthhi_flights`; o tempo de
voo médio é `sched_block_mean_min`; a presença da Gol e da Azul na rota é
`pres_glo`/`pres_azu`, e a entrada de um grupo na rota é `is_entry`. A
ponte completa, variável a variável, está em
[`../theory/03-do-modelo-ao-artigo.md`](../theory/03-do-modelo-ao-artigo.md).

**O que falta.** A dummy da Azul no seu próprio aeroporto exige o grão
par-de-aeroportos (`origin_icao`/`dest_icao` existem só nas camadas
staged e de modelagem; ADR-0001 dobra Viracopos em `MRSP`); o CR2 do
aeroporto, computável a partir da tabela-fato; os assentos por aeronave
(HOTRAN, não coletado); o clima mensal do ICEA (seção 4 acima); e os
passageiros em conexão da Infraero (fonte 13 de
`docs/data-availability.md`, com `src/airline_delays/definitions/hubs.py` como
substituto estrutural). O próximo passo concreto é uma agregação de `data/staged/`
por par de aeroportos em vez de por nó, reusando a limpeza do staging — o
mesmo caminho da seção 7.

## Exercício

Escolha uma das nove extensões acima cuja seção comece com "O que já
existe" mais longa que "O que falta". Rode o comando `grep`/`cat` que a
seção cita, confirme o número, e escreva as duas próximas linhas de
código (arquivo e função) que você adicionaria para completá-la —
sem escrevê-las de verdade, só nomeá-las.

## Limites e próximos passos

"A arquitetura já sustenta" não é o mesmo que "já está pronto" — das nove
extensões acima, três já têm número publicado hoje (o limiar de 30 minutos,
o atraso de LCC como resposta e a previsão por voo); as outras seis
precisam de uma fonte de dado ainda não coletada ou de uma função ainda não
escrita. Nenhuma dessas seis foi implementada neste módulo de documentação
— descrever o caminho não é percorrê-lo. O próximo passo de maior alcance é
a fonte 3 de `docs/data-availability.md`: com ela entram os HHI de
passageiros no painel reconstruído (extensão 2) e, deles, os instrumentos
do artigo (M6).
