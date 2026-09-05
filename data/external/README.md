# data/external/

Small, hand-curated reference tables, committed in git because their diff is
exactly what needs to stay reviewable in a pull request (they encode human
judgment: a node map, a merger date, a code's class -- see `.gitattributes`,
which deliberately does not mark this directory `linguist-generated`).

Every table is a UTF-8 CSV with a header, one row per fact. Every row cites
its own `source` and `url` -- this is the machine-readable half of the
README's "Data availability" section, not a separate claim -- plus a
`retrieved_at` date (`YYYY-MM-DD`) and a `confidence` grade:

- **A** -- the underlying primary source (a law, the IAC 1504 text, a
  downloaded dataset, an ANAC PDF) was read directly this session (or, for
  `nodes.csv`/`distances_km.csv`, computed directly from coordinates that
  were).
- **B** -- the fact rests on a search-engine summary, an unopened page, a
  convergent-but-unverified secondary source, or a placeholder convention
  (e.g. "month unknown, day set to the 1st"). Treat as not independently
  confirmed. `just reference` validates that every row has `source`, `url` and
  `confidence`.

Full methodology, what is verified vs. open, and outstanding items are in
[`docs/notes/references.md`](../../docs/notes/references.md) (Portuguese,
per `DECISIONS.md` ADR-0006). This file only lists what each table is, its
columns, its row count and where it came from.

## Geography (ADR-0001)

| File | Owner | Rows | Contents |
|---|---|---|---|
| `airports_br.csv` | references agent | 8,035 | Every OurAirports record with `iso_country == BR`: `icao, iata, name, municipality, region, lat, lon, type` (+ source/url/retrieved_at/confidence). Downloaded verbatim from OurAirports and filtered, not hand-curated -- this is the universe every Brazilian ICAO code in the VRA should resolve against, not just the 27 panel nodes. Licence: OurAirports publishes as public domain / CC0-equivalent ("no rights reserved"); it is a community-maintained mirror, not an official Brazilian government source. |
| `nodes.csv` | references agent | 31 (27 distinct nodes) | The airport -> panel-node crosswalk for the 27 nodes of ADR-0001: `icao, node, node_name, city, uf, metropolitan, lat, lon` (+ source/url/retrieved_at/confidence). One row per **constituent airport**: 3 rows for `MRSP` (SBSP+SBGR+SBKP), 2 for `MRRJ` (SBGL+SBRJ), 2 for `MRBH` (SBBH+SBCF), 1 each for the 24 single-airport capitals -- grouped by the `node` column into 27 distinct nodes. `lat`/`lon` give the **node's** representative coordinate (a simple, unweighted centroid of the constituent airports for the 3 metro nodes; the airport's own coordinate for single-airport nodes), not necessarily that row's airport's own coordinate -- cross-reference `airports_br.csv` for the latter. |
| `distances_km.csv` | references agent | 702 | Great-circle (haversine, R=6371.0088 km) distance for every ordered pair of the 27 distinct nodes in `nodes.csv` (27x26; same-node pairs omitted, distance would be 0 by construction): `origin_node, dest_node, distance_km, method, source, url, retrieved_at, confidence`. Computed directly from `nodes.csv`'s coordinates, not looked up. Spot-checked against commonly cited great-circle figures (e.g. `MRSP`-`MRRJ` = 366.8 km, `MRSP`-`SBSV` = 1,462.9 km). |

## Airlines (ADR-0003)

| File | Owner | Rows | Contents |
|---|---|---|---|
| `groups.csv` | references agent | 50 (40 distinct ICAO codes) | `airline, group, start, end, class, note, source, url, confidence`. Encodes the merger/rename history exactly as specified in ADR-0003 (Varig group -> Gol 2007-04, Webjet independent then -> Gol 2011-11, Azul from 2008-12, Trip -> Azul 2012-05, Total -> Trip 2007-11 -> Azul 2012-05, Pantanal -> TAM 2009-12, TAM+BLC+SUL, Transbrasil to 2001-12, Vasp to 2005-01, Oceanair/Avianca Brasil, Passaredo) plus 21 further ICAO codes observed in the author's own VRA-derived research notes (private and not redistributed: the airline dummies of two research bases, read via those notes' own inspection output -- not from ANAC's raw VRA files directly), defaulted to `class=other`. No two rows for the same `airline` have overlapping `[start, end]` periods (checked programmatically when the table was built). `start=2000-01` is used as a "VRA panel begins" placeholder wherever the airline's own true start/founding date was not established this session -- it is **not** a claim about when the airline was founded. |

