# A monografia de 2013: o que ela documenta e o que ela não permite afirmar

Nota de pesquisa em português (ADR-0006: código e nomes de coluna em inglês,
notas e relatórios em português). Registra o que a monografia de graduação
do autor, de 2013, diz sobre os dados, os grupos de empresas e as variáveis
do modelo, e o que dela é comparável — e o que não é — com o painel público
deste repositório. Todo número aqui ou vem de um script versionado
(`scripts/monograph_airports.py`), ou de uma tabela versionada
(`data/external/monograph_airports.csv`), ou está marcado como lido do
documento externo, que não é redistribuído.

O documento em si fica fora do repositório e é citado, nunca copiado: apenas
a transcrição da sua Lista de Siglas e passagens curtas entram aqui.

## 1. O documento

*Efeitos da entrada de uma empresa aérea de baixo custo na internalização
das externalidades do congestionamento*, monografia apresentada para a
obtenção do título de Bacharel em Ciências Econômicas, USP/ESALQ,
Piracicaba, 2013. Orientadores: Prof.ª Dra. Márcia Azanha Ferraz Dias de
Moraes e Prof. Dr. Alessandro Vinícius Marques de Oliveira — o segundo é
também orientador do mestrado e coautor do artigo de 2016 que este
repositório replica (`docs/data-availability.md`, fonte 12).

Nove seções, na ordem do sumário: 1 Introdução; 2 Princípios econômicos dos
atrasos em aeroportos; 3 Revisão de literatura; 4 Modelo econômico para um
líder de Stackelberg; 5 Análise da base de dados; 6 Modelagem econométrica;
7 Resultados das estimações; 8 Considerações finais; 9 Bibliografia.

Os metadados do arquivo dizem: criado em 2013-12-18, última impressão em
2013-12-19, revisões até 2014-02-17. A proposta de mestrado descrita no
módulo M1 do tutorial (`docs/tutorial/01-a-proposta.md`) é de 2013-09-16. Os
dois documentos são, portanto, **contemporâneos**: nada no material lido
permite dizer que um antecede conceitualmente o outro, e esta nota não
afirma isso.

Depósito no Zenodo pendente: `[DOI-MONOGRAFIA]`. Até que exista, a
monografia é **citada, não redistribuída** — a única coisa que este
repositório publica dela é a tabela derivada da Lista de Siglas e as
passagens citadas aqui e em `docs/theory/`.

## 2. Os dados

A seção 5.1 descreve quatro fontes, e é a descrição mais explícita do
encadeamento VRA -> HOTRAN + BAV que existe em qualquer documento deste
acervo.

**(i) Percentuais de atraso e cancelamento da ANAC.** Divulgados e
consolidados por par de aeroportos de origem e destino, sob a Resolução ANAC
nº 218 e seguindo os modelos da Portaria ANAC nº 464/SER. São apurados sobre
o **Voo Regular Ativo (VRA)**, que a monografia descreve como composto por
informações do **HOTRAN** — normatizado pela IAC 1223 e pela Portaria DGAC
nº 33/2000 — e dos **Boletins de Alteração de Voo (BAV)**, registrados pelas
empresas em cumprimento à IAC 1504. O percentual de cancelamento divide
etapas canceladas por etapas **previstas**; o de atraso divide etapas
atrasadas por etapas **realizadas**, já descontadas as canceladas. São
publicados **dois cortes**: 30 minutos ou mais, e 60 minutos ou mais
(monografia, seção 5.1 — documento externo).

**(ii) HOTRAN.** Documento aprovado e emitido pelo DAC, que formaliza as
concessões de linhas com horários, números de voo, frequências, tipos de
aeronave e oferta de assentos. Dá a **oferta planejada**, não o embarque: a
monografia registra explicitamente que as conexões não são observáveis no
HOTRAN.

