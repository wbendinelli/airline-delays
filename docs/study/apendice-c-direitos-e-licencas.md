# Apêndice C — Direitos, licenças e o que se publica onde

Português (ADR-0006).

Este apêndice diz, para cada camada do repositório, quem detém os direitos,
sob qual licença ela é publicada e onde ela vai parar: o código, o texto e as
tabelas curadas, os registros brutos da ANAC, o painel de estimação de
Bendinelli, Bettini & Oliveira (2016, *Transportation Research Part A* 85,
39-52, doi 10.1016/j.tra.2016.01.001) e os documentos que são apenas citados.
A declaração completa, fonte a fonte, é `docs/data-availability.md`; o guia
dos dados é `data/README.md`; as decisões são as ADR-0000 e ADR-0020 de
`DECISIONS.md`.

## A licença por camada

Três licenças, uma por natureza de conteúdo, e nenhuma delas relicencia o que
é de outro titular.

| Camada | O que é | Titular | Licença |
|---|---|---|---|
| código | `src/`, `scripts/`, `tests/`, `sql/`, `.github/`, `justfile` | o primeiro autor do artigo | MIT (`LICENSE`) |
| texto e dados curados | `README.md`, `docs/`, a prosa de `reports/`, `data/external/*.csv`, os dois painéis, a tabela-fato, as projeções de cidade e os manifestos de `data/analysis/` | o primeiro autor do artigo | CC BY 4.0 (`LICENSE-CC-BY-4.0.md`) |
| registros brutos do VRA | os 168 CSV mensais (`reconstruction.raw.files`) e tudo o que deles deriva | ANAC | CC BY, atribuído como "ANAC, Voo Regular Ativo (VRA), via dados.gov.br" (ADR-0000) |

`datapackage.json` repete a licença e as fontes em cada recurso;
`CITATION.cff` e `.zenodo.json` saem da mesma origem,
`src/airline_delays/schema/metadata.py`, para que título, autores e licenças
não divirjam entre os quatro arquivos (`tests/test_metadata_consistency.py`).

## O que o primeiro autor publica

O painel de estimação do artigo — o painel sobre o qual os autores estimaram
as Tabelas 2–7 — é publicado em `data/analysis/article_panel_route_month.parquet`
e `.csv.gz` sob CC BY 4.0 (ADR-0020): 24.589 rota-meses × 52 colunas
(`article_panel.rows`, `article_panel.columns`), curado uma vez a partir da
base final dos autores por `airline-delays article-panel`. Nos termos da
ADR-0020, o primeiro autor detém a base final, curou-a e publica o painel sob
a sua própria responsabilidade; os três autores do artigo são creditados em
toda citação do painel como autores da pesquisa subjacente. A citação do
dataset é:

> Bendinelli, W. E.; Bettini, H. F. A. J.; Oliveira, A. V. M. (dados de 2016;
> publicação de 2026). *Estimation panel of "Airline delays, congestion
> internalization and non-price spillover effects of low cost carrier entry"*,
> rota × mês, 2002–2013. Curado e publicado por W. E. Bendinelli. CC BY 4.0.
> DOI a seguir o depósito no Zenodo.

O que entra: as chaves e a geografia, as contagens de voos sobre as quais
toda participação é construída, os seis regressandos, os nove regressores
exógenos, os dois termos de concentração com o termo alternativo de cidade,
os sete instrumentos e os componentes das duas binárias de baixo custo — 52
colunas, todas declaradas na camada `article_panel` de
`src/airline_delays/schema/columns.py`. O que não entra: as dummies de rota,
tempo e sazonalidade, que `src/airline_delays/estimation/loader.py`
reconstrói exatamente; toda variável de fonte não aberta — as colunas de
clima cedidas pelo DECEA/ICEA, o relatório de conexões da Infraero, os preços
e receitas dos microdados tarifários; e a contabilidade interna da base.
`data/analysis/article_panel_manifest.json` registra o sha256 e o carimbo de
cabeçalho da base de origem, o sha256 dos dois arquivos publicados e a
contagem de nulos por coluna — nunca um caminho. Os dados da ANAC a montante
do painel — o VRA, os dados estatísticos e os microdados tarifários — são
atribuídos à ANAC, não relicenciados.

## O que é só citado

