# Tabelas de referência (`data/external/`): como foram construídas

Nota de pesquisa em português (padrão `DECISIONS.md` ADR-0006). Descreve
como cada tabela de `data/external/` foi montada, o que está verificado em
primeira mão (grau **A**) e o que depende de resumo de busca ou de
convenção não verificada (grau **B**), e o que continua em aberto. As
decisões de desenho (quais colunas, quais códigos, quais datas de corte)
vêm de `DECISIONS.md` (ADR-0001, 0003, 0005, 0007) e da tarefa que originou
este trabalho; esta nota documenta a evidência por trás de cada linha, não
repete a decisão em si.

Fontes de partida, todas lidas na íntegra antes de qualquer tabela ser
escrita: `DECISIONS.md`, `fontes-vra-anac.md` (nota de pesquisa do autor,
documento externo), o texto da IAC 1504 (`IAC1504.txt`, 30/abr/2000), e as
notas de pesquisa do autor (documento externo) para a lista de códigos de
empresas aéreas. Convenção de grau: **A** = fonte primária lida
diretamente nesta sessão (lei, texto da IAC, PDF baixado e convertido,
dataset baixado); **B** = resumo de busca, página não aberta, fonte
convergente mas não verificada, ou convenção de preenchimento (mês
desconhecido, dia fixado em 1º). Todas as tabelas têm `source`, `url`,
`retrieved_at` e `confidence` em cada linha; `just reference` (ver
`data/external/README.md`) valida a presença de `source`/`url`/`confidence`.

## 1. Geografia -- `airports_br.csv`, `nodes.csv`, `distances_km.csv` (ADR-0001)

**Como foi construída.** `airports_br.csv` é o `airports.csv` do OurAirports
(`https://davidmegginson.github.io/ourairports-data/airports.csv`, baixado
nesta sessão, HTTP 200, 86.042 aeródromos no mundo) filtrado para
`iso_country == BR` (8.035 linhas) e com as colunas renomeadas
(`icao, iata, name, municipality, region, lat, lon, type`). O ICAO vem do
campo `icao_code` do OurAirports, com fallback para `ident` quando
`icao_code` está vazio (não foi necessário para nenhum dos 31 aeroportos do
painel, todos tinham `icao_code` preenchido). Licença: OurAirports publica
os dados como domínio público / equivalente a CC0 ("no rights reserved");
é um espelho comunitário, não uma fonte oficial brasileira -- foi o único
dos três links testados em `fontes-vra-anac.md` que respondeu (os dois
links "oficiais" da ANAC deram 404 e falha de conexão).

`nodes.csv` aplica a definição de nós do ADR-0001 (MRSP = SBSP+SBGR+SBKP,
MRRJ = SBGL+SBRJ, MRBH = SBBH+SBCF, mais os 24 aeroportos-capital únicos)
sobre as coordenadas de `airports_br.csv`. Tem 31 linhas (uma por
aeroporto constituinte), agrupadas por `node` em 27 nós distintos. Para os
3 nós metropolitanos, `lat`/`lon` é o **centroide simples** (média
aritmética, não ponderada por passageiros) dos aeroportos que o compõem --
a tarefa pedia para explicitar a escolha entre centroide simples e
ponderado por passageiros: usei o simples porque não há, nesta tabela,
nenhum dado de passageiros por aeroporto para ponderar (isso existiria nos
"Dados Estatísticos do Transporte Aéreo" da ANAC, fora do escopo desta
tarefa). `distances_km.csv` é a distância *great-circle* (haversine, raio
6.371,0088 km) entre todos os pares ordenados dos 27 nós (27x26 = 702
linhas; pares nó-consigo-mesmo omitidos, seriam 0 por construção),
calculada diretamente das coordenadas de `nodes.csv`.

**Verificado (A).** As 8.035 linhas de `airports_br.csv` vêm de um download
direto e íntegro; os 31 aeroportos do painel foram conferidos um a um
(nenhum ausente). As distâncias foram conferidas por amostragem contra
valores de senso comum (MRSP-MRRJ = 366,8 km; MRSP-SBBR = 841,4 km;
SBBR-SBGO = 162,6 km; MRSP-SBSV = 1.462,9 km -- todos plausíveis para
essas rotas).

