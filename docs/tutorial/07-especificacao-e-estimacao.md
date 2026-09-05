# M7 — Especificação e estimação: 2SGMM, HAC, e uma estatística escrita do zero

**Objetivo.** Entender a especificação econométrica do artigo — 2SGMM com
HAC, dummies de rota e de tempo, dois blocos de instrumentos — e por que a
estatística que testa a força desses instrumentos (Kleibergen-Paap) não
veio de nenhum pacote pronto: teve de ser escrita e validada por uma
identidade algébrica, não por comparação com outra implementação.

## Contexto (fora deste repositório)

O código entregue do artigo original são nove do-files, todos da segunda
rodada de revisão — nenhum roda sem cerca de vinte comandos `.ado`
proprietários do laboratório (`labstart`, `projbase`, `gregrun`,
`dummymonthreg`, entre outros), nunca entregues. A numeração dos
do-files está deslocada em uma unidade em relação às tabelas publicadas
(`_tab2.do` produz a Tabela 3), e um deles, `_tab7.do`, roda seis colunas
inteiras que não correspondem a nenhuma tabela publicada — vira uma única
frase no texto final. A fórmula exata da largura de banda do kernel HAC
também não sobreviveu à extração de texto (é um objeto de equação
incorporado, não texto): os do-files usam `bw(5)`, consistente com
`T^(1/3) = 144^(1/3) ≈ 5,24`, mas a fórmula em si teve de ser **inferida**,
não lida (*avaliação em oito critérios*, seção C3 e "Não verificados",
item 8 — análise externa, arquivos privados, não incluídos aqui, M12).

## Arquivos deste repositório

- [`docs/notes/replication.md`](../notes/replication.md) — como cada
  tabela é montada aqui, o que bate e o que não bate, com evidência.
- `src/airline_delays/estimation/sample.py` e
  `src/airline_delays/estimation/loader.py` — o filtro de amostra dos
  do-files (`build_sample()`) e as dummies reconstruídas (`add_dummies()`).
  A fonte é única: o painel de estimação do artigo, publicado em
  `data/analysis/article_panel_route_month.parquet` (ADR-0020); a opção
  `--panel` de `airline-delays estimate` aceita outro painel que traga o
  mesmo contrato de colunas.
- `src/airline_delays/estimation/kp.py` — a estatística `rk` de Kleibergen e Paap (2006),
  escrita porque nenhum pacote Python a implementa (`linearmodels`,
  `pyfixest` e `ivmodels` foram inspecionados diretamente, não só a
  documentação).
- `tests/test_estimation_kp.py` — a validação: sob erros i.i.d., a versão
  Wald tem de colapsar exatamente na estatística de Cragg-Donald e a
  versão LM na de Anderson.

## Comandos

```bash
uv run pytest tests/test_estimation_kp.py -v
```

Este teste não precisa de dado nenhum — é puramente algébrico, sobre dados
sintéticos, e é o mesmo que a suíte completa (`uv run pytest -q`) já executa
em CI.

**Número esperado.** Todos os testes passam, incluindo
`test_bartlett_weights_match_the_linearmodels_convention`, que fixa a
convenção de peso do kernel: `bartlett_weights(4)` dá exatamente
`[0.8, 0.6, 0.4, 0.2]` — a prova de que "bandwidth 4" aqui é "bw(5)" no
Stata (`src/airline_delays/estimation/kp.py`, `docs/notes/replication.md`, seção 3).

## Exercício

Abra `src/airline_delays/estimation/kp.py` e localize `rk_statistics`. Sem ler o teste,
tente responder: por que a validação não pode ser "rodar outro pacote e
comparar"? (Dica: a resposta está na primeira frase do docstring do
arquivo.) Depois confira sua resposta em
`tests/test_estimation_kp.py`, no comentário acima de
`test_wald_collapses_to_cragg_donald_under_iid_errors`.

## Limites e próximos passos

Contra os valores publicados (`reports/replication/tables.md`, linha "KP
statistic (rk LM)"), a implementação acerta melhor nas colunas ODDS (entre
+3,3% e +6,4% acima do publicado) do que nas colunas MINS (+18,7% a
+31,0%) — porque MINS tem só 3 instrumentos para 2 endógenas, quase
identificação exata, onde a estatística é muito sensível ao tamanho da
amostra. As duas identidades algébricas fecham à precisão de máquina,
independente do formato do problema; a distância acompanha a amostra, e
os dois N — publicado e reestimado — ficam registrados lado a lado em cada
coluna (`reports/replication/summary.json`, `n_obs`; M8, "Nota sobre a
amostra"). O próximo passo é um painel sintético com estatísticas de
Kleibergen-Paap em forma fechada, que tornaria a checagem contra a Tabela 3
independente do artigo (`ROADMAP.md`).
