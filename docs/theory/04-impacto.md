# O impacto — o que o campo levou, e o que continua em aberto

Português (exceção deliberada ao inglês do repositório — `CLAUDE.md`,
`DECISIONS.md` ADR-0006). Este é o quarto e último capítulo da discussão
temática de `docs/theory/`: depois da economia do congestionamento (01), do
jogo derivado (02) e da ponte para a econometria de 2016 (03), o que
aconteceu ao artigo depois de publicado. O capítulo é curto de propósito:
a recepção já foi medida por um projeto irmão e narrada no tutorial (M11,
[`../tutorial/11-recepcao.md`](../tutorial/11-recepcao.md)); aqui só se
diz o que ela significa para a teoria dos capítulos anteriores. Todos os
números desta página são externos — vêm do repositório de auditoria de
citações, não de um script deste repositório — e são marcados como tal.

## 1. A recepção, medida

O artigo de 2016 acumulou 93 trabalhos citantes, mapeados alegação por
alegação pelo projeto
[`github.com/wbendinelli/citation-audit`](https://github.com/wbendinelli/citation-audit)
(números externos, os mesmos que M11 cita). Três achados concentram a
atenção: a internalização do congestionamento (identificador `AIR-F01`)
recebe 18 citações; o arcabouço que testa congestionamento e estrutura de
mercado numa única equação (`AIR-M01`), 8; os *spillovers* não-preço da
entrada de LCC (`AIR-F05`), que dão título ao artigo, 4. Três trabalhos
adotaram o método; 13% das citações deturpam o que o artigo mostra.

Lida com os capítulos anteriores, a distribuição diz algo sobre a teoria:
o que o campo levou do artigo foi, antes de tudo, o canal de
internalização — a Proposição 1 do capítulo 02 tornada regressor, o
`maxcthhi` do capítulo 03 — e a separação entre concentração da rota e
concentração do aeroporto. O achado que a monografia de 2013 antecipava
como "Pressuposição 3", a LCC que muda o jogo, é o menos citado dos três.

## 2. O artigo que levou a formulação aos preços

Entre os 93 citantes está Guo, Jiang e Wan (2018, *Transportation
Research Part A* 118, 648–661, DOI `10.1016/j.tra.2018.10.012`), o artigo
que o capítulo 02 apresenta como a formulação levada às tarifas. A
auditoria de citações o classifica como citação *foundational* e fiel
(`accurate`, sem distorção), apoiada nas alegações `AIR-F01`, `AIR-F02`,
`AIR-M01` e `AIR-M02` — o registro está no arquivo de classificação do
repositório irmão (classify.json), adjudicado em 2026-09-04 (rótulos
externos).
Ele é, dos citantes, o que mais diretamente continua a linha teórica: toma
a separação de 2016 entre concentração de mercado e de aeroporto, critica
o controle por tráfego do aeroporto (que remove o canal de internalização
via preço), e testa a internalização onde a monografia de 2013 não tinha
dado — nas tarifas. O seu resultado, que as empresas de serviço completo
internalizam e as de baixo custo não, é o que obriga a reler a
Pressuposição 3 por margem, como o capítulo 02 faz.

Há um fecho que o tutorial já registra por outro caminho: a pergunta
original do mestrado (M1) era "os atrasos aparecem nos preços quando as
empresas têm poder de mercado?", e foi deixada de lado (M5). O artigo de
2018 é essa pergunta respondida por outros autores, sobre o artigo que a
substituiu.

## 3. O que continua em aberto

- **As três margens de internalização** — reprogramar horários (Ater
  2012), reduzir tráfego via preço (Guo, Jiang e Wan 2018) e escolher o
  aeroporto (Gudmundsson, Paleari e Redondi 2014; a Azul em Viracopos na
  monografia) — são uma síntese deste repositório (capítulo 02, seção 9),
  não um resultado publicado. Testá-las exigiria, no mínimo, um painel com
  tarifas, o que este repositório não tem
  (`docs/data-availability.md`, fonte 4).
- **A decomposição de curto e longo prazo** da entrada de LCC, prometida
  no artigo e nunca publicada (M9), continua sendo a extensão 1 de
  [`../tutorial/13-propor-melhorias.md`](../tutorial/13-propor-melhorias.md).
- **O HHI ponderado por passageiros** (`rthhi`, `maxcthhi`), nulo no
  painel público, é a extensão 2 do mesmo módulo; sem ele, a ponte do
  capítulo 03 compara a construção da monografia (voos planejados) com a
  do artigo (passageiros) sem poder igualá-las.
- **A pergunta da monografia** — a dummy da Azul no seu próprio aeroporto,
  o CR2, os assentos, o clima — é a extensão 9 do mesmo módulo, aberta
  neste trabalho.

## 4. Limites declarados

Este capítulo descreve a recepção do artigo de 2016, não a deste
repositório, que é novo e não tem citações. Os números vêm de um projeto
irmão e de uma classificação feita por leitura de passagens; a taxonomia e
os critérios são dele (`citation-audit`, arquivo `METHOD.md` daquele
repositório), não deste. Nada aqui é reproduzível por um comando deste
repositório — M11 diz o mesmo, e é por isso que a nota honesta de M11
vale também para esta página.

## 5. Como conferir

Não há comando a rodar aqui. Os números da seção 1 conferem-se contra o
repositório de auditoria de citações linkado acima; os do capítulo 02
contra `reports/theory/model.json` (`just theory`); os do capítulo 03
contra `replication/published.json` e `reports/replication/private/summary.json`.

Referências completas em [bibliografia.md](bibliografia.md).
