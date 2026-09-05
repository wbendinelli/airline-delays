# docs/tutorial/

Tutorial em português (exceção deliberada ao inglês do repositório —
`CLAUDE.md`, `DECISIONS.md` ADR-0006): como replicar, ler criticamente e
estender o artigo que este repositório reconstrói, módulo por módulo.

Comece por [`00-como-usar.md`](00-como-usar.md) — o mapa do arco completo,
as convenções (o que é caminho real entre crases, o que é referência a um
documento fora deste repositório) e o índice dos treze módulos seguintes
(`01-a-proposta.md` até `13-propor-melhorias.md`).

Todo caminho e todo comando `just`/`vra` mencionado nestes arquivos e em
`README.md` é verificado por `uv run python scripts/check_docs_paths.py`
(também rodado em CI, `.github/workflows/ci.yml`).