**Em aberto.** (i) Centroide ponderado por passageiros não foi calculado
(exigiria os Dados Estatísticos do Transporte Aéreo, não coletados nesta
tarefa) -- se algum dia for necessário, o simples pode ser substituído sem
mudar o formato da tabela. (ii) SBNT (Natal) aparece no OurAirports como
"Natal Air Force Base", sem IATA -- é o aeroporto correto para o período do
painel (Augusto Severo, substituído por São Gonçalo do Amarante/SBSG só em
2014, fora da janela 2000-2013), mas vale checar se o pipeline de dados
espera algum outro código para Natal. (iii) Coordenadas não foram
cross-checadas linha a linha contra uma segunda fonte -- só por amostragem
de distâncias. (iv) `monograph_airports.csv` transcreve os 38 aeroportos da
Lista de Siglas da monografia de graduação do autor (2013); 31 deles estão
em `nodes.csv` e cobrem os 27 nós do ADR-0001. Os 7 ausentes -- Juiz de
Fora, Joinville, Londrina, Porto Seguro, Ribeirão Preto, São José dos
Campos e Uberlândia -- não são capitais, e é por isso que o ADR-0001 não os
tem. Três códigos IATA impressos na monografia divergem do OurAirports
(`CPQ` contra `VCP` em SBKP, `PWM` contra `PMW` em SBPJ, e `NAT` em SBNT,
cujo registro no OurAirports não traz IATA nenhum -- o item (ii) acima):
ficam **anotados, não corrigidos**, porque a tabela é transcrição de um
documento, não um cadastro de aeroportos. O script
`scripts/monograph_airports.py` imprime as três contagens, e
`docs/notes/monografia-2013.md` descreve o documento de onde vieram.

## 2. Empresas aéreas -- `groups.csv` (ADR-0003)

**Como foi construída.** As datas e grupos dos 19 códigos citados
explicitamente no ADR-0003 (grupo Varig: VRG/VLO/VRN/NES/RSL; GLO; WEB;
AZU; TIB; TTL; PTN; TAM/BLC/SUL; TBA/ITB; VSP; ONE; PTB) seguem a regra do
laboratório, tal como registrada em `fontes-vra-anac.md` e nas notas de
pesquisa do autor (documento externo), que já testam essas trocas de grupo
diretamente contra a coluna `airline` do VRA bruto. A transição TTL -> TRIP
-> AZUL foi resolvida por transitividade, porque a mesma regra reatribui o
grupo "TI2" (que já inclui TTL a partir de 2007m11) para "AZ2" a partir de
2012m5 -- ou seja, TTL segue TIB para dentro do grupo Azul, mesmo o
enunciado da tarefa não dizendo isso explicitamente para TTL.

Os outros 21 códigos (`ABJ, ABZ, AMG, AVI, BRB, LEG, MEL, MSQ, NHG, NRA,
PAM, PEP, PLY, RIO, RLE, SBA, SLX, TIM, TSD, TVJ, VCR`) vêm das notas de
pesquisa do autor (documento externo): a interseção de duas listas derivadas
independentemente -- (i) um filtro de códigos de empresa escrito para testar
universo de voos contra a coluna real `airline` de uma amostra de 12 rotas x
3 anos extraída do VRA; (ii) as cerca de 45 variáveis de presença por
empresa da base final dos autores do artigo. Das cerca de 45, eliminei as
que claramente não são códigos de empresa crus (`bdg, csrgta, duotagl,
maj, mglo, mtam, ogl, smareg, yazu, ygl, yglo, yone, yweb` -- artefatos
derivados/agregados, como as divisões "jovem"/"madura" de Gol e Azul) e
mantive as que aparecem também na primeira lista ou são claramente códigos
de 3 letras adicionais (`AVI`, `LEG`, que a primeira lista exclui por não
serem empresas brasileiras).

