# M3 — O primeiro desenho: nível aeroporto, capacidade de pátio

**Objetivo.** Ver o primeiro desenho empírico do projeto original — nível
aeroporto, não rota — e uma variável inteira que foi construída, testada
e abandonada antes do artigo. Depois, ver o que sobrevive dessa ideia
neste repositório, sob uma definição de capacidade diferente e por um
motivo declarado: a tabela de capacidade que a ideia original precisava
nunca existiu completa em nenhuma fonte pública encontrada.

## Contexto (fora deste repositório)

O primeiro seminário de tese (`1, Seminário de Tese.docx`, criado
2014-07-30) já não é sobre preços — o título é "DETERMINANTES DOS ATRASOS
EM AEROPORTOS BRASILEIROS", unidade empresa-rota-tempo, com efeitos fixos,
e quatro fontes declaradas: VRA, HOTRAN, o relatório de movimentação da
Infraero (RPE) e METAR/INPE. A Seção 4 inteira do documento — posições de
estacionamento, tempo de permanência, mix de aeronaves, mix de segmentos,
restrições operacionais — sustenta uma variável de capacidade de pátio:
"divide-se a movimentação média mensal na hora pico do pátio pela
capacidade atual do pátio". **Nada disso aparece no artigo publicado.**
Sobrou, no desenho final, "hora congestionada" definida sobre a
capacidade declarada de **pista**, do estudo BNDES (2010) — um conceito de
capacidade diferente (pátio de estacionamento contra pista de pouso e
decolagem), não uma continuação direta.

Esta descrição vem de uma análise de acervo produzida antes deste
repositório existir (*avaliação em oito critérios*, seção C5.4) — o
documento original é privado e não está aqui (M12).

## O que sobrevive aqui, e sob que forma

Este repositório também usa capacidade declarada de pista (o mesmo estudo
BNDES 2010, `DECISIONS.md` ADR-0007) — não a capacidade de pátio, que
nunca foi tentada de novo aqui. E, como no artigo original, a tabela de
capacidade é curta demais para cobrir o painel inteiro:

```bash
cat data/external/capacity.csv
```

**Número esperado.** Uma linha: Congonhas (`SBSP`), 33 movimentos/hora
para aviação comercial a partir de 2007-08, grau de confiança B
(`docs/notes/references.md`, seção 6). Nenhum outro aeroporto do painel
tem capacidade declarada transcrita ainda — ver a linha correspondente em
[`docs/data-availability.md`](../data-availability.md).

Como uma linha não é um painel, `src/vra/congestion.py` define um
**proxy interno**, que não depende de nenhuma tabela externa: dentro de um
nó e um ano, toda dia-hora com movimentos programados no p90 ou acima da
distribuição do próprio nó naquele ano é "congestionada". A leitura do
módulo (`src/vra/congestion.py`, docstring) explica por que o limiar é
relativo à escala do próprio aeroporto e fixo no ano — as mesmas
propriedades, noutra forma, que a ideia de capacidade de pátio também
tentava capturar (uso relativo à capacidade instalada).

## Exercício

Leia a docstring de `src/vra/congestion.py` e a linha "BNDES/McKinsey
(2010)" de [`docs/data-availability.md`](../data-availability.md). A
proposta original de capacidade de pátio precisava de dados de
posições de estacionamento por aeroporto (não públicos, tanto quanto se
sabe); o proxy p90 deste repositório precisa só do próprio VRA. Escreva em
duas frases: qual das duas definições um pesquisador sem acesso a dados de
infraestrutura aeroportuária conseguiria calcular para os 27 nós do
painel hoje, e por quê.

## Nota honesta

A capacidade de pátio nunca foi reconstruída nem no acervo original nem
aqui — não há dado público conhecido de posições de estacionamento por
aeroporto para o período 2000–2013. `prcongested` (a variável do artigo,
baseada em capacidade de pista declarada) segue **não reproduzida** neste
repositório por falta da mesma coisa que faltou à variável de pátio:
uma tabela de capacidade completa, não apenas um estudo com um exemplo.
