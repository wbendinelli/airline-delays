# Declared differences

Where this repository does not match the original article or the private
benchmark, the difference is stated here rather than adjusted away. The rule is
in `CLAUDE.md`: *"Fixing" a divergence against the benchmark by adjusting a
definition until the numbers match* is a policy violation, not an improvement.
`DECISIONS.md` ADR-0010 governs how a genuine disagreement between two defensible
options is resolved.

Every number below is printed by a versioned script; the "Evidence" column names
the file that prints it. Nothing here is typed from memory.

## Reconstruction (data layer)

Summarised in the README's "Declared differences" section: the asymmetry between
departure- and arrival-delay counts against the benchmark, `prwheather` folding
airport restrictions in with weather (ADR-0005), and `prcongested` not yet
reproduced for want of ANAC's seasonal capacity declarations (ADR-0007). See
`reports/reconciliation.md` and `docs/notes/staging.md`.

## Replication (Tables 2-7)

Produced by `uv run python -m replication.run --source private`; the full
side-by-side is `reports/replication/tables.md` and the Portuguese discussion is
`docs/notes/replication.md`.

Across the five regression tables, 306 coefficients are compared: 302 agree in
sign, 259 (85%) sit within half a published standard error, and the largest
single gap is 0.94 published standard errors. No conclusion of the article
changes. What does not close:

| # | What differs | Size | Cause, as far as the evidence goes |
|---|---|---|---|
| 1 | **N** | Every column is 5.31% larger on arrivals (20,450 against 19,419 in the ODDS columns; 20,630 against 19,590 in the MINS columns) and 5.35% larger on departures (20,447 against 19,408; 20,627 against 19,579) | Not explained by the delivered material. Applying the do-files' own filters — `drop if fsc_oddsarr==.` then `drop if _count_k<=5` — to the benchmark panel gives 20,630 rows over 190 routes, and the Table 2 descriptives match the published ones to the fourth decimal *on those 20,630 rows*. Either the undelivered `gregrun` `.ado` imposes a further restriction, or the delivered panel is a slightly different vintage from the one behind the published run. This is the dominant cause of everything below. |
| 2 | **J statistic (Hansen)** | Table 3 column 1: 1.7234 against 3.1132; column 3: 0.7926 against 0.2161. Moves in both directions across the 24 columns that report it | Sample (row 1), amplified by the J being a quadratic form on 1 or 3 degrees of freedom, so its sampling variability is large by construction. **No verdict changes**: in all 24 columns the replicated test reaches the same conclusion as the published one at the 5% level — 22 do not reject orthogonality and the same 2 (Table 4 columns 3 and 5) do. |
| 3 | **Adj. R-squared and RMSE in the MINS columns** | Table 3: 0.4833 against 0.4546, 0.4875 against 0.4629, 0.4715 against 0.4374, 0.4752 against 0.4456; RMSE 5.89-5.92 against 6.12-6.23 | The replication fits *better*, consistently, which points to a published sample carrying more hard-to-fit rows — coherent with the undocumented extra cut of row 1. In the ODDS columns the same statistics are nearly exact (0.6713 against 0.6801; RMSE 0.5900 against 0.5889). |
| 4 | **F statistic** | Not reproduced in any column | `ivreg2`'s F is the joint Wald test over all ~340 regressors under its own small-sample convention; `linearmodels` computes an analogue under a different one. Reporting it would be comparing two different quantities, so the cell is left empty rather than filled with a number that does not mean what the published one means. Every other statistics row of every table is reproduced. |
| 5 | **Identification statistics (KP, Weak KP, Weak CD)** | Always above the published value, never below. ODDS/ODDSD columns: rk LM +3.3% to +6.4%, Weak KP +5.9% to +9.3%, Weak CD +12.6% to +13.9%. MINS/MINSD columns: rk LM +18.7% to +31.0%, Weak KP +22.9% to +35.8%, Weak CD +32.3% to +46.4% (12 columns each) | Sample (row 1). The gap is larger in the MINS columns because 3 instruments against 2 endogenous regressors is nearly exact identification, where the statistic is very sensitive to N. The implementation itself is validated independently: under i.i.d. errors the rk Wald collapses exactly to Cragg-Donald and the rk LM to Anderson (`tests/test_replication_kp.py`). |
| 6 | **Standard errors** | Systematically smaller: median ratio 0.94 (Table 3) to 0.99 (Table 4); 51 of 60 below the published value in Table 3, range 0.79 to 1.14 | Sample (row 1) — a 5.3% larger N pushes standard errors down — plus the HAC kernel, which in `linearmodels` measures lags in row order and lets autocovariances cross route boundaries in an unbalanced panel. The panel-aware alternative is implemented (`replication/kp.hac_moment_cov`) and its effect is second-order. |
| 7 | **Four sign disagreements out of 306** | Table 4 column 5 `dailyflncong` (+0.0007 against -0.0003), Table 5 column 2 `lcc` (-0.0280 against +0.0100), Table 6 column 6 `dailyflcong` (+0.0010 against -0.0018), Table 7 column 1 `cshare` (-0.0053 against +0.0092) | All four are coefficients the article itself reports as statistically indistinguishable from zero, and all four sit within 0.52 published standard errors of the published value. A sign flip inside the noise band is not a disagreement about a result. |
| 8 | **Seasonality dummies `sz_*`** | Moves the headline coefficients by about 0.02-0.05 in level (Table 3 column 1 `rthhi`: 0.8843 with, 0.8661 without) | Irreducible without the `gregrun` `.ado`: `dummymonthreg` creates the 60 region x month dummies and `gregcontrols` never lists them. Resolved by approximation to the published values, not by evidence, and reported both ways in the sensitivity table (`reports/replication/sensitivity.json`). |
| 9 | **Outlier-threshold sensitivity is unavailable on the private source** | Two of the three ADR-0008 thresholds cannot be computed | The threshold applies to flight-level delays before aggregation; the benchmark panel is delivered already aggregated under a rule its authors never documented. The rows are reported as *unavailable* rather than approximated, and fill in automatically once the public panel ships the suffixed regressand variants (`replication.common.regressand_column`). |

