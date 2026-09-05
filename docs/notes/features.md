# Features, tabela-fato e painel reconstruído — o que cada coluna é e por que

Nota de pesquisa em português (ADR-0006: código e nomes de coluna em inglês,
notas e relatórios em português). Descreve o que `just fact` e `just panel`
constroem a partir de `data/staged/`, quais decisões estão embutidas em cada
número e o que o painel reconstruído compartilha com o painel de estimação do
artigo. Todos os números foram medidos nesta base
(`data/analysis/manifest.json`, `data/analysis/panel_manifest.json`,
`reports/summary.json`) e o dicionário completo, gerado do registro, está em
[`docs/dictionary.md`](../dictionary.md).

## 1. Uma tabela-fato, e todo o resto é projeção dela

O ADR-0004 fixa **um** grão canônico — `grupo × rota × mês`, no universo de
replicação — e obriga todo outro grão a ser uma projeção testada dele. A razão é
simples e cara de aprender: duas tabelas construídas independentemente no mesmo
recorte viram duas fontes de verdade, e a que estiver errada só aparece meses
depois, dentro de uma regressão.

```
data/staged/year=AAAA/part-0.parquet          13.652.322 etapas de voo
        │  uma varredura por ano (airline_delays.fact.build.build_fact)
        ▼
data/analysis/fact_group_route_month.parquet  165.763 células × 87 colunas
        │  airline_delays.fact.projections.aggregate(fact, grão)
        ├─► route_month  ──► airline_delays.panel.build  ──► panel_route_month  31.313 × 228
        ├─► city_month                                                          21.231 linhas
        └─► airline_city_month                                                  49.801 linhas
```

Custo medido (`reports/summary.json`, `reconstruction.fact.seconds` e
`reconstruction.panel.seconds`): cerca de **11 s** para a tabela-fato e as duas
projeções de cidade, cerca de **8 s** para o painel, numa máquina de 16 GB. A
varredura é ano a ano por regra do brief, não por lentidão — uma única
varredura das catorze partições com um `GROUP BY` largo é a forma que faz a
máquina usar swap.

A unidade da varredura é o **ano civil do voo**, não o diretório
`year=AAAA` (ADR-0016). O diretório é o ano do arquivo de origem e a coluna
`year` vem de `flight_date`: as duas divergem em 3.723 linhas, e agrupar dentro
do diretório e concatenar emitia a mesma célula duas vezes — 844 linhas sobre
422 chaves na tabela-fato e 866 linhas sobre 433 chaves no painel, com contagens
iguais e medianas diferentes, porque cada cópia calculava a sua sobre parte dos
voos. `year_source_sql()` (`src/airline_delays/fact/build.py`) seleciona
`WHERE year = <alvo>` sobre a árvore inteira (as estatísticas de row-group do
parquet podam o resto, e o custo não muda), `build_fact()` afirma a unicidade
na saída e `src/airline_delays/panel/build.py` na entrada.

O teste de aditividade (`TestAdditivity`, em `tests/test_fact.py`) e a view
`v_check_additivity` em `sql/views.sql` fecham o ciclo pelos dois lados: a soma
da projeção tem de bater com a contagem direta feita sobre os voos. Na base
completa a view devolve **zero linhas**.

### O que a tabela-fato carrega

87 colunas: as oito chaves, as contagens de voos (`flights` = realizados +
cancelados = o `f` do artigo), as famílias simétricas de partida e chegada
(observações, atrasos acima de 0/15/30/60 minutos, antecipações, outliers, somas
de minutos em três convenções), bloco programado e realizado com a soma dos
quadrados (para o desvio-padrão sair exato em qualquer grão), recuperação em
voo, folga de bloco, as sete categorias do ADR-0005 mais os três conjuntos do
artigo, os motivos de cancelamento, **24 contagens horárias** e as marcas de
entrada e saída de grupo na rota.

As 24 colunas horárias são o que permite recalcular `peak_hour_share`,
`hhi_hours` e `sh_night` em qualquer grão sem voltar aos voos. Elas ficam na
tabela-fato e são descartadas nas projeções: `slim()`
(`src/airline_delays/fact/build.py`) as remove e arredonda os floats, porque a
informação já saiu delas.

Estatísticas de ordem (mediana, p90) **não** estão na tabela-fato: mediana não
soma. Elas são calculadas direto dos voos no grão rota-mês, dentro da mesma
varredura, e é por isso que a convenção do ADR-0012 é um parâmetro de
`build_fact()` e não uma decisão implícita.

## 2. O parâmetro que muda tudo: `empty_actual_means_on_time` (ADR-0012)

