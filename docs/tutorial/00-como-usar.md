# M0 — Como usar este material

Português (exceção deliberada ao inglês do repositório — `CLAUDE.md`,
`DECISIONS.md` ADR-0006). Este tutorial existe para uma pessoa aprender, lendo
e rodando, como replicar um artigo científico publicado a partir de dado
público, e como estendê-lo depois. Não é uma introdução a econometria nem a
DuckDB — é um roteiro por **este repositório específico**, módulo por módulo,
cada um preso a arquivos que existem e a números que um script imprime.

## O arco, em uma frase por módulo

| Módulo | Do que trata |
|---|---|
| [`01-a-proposta.md`](01-a-proposta.md) | A proposta de mestrado (set/2013): a pergunta era sobre preços, não atrasos |
| [`02-a-leitura-do-orientador.md`](02-a-leitura-do-orientador.md) | O exercício bibliográfico que o orientador impôs (jun–ago/2014) e a virada de pergunta |
| [`03-primeiro-desenho.md`](03-primeiro-desenho.md) | O primeiro desenho (jul/2014): nível aeroporto, capacidade de pátio construída e abandonada |
| [`04-segundo-desenho.md`](04-segundo-desenho.md) | O segundo desenho (mar/2015): OLS com efeitos fixos, 38 aeroportos, instrumentação adiada |
| [`05-caminho-nao-tomado.md`](05-caminho-nao-tomado.md) | O projeto irmão sobre preços (jun/2015): descrito, não incluído neste repositório |
| [`06-dados-fonte-ao-painel.md`](06-dados-fonte-ao-painel.md) | Do VRA bruto ao painel público, com a reconciliação contra o gabarito |
| [`07-especificacao-e-estimacao.md`](07-especificacao-e-estimacao.md) | Especificação e estimação: 2SGMM, HAC, Kleibergen–Paap escrito do zero |
| [`08-o-que-reproduz.md`](08-o-que-reproduz.md) | O que reproduz e o que não, número a número, com a causa até onde a evidência vai |
| [`09-da-dissertacao-ao-artigo.md`](09-da-dissertacao-ao-artigo.md) | Da dissertação ao artigo: datas, título, autoria, a promessa removida |
| [`10-revisao-por-pares.md`](10-revisao-por-pares.md) | A revisão por pares, o buraco: o que não sobreviveu, e o que registrar da próxima vez |
| [`11-recepcao.md`](11-recepcao.md) | Recepção: quem citou, o que deturpou, quem adotou o método |
| [`12-consentimento-licencas-publicacao.md`](12-consentimento-licencas-publicacao.md) | Consentimento, licenças e o que fica de fora de um repositório público |
| [`13-propor-melhorias.md`](13-propor-melhorias.md) | Propor melhorias: as extensões que este repositório já sustenta |

## Convenções

- **Backticks marcam arquivo real.** Todo caminho entre crases
  (`README.md`, `data/analysis/taxas.csv`) existe neste repositório neste
  momento — `scripts/check_docs_paths.py` prova isso, rodando em CI a cada
  mudança. *Itálico* marca um documento **fora** deste repositório (a
  dissertação, os slides, as análises do acervo de pesquisa que
  antecederam este repositório) — descrito, não incluído; ver M12 para o
  porquê.
- **Todo número cita o arquivo que o imprime.** Nunca um número solto. Onde
  o número vem de uma análise externa ao repositório (a maior parte do
  arco histórico, M1–M5, M9–M11), o texto diz isso explicitamente — não é
  um script que se possa rodar aqui, é um achado documentado alhures.
  Onde o número vem de dentro do repositório (M6–M8, M12, M13), o comando
  que o produz está no módulo.
- **A honestidade é a pedagogia.** Cada módulo termina numa nota do que não
  fecha, não foi tentado, ou permanece em aberto. Isso não é uma falha de
  redação — é o ponto central de `CLAUDE.md`: *"Fixing" a divergence
  against the benchmark by adjusting a definition until the numbers
  match* é a única coisa proibida; declarar a divergência é o trabalho.
- **Nenhum fato sobre a pesquisa original é inventado.** Tudo que este
  tutorial afirma sobre a proposta de 2013, os seminários, a dissertação,
  a revisão por pares ou a recepção do artigo vem de uma análise já
  produzida sobre o acervo original — as citações literais entre aspas
  são exatamente o texto lido, não paráfrase.

## O que este repositório é e não é

É a reconstrução de uma base pública (VRA/ANAC), a replicação de um artigo
publicado a partir dela, e a previsão de atraso por voo — ver a visão
geral do [`README.md`](../../README.md). Não é a dissertação nem o artigo
em si (esses são citados por DOI, nunca redistribuídos —
[`docs/data-availability.md`](../data-availability.md)), e não é uma
cópia do acervo de pesquisa que motivou o projeto: os módulos M1–M5 e
M9–M11 descrevem esse acervo em prosa, com trechos literais, porque o
acervo em si é privado e não público (ver M12).

## Antes de começar

```bash
uv sync
uv run pytest -q
```

Se os testes passam, o ambiente está pronto para qualquer módulo a partir
do M6. Módulos M1–M5 e M9–M11 não pedem nenhum comando de reconstrução —
são leitura. Cada módulo lista os comandos que precisa, na ordem em que
precisa.
