# docs/study/

The final study of `airline-delays`, written in **Portuguese** (`DECISIONS.md`,
ADR-0006): the microeconomics of airport congestion, the game-theoretic model
of a Stackelberg leader derived and checked in `src/airline_delays/theory/`,
and Bendinelli, Bettini & Oliveira (2016, *Transportation Research Part A* 85,
39-52, doi 10.1016/j.tra.2016.01.001) -- its data, its specification, its
results and the replication of Tables 2-7 made in this repository -- in one
work of eight chapters and four appendices. Every number about the model is
printed by `just theory` (`airline-delays theory`) into
`reports/theory/model.json` and `reports/theory/figures.json`; every number
about the article comes from `src/airline_delays/estimation/published.json` or
from the replication's own outputs under `reports/replication/`; every headline
number is a value of `reports/summary.json`; everything else is marked as an
outside document. The study is also compiled as one PDF, `reports/pdf/study.pdf`,
by `just report` from `reports/study.typ`: the three parts plus two appendices
(the verified identities; how to reproduce), while the appendices on the delay
predictor, rights and extensions exist in this Markdown edition only.

Português (ADR-0006). O estudo lê-se na ordem abaixo. Cada capítulo abre
dizendo o que o leitor sai sabendo e fecha com "Onde conferir", os arquivos de
onde saíram os seus números e figuras; a apresentação diz por onde entrar
conforme o que se procura.

| Arquivo | Parte | Capítulo |
|---|---|---|
| [`00-apresentacao.md`](00-apresentacao.md) | abertura | Apresentação: a pergunta, a tese e o mapa do estudo |
| [`01-economia-do-congestionamento.md`](01-economia-do-congestionamento.md) | I | A economia do congestionamento aeroportuário |
| [`02-teoria-dos-jogos-fundamentos.md`](02-teoria-dos-jogos-fundamentos.md) | II | Teoria dos jogos: os fundamentos de que o modelo precisa |
| [`03-o-jogo-do-congestionamento.md`](03-o-jogo-do-congestionamento.md) | II | O jogo do congestionamento: um líder de Stackelberg, derivado passo a passo |
| [`04-do-modelo-as-hipoteses.md`](04-do-modelo-as-hipoteses.md) | III | Do modelo às hipóteses: o que o artigo de 2016 foi testar |
| [`05-os-dados.md`](05-os-dados.md) | III | Os dados: do registro de voo ao painel rota × mês |
| [`06-especificacao-e-identificacao.md`](06-especificacao-e-identificacao.md) | III | Especificação e identificação: 2SGMM, instrumentos, HAC e Kleibergen–Paap |
| [`07-resultados-e-replicacao.md`](07-resultados-e-replicacao.md) | III | Os resultados e a replicação das Tabelas 2–7 |
| [`08-recepcao.md`](08-recepcao.md) | III | A recepção: o que o campo levou e o que continua em aberto |
| [`apendice-a-previsao-de-atrasos.md`](apendice-a-previsao-de-atrasos.md) | apêndice | Apêndice A — Além do artigo: o preditor de atrasos por voo |
| [`apendice-b-como-reproduzir.md`](apendice-b-como-reproduzir.md) | apêndice | Apêndice B — Como reproduzir cada número deste estudo |
| [`apendice-c-direitos-e-licencas.md`](apendice-c-direitos-e-licencas.md) | apêndice | Apêndice C — Direitos, licenças e o que se publica onde |
| [`apendice-d-extensoes.md`](apendice-d-extensoes.md) | apêndice | Apêndice D — Extensões que o repositório já sustenta |
| [`bibliografia.md`](bibliografia.md) | apêndice | Bibliografia |

Três rótulos percorrem as Partes II e III. **[BVD]** marca um resultado de
Brueckner e Van Dender (2008) reenunciado; **[monografia]** marca um enunciado
da monografia de graduação do autor (USP, 2013), citada como documento
externo, a única origem admitida da teoria antes do artigo; **[aqui]** marca o
que a derivação deste repositório acrescenta. As equações (1)–(12) mantêm a
numeração de Brueckner e Van Dender (2008) e da monografia. A nota de pesquisa
sobre o lado de dados da monografia é `docs/notes/monografia-2013.md`.