Nos arquivos de 2000–2009 um voo `REALIZADO` sem ocorrência vem com os horários
reais **vazios**. Medido por ano na base inteira
(`data/analysis/manifest.json`, bloco `missing_actual_by_year`):

| ano | realizados no universo | sem chegada real | % |
|---|---|---|---|
| 2000 | 587.007 | 470.274 | 80,1% |
| 2001 | 610.676 | 462.913 | 75,8% |
| 2002 | 564.375 | 433.947 | 76,9% |
| 2003 | 431.646 | 332.415 | 77,0% |
| 2004 | 456.323 | 345.947 | 75,8% |
| 2005 | 476.192 | 337.941 | 71,0% |
| 2006 | 493.853 | 339.684 | 68,8% |
| 2007 | 513.081 | 303.510 | 59,2% |
| 2008 | 600.121 | 420.910 | 70,1% |
| 2009 | 686.216 | 533.389 | 77,7% |
| 2010 | 796.922 | 146 | 0,02% |
| 2011 | 898.923 | 145 | 0,02% |
| 2012 | 942.587 | 115 | 0,01% |
| 2013 | 894.671 | 11 | 0,001% |

A quebra em 2010 é a mudança de layout, não de pontualidade.

O painel de estimação do artigo adota a leitura "vazio = pontual" (ADR-0012);
o staging deste repositório mantém o campo nulo, e a leitura mora na camada
que declara qual convenção usa.

**O que a flag faz, exatamente.** Ela não imputa nada na tabela-fato, que carrega
as duas contagens lado a lado: `arr_delay_obs` (existe horário real) e
`arr_missing_actual` (realizado, sem horário real, com previsto). A flag escolhe
o **denominador** das proporções e das médias, em `delay_denominator()`
(`src/airline_delays/fact/projections.py`):

- `True` → `arr_delay_obs + arr_missing_actual`. O voo sem ocorrência entra no
  denominador e não no numerador, que é exatamente "operou no horário".
- `False` → `arr_delay_obs`. A ausência não é dado.

**O que ela não faz.** Não muda nenhuma contagem de atraso e nenhuma soma de
minutos — um voo imputado em 0 minuto não está "acima de 0" e soma zero. Isso
está fixado por teste (`test_the_flag_does_not_move_a_single_delayed_count`,
em `tests/test_fact.py`), e é a razão de a tabela-fato poder ser neutra em
relação à convenção.

**Consequência prática.** Sob `False`, as taxas de atraso de chegada de
2000–2009 são calculadas sobre os 20–40% de voos realizados que tiveram
ocorrência — uma amostra selecionada justamente por ter tido ocorrência — e
saem muito acima das publicadas. Não é um número melhor; é outra pergunta. O
painel reconstruído usa `True`, a convenção do painel de estimação do artigo,
e o valor vigente viaja com a tabela na coluna `empty_actual_means_on_time` e
no manifesto (`data/analysis/manifest.json`). A camada de previsão lê o campo
vazio pela ADR-0017, que supersede a metade de previsão da ADR-0012
(`docs/notes/prediction.md`).

## 3. Sinal do atraso e truncamento (ADR-0008)

Este repositório mantém a antecipação negativa: um voo que chega adiantado tem
atraso menor que zero, e a média de minutos o vê assim.

Para contagens por limiar isso é irrelevante — `max(x,0) > 15` e `x > 15` são o
mesmo teste —, então `fl_odel`, `fsc_prdelarr` e todos os `sh_*` são iguais sob
as duas convenções. Para somas de minutos não é, e o painel publica as duas:
`fsc_minsarr` com sinal e `fsc_minsarr_trunc` truncada em zero, idem na
partida. O corte de outlier é 313,25 minutos por ADR-0008, aplicado só às
somas e ao valor absoluto do atraso (ADR-0015): as contagens `*_outliers`
ficam ao lado para que qualquer média possa ser refeita com ou sem eles.

## 4. Grupos, classes e os conjuntos do artigo

`data/external/groups.csv` é a tabela datada ao mês (ADR-0003). Duas coisas que
parecem detalhe e não são:

**A classe segue o grupo absorvedor.** Pantanal dentro da TAM é FSC a partir de
2009-12; Trip e Total dentro da Azul são LCC a partir de 2012-05. A tabela já
codifica isso, uma linha por período, e nada a jusante precisa de caso especial.

**Empresa sem rótulo é `other`, nunca nula** (ADR-0011). São 11.114 voos do
universo, quase todos estrangeiros. Descartá-los encolheria silenciosamente o
denominador de todo share; chamá-los de "regional" seria uma afirmação sobre
modelo de negócio que ninguém verificou. O `group` cai no próprio código ICAO,
então continuam competidores distinguíveis no HHI.

