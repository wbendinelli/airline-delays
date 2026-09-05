# Features, tabela-fato e painel público — o que cada coluna é e por que

Nota de pesquisa em português (ADR-0006: código e nomes de coluna em inglês,
notas e relatórios em português). Descreve o que `just features` e `just panel`
constroem a partir de `data/staged/`, quais decisões estão embutidas em cada
número e o que a comparação com o gabarito privado mediu. Todos os números
foram medidos nesta base; a tabela coluna a coluna está em
`data/analysis/taxas.csv` e o dicionário completo, gerado do registro, em
[`docs/dictionary.md`](../dictionary.md).

## 1. Uma tabela-fato, e todo o resto é projeção dela

O ADR-0004 fixa **um** grão canônico — `grupo × rota × mês`, no universo de
replicação — e obriga todo outro grão a ser uma projeção testada dele. A razão é
simples e cara de aprender: duas tabelas construídas independentemente no mesmo
recorte viram duas fontes de verdade, e a que estiver errada só aparece meses
depois, dentro de uma regressão.

```
data/staged/year=AAAA/part-0.parquet          13.652.322 etapas de voo
        │  uma varredura por ano (vra.features.build_fact)
        ▼
data/analysis/fact_group_route_month.parquet  166.203 células × 87 colunas
        │  vra.features.aggregate(fact, grão)
        ├─► route_month  ──► vra.panel  ──► panel_route_month  31.760 × 228
        ├─► city_month                                          21.250 linhas
        └─► airline_city_month                                  49.828 linhas
```

Custo medido: **12 s** para a tabela-fato e as duas projeções de cidade, **9 s**
para o painel, numa máquina de 16 GB. A varredura é ano a ano por regra do
brief, não por lentidão — uma única varredura das catorze partições com um
`GROUP BY` largo é a forma que faz a máquina usar swap.

O teste de aditividade (`tests/test_features.py::TestAdditivity`) e a view
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
tabela-fato e são descartadas nas projeções: `vra.features.slim` as remove e
arredonda os floats, porque a informação já saiu delas.

Estatísticas de ordem (mediana, p90) **não** estão na tabela-fato: mediana não
soma. Elas são calculadas direto dos voos no grão rota-mês, dentro da mesma
varredura, e é por isso que a convenção do ADR-0012 é um parâmetro de
`build_fact` e não uma decisão implícita.

## 2. O parâmetro que muda tudo: `legacy_missing_actual_as_zero` (ADR-0012)

Nos arquivos de 2000–2009 um voo `REALIZADO` sem ocorrência vem com os horários
reais **vazios**. Medido por ano na base inteira
(`data/analysis/manifest.json`):

| ano | realizados no universo | sem chegada real | % |
|---|---|---|---|
| 2000 | 587.021 | 470.283 | 80,1% |
| 2001 | 610.682 | 462.920 | 75,8% |
| 2002 | 564.370 | 433.937 | 76,9% |
| 2003 | 431.640 | 332.414 | 77,0% |
| 2004 | 456.338 | 345.963 | 75,8% |
| 2005 | 476.183 | 337.932 | 71,0% |
| 2006 | 493.868 | 339.701 | 68,8% |
| 2007 | 513.074 | 303.498 | 59,2% |
| 2008 | 600.121 | 420.905 | 70,1% |
| 2009 | 686.264 | 533.440 | 77,7% |
| 2010 | 796.889 | 83 | 0,01% |
| 2011 | 898.907 | 145 | 0,02% |
| 2012 | 942.590 | 115 | 0,01% |
| 2013 | 894.658 | 11 | 0,001% |

A quebra em 2010 é a mudança de layout, não de pontualidade.

A safra privada de 2019 leu vazio como "operou no horário previsto"
(`reports/reconciliation.md`, seção 5: em 72.375 de 72.381 linhas o `.dta`
gravou exatamente o horário previsto). O staging deste repositório mantém nulo.

**O que a flag faz, exatamente.** Ela não imputa nada na tabela-fato, que carrega
as duas contagens lado a lado: `arr_delay_obs` (existe horário real) e
`arr_missing_actual` (realizado, sem horário real, com previsto). A flag escolhe
o **denominador** das proporções e das médias, em `features.delay_denominator`:

- `True` → `arr_delay_obs + arr_missing_actual`. O voo sem ocorrência entra no
  denominador e não no numerador, que é exatamente "operou no horário".
- `False` → `arr_delay_obs`. A ausência não é dado.

**O que ela não faz.** Não muda nenhuma contagem de atraso e nenhuma soma de
minutos — um voo imputado em 0 minuto não está "acima de 0" e soma zero. Isso
está fixado por teste (`test_the_flag_does_not_move_a_single_delayed_count`), e
é a razão de a tabela-fato poder ser neutra em relação à convenção.

**Consequência prática.** Sob `False`, as taxas de atraso de chegada de
2000–2009 são calculadas sobre os 20–40% de voos realizados que tiveram
ocorrência — uma amostra selecionada justamente por ter tido ocorrência — e
saem muito acima das publicadas. Não é um número melhor; é outra pergunta. O
painel usa `True` porque tem de reproduzir um gabarito construído assim, e o
valor vigente viaja com a tabela na coluna
`legacy_missing_actual_as_zero`. A camada de previsão usa `False`.

## 3. Sinal do atraso e truncamento (ADR-0008)

A safra de 2019 gravou `delarrive = max(real − previsto, 0)`: nenhum valor
negativo em 10.774.607 linhas comparáveis. Este repositório mantém a
antecipação negativa.