## The public panel cannot yet estimate the regression tables

`data/analysis/panel_route_month.parquet` (31,313 rows, 310 routes, the 168
months 2000m1-2013m12) loads, filters and describes cleanly through the same code
path. Restricted to the article's 2002m1-2013m12 window (3,803 rows drop) and put
through the do-files' own filters — `drop if fsc_oddsarr==.` (5,913 more) then
`drop if _count_k<=5` (31 more) — it gives **21,566 route-months over 207 routes
and 144 months**, which is the sample `reports/replication/public/tables.md`
prints under "Table 2" and which
`replication.common.build_sample("public").attrs["filters"]` recomputes on
demand. Both numbers are generated on 2026-09-05 from the same panel; an earlier
draft of this file quoted 22,490 route-months over 211 routes from a panel built
before ADR-0016 removed the duplicated route-months and before ADR-0015 made the
outlier cut symmetric.

Of the 13 descriptive variables of Table 2 this panel computes 7. Six of them now
land close to the published values: the weather, incident and late-connection
shares; `fsc_oddsarr` averaging -1.3927 against the published -1.38 (ADR-0013
fixed this column to the article's own carrier set; the class-based variant is
`fscc_oddsarr`); `LCC presence max endpoint cities` 0.9915 against 1.00; and the
`MINS` regressand, 6.8632 against 7.16, standard deviation 8.79 against 8.29,
range -106.5 to 136.5 against -9.80 to 131.91. `MINS` is the one that changed:
under the one-sided outlier cut it averaged **-1.3404** with a standard deviation
of **125** and a minimum of **-4,772** minutes, because the cut trimmed the late
tail and let the negative month typos of ADR-0015 straight through. The seventh,
`LCC presence city-pair`, still reads 0.7761 against 0.90 published — the
operation-against-ticket-sales difference of section 5 below, not an outlier
problem. What the panel does **not** carry is:

- `maxprdel`, `cshare`, `dailyflcong` and `dailyflncong` — absent. Codeshare is
  not in the VRA at all; the congested/uncongested split needs the declared
  hourly capacity of ADR-0007, which has not been collected.