**(iii) Movimento operacional da Infraero.** Obtido dos formulários RPE
(Relatório de Passageiros Embarcados) preenchidos pelas próprias empresas. A
monografia declara a ressalva de confiabilidade: a **Resolução ANAC nº 8, de
2007-03-13**, revogou a obrigatoriedade de envio do RPE aos aeroportos, que
a **Portaria 602-GC5, de 2000-09-22**, do DAC, estabelecia no seu artigo 7º.
E, a partir de 2013, aeroportos concedidos à iniciativa privada deixaram de
ter obrigação de disponibilizar seus dados — foi por isso, e não por outro
motivo, que **2013 inteiro foi descartado** e a série ficou em 2000-01 a
2012-12.

**(iv) Meteorologia aeronáutica do DECEA.** Médias mensais por aeródromo, na
Tabela 1 atribuídas ao ICEA: temperatura, vento, precipitação, visibilidade
e teto, na origem e no destino.

**As três contagens de aeroportos, declaradas e não reconciliadas.** A Lista
de Siglas tem 38 aeroportos; as Tabelas 3 e 4 (2000 e 2012) têm 37 — falta o
SBPS, Porto Seguro; e o texto da seção 5.2 diz que "selecionaram-se 36
aeroportos" para os quais havia dados meteorológicos e de movimento
operacional. As três convivem no mesmo documento e esta nota não escolhe
uma: `uv run python scripts/monograph_airports.py` imprime as três a partir
de `data/external/monograph_airports.csv`, e mostra também que 31 dos 38
estão no mapa do ADR-0001 (`data/external/nodes.csv`), cobrindo os 27 nós.

**Os seis grupos de empresas.** A seção 5.2 forma seis grupos a partir das
fusões: **VR2** (Varig, Nordeste e Rio Sul); **TB2** (Transbrasil e
Interstar Brasil); **TI2** (Trip, com a Total **a partir de novembro de
2007**, dominando as rotas regionais); **TA2** (Grupo TAM, com Helisul e
Brasil Central, e a Pantanal **a partir de dezembro de 2009**); **GL2** (Gol
e Varig); e **AZ2** (Azul e Trip, **a partir de maio de 2012**). São as
mesmas regras e as mesmas datas de corte que `data/external/groups.csv` já
usava — ver `docs/notes/references.md` seção 2 para o que isso muda e o que
não muda no grau de confiança de cada linha.

**As variáveis da Tabela 1 e seus sinais esperados.** A Tabela 1 divide as
variáveis em três conjuntos — operacionais, climáticas de controle, e de
concorrência e barreiras à entrada — e traz uma coluna de sinal esperado:
`prdeltot` é o dependente; `prconex` (+), `amovtot` (+), `fltime` (-),
`asize` (+); `precip` (+), `wind` (- ou +), `ceiling` (+); `hhi` (- ou +),
`cr2` (- ou +); `dummy_gol` (-) e `dummy_azul` (-). Os dois sinais ambíguos
são argumentados no texto: vento pode adiantar ou atrasar, e a literatura
não tem consenso sobre internalização (monografia, seção 5.3 — documento
externo).

**A lista de laboratório.** A base de regressão da monografia traz 46
variáveis descritas por famílias, não copiadas aqui uma a uma: frequências
planejadas, canceladas, realizadas, atrasadas em 30 e atrasadas em 60
minutos (ANAC, nos níveis de rota e de aeroporto, 2000-2012); HHI e CR1/CR2
na rota, na origem e no destino (cálculos próprios); temperatura, vento,
precipitação, visibilidade e teto na origem e no destino (ICEA, médias
mensais); frequências de dia útil, fim de semana e pico, e tamanho médio de
aeronave (HOTRAN, 1990-2012); e passageiros domésticos e internacionais
locais, embarcados e em conexão na origem e no destino (Infraero,
1990-2012).

**O painel final.** Depois dos ajustes, "obteve-se um painel de dados
desbalanceado contendo uma amostra com 87.237 observações" (monografia,
seção 5.2 — documento externo), no grão empresa x rota x mês.

## 3. A média geométrica ponderada

Esta seção existe porque o repositório tem uma coluna chamada `gmchhi` e a
monografia tem uma construção parecida com outro nome, e as duas **não são a
mesma coisa**. Três camadas, separadas de propósito.

