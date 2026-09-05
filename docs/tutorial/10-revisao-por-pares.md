# M10 — Revisão por pares, o buraco

**Objetivo.** Ver que a revisão por pares do artigo original não deixou
nenhum rastro em texto — nem os pareceres, nem a carta de resposta, nem
uma versão intermediária do manuscrito — e usar essa ausência para
justificar uma prática concreta deste repositório: escrever toda
divergência por escrito, no momento em que ela é encontrada, em vez de
confiar na memória de uma conversa.

## Contexto (fora deste repositório)

Entre a proposta de 2013 e a defesa de 2016 há artefato datado em quase
todo degrau — exceto um. Da submissão (2015-10-02) à publicação
(2016-01-19) não sobra **nada**: nenhuma carta, nenhum parecer, nenhuma
resposta aos revisores, nenhuma versão em inglês do manuscrito anterior à
aceita. O único rastro de todo o processo de revisão por pares, em
qualquer um dos dois documentos disponíveis (artigo e dissertação), é uma
única nota de rodapé — e ela muda de forma entre os dois textos: no
artigo, o crédito é explícito (*"as suggested by one anonymous
reviewer"*, nota 20); na dissertação, a mesma variável reaparece na nota
33, sem crédito (ver M9). Um terceiro não consegue, com o material
disponível, saber o que os pareceristas pediram, nem o que mudou entre a
rodada 1 (nunca entregue) e a rodada 2 (só o cabeçalho `*TRA - round2` nos
do-files sobrevive como prova de que ela existiu).

Esta descrição vem de uma análise de acervo produzida antes deste
repositório existir (*avaliação em oito critérios*, seção C1, "Por que 3
e não 4") — os documentos originais são privados e não estão aqui (M12).

## O que este repositório faz diferente, e por quê

`DECISIONS.md` ADR-0010 existe exatamente para não repetir esse buraco:
quando duas opções de implementação divergem e a evidência não resolve
sozinha, um painel de revisores avalia as duas, e **a divergência e o
raciocínio ficam registrados ali**, não numa conversa que ninguém
escreveu. `docs/declared-differences.md` é a mesma ideia aplicada a
resultados: cada divergência contra o artigo ou o gabarito privado tem
uma linha, com a causa até onde a evidência permite, no momento em que
foi medida — não reconstruída depois, de memória.

## Exercício

Abra [`docs/declared-differences.md`](../declared-differences.md) e
escolha uma das nove linhas da tabela "Replication (Tables 2-7)" (por
exemplo, a linha 1, sobre o N 5,3% maior). Escreva, na voz de um
parecerista imaginário, a pergunta de uma frase que essa linha
provocaria — e, ao lado, a resposta que o próprio texto já dá. Se a
resposta já está escrita, o "buraco" deste item específico já foi
fechado por antecipação; se você conseguir pensar numa pergunta que o
texto não responde, essa é uma lacuna real, candidata a virar uma issue.

## Nota honesta

Escrever as divergências no momento em que são medidas não é o mesmo que
ser revisado por pares de verdade — este repositório nunca passou por
revisão externa formal, e `docs/declared-differences.md` é a
autoavaliação de quem construiu o pipeline, não o julgamento independente
que faltou ao artigo original. O que se pode afirmar é mais modesto: pelo
menos aqui, se algum dia houver uma revisão de verdade, ela terá um
documento para começar a discordar, em vez de um vazio.
