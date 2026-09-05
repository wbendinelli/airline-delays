# M8 — O que reproduz e o que não, número a número

**Objetivo.** Ler a lista honesta: quais tabelas do artigo reproduzem
contra o gabarito privado, quais não, e por quê — sem arredondar nenhuma
divergência para dentro de uma definição.

## Contexto (fora deste repositório): o achado que provou a *vintage* errada

A análise que precedeu este repositório já tinha encontrado a pista mais
forte de que o `proj18.dta` entregue era outra *vintage* dos dados, não
só uma amostra diferente: o artigo e a dissertação imprimem o máximo de
"prop flights with incidents" como **0,30** — mas recomputando a mesma
variável sobre a base entregue, depois do mesmo corte de *singletons* dos
do-files, o máximo é **0,2667**. Um máximo só pode cair quando se
descartam linhas; como a amostra publicada (19.590) é **menor** que a
amostra recomputada (20.630), o seu máximo teria de ser ainda menor, não
maior. A conclusão, na época, foi que a base entregue não é um
subconjunto da amostra publicada — é outra vintage (*avaliação em oito
critérios*, seção C4; análise externa, arquivo privado, não incluído
aqui). Esta mesma assinatura — N maior na base entregue do que no
publicado — é o que este repositório mede de novo, de forma independente,
cinco anos e um pipeline inteiro depois.

## Arquivos deste repositório

- [`reports/replication/private/tables.md`](../../reports/replication/private/tables.md)
  — publicado contra replicado, tabela por tabela, gerado por
  `uv run python -m replication.run`.
- [`docs/declared-differences.md`](../declared-differences.md) — a causa
  de cada divergência, até onde a evidência vai.
- `data/analysis/taxas.csv` — a mesma pergunta, na camada de painel em vez
  de na de regressão.

## Comandos

```bash
grep -A10 "^## Scorecard" reports/replication/private/tables.md
```

Este arquivo já está commitado — o comando acima só lê o que
`uv run python -m replication.run --source private` já escreveu; rodar de
novo precisa de `AIRLINE_DELAYS_PRIVATE_DIR`.

**Número esperado.** Cinco linhas, uma por tabela de regressão. Somando a
coluna "coefficients" das cinco: 60+66+60+60+60 = **306**. Somando "signs
equal" (o numerador de cada fração): 60+65+59+59+59 = **302**. Somando
"within 0.5 s.e.": 53+51+53+51+51 = **259** — 85% de 306. O maior
`diff/s.e.` isolado de qualquer tabela é 0,941 (Tabela 6), abaixo de 1
erro-padrão publicado em toda a base comparada.

## Exercício

Confirme as três somas acima você mesmo, direto do arquivo
[`reports/replication/private/summary.json`](../../reports/replication/private/summary.json)
(os campos `n_coefficients`, `sign_agreement` e `within_half_se` de cada
uma das cinco tabelas). Elas batem com o que
`docs/declared-differences.md` afirma no primeiro parágrafo da seção
"Replication (Tables 2-7)"? Se você encontrar uma tabela cujo `sign_agreement`
não é 59 nem 60, qual é, e qual coeficiente inverteu o sinal?

## Nota honesta

O que não fecha, e por quê até onde a evidência permite dizer
(`docs/declared-differences.md`, tabela completa): **N é cerca de 5,3%
maior em toda coluna** replicada contra publicada, sem que nenhum filtro
visível nos do-files produza os números publicados — exatamente a mesma
assinatura que a análise externa já tinha encontrado no `princident` antes
deste repositório existir. O J de Hansen se move nos dois sentidos junto
com essa amostra maior, mas **não muda nenhum veredito** a 5%: as mesmas
22 colunas continuam sem rejeitar ortogonalidade e as mesmas 2 continuam
rejeitando. Nenhuma tentativa foi feita de cortar a amostra até bater —
isso seria exatamente o ajuste que `CLAUDE.md` proíbe.