**Verificado (A/B).** Nenhuma linha de `groups.csv` é grau A puro: mesmo as
datas mais concretas (Gol 2001-01, Azul 2008-12) vêm de eventos com grau B
em `fontes-vra-anac.md` (resumo de busca, não página aberta). As transições
por fusão (2007-04, 2009-12, 2011-11, 2007-11, 2012-05) seguem literalmente
"a regra usada pelo laboratório", como a própria tarefa instruiu para o
caso de o mês exato não estar verificado -- todas grau B, com nota
explicando que a data legal mais próxima (autorização ANAC, aprovação CADE)
está em `events.csv` e não necessariamente coincide com o mês usado na
regra de grupo. Os 21 códigos "other" são grau B: o código em si está bem
evidenciado (aparece em filtros diretos contra a coluna `airline` do VRA
real, em duas listas independentes das notas de pesquisa do autor), mas a
identidade da
empresa por trás de cada sigla e a data exata de entrada/saída no VRA não
foram verificadas nesta sessão -- deliberadamente não inventei nomes de
empresa para siglas que não reconheço com segurança (ex.: `RLE`, `TVJ`,
`SBA`, `MSQ`).

A monografia de graduação do autor (2013, seção 5.2) declara **os mesmos
seis grupos**, com as mesmas regras e as mesmas datas que esta tabela usa:
Trip com a Total "a partir de novembro de 2007", a Pantanal dentro da TAM
"a partir de dezembro de 2009", e Azul com a Trip "a partir de maio de
2012". É uma fonte convergente e datada -- escrita pelo próprio autor, não
o ato regulatório que falta. Por isso **nenhum grau muda**: 2007-11,
2009-12 e 2012-05 continuam B, exatamente como estavam. E a passagem da
Varig para dentro da Gol em 2007-04, que `groups.csv` registra, **não
aparece** na monografia: ali o grupo Gol é descrito como "a agregação entre
Gol e Varig", sem data de corte. Ver `docs/notes/monografia-2013.md` seção
2.

**Validação.** Nenhum código tem dois períodos sobrepostos (checado
programaticamente ao gerar o arquivo, não só por inspeção). 50 linhas para
40 códigos distintos.

**Em aberto.** (i) A lista de 21 códigos "other" **não é** uma varredura
completa do VRA bruto 2000-2013 -- é a união de duas amostras (12 rotas/3
anos e o painel de 209 rotas-capitais 2002-2013).
Qualquer código que apareça no VRA fora dessas amostras (rotas
não-capitais, anos 2000-2001 fora do painel de 209 rotas) não está nesta
tabela e cairia como `other` só se o pipeline de dados tratar ausência de
match como default `other` (como o `especificacao.md`/`especificação` da
tarefa já prevê). Recomendo reconciliar esta lista contra a saída real de
`src/airline_delays/staging/build.py` e
`src/airline_delays/definitions/carriers.py` assim que existir uma varredura
completa. (ii) Identidade real de `ABJ, ABZ, AMG, AVI, BRB, LEG, MEL, MSQ,
NHG, NRA, PAM, PEP, PLY, RIO, RLE, SBA, SLX, TIM, TSD, TVJ, VCR` não foi
pesquisada (nem por WebSearch) -- são provavelmente companhias regionais,
de táxi aéreo ou cargueiras de pequeno porte, ou códigos de empresas
estrangeiras que operaram algum trecho doméstico sob tipo de linha
internacional; ficam classificadas `other` até alguém identificar e
reclassificar. Uma pista nova: as Tabelas 3 e 4 da monografia de 2013
nomeiam seis transportadoras que `groups.csv` não tem por nome -- Penta,
Meta, Tavaj, Rico, Abaeté e Sete --, candidatas por semelhança de código a
`PEP`, `MSQ`, `TVJ`, `RLE`, `ABJ` e `SLX`, respectivamente. É hipótese de
grau B, não verificada: nenhum documento lido liga sigla a razão social, e
reclassificar qualquer uma delas mudaria o escopo da leitura B do ADR-0017
(que depende de a empresa ter classe FSC, LCC ou regional), o que é
território de ADR, não de edição de tabela. (iii) A data de entrada em
operação de TIB (Trip), PTB (Passaredo) e ONE (Oceanair) não foi
verificada -- usei 2000-01 (início do painel VRA) como placeholder, não
como data real de fundação/início.

## 3. Códigos da IAC 1504 -- `cause_codes.csv`, `di_codes.csv`, `line_types.csv` (ADR-0005)

