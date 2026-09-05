# M2 — A leitura do orientador: treze respostas sem perguntas

**Objetivo.** Ver que a virada de preços para atrasos (M1) não foi um
achado empírico — foi um exercício de literatura imposto pelo orientador,
e o único registro dele é incompleto por desenho: sobrevivem as
respostas, não as perguntas. E olhar, dentro deste repositório, para um
caso do mesmo formato — um julgamento apoiado em fonte convergente, não
em documento primário — e o modo honesto de o marcar.

## Contexto (fora deste repositório)

`Questões Alessandro.docx` (criado 2014-06-17, fechado 2014-08-01,
revision 18, 1.300 minutos de edição acumulados) contém treze respostas
numeradas — `QUESTÃO 1`, `2`, `3`, **`6`**… `13`. As respostas 4 e 5
**não existem no arquivo**. Todo o conteúdo é revisão de literatura (Mayer
e Sinai 2003, Mazzeo 2003, Morrison e Whinston 2008, Rupp 2009, Santos e
Robin 2010, entre outros — três delas, Mayer e Sinai 2003, Rupp 2009 e
Santos e Robin 2010, já estavam na bibliografia da monografia de 2013,
`docs/theory/bibliografia.md`) — nenhuma pergunta original do orientador
sobrevive; só se infere o tema de cada uma pela resposta que a segue. A
`QUESTÃO 3` é o único lugar onde o tema de preços reaparece, já como
possibilidade futura, não como plano:

> "sob o ponto de vista das empresas aéreas, pode-se estimar a demanda por
> viagens aéreas em função do preço e do desempenho em não atrasar."

Comparando a proposta (set/2013, M1) com o primeiro seminário (30 de
julho de 2014, M3), a pergunta já é outra: determinantes de atrasos, não
mais preços. O mecanismo dessa virada — treze respostas de literatura,
1.300 minutos, dezoito revisões — é o retrato de um aluno lendo o que foi
mandado ler, não de um resultado que apontou o caminho.

Esta descrição, incluindo os trechos entre aspas, vem de uma análise de
acervo produzida antes deste repositório existir (*avaliação em oito
critérios*, seção C5.2) — o arquivo em si é privado e não está aqui (M12).

## O mesmo formato, dentro deste repositório

`data/external/groups.csv` (o mapa de grupos econômicos e fusões de
empresas aéreas, `DECISIONS.md` ADR-0003) tem o mesmo problema em miniatura:
a maior parte das datas de fusão vem de "a regra usada pelo laboratório"
— uma convenção herdada, não uma verificação primária linha a linha. A
diferença é que aqui isso é **declarado por linha**, não perdido:

```bash
just refs
```

**Número esperado.** `just refs` roda sem erro — toda linha de
`data/external/groups.csv` tem `source`, `url` e `confidence` preenchidos
(a validação que `docs/notes/references.md` descreve). Nenhuma linha do
arquivo é grau A puro: mesmo as datas mais concretas (Gol 2001-01, Azul
2008-12) vêm de eventos com grau B — resumo de busca convergente, não
página aberta diretamente (`docs/notes/references.md`, seção 2).

## Exercício

`docs/notes/references.md`, seção "Itens em aberto, consolidado", item 2,
lista 21 códigos ICAO de empresa aérea (`ABJ, ABZ, AMG, AVI, BRB, LEG,
MEL, MSQ, NHG, NRA, PAM, PEP, PLY, RIO, RLE, SBA, SLX, TIM, TSD, TVJ,
VCR`) cuja identidade real nunca foi pesquisada — eles aparecem em
`data/external/groups.csv` classificados `other` (`DECISIONS.md`
ADR-0011). Escolha um código, procure por ele (empresa aérea regional, de
táxi aéreo ou cargueira brasileira, ativa entre 2000 e 2013) e, se
encontrar algo com fonte verificável, escreva a linha que você adicionaria
— com `source`, `url`, `retrieved_at` e `confidence` — no formato exato
das linhas existentes de `groups.csv`. Se não encontrar nada convincente,
essa também é uma resposta válida: documente a busca e o motivo, do mesmo
jeito que `docs/notes/references.md` já documenta as buscas que não
fecharam (ex.: Congonhas sem data de início de coordenação, seção 6).

## Nota honesta

O enunciado das perguntas do orientador não está no acervo original — só
as respostas sobreviveram, e as respostas 4 e 5 nem essas. Neste
repositório, o equivalente é a lista de 21 códigos `other` não
identificados: a ausência é documentada (não escondida), mas não
resolvida. Nenhum dos dois casos foi "consertado" inventando o que falta.