## IAC 1504 codes (ADR-0005)

Transcribed directly from the IAC 1504 text (30 Apr 2000, in force through
the VRA's "old layout" until its April-2020 revocation; see
`docs/notes/references.md` for the open question of what superseded it).
All rows `confidence=A`.

| File | Owner | Rows | Contents |
|---|---|---|---|
| `cause_codes.csv` | references agent | 49 | Every delay/cancellation/alteration/schedule-change justification code in IAC 1504's Annex 2: `code, description_pt, section, category, article_set, source, url, retrieved_at, confidence`. `section` is which of the Annex's four sub-lists the code belongs to (delay/cancellation/alteration/schedule_change). `category` is the second, ADR-0005 taxonomy (weather / airport_restricted / rotation / technical / operational / authorised / other). `article_set` flags the three columns the replicated article actually publishes (`prwheather`/16 codes, `princident`/5 codes, `pr_connc`/1 code, `none`/27 codes) using the exact code sets given in the brief -- deliberately not the same partition as `category` (ADR-0005 notes the article's `prwheather` itself merges weather with airport-restriction and rotation codes). |
| `di_codes.csv` | references agent | 12 | The "Digito Identificador" (DI) flight-type codes 0-9 plus letters A, B: `code, description_pt` (+ source/url/retrieved_at/confidence). This is ADR-0002's universe filter (DI==0). |
| `line_types.csv` | references agent | 8 | The "Natureza da Linha" (NAT LIN) codes I/N/R/E/L/H/C/G: `code, description_pt` (+ source/url/retrieved_at/confidence). |

## Calendar

| File | Owner | Rows | Contents |
|---|---|---|---|
| `holidays.csv` | references agent | 92 | National holidays 2000-2013 that exist by federal law: `date, name, law, url, source, retrieved_at, confidence`. 5/year (Jan 1, May 1, Sep 7, Nov 15, Dec 25) for 2000-2002; 7/year from 2003 on (adds Tiradentes and Finados, in force from Lei 10.607/2002, itself dated 2002-12-19 -- too late to apply retroactively to 2002's own Apr 21 / Nov 2). All rows `confidence=A` (Lei 662/1949 and Lei 10.607/2002 read in full at planalto.gov.br). Good Friday and Carnival are deliberately **excluded** here -- they are not national holidays by federal law -- see `observances.csv`. |
| `observances.csv` | references agent | 56 | Carnival Monday/Tuesday, Good Friday and Corpus Christi, 2000-2013 (14 years x 4 = 56 rows), flagged `type=observance`: `date, name, type, law, url, source, retrieved_at, confidence`. Dates are computed from Easter Sunday (Anonymous Gregorian / Meeus-Jones-Butcher algorithm), not looked up year by year; spot-checked against well-known Carnival dates (e.g. 2000-03-07, 2002-02-12). `confidence=B` throughout: the date arithmetic is deterministic, but the accompanying legal characterization ("Carnival is a discretionary executive `ponto facultativo`, not a federal holiday") is explicitly flagged as unverified-this-session in the author's research notes. |

## Events

| File | Owner | Rows | Contents |
|---|---|---|---|
| `events.csv` | references agent | 29 | `event, date, type, airlines, source, url, confidence, note`. Mergers (Gol-Varig, Gol-Webjet, TAM-Pantanal, TAM-LAN/LATAM, Azul-Trip), entries (Gol, Azul), exits (Transbrasil, Vasp), the 2006-2007 crisis ("apagao aereo": both fatal accidents plus the lab's own 2006m10-2007m12 period convention), an approximate 2008-2009 financial-crisis window, and the TAM-Varig codeshare (2003-2005, approximate). Where the author's research notes record genuinely divergent dates for the same fact (Vasp's bankruptcy decree: 2005, 2008 or 2013 depending on the source; TAM's Pantanal purchase: 19 or 21 Dec 2009), each version is kept as its own row with a `note`, not resolved into one. `airlines` is a `;`-separated list of ICAO codes (semicolon, not comma, so the field never needs CSV quoting). Only 4 of 29 rows are `confidence=A`. |

## Monograph (2013)

| File | Owner | Rows | Contents |
|---|---|---|---|
| `monograph_airports.csv` | theory layer | 38 | `icao, iata_as_printed, city_as_printed, uf, airport_name_as_printed, in_tables_3_4, note` (+ source/url/retrieved_at/confidence). A verbatim transcription of the "Lista de Siglas" of the author's 2013 undergraduate monograph (USP/ESALQ, Piracicaba) -- printed spellings kept as printed, including "São Luiz". `in_tables_3_4` is `True` for the 37 airports that also appear in that document's Tables 3 and 4 and `False` for the one that does not (`SBPS`, Porto Seguro). Three IATA codes differ from OurAirports (`CPQ`/`VCP` for SBKP, `PWM`/`PMW` for SBPJ, and `NAT` where the OurAirports record carries none, for SBNT); they are **annotated in `note`, not corrected** -- the table is a transcription of a document, not an airport register. `url` is deliberately blank: the source is a document, not a page. `scripts/monograph_airports.py` joins it to `nodes.csv` and prints the counts (38 listed, 37 in Tables 3-4, 31 in the ADR-0001 map covering all 27 nodes); the document itself is not redistributed -- see `docs/notes/monografia-2013.md` and `docs/data-availability.md` source 15. |

## Congestion and slots (ADR-0007)

Both tables were populated with a genuine WebSearch/WebFetch attempt this
session (beyond what the author's research notes already tried), not shipped as
bare headers -- but both remain thin. See `docs/notes/references.md` for
exactly what was tried and what is still open.

| File | Owner | Rows | Contents |
|---|---|---|---|
| `capacity.csv` | references agent | 1 | `icao, valid_from, valid_to, movements_per_hour, arrivals_per_hour, departures_per_hour, note, source, url, retrieved_at, confidence`. One row: Congonhas (`SBSP`), 33 movements/hour for commercial aviation after the 2007-07-17 TAM 3054 accident (`confidence=B`, convergent news retrospectives, no regulatory act opened directly). No pre-2007 figure, and no figure at all for `SBGR`/`SBRJ`/`SBBR`/`SBCF`/`SBKP`/`SBPA`/`SBCT`/`SBSV`/`SBRF`/`SBFZ` -- the BNDES/McKinsey (2010) study that ADR-0007 cites gives passengers/year by airport (2009), not movements/hour, so it does not belong in this table's numeric columns at all (see references.md). |
| `slots.csv` | references agent | 2 | `icao, coordinated_from, act, note, url, source, retrieved_at, confidence`. `SBGR` (Guarulhos, coordination process started 2009 per ANAC's own 2009 activity report, operating full IATA-conference slot allocation by 2010) and `SBRJ` (Santos Dumont, route restriction lifted and hour-distribution procedures published March 2009), both `confidence=A` (read directly from ANAC's "Relatorio de Atividades" PDFs via `pdftotext`). Congonhas, Recife and Brasilia are **not** in the table: Congonhas was clearly already under active slot management by April 2012 and was one of the three airports named in the original 2009 mandate alongside Guarulhos and Santos Dumont, but no specific act/date was found; Recife was not mentioned in any of the four ANAC annual reports checked (2009/2010/2012/2013); Brasilia appears to be "facilitated" rather than fully ANAC-coordinated on the current ANAC slot page, with no historical date found either way. |
