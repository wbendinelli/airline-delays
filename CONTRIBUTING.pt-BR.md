# Contribuindo

Português (ADR-0006) -- a versão em inglês desta página é
[CONTRIBUTING.md](CONTRIBUTING.md).

`airline-delays` publica o painel de estimação de Bendinelli, Bettini &
Oliveira (2016, *Transportation Research Part A* 85, 39-52, doi
10.1016/j.tra.2016.01.001), reestima suas tabelas, reconstrói os registros de
voo da ANAC num painel aberto, deriva a teoria do artigo e treina um preditor
de atraso. Correções, extensões e reestimações independentes são bem-vindas.
Esta página é o guia prático; a CI checa a maior parte dele em cada pull
request.

## Sua primeira contribuição

1. **Faça um fork** do repositório e clone o seu fork.
2. **Prepare o ambiente.** Python 3.12, gerenciado pelo `uv`:

   ```bash
   uv sync
   uv run pre-commit install
   ```

3. **Rode as duas reproduções.** `just demo` roda o pipeline de ponta a ponta
   sobre a amostra de teste versionada de 19.910 etapas de voo (etapas
   *staged*, tabela-fato, painel reconstruído, Tabela 2) em cerca de um
   segundo, sem rede, escrevendo só sob `data/derived/demo/`, fora do git.
   `just estimate` reestima as Tabelas 2-7 sobre o painel do artigo
   versionado, `data/analysis/article_panel_route_month.parquet`, em menos de
   um minuto, e escreve `reports/replication/`.
4. **Crie um branch, altere, abra um pull request.** `just check` roda o
   pre-commit sobre a árvore e a checagem de caminhos da documentação antes do
   push.

## O que a CI executa

| Job | O que garante |
|---|---|
| `lint` | `ruff check` e `ruff format --check` sobre toda a árvore |
| `test` | `pytest` contra a amostra de teste e as tabelas versionadas; sem rede, sem `data/raw/` |
| `citation` | `CITATION.cff` é válido segundo o esquema |
| `docs-paths` | todo caminho entre crases e todo comando `just` ou `airline-delays` nos READMEs, em `docs/` e nos guias de dados resolve para algo real (`scripts/check_docs_paths.py`) |
| `metadata` | `docs/dictionary.md`, `datapackage.json`, `.zenodo.json` e `reports/summary.json` são reconstruções do registro e das tabelas, e o Data Package valida |
| `docs-lint` | `README.md` segue o perfil de documentação declarado em `.sapians-repo.yml` |
| `security` | `gitleaks` varre todo o histórico em busca de segredos |

Um job vermelho é corrigido na causa, nunca enfraquecendo a checagem.

## As regras fixas

1. **Nenhuma coluna sem entrada em `src/airline_delays/schema/columns.py`.**
   O dicionário, `datapackage.json` e os testes de esquema são gerados do
   registro; `just panel` regenera os dois primeiros.
2. **Nenhum número nas páginas de entrada que não seja um valor de
   `reports/summary.json`** (`airline-delays summary`) ou esteja marcado como
   transcrição de um documento externo. `scripts/check_prose_numbers.py` faz
   valer a regra; um número sem script por trás é removido, não defendido.
3. **Nunca versione nada sob `data/raw/`, `data/staged/` ou `data/derived/`**
   além do seu `README.md` e de `data/raw/manifest.json`. Eles são regenerados
   a partir dos arquivos da ANAC. Os dados versionados vivem em
   `data/analysis/` e `data/external/`, e `just check-analysis` falha quando
   uma tabela versionada se afasta do que o código produziria.
4. **Uma medição que contradiz a prosa muda a prosa.** A correção é um commit
   `fix`, nunca `docs`, mesmo quando o diff é só texto.
5. **O universo, o limiar de outliers, a taxonomia de causas de atraso e os
   conjuntos de companhias são decisões**, registradas em `DECISIONS.md`.
   Mudar uma delas é uma nova ADR, não a edição de uma constante.

## Mudanças na documentação

`README.md` e `README.pt-BR.md` compartilham um único esqueleto
(`docs/editorial/readme-outline.md`) e mudam juntos;
`scripts/check_readme_parity.py` falha quando citam números, caminhos ou
receitas diferentes. A prosa segue `docs/editorial/style-guide.md`. Antes de
abrir um pull request que toque a prosa, rode as três checagens:

```bash
uv run python scripts/check_docs_paths.py
uv run python scripts/check_prose_numbers.py
uv run python scripts/check_readme_parity.py
```

Os relatórios Typst, o tutorial, as notas e os capítulos de teoria são
escritos em português por decisão (`DECISIONS.md`, ADR-0006); tudo o mais é em
inglês.

## Estilo

As mensagens de commit seguem `type(scope): summary`, com o escopo sendo o nome
de um estágio: `ingest`, `staging`, `reference`, `fact`, `panel`, `estimation`,
`prediction`, `theory`, `reporting`, `schema`, `docs` ou `ci`. Uma linha por
mudança notável no código ou nos dados curados entra em `CHANGELOG.md`.
