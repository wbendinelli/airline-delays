# docs/

Português (ADR-0006) -- a versão em inglês desta página é o `README.md` deste
diretório.

A documentação de `airline-delays` que não cabe no README. As duas páginas de
entrada -- `README.md`, em inglês, e `README.pt-BR.md`, em português --
compartilham um único esqueleto; tudo abaixo é alcançado a partir delas.

| Caminho | O que contém | Idioma |
|---|---|---|
| `dictionary.md` | O dicionário de dados: 636 colunas em 7 camadas, dos voos *staged* à tabela de modelagem por voo, cada uma com tipo, unidade, regra de agregação e definição. Gerado de `src/airline_delays/schema/columns.py` por `airline-delays dictionary`; nunca editado à mão. | Definições em inglês e em português |
| `data-availability.md` | A Declaração de Disponibilidade dos Dados, fonte por fonte: detentor, como obter, restrições, custo e prazo. `data/README.md` e a seção "Disponibilidade dos dados" do README são suas versões curtas. | Inglês |
| `editorial/` | As regras que a prosa segue: `style-guide.md` (dezessete regras, do tom à nomeação dos dois painéis), `readme-outline.md` (o esqueleto fixo dos dois READMEs e a chave de `reports/summary.json` de cada número) e `number-allowlist.txt` (os poucos números que são constantes, não medições). | Inglês |
| `notes/` | As notas de pesquisa por trás das decisões de `DECISIONS.md`: *staging*, tabela-fato e painel, replicação, tabelas de referência, camada de previsão, o colegiado de revisão da ADR-0017, o pedido de licença à ANAC e a monografia de 2013 do autor. Índice em `notes/README.md`. | Português (ADR-0006), índice em inglês |
| `study/` | O estudo, o trabalho final: uma apresentação, oito capítulos em três partes -- a economia do congestionamento aeroportuário; a teoria dos jogos, dos fundamentos ao modelo de congestionamento de Stackelberg derivado passo a passo; o artigo, do modelo às hipóteses, os dados, especificação e identificação, resultados e replicação, e a recepção -- quatro apêndices (o preditor de atrasos, como reproduzir, direitos e licenças, extensões) e a bibliografia. Compila para `reports/pdf/study.pdf`. Índice em `study/README.md`. | Português (ADR-0006), resumo em inglês no índice |

Todo caminho e todo comando `just` ou `airline-delays` citado sob `docs/` é
checado por `scripts/check_docs_paths.py`, e todo número das páginas de
entrada por `scripts/check_prose_numbers.py` contra `reports/summary.json`.
