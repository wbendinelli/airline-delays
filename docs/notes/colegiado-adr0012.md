# Colegiado da ADR-0012 — horário real vazio nos arquivos de 2000–2009

Nota de pesquisa em português (ADR-0006). Registra o colegiado previsto na
ADR-0010 e a decisão que virou a ADR-0017. O texto dos três pareceres e da
decisão do orquestrador está reproduzido **na íntegra** ao final, sem edição;
esta abertura só situa a pergunta e diz o que mudou no repositório.

## A pergunta

Nos arquivos brutos do VRA de 2000 a 2009, um voo **realizado** aparece com
horário real de partida e de chegada vazios em 59% a 80% das linhas de cada ano
(`data/analysis/manifest.json`), contra 0,0% de 2010 em diante. Duas leituras
são defensáveis e levam a bases de previsão diferentes:

* **Leitura A** — vazio é *desconhecido*. O voo não tem alvo de atraso. Foi o que
  a ADR-0012 mandou fazer na camada de previsão, e o resultado era que só
  4.965.966 de 10.200.578 voos programados tinham alvo de chegada e que 75% a
  94% dos sobreviventes anteriores a 2010 apareciam como atrasados.
* **Leitura B** — vazio é *sem alteração reportada*. A IAC 1504 manda emitir o
  Boletim de Alteração de Vôo "sempre que houver alguma alteração" (introdução e
  §3.1) e os horários realizados são campos **do boletim** (§4.2 n, o, p); o
  campo vazio é a ausência de ocorrência, e o atraso é 0.

A divergência não é sobre estilo de imputação: sob A, a amostra de treino é
selecionada pelo desfecho — só entra quem teve ocorrência — e a série ganha um
degrau artificial exatamente na fronteira de layout de 2010.

## Como foi decidido

Pelo procedimento da ADR-0010: três revisores independentes, um deles instruído
a ser cético, leram a IAC 1504, as saídas de previsão e a evidência então
disponível sobre os arquivos de 2000–2009. Dois votaram B; o
cético votou A e mediu, por companhia, o que ninguém tinha medido: a taxa de nulo
não é uma convenção só, vai de 0% em regionais pequenas a 90–100% em
estrangeiras e em trechos de code-share, com as majors domésticas no meio.

O orquestrador adotou **B com o escopo do cético**: a leitura vale só para voos
realizados de empresas cuja classe em `data/external/groups.csv` é FSC, LCC ou
regional; para `other` e não rotuladas o vazio continua desconhecido e o voo fica
fora de todo alvo de atraso. A IAC 1504 art. 6.6 sustenta o recorte: em
code-share só a operadora presta a informação, e o trecho da não operadora não
tem efeito sobre os índices.

## O que mudou no repositório

* `DECISIONS.md` ADR-0017 (e a emenda de escopo), que supersede a metade de
  previsão da ADR-0012. O painel reconstruído **não muda**: continua sob a
  convenção do painel de estimação do artigo — a convenção dos autores
  (ADR-0012).
* `src/airline_delays/prediction/dataset.py`: `BAV_CLASSES`, `BAV_LAST_LEGACY_YEAR`, a coluna
  diagnóstica `on_time_no_bav` e a mesma leitura aplicada aos alvos, à etapa
  anterior ligada e às taxas defasadas (`monthly_lags`, `flight_number_sql`).
* `docs/notes/prediction.md`: a regra do BAV com as seções da IAC 1504, a
  direção do viés (B é **piso** de pontualidade) e a quebra de layout de 2010;
  a tabela de nulo por companhia e ano, gerada por
  `scripts/null_actual_by_carrier.py`, está em
  `reports/prediction/null_actual_by_carrier.csv`.
* `reports/prediction/results.md`: bloco de sensibilidade com as métricas de
  origem rolante sob a leitura A ao lado da B, a partir de
  `reports/prediction/rolling_reading_A.json`.

## Candidata a ADR-0018

O cético levantou um item que **não** foi decidido aqui: se os trechos de
code-share operados por outra companhia deveriam sair dos universos por
completo, e não apenas ficar sem alvo. Fica para auditoria própria.

## Pareceres, na íntegra

O que segue é o texto entregue pelos revisores e pela decisão do orquestrador,
reproduzido sem corte nem correção. As únicas intervenções são as notas
editoriais entre colchetes, que dizem onde vive hoje cada artefato que os
pareceres citam.

---

# Colegiado ADR-0012 — pareceres (2026-09-05)

Pergunta: nos arquivos de 2000–2009, horário real vazio em voo realizado significa "desconhecido" (A) ou "sem alteração reportada, operou no horário" (B)?

## Revisor 1 (Opus) — VEREDITO: B

A IAC 1504 é inequívoca: as empresas registram "sempre que houver alguma alteração em seus vôos regulares" (introdução) e "será emitido um boletim para cada dia em que ocorra alteração" (§3.1). Os horários realizados e o código de justificativa são campos do BAV (§4.2 n, o, p), não do voo. O arquivo pré-2010 é o HOTRAN mais uma sobreposição de exceções: voo realizado sem horário real é voo sem BAV, logo sem alteração. O código de justificativa vazio é o mesmo fato, não evidência adicional.

