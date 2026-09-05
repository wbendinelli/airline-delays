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

`data/analysis/panel_route_month.parquet` (31,760 rows, 310 routes,
2000m1-2014m1) loads, filters and describes cleanly through the same code path:
restricted to the article's 2002m1-2013m12 window and put through the do-files'
own filters it gives 22,490 route-months over 211 routes, and Table 2
reproduces on 9 of its 13 variables — `fsc_oddsarr` averages -1.3844 against the
published -1.38 (ADR-0013 fixed this column to the article's own carrier set;
the class-based variant is `fscc_oddsarr`). What it does **not** carry is:

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
the arrival-delay proportion — 0.534 against **0.649** on the stable-vintage
half, where the reconstruction reported 0.651. The same holds for the minutes
columns: `fsc_minsarr` differs from the benchmark by a median of 0.060 minutes
and a p90 of 2.11, against the 0.07 and 2.2 the reconstruction reported for the
same approximation.

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
route — and the VRA only knows who *flew* it. The two agree on 88.9% of
route-months (0.920 on the stable-vintage half). The columns keep the article's
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

<!-- generated: gabarito-rates -->

Generated by `replication/gabarito/compare.py` on 2026-09-05 against 24,589 benchmark route-months. `rate` is the share of comparable route-months where the public value equals the benchmark's within the tolerance. Nothing below was tuned; where the rate is low, the difference is the finding.

| public column | benchmark column | rate | rate, stable vintage | expected | median abs diff | p90 abs diff | n | note |
|---|---|---|---|---|---|---|---|---|
| `f` | `f` | 0.901 | 0.953 | 0.975 | 0 | 0 | 24,929 |  |
| `fl_can` | `fl_can` | 0.937 | 0.948 | 0.978 | 0 | 0 | 24,929 |  |
| `fl_odel` | `fl_odel` | 0.854 | 0.877 | 0.924 | 0 | 1 | 24,929 |  |
| `fl_ddel` | `fl_ddel` | 0.561 | 0.560 |  | 0 | 12 | 24,929 | known to reproduce far below fl_odel (ADR-0002) |
| `ndays` | `ndays` | 1.000 | 1.000 |  | 0 | 0 | 24,929 |  |
| `dailyfl` | `dailyfl` | 0.901 | 0.953 |  | 0 | 3.815e-06 | 24,929 |  |
| `fsc_prdelarr` | `fsc_prdelarr` | 0.610 | 0.649 | 0.651 | 3.874e-07 | 0.02959 | 21,861 | FSC = the article's group set, without Avianca Brasil |
| `fscc_prdelarr` | `fsc_prdelarr` | 0.527 | 0.534 |  | 4.619e-07 | 0.04915 | 21,861 | FSC = class FSC, which includes Avianca Brasil |
| `fsc_prdelarr1530` | `fsc_prdelarr1530` | 0.585 | 0.618 |  | 3.874e-07 | 0.01818 | 21,861 |  |
| `fsc_prdelarr30m` | `fsc_prdelarr30m` | 0.597 | 0.637 |  | 3.874e-07 | 0.02273 | 21,861 |  |
| `fscc_prdeldep` | `fsc_prdeldep` | 0.556 | 0.559 |  | 4.321e-07 | 0.04137 | 21,861 |  |
| `fscc_oddsarr` | `fsc_oddsarr` | 0.513 | 0.521 |  | 4.917e-07 | 0.3293 | 20,956 |  |
| `fsc_minsarr` | `fsc_minsarr` | 0.238 | 0.271 |  | 0.06004 | 2.112 | 24,929 | same, on the article's FSC group set |
| `fscc_minsarr` | `fsc_minsarr` | 0.199 | 0.218 |  | 0.1 | 3.509 | 24,929 | denominator is every carrier's realised flights |
| `fsc_minsdep` | `fsc_minsdep` | 0.241 | 0.271 |  | 0.05 | 1.689 | 24,929 |  |
| `fscc_minsp15arr` | `fsc_minsp15arr` | 0.222 | 0.242 |  | 0.07692 | 2.344 | 24,929 |  |
| `all_prdelarr` | `all_prdelarr` | 0.482 | 0.476 |  | 0.0005075 | 0.01852 | 24,929 |  |
| `all_minsarr` | `all_minsarr` | 0.076 | 0.071 |  | 0.1479 | 4.126 | 24,929 |  |
| `lccfu_prdelarr` | `lccfu_prdelarr` | 0.561 | 0.532 |  | 4.172e-07 | 0.03571 | 19,509 | Gol and Azul, the article's LCC set |
| `lccclass_prdelarr` | `lccfu_prdelarr` | 0.514 | 0.474 |  | 4.768e-07 | 0.05218 | 19,509 | class LCC, which also holds Webjet |
| `prwheather` | `prwheather` | 0.882 | 0.919 | 0.985 | 2.757e-07 | 0.001358 | 24,929 |  |
| `princident` | `princident` | 0.923 | 0.955 | 0.991 | 1.267e-07 | 4.899e-07 | 24,929 |  |
| `pr_connc` | `pr_connc` | 0.913 | 0.945 | 0.992 | 1.639e-07 | 4.992e-07 | 24,929 |  |
| `lcc` | `lcc` | 0.889 | 0.920 |  | 0 | 1 | 24,929 | operation here, ticket sales in the benchmark |
| `pres_glo` | `pres_glo` | 0.881 | 0.908 |  | 0 | 1 | 24,929 | operation here, ticket sales in the benchmark |
| `pres_azu` | `pres_azu` | 0.956 | 0.937 |  | 0 | 0 | 24,929 | operation here, ticket sales in the benchmark |
| `pres_tam` | `pres_tam` | 0.914 | 0.928 |  | 0 | 0 | 24,929 | operation here, ticket sales in the benchmark |
| `olccfu` | `olccfu` | 1.000 | 1.000 |  | 0 | 0 | 24,929 |  |
| `dlccfu` | `dlccfu` | 1.000 | 1.000 |  | 0 | 0 | 24,929 |  |
| `maxalccfu` | `maxalccfu` | 1.000 | 1.000 | 1.000 | 0 | 0 | 24,929 |  |

<!-- /generated: gabarito-rates -->
