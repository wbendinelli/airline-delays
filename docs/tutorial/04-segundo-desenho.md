# M4 — O segundo desenho: OLS, 38 aeroportos, a instrumentação adiada

**Objetivo.** Ver o desenho de março de 2015 — OLS com efeitos fixos, ainda
em nível aeroporto, ainda sem instrumentar nada — e a frase que o fecha,
prometendo a instrumentação "para depois". Sete meses depois essa promessa
vira a espinha dorsal do artigo (o 2SGMM), e o OLS muda de papel: de
modelo principal a **tabela de advertência**. Este módulo mostra que essa
inversão de papel é verificável, hoje, num artefato real deste
repositório.

## Contexto (fora deste repositório)

O segundo seminário de tese (`2, Seminário de Tese.pdf`, 2015-03-16) ainda
tem o mesmo título do primeiro, mas já é rota, não aeroporto isolado: "a
rota no período t", 38 aeroportos, **29.232 observações**, estimador
**OLS** com efeitos fixos. O documento fecha assim:

> "Outro problema a ser endereçado futuramente será a instrumentação das
> variáveis endógenas de modo a se obter o melhor modelo para o caso
> brasileiro."

Em março de 2015, portanto, a instrumentação ainda era promessa e o OLS
era **o** modelo. No artigo publicado sete meses depois, o 2SGMM é a
espinha dorsal e o OLS virou a tabela que demonstra o que acontece quando
se ignora a endogeneidade (Tabela 6 publicada). A dissertação descreve o
mesmo achado: "Os resultados são alterados consideravelmente […] quando se
emprega o estimador OLS, com mudanças nos sinais estimados do HHI"
(§7.1). É uma inversão completa do papel do mesmo estimador em sete
meses.

Esta descrição vem de uma análise de acervo produzida antes deste
repositório existir (*avaliação em oito critérios*, seção C5.3) — o
documento original é privado e não está aqui (M12).

## A mesma inversão, dentro deste repositório

`src/airline_delays/estimation/table6.py` reproduz exatamente essa comparação, e o arquivo
já commitado neste repositório carrega os dois lados lado a lado:

```bash
grep -c "^| HHI city-pair" reports/replication/tables.md
```

**Número esperado.** `6` — uma linha "HHI city-pair" por tabela onde a
variável aparece (a correlação da Tabela 2, e as cinco tabelas de
regressão 3 a 7). Abra o arquivo e compare a linha sob `## Table 3 -
Estimation results (2SGMM)` com a linha sob `## Table 6 - Estimation
results (OLS)`, coluna (1) de cada uma: em 2SGMM, `HHI city-pair` sai
**positivo** (+0,8050 publicado, +0,8843 replicado); em OLS, sai
**negativo** (-0,2086 publicado, -0,2080 replicado). `HHI max endpoint
cities` faz o caminho inverso (negativo em 2SGMM, positivo em OLS). É a
mesma demonstração que a dissertação registrou em 2016 — reproduzida aqui
célula a célula, não parafraseada (`docs/notes/replication.md`, seção 4).

## Exercício

Abra `reports/replication/tables.md` você mesmo e localize as
quatro linhas (Tabela 3 e Tabela 6, `HHI city-pair` e `HHI max endpoint
cities`, coluna 1). Sem olhar o texto acima, escreva qual sinal cada uma
tem em cada tabela, e se o sinal replicado bate com o publicado (coluna
`diff/s.e.` ao lado de cada par). As quatro concordam?

## Limites e próximos passos

O segundo desenho não tem em si nenhum "erro" — é um passo intermediário
legítimo, e o próprio autor já sabia, em março de 2015, que faltava
instrumentar. O que este módulo mostra é o tamanho da distância entre
"sabemos que falta algo" e o desenho final: sete meses, uma mudança de
nível de análise implícita (a amostra de 2015-03 tem 38 aeroportos; a de
2015-10 tem 209 rotas), e nenhum documento no acervo original registra os
passos intermediários dessa transição — ver M9 e M10 para o que mais
falta no meio do caminho.
