# Staging do VRA — layouts brutos, mapeamento de campos e decisões de limpeza

Nota de pesquisa, em português (ADR-0006: código e nomes de coluna em inglês, notas
e relatórios em português). Descreve o que os arquivos brutos da ANAC realmente são,
ano a ano, e o que `src/airline_delays/staging/build.py` faz com cada campo. Todos os
números foram medidos nos arquivos baixados, não estimados; a contagem exata por ano
está em `data/staged/manifest.json`.

Fonte: `https://siros.anac.gov.br/siros/registros/diversos/vra/{ano}/`, listagem de
diretório IIS. A listagem é a autoridade sobre quais arquivos existem —
`airline-delays fetch` lê o índice e só cai nos padrões de nome conhecidos se o
índice não abrir.

## 1. Dois layouts, não um

Medido com `airline-delays layouts` (que roda `inspect_file()`, de
`src/airline_delays/ingest/layouts.py`, no primeiro arquivo de cada ano). **Não são 12 nem 17 colunas em toda a série: são 12 até 2009 e 20 de
2010 em diante.**

| Anos | Nome interno | Colunas | Separador | Encoding | Fim de linha | Aspas | Justificativa |
|---|---|---|---|---|---|---|---|
| 2000–2009 | `legacy_12col` | 12 | vírgula | latin-1 | CRLF | nenhuma | código de 2 letras |
| 2010–2013 | `wide_20col` | 20 | ponto e vírgula | UTF-8 | LF | nenhuma | texto livre |

Padrão de nome: `VRA_{ano}{mês}` sem zero à esquerda até 2009 (`VRA_20071.csv`,
`VRA_200712.csv`); `VRA_{ano}_{MM}` de 2010 em diante (`VRA_2010_01.csv`). Doze
arquivos por ano, 168 no total, sem lacuna.

### 1.1 Layout antigo (2000–2009), cabeçalho literal

```
ICAO Empresa Aérea,Número Voo,Código Autorização (DI),Código Tipo Linha,
ICAO Aeródromo Origem,ICAO Aeródromoo Destino,Partida Prevista,Partida Real,
Chegada Prevista,Chegada Real,Situação Voo,Código Justificativa
```

O erro de digitação "Aeródromoo" está no arquivo da ANAC e é preservado em
`LAYOUT_LEGACY.columns` (`src/airline_delays/ingest/layouts.py`) — renomear aqui
esconderia o que o arquivo é.
O campo do DI chama-se "Código Autorização (DI)", não "Código DI".

### 1.2 Layout novo (2010–2013), cabeçalho literal

```
Sigla ICAO Empresa Aérea;Empresa Aérea;Número Voo;Código DI;Código Tipo Linha;
Modelo Equipamento;Número de Assentos;Sigla ICAO Aeroporto Origem;
Descrição Aeroporto Origem;Partida Prevista;Partida Real;
Sigla ICAO Aeroporto Destino;Descrição Aeroporto Destino;Chegada Prevista;
Chegada Real;Situação Voo;Justificativa;Referência;Situação Partida;Situação Chegada
```

São **20** campos, não os 19 que a página de metadados da ANAC lista: há uma coluna
`Referência` (a data do voo em ISO) que a tabela oficial não documenta.

**A ordem das colunas muda entre os dois layouts.** No layout novo o aeroporto de
destino fica *entre* os horários de partida e os de chegada. Uma leitura posicional
com a ordem antiga colocaria um horário dentro de `dest_icao` sem erro nenhum — por
isso `TestWideLayout::test_the_column_order_of_this_layout_is_respected`, em
`tests/test_staging.py`, exige que mais de 99% dos códigos ICAO tenham quatro letras.

### 1.3 Quirks medidos