**Os conjuntos do artigo não são as classes.** O artigo usa quatro grupos como
FSC (TAM, Varig, Transbrasil, Vasp) e o ADR-0003 classifica também a Avianca
Brasil como FSC; o "LCC" do artigo são os grupos Gol e Azul, e a classe LCC
inclui a Webjet enquanto independente. As duas versões são calculadas e as duas
são publicadas: `fscc_*`/`lccclass_*` pela classe, `fsc_*`/`lccfu_*` pelo
conjunto do artigo (ADR-0013). Nenhuma foi ajustada para a outra — e a seção 6
diz qual das duas é a do painel de estimação do artigo.

## 5. As famílias novas

**Estrutura de mercado.** `n_groups`, `hhi_flights` (Σ s² sobre participação em
voos), `sh_leader`, `sh_flights_{fsc,lcc,regional,other}`, `n_entries`,
`n_exits`, `entry_lcc`. O HHI é sempre **recalculado** no grão de destino, nunca
promediado — `src/airline_delays/schema/columns.py` marca a regra e o teste
`test_a_proportion_is_never_declared_additive` a cobra.

O HHI de passageiros do artigo (`rthhi`, `maxcthhi`, `gmchhi`) não sai do VRA,
que é um arquivo de operação sem tráfego. As colunas existem e são inteiramente
nulas; as versões por voo vão ao lado com outro nome (`rthhi_flights`, …).
`passenger_weighted_hhi()` (`src/airline_delays/definitions/concentration.py`)
é a função com a assinatura certa que devolve `None` até os dados estatísticos
da ANAC serem coletados. Os nomes `gmchhi` e `maxcthhi` têm antecedente
documentado de 2013: a monografia de graduação do autor já compunha os dois
extremos da rota por uma média geométrica **ponderada** pelos voos planejados
de cada ponta, enquanto aqui a média é a não ponderada — ver
`docs/notes/monografia-2013.md` seção 3.

**Congestionamento (ADR-0007).** `data/external/capacity.csv` tem **um**
aeroporto, e uma linha não é um painel: `prcongested` fica nulo e declarado como
não reproduzido. O proxy interno é o que dá para calcular hoje: dentro de um nó
e de um **ano**, toma-se a distribuição de movimentos por dia-hora e chama-se
congestionada toda dia-hora igual ou acima do p90 dessa distribuição. Duas
propriedades importam — o limiar é relativo à escala do próprio aeroporto, então
Congonhas não é congestionada só por ser grande; e o limiar é fixo no ano, então
um mês pode ter mais ou menos que 10% de horas congestionadas, que é justamente
o sinal. A unidade é o **movimento** (partida na origem + chegada no destino),
sobre horários **programados**, o que a torna conhecível de véspera e livre de
vazamento para a camada de previsão.

**Hub.** O artigo usa participação de passageiros em conexão da Infraero, que
não é pública. O substituto é estrutural: a cidade é hub *de um grupo* quando
ele tem ≥ 20% dos movimentos dela **e** essa participação é ≥ 2× a participação
dele no sistema no mesmo mês, com piso de 100 movimentos na cidade-mês e 30 do
próprio grupo. O piso é o que separa medida de ruído: sem ele, a razão promove
uma regional com quatro movimentos mensais numa cidade pequena acima da Gol no
Rio de Janeiro.

**Contexto fora do universo.** `n_rows_all`, `n_extra` (DI 1 e 2), `n_return`
(DI 3), `n_intl_leg`, `n_cargo`, `n_postal`, `n_off_universe`. O universo é um
filtro, não um fato sobre o mundo: esses voos ocupam a mesma pista na mesma
hora e por isso entram no painel como contexto, sem nunca entrar em `f`.

## 6. Os dois painéis: as mesmas definições

Há dois painéis de rota-mês em `data/analysis/`, e eles são produtos
diferentes:

| | painel reconstruído | painel de estimação do artigo |
|---|---|---|
| arquivo | `panel_route_month.parquet` | `article_panel_route_month.parquet` |
| origem | os 168 CSV do VRA, pelo pipeline desta nota | a base final dos autores (dezembro de 2015), curada por `airline-delays article-panel` (ADR-0020) |
| rota-meses × colunas | 31.313 × 228 | 24.589 × 52 |
| rotas, meses | 310, 168 (2000-01 a 2013-12) | 209, 144 (2002-01 a 2013-12) |
| papel | a base aberta estendida e a entrada do preditor | a entrada de `airline-delays estimate` (`docs/notes/replication.md`) |
| chave em `reports/summary.json` | `reconstruction.panel` | `article_panel` |