- **O artigo.** Citado por DOI em `CITATION.cff` (`preferred-citation`) e no
  `README.md`; nenhum PDF, editorado ou aceito, está aqui, e o titular do texto
  publicado é a Elsevier. As células publicadas com que a replicação se
  compara são parseadas do texto do artigo em
  `src/airline_delays/estimation/published.json` e marcadas "(artigo, Tabela N)".
- **A monografia de graduação do autor (USP, 2013).** Documento externo,
  citado com o marcador `[DOI-MONOGRAFIA]` até que o depósito no Zenodo cunhe
  o seu DOI. Dela entram aqui uma tabela derivada —
  `data/external/monograph_airports.csv`, os 38 aeroportos da sua Lista de
  Siglas (`external.monograph_airports`) — e passagens curtas, em
  `docs/notes/monografia-2013.md` e nos capítulos deste estudo, marcadas
  "(monografia — documento externo)". A base de regressão das suas Tabelas 5
  e 6 não é redistribuída e não é lida por nada aqui (ADR-0019).

## O que a licença da ANAC permite

O catálogo federal de dados abertos declara "Creative Commons Attribution"
para o conjunto Voo Regular Ativo; o rodapé do sítio da ANAC declara CC BY-ND
para o conteúdo do sítio, e nenhuma página da ANAC declara licença para o
conjunto em si. A ADR-0000 adota a declaração mais específica e mais recente,
a do catálogo: redistribuir dados derivados com atribuição, sempre como
"ANAC, Voo Regular Ativo (VRA), via dados.gov.br". Um pedido de confirmação
escrita pelo e-SIC está redigido em `docs/notes/esic-licenca-vra.md` e ainda
não foi protocolado; a publicação não espera por ele. Os arquivos brutos em si
não são redistribuídos: quem clona refaz o download da ANAC com `just fetch`,
e o sha256 de cada arquivo em `data/raw/manifest.json` prova que são os
mesmos.

## As outras fontes

| Fonte | Titular | O que este repositório redistribui |
|---|---|---|
| IAC 1504, a taxonomia de códigos de justificativa | ANAC | as tabelas derivadas `data/external/cause_codes.csv`, `di_codes.csv` e `line_types.csv`, não o texto do instrumento |
| dados estatísticos e microdados tarifários | ANAC | nada da fonte; os termos derivados viajam dentro do painel de estimação do artigo, atribuídos à ANAC |
| geografia dos aeroportos | OurAirports (domínio público, CC0) | `data/external/airports_br.csv`, `nodes.csv` e `distances_km.csv` |
| leis federais de feriados | Diário Oficial da União | `data/external/holidays.csv` e `observances.csv` |
| capacidade, slots, fusões e eventos | BNDES, ANAC, CADE | linhas transcritas em `data/external/capacity.csv`, `slots.csv`, `groups.csv` e `events.csv`, com fonte e grau de confiança em cada linha |
| METAR | DECEA, via REDEMET | nada; não integrado |
| relatório de conexões | Infraero | nada; não é público e nenhuma coluna publicada depende dele |

## O que vai para o Zenodo

O depósito arquiva o repositório como etiquetado na versão v1.0.0, com as
tabelas versionadas: os dois painéis, a tabela-fato, as duas projeções de
cidade, as tabelas de `data/external/` e os manifestos — o que
`datapackage.json` descreve como recurso — e os três PDF de `reports/pdf/`
(ADR-0022). As camadas pesadas — `data/raw/`, `data/staged/` e
`data/derived/` — não vão: são regeneradas pelos comandos do
[`apendice-b-como-reproduzir.md`](apendice-b-como-reproduzir.md), e
`datapackage.json` as descreve sob `x-regenerated` com o comando que refaz
cada uma.

Dois DOI ainda não existem, e os dois têm lugar reservado.
`src/airline_delays/schema/metadata.py` carrega `DOI = None` até que o Zenodo
cunhe o DOI do repositório; quando ele existir, entra em `CITATION.cff`, no
`id` de `datapackage.json`, no selo do `README.md` — que até então resolve o
DOI do artigo — e na citação do dataset acima, num único commit `fix`
(`ROADMAP.md`). O DOI da monografia, cunhado pelo depósito do próprio autor,
substitui `[DOI-MONOGRAFIA]` onde o marcador estiver e entra em
`CITATION.cff` como referência. A resposta do e-SIC, quando chegar, é
registrada em `docs/notes/esic-licenca-vra.md`; a leitura CC BY da ADR-0000
já sustenta a redistribuição feita aqui.