Aritmética: reconstruindo a taxa sob B a partir de `dataset.json`, 2002–2005 dá 20,3% contra 21% publicados na Tabela 1; 2006–2010 dá 26,8% contra 30%. Sob A as mesmas janelas dão 75–94%, e a série entra em 2010 (24,3%) sem degrau só sob B. A leitura A não é neutra: descarta 5.234.612 de 10.200.578 voos condicionando no desfecho, seleção endógena; o viés de B é atenuação de direção conhecida sobre 100% da amostra.

Consequências: `ml/dataset_flights.py` com a leitura B no escopo realizado e ano < 2010, flag `on_time_no_bav`; recomputar dataset, rolling, split fixo, subconjunto ligado e importâncias; declarar a regra do BAV, o escopo, a direção do viés, o código vazio como mesmo fato e a quebra de layout de 2010; README dizendo "sem alteração reportada"; manter ADR-0015; [a tabela de concordância e a reconciliação, artefatos hoje removidos — nota editorial: hoje, as saídas de previsão e a convenção do painel do artigo] não mudam; a assimetria `fl_ddel` × `fl_odel` segue declarada. Alerta: `prev_arr_delay_min` passa a existir para quase todo voo pré-2010, o contraste D−1 × H−1 muda de significado antes de 2010 e precisa ser dito.

## Revisor 2 (Sonnet) — VEREDITO: B

A norma define um sistema de exceção: o BAV só é preenchido "sempre que houver alguma alteração" (introdução, §3.1) e o SITAR "diariamente, para todas as alterações verificadas" (§5.1); o anexo 2 só tem códigos de atraso, cancelamento e alteração, nenhum para "operou no horário". Silêncio no BAV é o sinal esperado do voo sem ocorrência. A reconciliação confirma: em 72.381 casos, 72.375 (99,99%) trazem exatamente o horário previsto na vintage de 2019 [nota editorial: a reconciliação e a sua base não integram mais o repositório; hoje, as saídas de previsão e a convenção do painel do artigo].

Sob A, o alvo pré-2010 sobrevive em 20–30% dos voos realizados e a taxa salta para 75–94%; cai de 0,883 (2009) para 0,243 (2010) exatamente na fronteira de layout, descontinuidade artificial que nenhum modelo deveria aprender. Contraponto sustentado: B é presunção regulatória, piso de pontualidade; atraso não capturado por falha de preenchimento permanece invisível sob as duas leituras.

Consequências: leitura B no dataset de previsão com flag (`no_alteration_reported`); regenerar os JSON e o `results.md`; nova entrada em [a lista de diferenças da época; hoje: `docs/notes/prediction.md`] com a natureza de exceção do BAV/SITAR, a série de nulos por ano, os 72.375/72.381 e a condição de limite inferior; painel de replicação e [a tabela de concordância, hoje removida] não mudam; publicar A como variante nomeada onde a tabela cobrir 2000–2009, nunca como padrão silencioso.

## Revisor 3 (Sonnet, cético) — parecer

VEREDITO: A. Testou a suposição de convenção uniforme quebrando a taxa de nulo de `actual_arr` por companhia em 2005 (voos realizados, companhias com ≥ 500 voos): 0,0% em BRB e BET, 0,8% em VLO, contra 90–100% em quase toda estrangeira ou code-share (TPU 100%, AVA 99,5%, ACA 98,8%, DAL 94,2%, AAL 94,9%, UAL 90,6%, BAW 90,4%, COA 90,0%), com as majors domésticas no meio (TAM 71,8%, GLO 64,4%, VRG 57,0%). Se vazio fosse "operou no horário", American, Delta, Air Canada, Avianca e United teriam 90–100% de pontualidade no Brasil em 2005, o que é implausível e coerente com a IAC 1504 art. 6.6: em code-share só a operadora presta informação e o voo da não operadora fica sem efeito para os índices. É sub-registro estrutural por companhia, não uma semântica única de campo vazio. As evidências a favor de B mostram que B aproxima bem o agregado das majors domésticas, não que a convenção vale linha a linha. Para a réplica, manter B é defensável porque `fsc_*` e `lccfu_*` se restringem a TAM, Varig, Transbrasil, Vasp, Gol e Azul, o bloco de nulo moderado; mas declarar a taxa de nulo por companhia dentro dos grupos, e que a leitura não tem validação fora deles. Consequências mínimas: auditar `universe_ml` quanto a estrangeiras e code-share; acrescentar a taxa de nulo por companhia às diferenças declaradas [hoje: `reports/prediction/null_actual_by_carrier.csv`] e ao README; nenhum número publicado muda.

## Decisão do orquestrador

Maioria B com o escopo do revisor 3: leitura B aplicada só a voos realizados de empresas de classe FSC, LCC ou regional em `groups.csv`; para `other` e não rotuladas, vazio segue desconhecido. Registrado como emenda de escopo no ADR-0017; a exclusão dos trechos de code-share da não operadora fica como candidata a ADR-0018 após auditoria.
