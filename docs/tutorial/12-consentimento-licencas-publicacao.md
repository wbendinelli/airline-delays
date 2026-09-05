# M12 — Direitos, licenças e o que se publica onde

**Objetivo.** Saber, para cada camada deste repositório, quem detém os
direitos, sob qual licença ela é publicada e onde ela vai parar: o código,
o texto e as tabelas curadas, o VRA bruto, o painel de estimação do
artigo, e os documentos que são só citados.

## A licença por camada

Três licenças, uma por natureza de conteúdo, e nenhuma delas relicencia o
que é de outro titular.

| Camada | O que é | Titular | Licença |
|---|---|---|---|
| código | `src/`, `scripts/`, `tests/`, `.github/`, `justfile` | o primeiro autor do artigo | MIT (`LICENSE`) |
| texto e dados curados | `README.md`, `docs/`, a prosa de `reports/`, `data/external/*.csv`, os dois painéis e as tabelas de `data/analysis/` | o primeiro autor do artigo | CC BY 4.0 (`LICENSE-CC-BY-4.0.md`) |
| VRA bruto | os 168 CSV mensais e o que deles deriva | ANAC | CC BY, atribuído como "ANAC, Voo Regular Ativo (VRA), via dados.gov.br" (ADR-0000) |

O `datapackage.json` repete a licença em cada recurso e a fonte de cada
tabela; `CITATION.cff` e `.zenodo.json` saem da mesma origem
(`src/airline_delays/schema/metadata.py`), para que título, autores e
licenças não divirjam entre os quatro arquivos.

## O que o autor publica como autor

O painel de estimação do artigo — Bendinelli, Bettini e Oliveira (2016,
*Transportation Research Part A* 85, 39-52, doi 10.1016/j.tra.2016.01.001)
— é publicado em `data/analysis/article_panel_route_month.parquet` sob
CC BY 4.0 (ADR-0020). A citação do dataset credita os três autores dos
dados: Bendinelli, W. E.; Bettini, H. F. A. J.; Oliveira, A. V. M. (dados
de 2016; publicação 2026), curado e publicado por W. E. Bendinelli. O
`datapackage.json` lista as fontes a montante do painel — o VRA, os dados
estatísticos e tarifários da ANAC e o próprio artigo — no recurso
`article_panel_route_month`.

## O que é só citado

- **O artigo.** Citado por DOI em `CITATION.cff` (`preferred-citation`) e
  no README; nenhum PDF, editorado ou aceito, está aqui. O titular do texto
  publicado é a Elsevier (`docs/data-availability.md`).
- **A monografia de 2013.** Documento do autor (USP/ESALQ), citado com o
  marcador `[DOI-MONOGRAFIA]` até o depósito no Zenodo; dela entram aqui uma
  tabela derivada (`data/external/monograph_airports.csv`) e passagens
  curtas (`docs/notes/monografia-2013.md`), não o documento.

## O que a licença da ANAC permite

O catálogo federal de dados abertos declara "Creative Commons Attribution"
para o conjunto Voo Regular Ativo; o rodapé do sítio da ANAC declara CC
BY-ND para o conteúdo do sítio. A ADR-0000 adota a declaração mais
específica, a do catálogo: redistribuir dados derivados com atribuição.
Um pedido de confirmação escrita via e-SIC está redigido em
`docs/notes/esic-licenca-vra.md` e ainda não foi protocolado; a publicação
não espera por ele.

## O que vai para o Zenodo

O depósito arquiva o repositório com as tabelas curadas: os dois painéis,
a tabela-fato, as duas projeções, as tabelas de `data/external/` e os
manifestos — o que `datapackage.json` descreve como recurso. As camadas
pesadas — os CSV brutos, o *staged* e a tabela de modelagem por voo — não
vão: são regeneradas pelos comandos de M6 e de `docs/notes/prediction.md`,
com o sha256 de cada arquivo bruto em `data/raw/manifest.json`
(`.zenodo.json`, campo `notes`).

## Exercício

Abra a tabela-resumo de [`docs/data-availability.md`](../data-availability.md)
e, para cada fonte, escreva em uma linha quem detém os direitos e qual
licença permite redistribuir o que este repositório redistribui dela —
ou por que nada é redistribuído. Depois responda: quais fontes são
redistribuídas sob CC BY com atribuição a um terceiro, quais sob a CC BY
4.0 do próprio repositório, e quais são apenas citadas? Confira contra a
seção de licenças do mesmo arquivo.

## Limites e próximos passos

O depósito no Zenodo é o próximo marco: ele cunha o DOI do repositório,
que entra em `CITATION.cff`, no README e no `id` de `datapackage.json`
(`ROADMAP.md`, "Next milestone: publication"). O da monografia substitui `[DOI-MONOGRAFIA]` nos
capítulos de `docs/theory/` e entra em `CITATION.cff` como referência. A
resposta do e-SIC, quando chegar, é registrada em
`docs/notes/esic-licenca-vra.md`; a leitura CC BY da ADR-0000 já sustenta
a redistribuição feita aqui.
