# M1 — A proposta: a pergunta era sobre preços

**Objetivo.** Ver que o artigo que este repositório replica não nasceu como
um projeto sobre atrasos. Nasceu como um projeto sobre **preços**, e a
pergunta mudou antes de qualquer resultado empírico existir. Isso importa
para quem for propor uma extensão (M13): a pergunta de preços não morreu
por ser ruim — morreu por uma decisão de orientação, e os dados para
retomá-la continuam públicos.

## Contexto (fora deste repositório)

A proposta de mestrado (`Proposta Mestrado.docx`, criada em 2013-09-16,
fechada em 2013-09-19, ITA) tem título em caixa alta:

> **EFEITO DOS ATRASOS NOS PREÇOS DAS PASSAGENS AÉREAS QUANDO AS EMPRESAS
> AÉREAS TÊM PODER DE MERCADO**

e declara a ambição:

> "Objetiva-se estimar a relação entre os atrasos e a resposta de preço
> quando as empresas aéreas têm poder de mercado. […] será o primeiro
> estudo a investigar determinantes de atrasos em conjunto com preços."

Três fontes são declaradas: ANAC (atrasos), o **Relatório de Tarifas
Aéreas** da ANAC, e o ICEA (clima). Dois periódicos-alvo: *Transportation
Research Part B* e o *International Journal of Industrial Organization* —
nenhum dos dois é onde o artigo saiu (*Transportation Research Part A*,
ver M9). Um cronograma previa submissão em 2015m2 e defesa em 2015m11–12;
a submissão real foi 2015-10-02 e a defesa 2016-02-22 — sete e três meses
de atraso sobre o próprio cronograma de um estudo sobre atrasos.

Esta narrativa e as citações literais acima vêm de uma análise de acervo
produzida antes deste repositório existir — *avaliação em oito critérios,
seção C5.1* — não de um arquivo presente aqui. O acervo original (a
proposta, os seminários, a dissertação) é privado e não foi incluído
neste repositório; ver
[`12-consentimento-licencas-publicacao.md`](12-consentimento-licencas-publicacao.md)
para o porquê.

## O que sobrevive disso neste repositório: nada, e dá para provar

Nenhuma das três colunas tarifárias que a proposta previa (`yield`,
`fare`, contagem de bilhetes) existe no registro de colunas deste
repositório.

```bash
grep -n '"yield"\|"fare"' src/vra/registry.py
```

**Número esperado.** Zero ocorrências — `src/vra/registry.py` não declara
nenhuma coluna de tarifa ou receita, porque o VRA (a fonte deste
repositório) é um arquivo de **operação**, não de bilhetagem
([`docs/data-availability.md`](../data-availability.md), fonte 4: "ANAC
tariff microdata... Not yet collected"). A pergunta de preços não foi
respondida aqui — foi deixada de fora desde a raiz.

## Exercício

Leia a linha "ANAC tariff microdata" de
[`docs/data-availability.md`](../data-availability.md) e a entrada
correspondente em
[`13-propor-melhorias.md`](13-propor-melhorias.md) (seção "a pergunta
original de preços"). Sem baixar nada, escreva em três frases: que chave
(`route`, `ym`, `group`) uma tabela de tarifas por rota-mês-empresa
precisaria ter para ser unida ao painel público
(`data/analysis/panel_route_month.parquet`) sem reextrair nada? A resposta
está na própria definição de `route` e `ym` no dicionário
(`docs/dictionary.md`).

## Nota honesta

O que motivou a virada de preços para atrasos não está registrado em
nenhum documento datado do acervo original — só a sequência de datas entre
a proposta (set/2013) e o primeiro seminário (jul/2014) permite inferir
que algo mudou nesse intervalo. O module seguinte (M2) mostra o único
artefato desse intervalo: um exercício bibliográfico de treze respostas,
sem as perguntas que as provocaram.