- the seven Hausman-type instruments (`h1_maxcthhi`, `h2_maxcthhi`,
  `h3_maxcthhi`, `lnh1_maxcthhi`, `l1h1_maxcthhi`, `l1h2_maxcthhi`,
  `h2_rthhi`) — absent, and not reconstructible from the delivered material
  (the inter-city distance matrix, the "nearby city" rule and the weights were
  never delivered).
- `rthhi` and `maxcthhi` — present as columns but entirely null. The panel ships
  `rthhi_flights` and `maxcthhi_flights`, which are concentration indices over
  *flights* rather than the article's measure. **They are not substituted in.**
  A near-equivalent column standing in for a published variable is exactly the
  adjustment `CLAUDE.md` forbids, so the affected columns report the variable as
  missing instead.

Consequently `just replicate` (public) today produces Table 2 and a written list
of the five regression tables it cannot estimate, with the variables each one
needs. `just replicate private` produces the full comparison. Nothing about the
code changes when the panel gains those variables.

## Not attempted, and why

- **Rebuilding the benchmark panel itself.** No script exists between the raw
  data and the authors' final panel; 14 intermediate files were never delivered.
  This replication starts from the delivered panel and says so.
- **The Hausman-type instruments.** Reconstructing them needs the distance
  matrix between the 27 cities, the "nearby city" rule and the weighting
  formula, none of which were delivered. The instruments are taken from the
  panel as given.
- **`_tab7.do`.** It swaps a passenger-weighted city HHI in for `maxcthhi` and
  corresponds to no published table — the article mentions the check in one
  sentence and never tabulates it.

## Panel and feature layer

Written by `just features` and `just panel`; measured against the private
benchmark by `replication/gabarito/compare.py`, whose output is the generated
table at the end of this file. Portuguese discussion in
`docs/notes/features.md`.

### 1. The raw files are not the ones the benchmark was built from

This is the largest single cause of every rate below, and it is not a
definition at all. The earlier reconstruction (`reconstrucao-vra.md`) read the
**2019 vintage** of the VRA — the same `vra.dta` the benchmark panel itself was
built from — and reported 97.5% agreement on `f`. This repository rebuilds
everything from the files ANAC publishes today, and
`reports/reconciliation.md` measures the two vintages differing by up to 48,215
flight rows in a single month.

The two questions separate cleanly. Splitting the 144 months on the median of
their relative row difference and measuring `f` in each quartile gives 0.94,
0.96 and 0.97 in the three quieter ones against **0.74** in the noisiest, with a
correlation of -0.45 between the agreement rate and the size of the vintage
drift. `taxas.csv` therefore reports two rates per column: `rate` over the whole
panel, and `rate_stable_vintage` over the quieter half, which is the
like-for-like comparison with the reconstruction. Where they disagree, the
vintage is the reason.

The disagreements are also *small*: on `f` and `fl_can` both the median and the
90th percentile of the absolute difference are **zero flights**, and on
`fl_odel` the 90th percentile is one flight. The panel is not systematically
off; it differs on a minority of route-months by a flight or two.

### 2. `fscc_*` uses the FSC **class**, and the article used an FSC **group set**

ADR-0003 classes Avianca Brasil (ICAO `ONE`) as FSC; the article's FSC set is
the four groups TAM, Varig, Transbrasil and Vasp, and excludes it. Both are
computed and both are published: `fscc_*` on the class, `fsc_*` on the
article's set (ADR-0013). The difference is worth 11 points of agreement on
the arrival-delay proportion — 0.535 against **0.651** on the stable-vintage
half, exactly the 0.651 the reconstruction reported. The same holds for the
minutes columns: `fsc_minsarr` differs from the benchmark by a median of 0.058
minutes and a p90 of 1.68, against the 0.07 and 2.2 the reconstruction reported
for the same approximation — the p90 was 2.11 before ADR-0015 made the outlier
cut symmetric (section 8).

Read the other way: with the article's own carrier set, this pipeline
reproduces the benchmark's FSC delay columns to the same accuracy as the
reconstruction that had the private raw data. The `fscc_*` gap is a **choice
of carrier set**, not a defect in the delay definitions.

