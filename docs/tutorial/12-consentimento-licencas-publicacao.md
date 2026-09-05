# M12 — Consentimento, licenças e o que fica de fora

**Objetivo.** Ver o mapa completo de quem precisaria autorizar o quê para
publicar o acervo de pesquisa original — e comparar com a solução deste
repositório, que evita a maior parte dessas autorizações escolhendo, desde
o início, uma trilha (VRA público + artigo citado só por DOI) que não
depende de ninguém conceder nada.

## Contexto (fora deste repositório): um mapa completo, zero autorizações

O acervo original tem um mapa de consentimento completo — sai inteiro dos
próprios metadados, notas de tabela e cabeçalhos de do-file — e o número
de autorizações **de fato obtidas** é zero. Três titulares seriam
bloqueantes: o orientador e coautor (dono dos comandos `.ado` de
estimação e da base de laboratório), o co-autor externo, e a Elsevier
(o PDF editorado nunca é redistribuível; nenhuma versão aceita do
manuscrito, que a política da própria Elsevier permitiria depositar sob
embargo, existe no acervo). A aritmética de tamanho também não ajuda: o
GitHub bloqueia arquivo acima de 100 MiB sem LFS, e três das quatro bases
brutas do acervo ultrapassam isso — a base final sozinha carrega colunas
derivadas do relatório não publicado da Infraero e de microdados
tarifários cuja redistribuição nunca foi verificada.

Esta descrição vem de uma análise de acervo produzida antes deste
repositório existir (*avaliação em oito critérios*, seções C7 e C8) — os
arquivos citados são privados e não estão aqui.

## O que este repositório resolveu, e como

Não obtendo as autorizações que faltavam — evitando precisar delas.

- **A fonte de dados é diferente.** O VRA é público
  (`DECISIONS.md` ADR-0000); nenhum dado da Infraero, do laboratório, ou
  microdados tarifários entra em qualquer tabela redistribuída aqui.
- **O artigo é citado, nunca redistribuído.** `CITATION.cff` e o README
  apontam para o DOI; nenhum PDF, editorado ou aceito, está neste
  repositório.
- **O benchmark privado nunca sai da máquina de quem o possui.** É lido
  só via `AIRLINE_DELAYS_PRIVATE_DIR`, e um gancho de pre-commit garante
  isso na prática, não só na intenção:

```bash
grep -n "no-private-data" .pre-commit-config.yaml
```

**Número esperado.** Duas ocorrências — o `id` do gancho e seu `name`
(`.pre-commit-config.yaml`). O corpo do gancho barra qualquer arquivo
staged que contenha `proj18`, `labtar`, `nectarbase`, termine em `.dta`,
ou esteja sob `data/raw/`, `data/staged/`, `data/derived/` ou
`data/private/` (exceto os `README.md` e `manifest.json` que essas pastas
têm permissão de carregar).

## Exercício

Abra [`docs/data-availability.md`](../data-availability.md) e conte
quantas das 14 linhas da tabela-resumo têm "Not redistributed" em
negrito. Compare esse número com o "zero autorizações obtidas" do acervo
original: este repositório chegou a um número pequeno de fontes não
redistribuídas (três) sem precisar pedir permissão a ninguém — porque
optou por não depender delas desde o desenho, não porque negociou
melhor. Qual das três linhas você acha que teria a maior chance de virar
redistribuível um dia, e o que precisaria acontecer para isso (a resposta
de cada uma está na própria linha)?

## Nota honesta

A comparação privada contra o gabarito (`data/analysis/taxas.csv`) só
existe porque o autor deste repositório tem acesso pessoal ao mesmo
acervo que gerou o `proj18.dta` — não porque algum titular concedeu uma
licença nova. Um terceiro sem esse acesso pode rodar todo o resto deste
repositório (`just fetch` até `just replicate`, sem `private`), mas não
pode reproduzir a comparação da seção "Panel and feature layer" do
README nem as tabelas da fonte `private` — exatamente o mesmo limite que
`docs/data-availability.md`, fonte 12, declara.
