# docs/tutorial/

Fifteen modules in Portuguese (`DECISIONS.md`, ADR-0006), M0 to M14: the
research arc of Bendinelli, Bettini & Oliveira (2016, *Transportation Research
Part A* 85, 39-52, doi 10.1016/j.tra.2016.01.001) as its first author lived it
-- the 2013 proposal, the two research designs, the data, the specification and
estimation, what reproduces, the road from dissertation to article, peer review,
reception, licences and the extensions this repository already supports. M0 is
the map and the conventions; M14 opens the theory chapters of `docs/theory/`.
Every path and every `just` or `airline-delays` command quoted in the modules is
checked by `scripts/check_docs_paths.py`.

Tutorial em português (exceção deliberada ao inglês do repositório --
`CLAUDE.md`, `DECISIONS.md` ADR-0006): como replicar, ler criticamente e
estender o artigo que este repositório reconstrói, módulo por módulo.

Comece por [`00-como-usar.md`](00-como-usar.md) -- o mapa do arco completo,
as convenções (o que é caminho real entre crases, o que é referência a um
documento fora deste repositório) e o índice dos catorze módulos seguintes
(`01-a-proposta.md` até `14-a-teoria-por-tras-do-artigo.md`).

Todo caminho e todo comando `just`/`airline-delays` mencionado nestes arquivos
e em `README.md` é verificado por `uv run python scripts/check_docs_paths.py`
(também rodado em CI, `.github/workflows/ci.yml`).