**Como foi construída.** Transcrição direta do texto da IAC 1504 (Anexo 2,
"Códigos de Justificativas", e os itens 4.2-f e 4.2-m do corpo da norma).
49 códigos de causa (28 de atraso, 11 de cancelamento, 5 de alteração de
voo/escala, 5 de alteração de horário), 12 códigos de DI (0-9, A, B) e 8
tipos de linha (I, N, R, E, L, H, C, G). `category` segue literalmente a
segunda taxonomia do ADR-0005 (weather/airport_restricted/rotation/
technical/operational/authorised, com os códigos não citados no ADR caindo
em `other` -- 14 dos 49). `article_set` usa exatamente os três conjuntos
dados na tarefa (`prwheather` com 16 códigos, `princident` com 5,
`pr_connc` com 1, `RA`); os 27 códigos restantes ficam `none`. Os dois
conjuntos são independentes por desenho -- por exemplo `RI`/`RM` são
`category=rotation` e ao mesmo tempo `article_set=prwheather`, porque o
ADR-0005 já registrava que a variável `prwheather` do artigo original
"mescla clima com aeroporto interditado/restrito" (e, por extensão nesta
tarefa, com os códigos de conexão-por-interdição/clima).

**Verificado (A).** As três tabelas inteiras são grau A: o texto da IAC
1504 foi lido linha por linha (`IAC1504.txt`, fornecido para esta tarefa),
e a contagem de códigos por seção/categoria/article_set foi checada
programaticamente contra a leitura manual (49/12/8 confere; 28+11+5+5=49;
16+5+1+27=49; 10+6+3+5+6+5+14=49).

**Em aberto.** A página oficial da ANAC afirma que a IAC 1504 foi revogada
em abril de 2020 e que o campo "Justificativa" deixou de ser exigido a
partir de então -- `fontes-vra-anac.md` tentou achar o ato revogador e a
tabela substituta de códigos e não encontrou nenhum dos dois (testou a
Instrução Normativa 154/2020, que não é o instrumento certo). Isso não
afeta o painel 2000-2013 (a IAC estava em vigor o período inteiro), mas
importa se o projeto algum dia estender a janela temporal além de 2020.

## 4. Calendário -- `holidays.csv`, `observances.csv`

**Como foi construída.** `holidays.csv` aplica literalmente o texto de três
leis lidas na íntegra em `fontes-vra-anac.md` (Lei 662/1949, Lei
10.607/2002, Lei 9.093/1995, todas em `planalto.gov.br`): 5 feriados fixos
por ano (1/1, 1/5, 7/9, 15/11, 25/12) para 2000-2002, e 7 a partir de 2003
(soma Tiradentes 21/4 e Finados 2/11). A Lei 10.607/2002 é datada de
19/12/2002 -- tarde demais no ano para valer para o próprio 21/4 e 2/11 de
2002, por isso 2002 fica com 5, não 7. `observances.csv` cobre Carnaval
(segunda e terça), Sexta-feira Santa e Corpus Christi 2000-2013,
calculados a partir do Domingo de Páscoa (algoritmo gregoriano anônimo /
Meeus-Jones-Butcher, implementado em Python, não consultado ano a ano em
alguma tabela pronta).