* **Sem aspas em lugar nenhum.** Nomes de empresa com vírgula ("AMERICAN AIRLINES,
  INC.") só existem no layout novo, onde o separador é `;` — não há campo citado em
  nenhum dos dois layouts, e a leitura roda com `quote=''`.
* **Sem separador decimal.** Nenhum campo numérico com casa decimal; não há vírgula
  decimal para tratar.
* **Sem separador sobrando no fim da linha.** O histograma de contagem de campos por
  linha tem um único valor em cada layout (12 e 20).
* **Fim de linha muda com o layout**: CRLF em 2000–2009, LF em 2010–2013. Medido com
  `airline-delays layouts`, não presumido — a primeira versão desta nota declarava
  CRLF para os dois e estava errada.
* **Datas** em `DD/MM/AAAA HH:MM` nos dois layouts, horário de Brasília, sem segundos
  e sem fuso.
* **Ano errado na origem.** Existem carimbos com o ano digitado errado (por exemplo
  `2088` no lugar de `2002` em voos da ARG em agosto de 2002). São erros da ANAC, não
  do parser: o horário previsto está certo e o realizado vem com o ano trocado.
  Nenhuma linha é descartada por isso; o atraso resultante fica absurdo e é problema
  do filtro de outlier a jusante (ADR-0008), não do staging.

## 2. Mapeamento campo a campo

| Coluna staged | Layout antigo | Layout novo | Transformação |
|---|---|---|---|
| `airline` | col. 1 | col. 1 | `upper(trim(x))`, vazio vira nulo |
| `flight_number` | col. 2 | col. 3 | `TRY_CAST` para inteiro; zeros à esquerda do layout novo caem; não numérico vira nulo |
| `di` | col. 3 | col. 4 | dígito vira inteiro; `A`→10, `B`→11; qualquer outra coisa vira nulo |
| `line_type` | col. 4 | col. 5 | `upper(trim(x))`; `NA`, `N/A`, `N/I`, `NI` e vazio viram nulo |
| `origin_icao` | col. 5 | col. 8 | `upper(trim(x))` |
| `dest_icao` | col. 6 | **col. 12** | `upper(trim(x))` |
| `sched_dep` | col. 7 | col. 10 | `try_strptime(x, '%d/%m/%Y %H:%M')` |
| `actual_dep` | col. 8 | col. 11 | idem |
| `sched_arr` | col. 9 | col. 14 | idem |
| `actual_arr` | col. 10 | col. 15 | idem |
| `status` | col. 11 | col. 16 | `REALIZADO`→`realized`, `CANCELADO`→`cancelled`, resto→`other` |
| `cause_code` | col. 12 | col. 17 | antigo: código validado contra `^[A-Z]{2}$`; novo: texto livre mapeado de volta ao código |

Campos do layout novo que **não** entram no staged: `Empresa Aérea` (nome),
`Modelo Equipamento`, `Número de Assentos`, as duas `Descrição Aeroporto`,
`Referência`, `Situação Partida` e `Situação Chegada`. Os dois últimos são faixas de
atraso já classificadas pela ANAC; guardá-las convidaria a usar a classificação da
agência em vez da definição declarada do projeto, e elas não existem antes de 2010,
o que quebraria a série. `Modelo Equipamento` e `Número de Assentos` são candidatos
naturais a uma extensão futura (só 2010+).

`group` e `class` vêm de `data/external/groups.csv` (ADR-0003), por intervalo datado
ao mês. A tabela traz `start`/`end` no formato `AAAA-MM`; o join compara chaves
`AAAAMM`, não datas — um `TRY_CAST` para `DATE` anularia todo `"2007-03"` e o teste de
intervalo viraria "sempre verdadeiro", duplicando cada voo de empresa que trocou de
grupo. `_register_groups` recusa a tabela se dois intervalos da mesma empresa se
sobrepuserem, em vez de alargar o join. Trocas conferidas na saída: Varig→Gol em
2007-04, Webjet→Gol em 2011-11, Trip→Azul em 2012-05. 1.536.481 linhas ficam com
`group` nulo — empresas fora da tabela, sobretudo estrangeiras.

Colunas derivadas: `flight_date` (data da partida prevista, com fallback na partida
real), `year`, `month`, `ym`, `origin_node`, `dest_node`, `route` (ADR-0001),
`dep_delay_min`, `arr_delay_min` (ADR-0008), `sched_block_min`, `actual_block_min`,
`dep_hour`, `arr_hour`, `dow`, `universe_repl`, `universe_ml`, `is_realized`
(ADR-0002). Definição de cada uma em `src/airline_delays/schema/columns.py`.

## 3. Justificativa: código em 2000–2009, texto em 2010–2013

Esta é a diferença de layout mais cara de descobrir e a mais fácil de ignorar.

Até 2009 o campo traz o código de duas letras da IAC 1504 direto (`RA`, `AR`, `XS`)
ou o literal `N/A` quando o voo foi realizado sem ocorrência. De 2010 em diante o
mesmo campo traz a **descrição por extenso**: `CONEXÃO DE AERONAVE`,
`AEROPORTO COM RESTRIÇÕES OPERACIONAIS`, `ATRASOS NÃO ESPECÍFICOS, OUTROS`.

`src/airline_delays/staging/clean.py` remapeia o texto para o código com a tabela do
anexo 2 da IAC 1504 (`IAC1504_CODES`, 49 códigos transcritos do PDF da ANAC). A comparação é feita sobre
uma chave normalizada — acentos removidos, tudo em maiúsculas, qualquer sequência de
pontuação ou espaço colapsada em um espaço — porque a pontuação do arquivo difere da
do PDF (vírgula onde o PDF tem travessão, por exemplo). A normalização existe em
duas formas, `normalise_text` (Python) e `normalise_text_sql` (DuckDB); o staging usa
a SQL para não fazer dez milhões de linhas cruzarem a fronteira do Python, e um teste
exige que as duas concordem em todos os 49 textos.

**Um texto é ambíguo**: `AUTORIZADO` é a descrição de dois códigos, `OA` (atraso
autorizado) e `XB` (cancelamento autorizado). A desambiguação é pela situação do voo:
cancelado → `XB`, caso contrário → `OA`. É uma decisão, não uma dedução; está isolada
em `AMBIGUOUS_CAUSE_TEXTS` para poder ser revista.

Cobertura medida: **todos** os textos distintos encontrados em 2010–2013 mapeiam para
um código da IAC 1504 — nenhuma linha ficou sem código por falta de correspondência.

## 4. Decisões de limpeza, com contagem

Contagens medidas sobre os 168 arquivos brutos (2000–2013).

| Decisão | Efeito | Linhas afetadas |
|---|---|---|
| `DI` fora de `0–9`, `A`, `B` (`O`, `NA`, `?`, `I`, `C`, `D`, `E`, `U`, `S`) vira nulo | `di` nulo, fora do universo de replicação | ~105 no layout antigo |
| `A`→10, `B`→11 | mantém o valor em vez de perdê-lo | 1.502 + 2.277 no layout antigo |
| `line_type` igual a `NA`/`N/A`/`N/I` vira nulo | fora do universo | 582 no layout antigo |
| `line_type` com dígito ou letra fora da IAC (`0`,`1`,`3`,`4`,`5`,`6`,`8`,`9`,`S`) é mantido como veio | não inventa valor; fica fora do universo por não ser N/R/E | ~41 no layout antigo |
| `Código Justificativa` = `N/A` vira nulo | distingue "sem ocorrência" de "ocorrência desconhecida" | ~5,8 milhões no layout antigo |
| `Código Justificativa` que não é duas letras (`00`, `M`, `X0`, `30`, …) vira nulo | idem | ~1.220 no layout antigo |
| Carimbo que não parseia vira nulo | atraso construído sobre ele também fica nulo | conferir `rows_without_flight_date` no manifesto |
| `flight_date` usa a partida prevista, com fallback na partida real | linhas sem partida prevista (DI 7 e 9, sobretudo) não perdem a data | ver manifesto |
| Nenhum aeroporto é descartado | voos internacionais e aeródromos fora das capitais ficam na base | — |
| Nenhum outlier é cortado no staging | o corte é decisão da camada de análise (ADR-0008) | — |

### 4.1 O achado que mais afeta interpretação: horário real vazio no layout antigo

Em 2002, dos 785.546 voos com situação `REALIZADO`, apenas **152.104** têm
`Partida Real` preenchida — e 154.341 têm código de justificativa. Os dois conjuntos
quase coincidem. Isto é, **no layout antigo o horário realizado só é registrado
quando houve ocorrência**; um voo realizado sem ocorrência vem com os dois campos
"real" vazios.

A leitura natural é que campo vazio significa "operou no horário previsto", e no
layout novo (2010–2013) é exatamente assim que aparece: o voo pontual traz
`Partida Real` igual a `Partida Prevista` e `Situação Partida = Pontual`. Em 2010 mais
de 99% dos voos realizados têm horário real preenchido.

**O staging não imputa.** A especificação é explícita: atraso nulo quando falta o
horário realizado (ADR-0008), e imputar zero transformaria uma ausência em um dado.
A consequência prática é grande e precisa estar na frente de quem for usar a base:
médias e proporções de atraso calculadas sobre `dep_delay_min`/`arr_delay_min` em
2000–2009 são calculadas sobre uma **amostra selecionada de voos com ocorrência**, que
é fortemente enviesada para atraso. Em 2002 a mediana do atraso de chegada nessa
amostra é de 35 minutos.

O painel de estimação do artigo adota a leitura "vazio = pontual" (ADR-0012); o
staging mantém o nulo. Quem quiser tratar vazio como pontual deve fazê-lo
explicitamente, numa camada acima, e declarar a escolha; ela muda toda média de
atraso de 2000–2009. É o que o painel reconstruído faz, com o parâmetro
`empty_actual_means_on_time` (`docs/notes/features.md`, seção 2).

**E é o que a ADR-0017 passou a fazer, fora do staging.** Um colegiado de três
revisores (ADR-0010, pareceres em `docs/notes/colegiado-adr0012.md`) leu a IAC 1504 e
concluiu que o campo vazio é a ausência de Boletim de Alteração de Vôo, isto é, "sem
alteração reportada": a camada de previsão passa a ler atraso 0 nesse caso, com a
marca `on_time_no_bav`, e só para empresas de classe FSC, LCC ou regional. O staging
continua sem imputar nada — a coluna crua fica nula, e a leitura mora na camada que
declara qual convenção usa.

### 4.2 `actual_time_suspect`: erro de digitação de mês, não operação

Os arquivos brutos trazem horários reais com o mês errado. O caso citado na ADR-0015 é
o VSP 4374 de dezembro de 2003, cuja chegada real está datada de novembro: −43.170
minutos. O staging não conserta e não descarta; marca. `actual_time_suspect` é
verdadeiro quando o atraso de partida **ou** de chegada tem valor absoluto de um dia
civil ou mais (|atraso| ≥ 1.440 minutos), e falso quando não há horário real nenhum —
ausência não é horário suspeito. A camada de previsão exclui essas linhas dos alvos e
conta quantas são por ano; a camada de análise nunca as vê num somatório de minutos,
porque o corte de outlier da ADR-0015 é simétrico (|atraso| < 313,25).

## 5. Contagem por ano (staged)

Medido em 2026-09-05, DuckDB 1.5.5, PyArrow
25.0.1, Python 3.12.13. Fonte:
`data/staged/manifest.json`.

| ano | layout | linhas | parquet (MB) | sem `flight_date` | ano derivado ≠ ano do arquivo |
|---|---|---|---|---|---|
| 2000 | legacy_12col | 883,313 | 16.5 | 36 | 306 |
| 2001 | legacy_12col | 927,440 | 17.0 | 136 | 204 |
| 2002 | legacy_12col | 918,079 | 16.8 | 504 | 580 |
| 2003 | legacy_12col | 801,739 | 14.1 | 284 | 370 |
| 2004 | legacy_12col | 752,818 | 13.1 | 53 | 166 |
| 2005 | legacy_12col | 787,750 | 14.1 | 130 | 245 |
| 2006 | legacy_12col | 832,069 | 14.9 | 101 | 224 |
| 2007 | legacy_12col | 940,217 | 17.7 | 132 | 232 |
| 2008 | legacy_12col | 894,597 | 16.5 | 235 | 345 |
| 2009 | legacy_12col | 990,233 | 18.3 | 144 | 334 |
| 2010 | wide_20col | 1,125,951 | 23.3 | 28 | 154 |
| 2011 | wide_20col | 1,253,200 | 26.9 | 316 | 408 |
| 2012 | wide_20col | 1,289,283 | 28.2 | 1 | 85 |
| 2013 | wide_20col | 1,255,633 | 27.3 | 0 | 70 |

Total: **13,652,322 etapas de voo** em 168 arquivos, 265 MB de parquet
a partir de 2,17 GB de CSV. As duas últimas colunas medem sujeira de data na origem:
3.723 linhas no total (0,03%) têm o ano derivado diferente do ano do arquivo, e 2.100
delas não têm data nenhuma. Nenhuma linha é descartada por isso.

A maior parte dessas 3.723 é fronteira de calendário — um arquivo de dezembro que
carrega etapas programadas para 1º de janeiro, e vice-versa —, e o resto são erros
de digitação de ano: 136 linhas datadas de 2099, 88 de 2020, 7 de 2088 e mais nove
espalhadas entre 2018 e 2071. **Nenhuma das linhas com ano tipográfico está no
universo de replicação**; as de fronteira estão: 494 linhas ±1 ano, mais 18 linhas
datadas de janeiro de 2014 nos arquivos de 2013.

Foi exatamente essa divergência que produziu as chaves duplicadas da ADR-0016. O
consumidor não pode ler o diretório como se fosse o ano: `build_fact()`
(`src/airline_delays/fact/build.py`) seleciona `WHERE year = <alvo>` sobre a árvore
inteira (`year_source_sql()`), afirma a unicidade das chaves e reporta as linhas
datadas fora da janela construída em `rows_outside_years`
(`data/analysis/manifest.json`). As 18 linhas de 2014-01 ficam de fora do painel,
que passa a ter exatamente 168 meses, 2000m1 a 2013m12.

## 6. Formato de saída

`data/staged/year=AAAA/part-0.parquet`, um arquivo por ano, zstd nível 9,
`ROW_GROUP_SIZE` 262.144. Tipos apertados: `int8` para mês, DI, horas e dia da
semana; `int16` para ano e tempos de bloco; `int32` para `ym` e número do voo;
`float32` para os atrasos.

Uma ressalva de formato: o registro declara `timestamp[s]` e o DuckDB carrega
`TIMESTAMP_S`, mas o Parquet **não tem unidade de segundo** — as menores unidades do
formato são milissegundos e microssegundos —, então o arquivo grava
`timestamp[us]`. `dtype_matches()` (`src/airline_delays/schema/columns.py`) aceita as
duas, e nenhuma precisão é perdida: a fonte tem resolução de minuto.

O particionamento é pelo **ano do arquivo de origem**, e a coluna `year` é derivada de
`flight_date`. As duas quase sempre coincidem; `rows_year_mismatch` no manifesto conta
as exceções, e a seção 5 mostra o que elas causaram. Por isso `read_staged()`
(`src/airline_delays/staging/build.py`) lê com `hive_partitioning=false`: senão o nome
do diretório `year=AAAA` criaria uma segunda
coluna `year` em conflito com a derivada — e o descasamento ficaria zero por
construção, sem deixar de existir.

`data/staged/manifest.json` registra, por ano: linhas, arquivos de origem, layout,
caminho, bytes, sha256, linhas sem data, linhas com ano divergente e o tempo gasto;
e, no cabeçalho, `git_commit` e as versões de Python, DuckDB e PyArrow.

## 7. Como reproduzir

```bash
uv run airline-delays fetch      # 168 arquivos, 2,17 GB, sequencial e educado (~17 min)
uv run airline-delays layouts    # mede o layout do primeiro arquivo de cada ano
uv run airline-delays stage      # um ano por vez
uv run airline-delays fixture    # regenera tests/fixtures a partir do real
```

`just fetch` e `just stage` embrulham o primeiro e o terceiro comandos.
`airline-delays fetch` é idempotente: um arquivo já em disco cujo sha256 bate com
`data/raw/manifest.json` é pulado.
