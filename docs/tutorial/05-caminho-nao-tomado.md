# M5 — O caminho não tomado: o projeto sobre preços

**Objetivo.** Conhecer o projeto irmão que retomou a pergunta original de
preços (M1) — e entender por que ele não está incluído neste repositório,
nunca foi publicado, e mesmo assim já continha, escrita e não usada, uma
decisão que este repositório resolve de outro jeito: um limiar de atraso
ambíguo entre 15 e 30 minutos.

## Contexto (fora deste repositório)

Existe um segundo projeto no mesmo acervo de pesquisa, sobre atrasos
**e preços** — a pergunta original de 2013 (M1), retomada dois anos depois
por conta própria. Ele nasce e morre em uma semana: um rascunho de artigo
completo, com três autores (Bendinelli, Oliveira e Correia), escrito entre
24 e 29 de junho de 2015, apresentado num único seminário com o brasão do
ITA — e nunca circulou depois disso. Sem proposta própria antes, sem nada
depois: nenhum periódico, nenhuma citação, nenhum vestígio de submissão.

O que existe é surpreendentemente reproduzível para um projeto que nunca
foi publicado: os efeitos fixos (FE) e FE2SLS do rascunho reproduzem com
erro abaixo de 1e-4 e N = 13.887 — igual à amostra do próprio rascunho —
desde que o operador de defasagem (`L.`) respeite os buracos do painel
(ignorá-los dá 14.390 linhas, um número diferente e errado). Uma
das variáveis-endógenas do artigo replicado neste repositório, a
**equação do TRA**, já estava dentro da pasta desse projeto irmão, num
script chamado `internalizationinbrazil.do` — antes de o artigo em si
existir.

E há uma ambiguidade não resolvida, exatamente do tipo que este
repositório existe para não deixar passar em silêncio: o texto do
rascunho descreve um limiar de atraso de **30 minutos** (citando a
Resolução ANAC 218); o código que o acompanha roda com **15 minutos**. As
duas versões nunca foram reconciliadas, porque o projeto parou antes
disso importar.

O limiar de 30 minutos não nasceu nesse rascunho: é o primeiro dos dois
cortes (30 e 60 minutos) que a ANAC publicava pela Resolução 218, e foi a
variável dependente da monografia de graduação de 2013 (M14,
`docs/notes/monografia-2013.md`), cujo texto já contrasta "mais de trinta
minutos" no Brasil com "mais de quinze minutos" nos Estados Unidos. O
artigo de 2016 adotou os 15 minutos; o rascunho de 2015 ficou no meio, com
o texto em 30 e o código em 15.

Esta descrição vem de uma análise de acervo produzida antes deste
repositório existir (*avaliação comparativa*, projeto 02, e *avaliação em
oito critérios*, seção C5) — nenhum arquivo desse projeto está neste
repositório: nem o rascunho, nem os do-files, nem os slides. É descrito
aqui, não incluído — ver M12 para as razões de consentimento e licença.

## A mesma ambiguidade, resolvida aqui por nomeação

O painel reconstruído deste repositório não escolhe entre 15 e 30 minutos —
publica os dois, sob nomes que dizem o que cada um é:

```bash
grep -n "prdelarr1530\|prdelarr30m" src/airline_delays/schema/columns.py
```

**Número esperado.** Duas entradas: `prdelarr1530` (chegadas entre 15 e 30
minutos de atraso) e `prdelarr30m` (chegadas com mais de 30 minutos) — os
dois são sufixos de um só molde, aplicados a cada família de empresa
(`fsc_`, `fscc_`, `all_`, `lccfu_`, `lccclass_`; `docs/dictionary.md` lista
cada coluna gerada). A ambiguidade do projeto irmão — texto contra código —
não se repete aqui porque as duas leituras têm nomes diferentes desde o
início, para cada conjunto de empresas.

## Exercício

Leia a entrada "ANAC tariff microdata" de
[`docs/data-availability.md`](../data-availability.md) de novo (M1 já
apontou para ela). O projeto irmão retomou a pergunta de preços com dados
que não são públicos. Escreva, em três frases, o que
mudaria no desenho se alguém tentasse retomar essa mesma pergunta hoje,
usando só a fonte pública listada ali — e por que a chave `route`/`ym` do
painel reconstruído (`data/analysis/panel_route_month.parquet`) já deixaria
essa tentativa mais fácil do que reconstruir tudo do zero.

## Limites e próximos passos

Nada do projeto irmão foi reconstruído neste repositório — nem a base, nem
o código, nem os resultados. A avaliação comparativa que precedeu este
repositório recomendou explicitamente não usá-lo como espinha dorsal
(ele "não é um projeto concorrente: é o prólogo" do projeto que este
repositório replica), mas registrou que ele tem a melhor
reprodutibilidade dos três acervos comparados — um contraexemplo do que
uma estimação reproduzível parece, mesmo sem nunca ter sido publicada.