Para contagens por limiar isso é irrelevante — `max(x,0) > 15` e `x > 15` são o
mesmo teste —, então `fl_odel`, `fsc_prdelarr` e todos os `sh_*` são comparáveis
entre as duas convenções. Para somas de minutos não é, e o painel publica as
duas: `fsc_minsarr` com sinal e `fsc_minsarr_trunc` truncada, idem na partida.
O corte de outlier é 313,25 minutos por ADR-0008, aplicado só às somas: as
contagens `*_outliers` ficam ao lado para que qualquer média possa ser refeita
com ou sem eles.

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
são publicadas: `fsc_*`/`lccclass_*` pela classe, `fscb_*`/`lccfu_*` pelo
conjunto do artigo. Nenhuma foi ajustada para a outra — e a seção 6 mostra o
tamanho da diferença.

## 5. As famílias novas

**Estrutura de mercado.** `n_groups`, `hhi_flights` (Σ s² sobre participação em
voos), `sh_leader`, `sh_flights_{fsc,lcc,regional,other}`, `n_entries`,
`n_exits`, `entry_lcc`. O HHI é sempre **recalculado** no grão de destino, nunca
promediado — `registry.py` marca a regra e o teste
`test_a_proportion_is_never_declared_additive` a cobra.

O HHI de passageiros do artigo (`rthhi`, `maxcthhi`, `gmchhi`) não sai do VRA,
que é um arquivo de operação sem tráfego. As colunas existem e são inteiramente
nulas; as versões por voo vão ao lado com outro nome (`rthhi_flights`, …).
`hhi.passenger_weighted_hhi` é a função com a assinatura certa que devolve
`None` até os dados estatísticos da ANAC serem coletados.

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

## 6. O que a comparação com o gabarito mediu

`replication/gabarito/compare.py` é o único módulo que lê
`AIRLINE_DELAYS_PRIVATE_DIR`, e o que ele escreve são estatísticas de
concordância, nunca um valor do gabarito. Saída em `data/analysis/taxas.csv` e
no bloco gerado de `docs/declared-differences.md`.

| coluna | taxa | taxa, safra estável | reconstrução (2019) |
|---|---|---|---|
| `f` | 0,901 | 0,953 | 0,975 |
| `fl_can` | 0,937 | 0,948 | 0,978 |
| `fl_odel` | 0,854 | 0,877 | 0,924 |
| `fsc_prdelarr` (classe FSC) | 0,527 | 0,534 | 0,651 |
| **`fscb_prdelarr` (conjunto do artigo)** | 0,610 | **0,649** | 0,651 |
| `prwheather` | 0,882 | 0,919 | 0,985 |
| `princident` | 0,923 | 0,955 | 0,991 |
| `pr_connc` | 0,913 | 0,945 | 0,992 |
| `maxalccfu` | 1,000 | 1,000 | 1,000 |

Duas leituras, ambas medidas e nenhuma ajustada.

**Primeira: a safra do arquivo bruto.** A reconstrução de 2026-09-04 leu o
`vra.dta` de 2019 — a mesma safra de que o próprio gabarito foi feito. Este
repositório reconstrói dos arquivos que a ANAC publica hoje, e
`reports/reconciliation.md` mede as duas safras diferindo em até 48.215 linhas
num único mês. Separando os 144 meses pela mediana da diferença relativa de
linhas, a concordância de `f` é 0,94 / 0,96 / 0,97 nos três quartis mais quietos
e **0,74** no mais ruidoso, com correlação de −0,45 entre a taxa e o tamanho da
divergência de safra. Por isso `taxas.csv` traz duas taxas por coluna. E as
divergências são pequenas: em `f` e `fl_can` a mediana **e** o p90 da diferença
absoluta são **zero voo**; em `fl_odel` o p90 é um voo.

**Segunda: o conjunto FSC.** `fscb_prdelarr` — o conjunto de grupos do artigo,
sem a Avianca — chega a **0,649** na metade estável, contra os 0,651 da
reconstrução. Nos minutos, `fscb_minsarr` difere do gabarito por uma mediana de
0,060 min e p90 de 2,11, contra os 0,07 e 2,2 que a reconstrução reportou para a
mesma aproximação. Ou seja: **com o conjunto de empresas do artigo, este
pipeline reproduz as colunas de atraso FSC com a mesma precisão de quem tinha o
bruto privado.** A diferença em `fsc_*` é escolha de conjunto de empresas, não
defeito de definição de atraso — e é o que valida, de lado, a flag do ADR-0012.

O que continua sem explicação é o de sempre (ADR-0002): `fl_ddel` reproduz 0,56
onde `fl_odel` reproduz 0,88, sob a mesma regra e no mesmo universo, com p90 de
12 voos contra 1. Declarado, não resolvido.

## 7. Como reproduzir

```bash
uv run vra refs        # valida data/external: procedência linha a linha e os conjuntos do ADR
uv run vra features    # tabela-fato + cidade-mês + empresa-cidade-mês        (~12 s)
uv run vra panel       # painel rota-mês, parquet e csv.gz                    (~9 s)
uv run vra dictionary  # docs/dictionary.md, gerado do registro
uv run vra datapackage # datapackage.json (Frictionless v2), idem
AIRLINE_DELAYS_PRIVATE_DIR=... uv run python -m replication.gabarito.compare
```

As tabelas grandes de `data/analysis/` não vão para o git (regra 4 do brief:
tabelas de análise abaixo de poucos MB). O que fica versionado é a procedência —
os dois manifestos, `taxas.csv` e o `README.md` que diz como refazer o resto.
Ver [`data/analysis/README.md`](../../data/analysis/README.md).