**Verificado (A) vs. não (B).** `holidays.csv` é 100% grau A -- as três
leis foram lidas por inteiro nesta sessão (não a esta, na sessão que gerou
`fontes-vra-anac.md`, mas com citação literal do Art. 1º reproduzida ali).
`observances.csv` é grau B: a aritmética da data em si é determinística e
conferível por qualquer um (2000-03-07, 2001-02-27, 2002-02-12 conferem
com o conhecimento comum sobre essas datas de Carnaval), mas a
caracterização jurídica que acompanha cada linha ("Carnaval não é feriado
nacional por lei federal, é ponto facultativo decretado pelo Executivo")
está marcada como não verificada com fonte primária nesta sessão -- é
conhecimento geral, e o próprio `fontes-vra-anac.md` já pedia para marcar
como tal se fosse usado no pipeline.

**Em aberto.** Nenhum item crítico. Um refinamento possível seria verificar
se algum estado/município específico do painel (as 27 cidades-nó) teve
algum feriado municipal ou estadual relevante para tráfego aéreo -- fora do
escopo desta tarefa, que pedia só feriados nacionais.

## 5. Eventos -- `events.csv`

**Como foi construída.** Transcrição da tabela "Datas de eventos" de
`fontes-vra-anac.md`, mais os tratamentos de regime citados em
`avaliacao-vra-como-fonte.md` (janela do apagão aéreo 2006m10-2007m12,
crise financeira 2008-2009, codeshare TAM-Varig 2003-2005) que não tinham
uma data exata dia-a-dia em nenhuma das duas fontes -- para esses, usei o
1º dia do mês/ano como marcador de precisão, deixado explícito na nota de
cada linha. Onde `fontes-vra-anac.md` já registrava datas divergentes para
o mesmo fato (a falência da Vasp: 2005, 2008 ou 2013 dependendo da fonte;
a compra da Pantanal pela TAM: 19 ou 21/12/2009), mantive cada versão como
linha própria com nota, exatamente como a tarefa pediu, em vez de escolher
uma.

**Verificado (A).** Só 4 das 29 linhas: a falência da Transbrasil
decretada em 2002 (ano, Exame), a suspensão da Vasp em 2005 (ano, Exame),
o acidente do voo TAM 3054 (Wikipédia), e o anúncio da compra da Varig
pela Gol em 28/03/2007 (Agência Brasil/EBC) -- todas com o trecho literal
já conferido em `fontes-vra-anac.md`. As outras 25 são grau B (resumo de
busca, página não aberta, ou acesso bloqueado como o 403 da Conjur sobre a
aprovação do CADE em 2008).

**Em aberto.** As três versões divergentes da falência da Vasp continuam
sem resolução -- `fontes-vra-anac.md` já recomendava checar o processo
judicial original antes de fixar uma data única, e isso não foi feito
nesta tarefa. A janela do apagão aéreo e da crise 2008-2009 usa fronteiras
de calendário (início/fim de mês) como placeholder -- se a definição exata
da dummy do laboratório for localizada em algum `.do` não lido, as duas
linhas correspondentes devem ser corrigidas.

## 6. Capacidade e slots -- `capacity.csv`, `slots.csv` (ADR-0007)

**Como foi construída.** Estas duas tabelas são as mais fracas do conjunto,
e a tarefa já previa essa possibilidade ("if nothing verifiable is found,
write the file with the header only and explain"). Fiz uma rodada nova de
WebSearch/WebFetch além do que `fontes-vra-anac.md` já tinha tentado, e
achei algo em ambos os casos -- por isso as tabelas não ficaram só com
cabeçalho.

Para `capacity.csv`: uma busca por "Congonhas restrição operacional 2007
acidente TAM redução movimentos por hora" convergiu (Exame, CNN Brasil,
Agência Brasil, em reportagens de aniversário do acidente) para o número
33 movimentos/hora para aviação comercial em Congonhas depois do acidente
do voo TAM 3054 (17/07/2007) -- antes do acidente não havia limite formal
definido (throughput empírico citado de até 38/hora). Não abri nenhum ato
regulatório diretamente; é resumo de busca convergente, grau B. Não achei
nada equivalente (movimentos/hora, não passageiros/ano) para nenhum outro
aeroporto do painel -- o estudo BNDES/McKinsey (2010) que o ADR-0007 cita
dá passageiros/ano por aeroporto em 2009 (VCP 3,5 milhões, CGH 12,0, SDU
8,5, GRU 20,5, GIG 18,0), unidade diferente da pedida pela tabela, então
deliberadamente não a incluí nas colunas numéricas de `capacity.csv` (isso
seria "ajustar a definição para preencher a tabela", o que o `CLAUDE.md`
deste repositório proíbe explicitamente).

Para `slots.csv`: a melhor pista veio de abrir e extrair texto (via
`pdftotext -layout`, mesma técnica que `fontes-vra-anac.md` usou para o PDF
do BNDES) dos "Relatórios de Atividades" anuais da própria ANAC --
documentos primários que nenhuma pesquisa anterior deste projeto tinha
consultado. O relatório de 2009 (seção 3.2 "Coordenação de slots") descreve
um grupo de trabalho (depois "Comitê de Facilitação", com ANAC, INFRAERO e
CGNA) criado para coordenar horários em Congonhas, Santos Dumont e
Guarulhos, mas que "focou suas atividades no Aeroporto de Guarulhos" em
2009; a mesma seção 3.4 ("Liberação do Santos Dumont") descreve a revogação
da Portaria DAC 187/DGAC (de 08/03/2005, que restringia o SBRJ a ligações
específicas) e a publicação de novos procedimentos de distribuição de
horários em março de 2009. O relatório de 2010 (seção 2.5) confirma que,
por 2010, Guarulhos já operava alocação de slots plenamente coordenada via
Conferências Internacionais IATA (a 126ª, para a temporada IATA
Inverno 2010, alocou 112.685 slots em 147 dias; a 127ª, para o Verão 2011,
alocou 166.915 em 217 dias). O relatório de 2012 confirma que, em
18/04/2012, a ANAC já redistribuía 119 dos 227 slots de Congonhas -- ou
seja, Congonhas já estava sob coordenação ativa naquela data, mas o ato/
data exata em que isso começou não apareceu em nenhum dos quatro relatórios
lidos (2009, 2010, 2012, 2013). O relatório de 2013 mostra que, em
fevereiro de 2013, a ANAC ainda discutia em audiência pública a resolução
que unificaria o conceito de "aeroporto coordenado" e "aeroporto de
interesse" (o que a busca de contexto já indicava ter virado as Resoluções
336/2014 e 338/2014) -- ou seja, o arcabouço regulatório único só se
consolida depois do fim do painel (2013).