O que os liga são **as mesmas definições**, registradas em `DECISIONS.md` e
restabelecidas pelo primeiro autor do artigo: o universo de voos (ADR-0002), o
mapa de nós (ADR-0001), os conjuntos de companhias (ADR-0003 com ADR-0013), a
taxonomia das causas (ADR-0005), o sinal e o corte do atraso (ADR-0008 com
ADR-0015) e a leitura do horário real vazio (ADR-0012). O painel reconstruído
carrega essa última como coluna, `empty_actual_means_on_time = 1` em toda
linha (`tests/test_panel.py`,
`test_the_convention_travels_with_the_table`).

**As colunas do artigo com o mesmo nome.** As contagens (`f`, `fl_can`,
`fl_odel`, `fl_ddel`, `dailyfl`, `ndays`, `prcanc`), os seis regressandos
(`fsc_oddsarr`, `fsc_minsarr`, `fsc_minsp15arr` e os três de partida) com as
proporções `fsc_prdelarr`/`fsc_prdeldep`, as três participações de causa
(`prwheather`, `princident`, `pr_connc`), as binárias de baixo custo (`lcc`,
`olccfu`, `dlccfu`, `maxalccfu`) e as de presença (`pres_glo`, `pres_azu`,
`pres_tam`) existem nos dois painéis sob o mesmo nome e a mesma definição —
`docs/dictionary.md` traz as duas camadas, `panel` e `article_panel`, uma
abaixo da outra. `rthhi`, `maxcthhi` e `gmchhi` existem nos dois, mas no
reconstruído são inteiramente nulos (seção 5); `prcongested` idem (ADR-0007).

**As colunas do artigo que o reconstruído não traz com valor** são a lista
`reconstruction.article_columns_missing` de `reports/summary.json`: `cshare`,
`dailyflcong`, `dailyflncong`, `maxprdel`, `rthhi`, `maxcthhi` e os sete
instrumentos `h1_maxcthhi`, `h2_maxcthhi`, `h3_maxcthhi`, `lnh1_maxcthhi`,
`l1h1_maxcthhi`, `l1h2_maxcthhi`, `h2_rthhi`. Os dois HHI e os instrumentos
esperam os dados estatísticos da ANAC (`docs/data-availability.md`, fonte 3);
`dailyflcong`/`dailyflncong` esperam as declarações de capacidade (fonte 6);
`cshare` esperaria uma tabela de codeshare por rota-mês; para `maxprdel` o
painel traz `maxprdel_proxy`, sob outro nome, porque a definição exata do
artigo não foi recuperada (`docs/dictionary.md`). As chaves e a geografia
(`od`, `o`, `d`, `o_region`, `d_region`, `o_uf`, `d_uf`, `km`) têm outros
nomes no reconstruído (`route`, `origin_node`, `dest_node`, `distance_km`), e
`pres_web` não é publicado nele.

**`fsc_*` e `fscc_*` são um fato definicional, não uma escolha de ajuste.** O
`fsc_*` dos dois painéis usa o conjunto de companhias do artigo — TAM, Varig
até 2007-03, Transbrasil e Vasp (ADR-0013); `fscc_*`, só no reconstruído, é a
variante pela classe FSC do ADR-0003, que inclui a Avianca Brasil. Quem
compara uma coluna `fsc_*` entre os dois painéis compara a mesma definição
sobre duas leituras dos mesmos arquivos brutos, colhidos em datas diferentes
(a base dos autores em 2015, o VRA de hoje em 2026-09-05,
`data/raw/manifest.json`).

## 7. Como reproduzir

```bash
uv run airline-delays reference    # valida data/external: procedência linha a linha e os conjuntos do ADR
uv run airline-delays fact         # tabela-fato + cidade-mês + empresa-cidade-mês        (~11 s)
uv run airline-delays panel        # painel rota-mês reconstruído, parquet e csv.gz        (~8 s)
uv run airline-delays dictionary   # docs/dictionary.md, gerado do registro
uv run airline-delays datapackage  # datapackage.json (Frictionless v2), idem
```

`just fact` e `just panel` embrulham os mesmos comandos; `just panel` já
regenera o dicionário e o datapackage. As tabelas de `data/analysis/` são
versionadas (ADR-0014) junto com os manifestos que dizem como refazê-las, e
`just check-analysis` falha quando uma tabela commitada deixa de corresponder
ao código — ver [`data/analysis/README.md`](../../data/analysis/README.md).
