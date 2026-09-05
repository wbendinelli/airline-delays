# M6 — Dados: da fonte pública ao painel, com a reconciliação

**Objetivo.** Percorrer o caminho inteiro que o projeto original nunca
documentou — do CSV bruto da ANAC ao painel de rota-mês — e ver, com
números medidos, o quanto disso é reconstruível a partir de dado
público, e o quanto diverge de um gabarito privado que serviu de
referência.

## O elo que faltava

O projeto original citava o VRA como fonte ("a maior parte dos dados
utilizados nesta pesquisa é publicamente disponível pela ANAC"), mas
nenhum script entre o arquivo bruto e o painel final dos autores foi
entregue — catorze arquivos intermediários nunca existiram no acervo
(*avaliação em oito critérios*, seção C2; descrição externa, arquivo
privado, não incluído aqui — M12). Este módulo é o preenchimento desse
elo, com código real e números medidos, não uma reconstituição do
processo original.

## Arquivos deste repositório

- [`docs/notes/staging.md`](../notes/staging.md) — os dois layouts brutos
  (12 colunas até 2009, 20 de 2010 em diante), campo a campo, com todas as
  decisões de limpeza contadas.
- [`reports/reconciliation.md`](../../reports/reconciliation.md) — o CSV
  de hoje contra o `vra.dta` de 2019 que serviu de gabarito, linha por
  linha.
- [`docs/notes/features.md`](../notes/features.md) — a tabela-fato e o
  painel, e o que a comparação com o gabarito privado mediu.
- `DECISIONS.md` ADR-0001 (nós metropolitanos), ADR-0002 (universo de
  voos), ADR-0012 (horário realizado ausente nos arquivos de 2000-2009).

## Comandos

```bash
just fetch      # ~17 min, 2,17 GB, 168 arquivos (data/raw/manifest.json)
just stage      # ~8,4 s, os dois layouts em um só schema (data/staged/manifest.json)
just refs       # valida data/external/*.csv linha a linha
just features   # ~11 s, a tabela-fato grupo x rota x mês (data/analysis/manifest.json)
just panel      # ~7,5 s, o painel público de rota-mês (data/analysis/panel_manifest.json)
```

Os dois primeiros comandos custam tempo real (download e parsing dos 168
arquivos); os três últimos rodam em segundos porque operam sobre o que já
foi baixado. Quem só quer ver os números sem baixar nada pode ir direto ao
próximo parágrafo — os manifestos já commitados dizem a mesma coisa.

## Números esperados

`data/staged/manifest.json`: **13.652.322** etapas de voo em 168 arquivos,
265 MB de parquet a partir de 2,17 GB de CSV — dois layouts, não um: 12
colunas por vírgula até 2009, 20 colunas por ponto e vírgula de 2010 em
diante, com a ordem das colunas diferente entre os dois
(`docs/notes/staging.md`, seção 1).

`reports/reconciliation.md`: numa amostra determinística de **184.522**
voos casados entre o CSV de hoje e o `vra.dta` de 2019, `status` concorda
em 99,9%, `cause_code` em 99,6% — e `actual_dep`/`actual_arr` concordam em
apenas **60,2%**, porque a safra de 2019 tratou horário real vazio como
"pontual" e este repositório mantém o campo nulo (ADR-0012). É o achado
que mais muda a leitura de qualquer média de atraso 2000-2009.

`data/analysis/taxas.csv`: o artigo `f` (voos programados) reproduz o
gabarito em 90,2% das rota-meses no painel inteiro e **95,3%** na metade
da série cujos arquivos brutos não mudaram desde 2019 — a reconstrução
anterior, lendo a mesma safra de 2019 diretamente, tinha relatado 97,5%.
O mapa de nós (`DECISIONS.md` ADR-0001) sozinho muda a concordância de `f`
de 86,8% para 97,4%: colocar Viracopos dentro do nó de São Paulo, em vez
de tratá-lo como "Campinas" — como faz a base tarifária —, fecha a maior
parte dessa diferença.

## Exercício

Abra `data/analysis/manifest.json` e localize o bloco
`missing_actual_by_year`. Para 2002, quantos dos voos realizados no
universo de replicação **não têm** chegada real registrada? Compare esse
percentual com o de 2010. O que muda entre os dois anos não é
pontualidade — é o layout do arquivo bruto (`docs/notes/staging.md`,
seção 4.1). Depois, decida: se você estivesse calculando a taxa de atraso
de chegada de 2002 sozinho, sem saber disso, que erro cometeria?

## Nota honesta

Duas coisas continuam sem explicação, declaradas e não resolvidas: a
concordância de `fl_ddel` (atraso de chegada) fica em 56,3% contra 87,9%
de `fl_odel` (atraso de partida) sob a mesma regra exata — a assimetria é
citada em `DECISIONS.md` ADR-0002 e permanece um mistério; e o painel
final dos autores do artigo original nunca foi reconstruído do zero por
nenhum dos dois lados (nem no acervo, nem aqui) — este repositório parte
do gabarito entregue e diz isso, em vez de fingir uma cadeia que não foi
percorrida (`docs/declared-differences.md`, "Not attempted, and why").