The same shape applies to `lccclass_*` (class LCC, which holds Webjet while it
was independent) against `lccfu_*` (the article's Gol-and-Azul set).

### 3. Missing actual times: `legacy_missing_actual_as_zero` (ADR-0012)

In the 2000-2009 files a realised flight with no reported occurrence has empty
actual times — **59% to 80% of realised flights each year**, against 0.0% from
2010 on (`data/analysis/manifest.json`). The 2019 vintage read empty as "on
schedule"; the staged data keeps nulls.

The flag changes exactly one thing, and the test suite pins it: the
**denominator** of every delay proportion and mean. It moves no count and no sum
— a flight imputed at 0 minutes is not "more than 0 minutes late" and adds
nothing to a sum of minutes. `True` is the panel's default, because the panel
has to reproduce a benchmark built under that convention; `False` is the
repository's own reading and what the prediction layer uses. The value in force
travels with the table as the `legacy_missing_actual_as_zero` column.

Under `False`, arrival-delay rates for 2000-2009 are computed over the 20-40% of
realised flights that had an occurrence — a sample selected on having had one —
and come out far above the published figures. That is not a better number; it
is a different question, and it is why both conventions exist.

**The prediction half of this decision was superseded by ADR-0017**, which reads
the empty field as *no alteration reported* rather than as unknown; see section 9.
The panel is unchanged: it still has to reproduce a benchmark built under the
vintage's convention, and `legacy_missing_actual_as_zero=True` is what does that.

### 4. Signed delays against the vintage's truncation (ADR-0008)

The 2019 vintage stored `delarrive = max(actual - scheduled, 0)`, with no
negative value in 10.77 million comparable rows. This repository keeps early
arrivals negative. Threshold counts are unaffected — `max(x, 0) > 15` and
`x > 15` are the same test — so `fl_odel`, `fsc_prdelarr` and every `sh_*` share
are comparable across the two conventions. Sums of minutes are not, so the panel
publishes both: `fsc_minsarr` signed, `fsc_minsarr_trunc` truncated, and the
same pair on the departure side.

### 5. `lcc`, `pres_glo`, `pres_azu`, `pres_tam`: operation, not ticket sales

The benchmark reads these from the tariff base — who *sold tickets* on the
route — and the VRA only knows who *flew* it. The two agree on 88.8% of
route-months (0.919 on the stable-vintage half). The columns keep the article's
names so the comparison is possible; the source difference is not closed. The
city-level dummies, which the article does take from operations, agree on
**100%** of route-months (`maxalccfu`).

### 6. What the VRA cannot produce, published as null

`rthhi`, `maxcthhi` and `gmchhi` are concentration over paid passengers, which
lives in ANAC's statistical data and not in an operations file; `prcongested`
needs declared hourly capacity, of which `data/external/capacity.csv` holds one
airport (ADR-0007). All four are present and entirely null. The
flight-based indices ship next to them under different names — `rthhi_flights`,
`maxcthhi_flights`, `gmchhi_flights` — and the p90 congestion proxy as
`o_sh_movements_congested` / `d_sh_movements_congested`. Substituting one for
the other under the published name is the adjustment `CLAUDE.md` forbids.

The article's `pr_odel`, `pr_ddel` and `maxprdel` are not reproduced at all: the
reconstruction tested over forty candidate definitions and none matched. The
panel carries `maxprdel_proxy` under a name that says what it is.

### 7. `fl_ddel` reproduces at 0.56 where `fl_odel` reproduces at 0.88

Unchanged from ADR-0002 and still unexplained. Both columns use the same rule —
realised flights more than 0 minutes late — on the same universe, and the
arrival side reproduces far worse, with a 90th-percentile difference of 12
flights against 1 for departures. Month-of-arrival keys, midnight rollovers and
alternative cut points were tested by the earlier reconstruction and rejected.
Declared, not resolved.

### 8. City aggregates are computed over the panel network

`city_month` counts movements on routes whose **both** endpoints are among the
27 nodes of ADR-0001, because that is what reproduces the benchmark's city
dummies exactly (`olccfu`, `dlccfu` and `maxalccfu` at 100%). A city's true
movement count includes routes to airports outside the panel; the columns
therefore measure the city's presence *in this network*, not its total traffic.

### 9. The outlier cut is symmetric, and month typos are flagged (ADR-0015)

The laboratory scripts cut delays at `delay < 313.25`, one-sided. The raw files
carry month typos in the actual times — VSP 4374 in December 2003 has an actual
arrival dated November, `-43,170` minutes — and a one-sided cut trims the late
tail while letting every negative typo through. It reached the published panel:
133 route-months had |FSC minutes| above 200, the minimum was `-4,772`, and the
`MINS` regressand of Table 2 came out at -1.34 with a standard deviation of 125
against a published 7.16 and 8.29.

ADR-0015 applies the threshold to `abs(delay)` in every sum, mean and share of
minutes, on both sides. Counts of delayed flights do not move — `x > 15` is the
same test whatever the tail rule — so `fl_odel`, `fsc_prdelarr` and every `sh_*`
share are unchanged. What changes is the tails of the minutes columns: on the
regenerated panel `fsc_minsarr` runs from `-239.90` to `226.27` (1st percentile
`-4.97`, 99th `38.45`), inside `±313.25` by construction, and its 90th-percentile
distance from the benchmark falls from 2.11 to 1.68 minutes; `all_minsarr`'s
falls from 4.13 to 2.49. Staging additionally writes `actual_time_suspect` for a
row whose departure or arrival delay is a whole calendar day or more
(|delay| >= 1,440 minutes), and the prediction dataset keeps those rows but takes
them out of every target, counted per year.

This is a **correction of an implementation**, not a change of definition: the
threshold is still ADR-0008's 313.25 minutes, still a named parameter, still
shipped with a sensitivity table.

### 10. Route-month keys are unique, and the panel is exactly 168 months (ADR-0016)

`data/staged/` is partitioned by the year of the **source file**; `year` and `ym`
come from `flight_date`, the scheduled departure. They disagree on 3,723 rows of
13,652,322 (`docs/notes/staging.md` section 5): mostly a December file carrying
legs scheduled for 1 January, plus a few typed years (2099, 2020, 2088). The
first public build grouped inside each directory and concatenated the results, so
a route-month present in two directories was emitted twice: 844 rows over 422
`(group, route, ym)` keys in the fact table and, through the route-month context
join, **866 rows over 433 `(route, ym)` keys in the panel** — the copies carrying
equal flight counts and different `n_rows_all`, `n_extra`, `sh_extra` and
order statistics, because each copy's median was taken over part of its flights.

`build_fact` now selects each **calendar year** across the whole staged tree
(`vra.features.year_source_sql`) and asserts uniqueness on the way out; `panel.py`
asserts it again on the way in. Rows dated outside the built years are counted in
`data/analysis/manifest.json` under `rows_outside_years` rather than folded into a
neighbour: 69 rows dated 2014 (18 of them in the replication universe, legs
scheduled for 1 January 2014 that sit in the December 2013 file), 239 with a typed
year, none of which is in the universe, and 2,100 with no date at all. The panel
therefore covers **exactly the 168 months 2000m1-2013m12**; the 2014m1 month that
the first build published, on a handful of routes and 18 flights, is gone.

Effect on the benchmark comparison: 24,551 comparable route-months instead of
24,929, and every rate moves by less than a point — `f` from 0.901 to 0.902,
`fl_odel` from 0.854 to 0.857, `fsc_prdelarr` from 0.610 to 0.612, `prwheather`
from 0.882 to 0.884. Nothing here was tuned; the duplicated rows were being
compared twice.

### 11. Empty actual times mean "no alteration reported" (ADR-0017, prediction only)

**The rule.** IAC 1504 sets up an *exception* system. The Boletim de Alteração de
Vôo is issued "sempre que houver alguma alteração em seus vôos regulares"
(introduction) and "será emitido um boletim para cada dia em que ocorra
alteração" (§3.1); the realised times and the justification code are fields of
that boletim (§4.2 n, o, p); the SITAR is filled "diariamente, para todas as
alterações verificadas" (§5.1); and annex 2 contains codes for delay,
cancellation and schedule change — none for "operated on schedule". An empty
actual time on a realised flight of the 2000-2009 layout is therefore the absence
of a reported alteration, and the empty justification code is the same fact, not
a second piece of evidence.

**The scope.** Reading B is applied only to realised flights of years up to 2009
whose carrier class in `data/external/groups.csv` is FSC, LCC or regional. For
`other` and unlabelled carriers the empty field stays unknown and the flight
keeps no delay target: the null rate is not one convention but many, and IAC 1504
art. 6.6 says that in a code-share only the operating carrier reports and the
non-operator's leg has no effect on the indices. Measured over 2000-2009 in the
replication universe, the null actual-arrival rate is **72.9%** for the 5,106,122
realised flights in scope and **83.0%** for the 313,368 out of it; within the
scope it ranges from 65.5% (`GLO`) and 66.0% (`VRG`) to 75.5% (`TAM`) and 81.0%
(`VSP`), and among the eight largest carriers out of it from 65.0% (`PEP`) to
92.8% (`RLE`). The sceptical reviewer's own 2005 cross-section,
taken over *all* flights rather than this universe, found 90-100% for foreign
carriers and code-share legs (`docs/notes/colegiado-adr0012.md`). The generated
table at the end of this file gives the rate by carrier and year; 260,190 of the
out-of-scope flights have no actual arrival time.

**The direction of the residual bias.** Reading B is a **floor on punctuality**: a
delay that the carrier never reported counts as on time, so the pre-2010 late
rate this repository publishes is a lower bound. Reading A is not the neutral
alternative — it conditions on the outcome, keeping only the flights that had an
occurrence, which is endogenous selection over half the sample. Both readings are
declared and the headline metrics are published under each
(`reports/prediction/results.md`, "Sensitivity: reading A against reading B").
The reading-A run is preserved rather than re-estimated:
`reports/prediction/rolling_reading_A.json` holds its rolling-origin folds and
`reports/prediction/dataset_reading_A.json` its per-year accounting, where the
pre-2010 target rows are the 116,491 to 209,328 flights that had an occurrence
instead of the 410,046 to 665,407 reading B admits.

**The layout break stays a comparability break.** From 2010 the files carry an
actual time on essentially every realised flight (0.0% missing against 59-80%
before), so 2010 onwards is the same quantity under both readings and the earlier
years are not. A metric compared across 2009 and 2010 is compared across a change
of instrument, whichever reading is in force.

**What does not change.** The replication panel, `data/analysis/taxas.csv` and
every number in the sections above: they run under the vintage's own convention
(`legacy_missing_actual_as_zero=True`, section 3), which is what reproduces the
benchmark. ADR-0017 supersedes only the prediction half of ADR-0012. The
`fl_ddel` / `fl_odel` asymmetry of section 7 is untouched and still unexplained.

<!-- generated: gabarito-rates -->

Generated by `replication/gabarito/compare.py` on 2026-09-05 against 24,589 benchmark route-months. `rate` is the share of comparable route-months where the public value equals the benchmark's within the tolerance. Nothing below was tuned; where the rate is low, the difference is the finding.

| public column | benchmark column | rate | rate, stable vintage | expected | median abs diff | p90 abs diff | n | note |
|---|---|---|---|---|---|---|---|---|
| `f` | `f` | 0.902 | 0.953 | 0.975 | 0 | 0 | 24,551 |  |
| `fl_can` | `fl_can` | 0.938 | 0.949 | 0.978 | 0 | 0 | 24,551 |  |
| `fl_odel` | `fl_odel` | 0.857 | 0.879 | 0.924 | 0 | 1 | 24,551 |  |
| `fl_ddel` | `fl_ddel` | 0.564 | 0.563 |  | 0 | 12 | 24,551 | known to reproduce far below fl_odel (ADR-0002) |
| `ndays` | `ndays` | 1.000 | 1.000 |  | 0 | 0 | 24,551 |  |
| `dailyfl` | `dailyfl` | 0.902 | 0.953 |  | 0 | 3.815e-06 | 24,551 |  |
| `fsc_prdelarr` | `fsc_prdelarr` | 0.612 | 0.651 | 0.651 | 3.8e-07 | 0.02901 | 21,506 | FSC = the article's group set, without Avianca Brasil |
| `fscc_prdelarr` | `fsc_prdelarr` | 0.530 | 0.535 |  | 4.619e-07 | 0.04839 | 21,506 | FSC = class FSC, which includes Avianca Brasil |
| `fsc_prdelarr1530` | `fsc_prdelarr1530` | 0.587 | 0.619 |  | 3.874e-07 | 0.01793 | 21,506 |  |
| `fsc_prdelarr30m` | `fsc_prdelarr30m` | 0.599 | 0.638 |  | 3.874e-07 | 0.02233 | 21,506 |  |
| `fscc_prdeldep` | `fsc_prdeldep` | 0.559 | 0.561 |  | 4.321e-07 | 0.04063 | 21,506 |  |
| `fscc_oddsarr` | `fsc_oddsarr` | 0.515 | 0.523 |  | 4.768e-07 | 0.3269 | 20,607 |  |
| `fsc_minsarr` | `fsc_minsarr` | 0.240 | 0.273 |  | 0.05797 | 1.684 | 24,551 | same, on the article's FSC group set |
| `fscc_minsarr` | `fsc_minsarr` | 0.201 | 0.220 |  | 0.09646 | 2.866 | 24,551 | denominator is every carrier's realised flights |
| `fsc_minsdep` | `fsc_minsdep` | 0.244 | 0.274 |  | 0.04861 | 1.211 | 24,551 |  |
| `fscc_minsp15arr` | `fsc_minsp15arr` | 0.224 | 0.244 |  | 0.075 | 2.311 | 24,551 |  |
| `all_prdelarr` | `all_prdelarr` | 0.485 | 0.478 |  | 0.0004588 | 0.01818 | 24,551 |  |
| `all_minsarr` | `all_minsarr` | 0.079 | 0.073 |  | 0.1369 | 2.486 | 24,551 |  |
| `lccfu_prdelarr` | `lccfu_prdelarr` | 0.562 | 0.533 |  | 4.172e-07 | 0.03571 | 19,195 | Gol and Azul, the article's LCC set |
| `lccclass_prdelarr` | `lccfu_prdelarr` | 0.515 | 0.475 |  | 4.768e-07 | 0.05201 | 19,195 | class LCC, which also holds Webjet |
| `prwheather` | `prwheather` | 0.884 | 0.920 | 0.985 | 2.757e-07 | 0.001242 | 24,551 |  |
| `princident` | `princident` | 0.925 | 0.957 | 0.991 | 1.267e-07 | 4.871e-07 | 24,551 |  |
| `pr_connc` | `pr_connc` | 0.915 | 0.947 | 0.992 | 1.621e-07 | 4.945e-07 | 24,551 |  |
| `lcc` | `lcc` | 0.888 | 0.919 |  | 0 | 1 | 24,551 | operation here, ticket sales in the benchmark |
| `pres_glo` | `pres_glo` | 0.880 | 0.907 |  | 0 | 1 | 24,551 | operation here, ticket sales in the benchmark |
| `pres_azu` | `pres_azu` | 0.955 | 0.936 |  | 0 | 0 | 24,551 | operation here, ticket sales in the benchmark |
| `pres_tam` | `pres_tam` | 0.913 | 0.927 |  | 0 | 0 | 24,551 | operation here, ticket sales in the benchmark |
| `olccfu` | `olccfu` | 1.000 | 1.000 |  | 0 | 0 | 24,551 |  |
| `dlccfu` | `dlccfu` | 1.000 | 1.000 |  | 0 | 0 | 24,551 |  |
| `maxalccfu` | `maxalccfu` | 1.000 | 1.000 | 1.000 | 0 | 0 | 24,551 |  |

<!-- /generated: gabarito-rates -->

<!-- generated: null-actual-by-carrier -->

Generated by `uv run python scripts/null_actual_by_carrier.py` on 2026-09-05 over `data/staged/`. Share of **realised** flights of the replication universe with no actual arrival time, by carrier and year, for the 10 years of the legacy layout; the 25 carriers with the most realised flights in that window. From 2010 the rate is 0.0% for every carrier. Nothing here is imputed: the cell is the share the raw files carry.

| carrier | class | realised | 2000 | 2001 | 2002 | 2003 | 2004 | 2005 | 2006 | 2007 | 2008 | 2009 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `TAM` | FSC | 1,747,743 | 0.769 | 0.702 | 0.824 | 0.836 | 0.888 | 0.792 | 0.689 | 0.576 | 0.726 | 0.827 |
| `GLO` | LCC | 1,086,986 | -- | 0.753 | 0.773 | 0.773 | 0.723 | 0.671 | 0.674 | 0.491 | 0.622 | 0.688 |
| `VRG` | FSC/LCC | 657,495 | 0.745 | 0.707 | 0.626 | 0.674 | 0.655 | 0.596 | 0.562 | 1.000 | -- | -- |
| `VSP` | FSC | 330,568 | 0.841 | 0.811 | 0.839 | 0.804 | 0.736 | 0.265 | -- | -- | -- | -- |
| `RSL` | FSC | 291,221 | 0.837 | 0.794 | 0.704 | 0.722 | 0.638 | 0.716 | 0.583 | -- | -- | -- |
| `TIB` | regional | 165,556 | 0.749 | 0.528 | 0.744 | 0.593 | 0.955 | 0.975 | 0.971 | 0.948 | 0.963 | 0.876 |
| `NES` | FSC | 139,894 | 0.769 | 0.821 | 0.707 | 0.660 | 0.609 | 0.105 | 0.602 | -- | -- | -- |
| `ONE` | FSC | 126,231 | -- | -- | -- | 0.754 | 0.639 | 0.555 | 0.540 | 0.535 | 0.642 | 0.835 |
| `PTN` | regional | 105,247 | 0.731 | 0.747 | 0.774 | 0.796 | 0.629 | 0.595 | 0.735 | 0.886 | 0.672 | 0.743 |
| `RLE` | other | 84,517 | 0.948 | 0.981 | 0.981 | 0.955 | 0.904 | 0.931 | 0.881 | 0.849 | 0.829 | 0.783 |
| `VRN` | FSC/LCC | 80,615 | -- | -- | -- | -- | -- | -- | 0.582 | 0.478 | 0.597 | 0.749 |
| `TTL` | regional | 72,373 | 0.829 | 0.644 | 0.747 | 0.802 | 0.717 | 0.614 | 0.685 | 0.754 | -- | -- |
| `BLC` | FSC | 66,998 | 0.798 | -- | -- | -- | -- | -- | -- | -- | -- | -- |
| `TBA` | FSC/other | 63,094 | 0.893 | 0.800 | 1.000 | -- | -- | -- | -- | -- | -- | -- |
| `PTB` | regional | 54,805 | 0.892 | 0.919 | 0.911 | -- | 0.969 | 0.944 | 0.920 | 0.989 | 0.947 | 0.923 |
| `WEB` | LCC | 49,304 | -- | -- | -- | -- | -- | 0.657 | 0.601 | 0.535 | 0.641 | 0.739 |
| `ITB` | FSC/other | 46,323 | 0.873 | 0.885 | 1.000 | -- | -- | -- | -- | -- | -- | -- |
| `PEP` | other | 32,803 | 0.619 | 0.700 | 0.634 | 0.818 | 0.521 | -- | -- | -- | -- | -- |
| `MSQ` | other | 30,470 | 0.843 | 0.877 | 0.918 | 0.828 | 0.841 | 0.887 | 0.725 | 0.997 | 0.951 | 0.424 |
| `NHG` | other | 26,189 | -- | -- | -- | -- | -- | -- | -- | 0.698 | 0.752 | 0.708 |
| `AZU` | LCC | 24,637 | -- | -- | -- | -- | -- | -- | -- | -- | 0.723 | 0.888 |
| `SLX` | other | 22,457 | -- | -- | -- | -- | -- | -- | -- | 0.715 | 0.659 | 0.688 |
| `BRB` | other | 21,910 | -- | -- | -- | -- | -- | -- | 0.793 | 0.867 | -- | -- |
| `TVJ` | other | 18,309 | 0.847 | 0.955 | 0.955 | 0.923 | 0.950 | 1.000 | -- | -- | -- | -- |
| `PLY` | other | 14,225 | -- | -- | 0.960 | 0.863 | 0.903 | 0.878 | 0.894 | 0.494 | 0.673 | -- |

Reading B covers **5,106,122** realised flights of 2000-2009 (class FSC, LCC or regional). It leaves **313,368** out of scope, flown by 20 carriers whose class is `other` or unlabelled; **260,190** of those have no actual arrival time and therefore no delay target under either reading. Full detail, every carrier and every year: `reports/prediction/null_actual_by_carrier.csv`.

<!-- /generated: null-actual-by-carrier -->