**Documentado.** O único do-file sobrevivente da monografia,
`nectarbase_delays.do` (documento externo, nunca redistribuído), define
`aplantot = ofplantot + dfplantot`, `sofplantot = ofplantot/aplantot` e
`sdfplantot = dfplantot/aplantot` e, sobre isso, a **média geométrica
ponderada** dos dois extremos da rota:

```
ahhi = ohhi^sofplantot * dhhi^sdfplantot
```

E a mesma forma para `acrat1`, `acrat2` e as cinco médias climáticas
(`temp`, `wind`, `precip`, `visib`, `ceiling`). A Tabela 1 confirma em
prosa: `cr2`, `amovtot`, `prconex`, `precip` e `wind` são descritas como
"média geométrica … ponderada pela frequência total de voos planejados da
empresa aérea *j* no par origem e destino *h* no mês *t*". Do outro lado,
`src/vra/hhi.py` define `gmchhi` como a média geométrica **não ponderada**,
`sqrt(origem * destino)`, e `maxcthhi` como o **máximo** dos dois extremos —
é o que `src/vra/registry.py` documenta e o que os testes cobram.

**Inferência.** É razoável ler `gmchhi` como descendente de `ahhi` com os
pesos retirados: mesma operação sobre os mesmos dois extremos, sem os
expoentes `sofplantot`/`sdfplantot`. É inferência, não citação — nenhum
documento lido diz isso.

**Não comparável.** `ahhi` é calculado sobre **voos planejados**; `gmchhi`,
`maxcthhi` e `rthhi` são, no artigo de 2016 e neste repositório, HHIs sobre
**passageiros pagos** — e por isso estão nulos em toda a base enquanto os
dados estatísticos da ANAC não forem coletados (`docs/notes/features.md`
seção 5, `docs/data-availability.md` fonte 3). Comparar os dois números
seria comparar unidades diferentes.

**A quase-identidade que é documentável.** O que *é* a mesma construção é o
`hhi` de rota da monografia — soma dos quadrados das participações de cada
empresa nos voos planejados do par origem-destino no mês — e a coluna
`rthhi_flights` do painel público, que `src/vra/panel.py` define como igual
a `hhi_flights`, isto é, Σ (participação)² sobre as etapas **programadas**
(`src/vra/registry.py`). Mesma operação, mesma unidade, nomes diferentes
porque o artigo reservou `rthhi` para a versão de passageiros.

## 4. Texto contra código

Quatro pontos em que o texto da monografia e o do-file sobrevivente dizem
coisas diferentes. Estão escritos como **perguntas para o autor confirmar
contra o documento e a pasta original**, não como veredictos — o material
lido não é suficiente para fechar nenhum deles.

1. **Pesos.** A seção 6.2 desenvolve, nas equações (17) a (21) e seguindo
   Wooldridge (2010), um estimador-M **ponderado pelo inverso da
   probabilidade de amostragem** para uma amostra estratificada. O do-file,
   porém, roda `[aweight=fplan]` — peso **analítico** pela frequência de
   voos planejados. São coisas distintas em Stata e respondem a problemas
   distintos. A pergunta: o texto descreve o estimador que de fato gerou a
   Tabela 5, ou descreve o arcabouço teórico e a implementação usou o peso
   analítico como aproximação?

2. **Variável dependente.** A Tabela 1 e a equação (22) usam `prdeltot`,
   descrita como "média geométrica ponderada dos atrasos totais". O do-file
   define `prdel30 = fdel30/fplan` — atrasos de 30 minutos sobre etapas
   **planejadas**, enquanto a própria seção 5.1 registra que a ANAC apura o
   percentual de atraso sobre etapas **realizadas**. A pergunta: `prdeltot`
   é construído em algum lugar que não foi lido, e qual dos dois
   denominadores vale para a tabela publicada?