**Verificado (A) vs. não (B).** As duas linhas de `slots.csv` (Guarulhos,
Santos Dumont) são grau A -- texto lido diretamente do PDF oficial da ANAC
via `pdftotext`. A linha de `capacity.csv` (Congonhas, 33 mov/h) é grau B
-- resumo de busca convergente, nenhum ato aberto diretamente.

**Em aberto.** (i) Congonhas: sem data/ato específico de quando passou a
ser "coordenada" no sentido pleno, apesar de checar diretamente os
relatórios de atividades da ANAC de 2009, 2010, 2012 e 2013 e de fazer
buscas direcionadas -- só se sabe que já estava sob gestão ativa de slots
em abril de 2012 e que era um dos três aeroportos do mandato original de
2009. (ii) Recife: não apareceu em nenhum dos quatro relatórios anuais
checados; é um dos 4 aeroportos atualmente coordenados pela ANAC (junto com
Congonhas, Guarulhos e Santos Dumont), mas pode ter entrado nessa lista
depois de 2013, fora da janela do painel. (iii) Brasília: a página atual de
slots da ANAC (lida via WebFetch) classifica Brasília como "facilitado"
(coordenação do operador aeroportuário), não "coordenado pela ANAC" -- não
achei nenhuma fonte histórica que diga se isso já era assim em 2000-2013 ou
se mudou. (iv) Nenhum ato com número de portaria/resolução específico foi
encontrado para o início da coordenação em Guarulhos -- só a menção
genérica a um "programa de coordenação de horários" sob diretrizes do
CONAC. (v) Não tentei os relatórios de atividades de 2011 nem de anos
anteriores a 2009 -- um relatório de 2007 ou 2008, se existir com o mesmo
formato, poderia ter informação sobre Congonhas logo após o acidente TAM
3054.

## Itens em aberto, consolidado

Para quem for revisar ou estender este trabalho, em ordem de impacto:

1. `groups.csv`: os 21 códigos "other" vêm de duas amostras do laboratório,
   não de uma varredura completa do VRA 2000-2013 -- reconciliar contra a
   saída real do pipeline de dados assim que existir.
2. `groups.csv`: identidade real das 21 siglas "other" não pesquisada.
3. `capacity.csv`/`slots.csv`: Congonhas sem data de início de coordenação;
   Recife ausente; Brasília com status histórico incerto; nenhum número de
   portaria/resolução específico encontrado para Guarulhos.
4. `events.csv`: três datas divergentes para a falência da Vasp, não
   resolvidas (processo judicial original não consultado).
5. IAC 1504: ato revogador (abril/2020) e tabela substituta de códigos não
   localizados (não afeta 2000-2013, mas limita extensão futura).
6. `nodes.csv`: centroide dos nós metropolitanos é simples, não ponderado
   por passageiros, por falta de dado de passageiros por aeroporto nesta
   tarefa.

## Correção do orquestrador (2026-09-05)

Em `groups.csv`, a classe de uma empresa absorvida passa a seguir o grupo que a absorveu: Pantanal dentro da TAM (desde 2009-12) é FSC; Trip e Total dentro da Azul (desde 2012-05) são LCC. É a regra do laboratório que reproduz as proporções FSC do painel com diferença mediana zero (`reconstrucao-vra.md`), e é o que o ADR-0003 registra. A lista de 21 códigos "other" deve ser reconciliada com a varredura completa do VRA na fase de features.
