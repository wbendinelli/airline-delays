# M9 — Da dissertação ao artigo: datas, título, autoria

**Objetivo.** Ver o que muda entre a dissertação de mestrado (depositada
em português, março de 2016) e o artigo publicado (em inglês, aceito um
mês e meio antes) — e por que, apesar das datas parecerem fora de ordem,
elas não estão.

## Contexto (fora deste repositório)

A cronologia, lida diretamente dos metadados internos e do texto
publicado: o artigo foi recebido em 2015-10-02, revisto em 2015-12-05,
**aceito em 2016-01-05**; a base final (`proj18.dta`) foi fechada em
2015-12-03, dois dias antes do reenvio da versão revisada. A defesa da
dissertação aconteceu em **2016-02-22** — depois de o artigo já ter sido
aceito — e o registro formal na biblioteca do ITA é de 2016-03-17. Ou
seja: o artigo foi escrito, revisado e aceito **antes** da defesa que
formalmente o antecede academicamente. Entre a montagem das bases brutas
(2015-04-01) e a submissão (2015-10-02) há **seis meses sem nenhum
artefato no acervo** — exatamente o período em que o painel final foi
construído e o modelo virou 2SGMM.

Título e autoria mudam entre os dois documentos. O artigo: *"Airline
delays, congestion internalization and **non-price spillover effects** of
low cost carrier entry"*, com Bendinelli, Bettini e Oliveira como autores.
A dissertação: *"Atrasos de empresas aéreas, internalização do
congestionamento e **concorrência**"*, só com Bendinelli — Bettini aparece
apenas como membro externo da banca examinadora (USP), não como coautor
do texto em português.

A decomposição de curto e longo prazo, prometida na introdução do artigo
("Another contribution of the paper lies in... time decomposition into
its short-run and long-run effects"), não é entregue em nenhuma tabela —
e a dissertação, dois meses depois, **remove a promessa inteira**: as
palavras "curto prazo", "longo prazo" e "decomposição" têm zero
ocorrências no texto em português. E o único rastro de revisão por pares
em qualquer um dos dois documentos muda de forma entre eles: o artigo
credita a ideia a *"as suggested by one anonymous reviewer"* (nota de
rodapé 20); a dissertação reproduz o mesmo teste na nota 33 — **sem** essa
atribuição.

Esta cronologia e as citações literais vêm de uma análise de acervo
produzida antes deste repositório existir (*avaliação em oito critérios*,
seção C1 e C5.6) — os dois documentos originais são privados e não estão
aqui (M12); o artigo publicado é citado só por DOI
(`docs/data-availability.md`).

## Arquivos deste repositório

O título e a autoria que sobrevivem aqui são os do artigo publicado — a
única versão citável, e a única redistribuível por DOI:

```bash
grep -n "title:" CITATION.cff
```

**Número esperado.** Duas linhas: o título deste software
(`airline-delays: from ANAC's raw VRA records to replication and delay
prediction`) e o título do `preferred-citation` — o artigo, com o título
em inglês exatamente como publicado, `non-price spillover effects`
incluído. `DECISIONS.md` ADR-0006 é a decisão deste repositório sobre
língua (inglês para código e README, português para notas e tutorial) —
uma escolha que o próprio arco original já antecipava, ao publicar em
inglês e defender em português.

## Exercício

Sem abrir nenhum arquivo além do que já foi citado acima, escreva de
memória o título da dissertação e o do artigo, lado a lado, e circule a
palavra que muda. Depois pense: por que "concorrência" e "non-price
spillover effects" descrevem o mesmo achado de dois jeitos tão diferentes?
(Pista: releia a frase do resumo do artigo sobre "spillover" citada em
`avaliacao-8-criterios.md`, C5.7, ou pergunte a si mesmo o que "spillover"
significaria em português numa única palavra.)

## Nota honesta

Nenhum documento do acervo original registra o que aconteceu nos seis
meses entre a montagem das bases e a submissão — nem uma versão
intermediária do manuscrito em inglês, nem uma ata de decisão sobre o
2SGMM substituir o OLS. O que se sabe vem inteiramente do produto final
de cada etapa, nunca da conversa que o produziu. O próximo módulo (M10)
trata do buraco ainda maior: a revisão por pares em si.