3. **Regressores.** O comando ativo do do-file é

   ```
   reg prdel30 prdeltt_jt amovtot000 temp wind precip visib ceiling fltime asize acrat2 rhhi ahhi k_* j_* t_* [aweight= fplan]
   ```

   Os efeitos fixos vêm de três expansões de dummies e de um painel
   declarado:

   ```
   tab lab_k, gen(k_)   // rota
   tab lab_j, gen(j_)   // empresa
   tab lab_t, gen(t_)   // mês
   tsset ind_kj ind_t
   ```

   Os regressores de concentração ali são `rhhi` e `ahhi`, mais `acrat2` e
   as cinco climáticas — **não** o par `hhi` + `cr2` que a Tabela 5 publica.
   A leitura mais econômica é que este do-file é uma **variante
   preliminar**, não o script da Tabela 5. A pergunta: existe outro do-file,
   e este é anterior ou posterior a ele?

4. **Rótulos das Tabelas 5 e 6.** Os rótulos de linha das duas tabelas foram
   **recuperados dos objetos de equação do próprio documento** (Constante;
   Passageiros em conexão; Movimento aeronaves; Tempo de voo médio; Tamanho
   médio da aeronave; Velocidade do vento; Precipitação; Teto da nuvem — só
   na especificação 4; Índice HHI; Índice CR2; Dummy Gol; Dummy Azul;
   Efeitos fixos; R²). O mapeamento rótulo -> variável é, portanto,
   **lido**, não inferido — e é o único ponto desta seção que não depende de
   nenhuma hipótese.

Nada disto é erro demonstrado; é o que o material lido permite e não permite
afirmar, para o autor confirmar contra o documento e a pasta original.

## 5. A ponte com o artigo de 2016

A continuidade conceitual entre o modelo de Stackelberg da seção 4 da
monografia e a especificação do artigo de 2016 é tratada em
`docs/theory/03-do-modelo-ao-artigo.md`, escrito em paralelo a esta nota. A
tabela de correspondência entre as variáveis das duas peças vive lá, não
aqui: esta nota cuida da evidência documental, aquela cuida do argumento
econômico.

## 6. Não tentado

A Tabela 5 da monografia — cinco especificações de efeitos fixos ponderadas
— **não foi reestimada**, nem publicamente nem em modo privado. Três
motivos, os mesmos que `docs/declared-differences.md` registra em inglês na
seção "Not attempted, and why": (i) a base de regressão é um arquivo de
laboratório, `nectarbase_delays.dta` (documento externo), que nunca entra
neste repositório e só poderia ser lido por `replication/gabarito/` através
da variável de ambiente `AIRLINE_DELAYS_PRIVATE_DIR`; (ii) a variável
dependente `prdeltot` não é construída em nenhum lugar do material lido, e o
do-file sobrevivente é uma variante preliminar (seção 4 acima), não o script
da tabela publicada; (iii) a econometria de referência deste repositório é a
do artigo de 2016 (Tabelas 2-7), e o estimador da monografia responde a
outra pergunta em outra unidade — empresa x rota x mês, N = 87.237,
2000-2012, corte de 30 minutos.

O que o painel público oferece no lugar está na seção 3: `rthhi_flights` usa
a mesma construção que o `hhi` de rota da monografia sobre voos planejados,
e `fsc_prdelarr30m` carrega o mesmo corte de 30 minutos. Se o script da
Tabela 5 for algum dia localizado, o lugar dele é um módulo marcado
`gabarito` sob `replication/gabarito/`, escrevendo apenas estatísticas de
concordância.

## 7. Como conferir

```bash
uv run python scripts/monograph_airports.py
uv run vra refs
```

O primeiro comando imprime exatamente três linhas:

```
monograph (2013): 38 airports in the Lista de Siglas; 37 in Tables 3-4 (absent: SBPS); the text of section 5.2 says 36
ADR-0001 map (data/external/nodes.csv): 31 of 38 present -> 27 nodes (all 27 nodes covered)
absent from the map (7): SBJF SBJV SBLO SBPS SBRP SBSJ SBUL
```

O segundo valida que cada linha de `data/external/monograph_airports.csv` —
as 38 — carrega `source`, `url` e `confidence`, como toda tabela de
referência deste repositório. As 38 são grau **A**: transcrição direta do
documento, com `url` em branco porque a fonte é um documento em
papel/arquivo, não uma página.
