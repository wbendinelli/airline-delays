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
| [`06-dados-fonte-ao-painel.md`](06-dados-fonte-ao-painel.md) | Dados: do CSV bruto da ANAC ao painel reconstruído — *staged*, tabela-fato, painel — com os números medidos |
| [`07-especificacao-e-estimacao.md`](07-especificacao-e-estimacao.md) | Especificação e estimação: 2SGMM, HAC, Kleibergen–Paap escrito do zero |
| [`08-o-que-reproduz.md`](08-o-que-reproduz.md) | A replicação: as Tabelas 2–7 reestimadas sobre o painel de estimação do artigo, publicado aqui, e o placar contra as tabelas publicadas |
| [`09-da-dissertacao-ao-artigo.md`](09-da-dissertacao-ao-artigo.md) | Da dissertação ao artigo: datas, título, autoria, a promessa removida |
| [`10-revisao-por-pares.md`](10-revisao-por-pares.md) | A revisão por pares, o buraco: o que não sobreviveu, e o que registrar da próxima vez |
| [`11-recepcao.md`](11-recepcao.md) | Recepção: quem citou, o que deturpou, quem adotou o método |
| [`12-consentimento-licencas-publicacao.md`](12-consentimento-licencas-publicacao.md) | Direitos, licenças e o que se publica onde: MIT, CC BY 4.0, a atribuição à ANAC, o painel do artigo, o depósito no Zenodo |
| [`13-propor-melhorias.md`](13-propor-melhorias.md) | Propor melhorias: as extensões que este repositório já sustenta |
| [`14-a-teoria-por-tras-do-artigo.md`](14-a-teoria-por-tras-do-artigo.md) | A teoria por trás do artigo: a porta para `docs/theory/` — a economia do congestionamento, o jogo derivado e verificado, a ponte para o artigo de 2016 e o seu impacto |

A discussão temática da teoria — da economia do congestionamento ao
artigo de 2016 e às suas citações — vive em
[`../theory/README.md`](../theory/README.md); M14 é a porta. Ela não é
cronológica e não renumera nada: os módulos M1–M13 continuam sendo o arco
documental, na ordem em que os documentos existiram.

## Convenções

- **Backticks marcam arquivo real.** Todo caminho entre crases
  (`README.md`, `data/analysis/manifest.json`) existe neste repositório neste
  momento — `scripts/check_docs_paths.py` prova isso, rodando em CI a cada
  mudança. *Itálico* marca um documento **fora** deste repositório (a
  monografia de 2013, a dissertação, os slides, as análises do acervo de pesquisa que
  antecederam este repositório) — descrito, não incluído; ver M12 para o
  porquê.
- **Todo número cita o arquivo que o imprime.** Nunca um número solto. Onde
  o número vem de uma análise externa ao repositório (a maior parte do
  arco histórico, M1–M5, M9–M11), o texto diz isso explicitamente — não é
  um script que se possa rodar aqui, é um achado documentado alhures.
  Onde o número vem de dentro do repositório (M6–M8, M12–M14), o comando
  que o produz está no módulo.
- **Fórmulas.** Equações em `$…$` seguem a numeração da monografia de
  2013, (1)–(12); toda desigualdade ou constante afirmada em prosa é
  verificada por `src/airline_delays/theory/model.py` e impressa em
  `reports/theory/model.json` — "nenhum número solto", aplicado à
  álgebra.
- **Limites e próximos passos.** Cada módulo termina numa seção com esse
  nome, que diz o que o módulo cobre e qual é o próximo passo — a fonte
  ainda não coletada, a função ainda não escrita, o depósito ainda não
  feito. Limite é escopo, não confissão.
- **Nenhum fato sobre a pesquisa original é inventado.** Tudo que este
  tutorial afirma sobre a proposta de 2013, os seminários, a dissertação,
  a revisão por pares ou a recepção do artigo vem de uma análise já
  produzida sobre o acervo original — as citações literais entre aspas
  são exatamente o texto lido, não paráfrase.

## O que este repositório é e não é

É a reconstrução de uma base pública (VRA/ANAC), a replicação de um artigo
publicado a partir dela, e a previsão de atraso por voo — ver a visão
geral do [`README.md`](../../README.md). Não é a monografia de 2013, a dissertação nem o artigo
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
são leitura. M14 pede só `just theory` e
`uv run pytest tests/test_theory.py -q`, sem dado nenhum. Cada módulo lista os comandos que precisa, na ordem em que
precisa.
