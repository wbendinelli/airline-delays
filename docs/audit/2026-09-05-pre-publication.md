# Pre-publication audit — 2026-09-05

Independent audit of `airline-delays` at commit `d993b74` (14 commits, working
tree clean at the start of the audit). The auditor did not build this
repository; every claim in `README.md`, `DECISIONS.md`, `docs/` and `reports/`
was treated as something to verify with a command or a file read. Nothing was
fixed.

Environment: macOS (Darwin arm64), Python 3.12.13, `uv` with `uv.lock`,
`just` 1.58.0, `gh` 2.93.0, `node` for the SAPIANS doclint copy.

**Method.** Two working copies were used. A fresh clone at
`…/scratchpad/audit-clone`, created with
`git clone /Users/wbendinelli/Documents/airline-delays …`, stands in for a
stranger's checkout and was run with `AIRLINE_DELAYS_PRIVATE_DIR` **unset**
throughout. The original repository was used only for the `gabarito` tests,
with the variable exported inline in the audit shell and never written to any
file.

Findings are ranked blocker / major / minor. Section 7 records what passed.

---

## 1. Blockers

### B-1 · `uv run pytest -q` fails on a fresh clone; CI will be red on first push

```
$ git clone /Users/wbendinelli/Documents/airline-delays …/audit-clone
$ cd …/audit-clone && uv sync --group dev     # 0.53 s wall, 0 errors
$ uv run pytest -q
_ TestMeasuredAgainstDeclared.test_measured_layout_matches_the_declaration[2002] _
>       assert measured["line_ending"] == declared.line_ending
E       AssertionError: assert 'lf' == 'crlf'
E         - crlf
E         + lf
tests/test_io.py:55: AssertionError
1 failed, 335 passed, 5 skipped, 16 deselected, 1 warning in 14.29s
```

The same command in the original working tree passes
(`340 passed, 1 skipped, 16 deselected in 5.11s`), which is why the failure has
not been seen before.

Root cause — `.gitattributes` line 4 normalises the legacy fixture's line
endings away:

```
$ cat .gitattributes | head -4
* text=auto eol=lf
*.parquet binary
*.csv.gz binary
*.csv text eol=lf          <-- forces LF on checkout

$ # working tree (original) vs the same file in a fresh clone
tests/fixtures/vra_raw_sample_2002.csv: CRLF= 3001  bare LF= 0     size= 235640
…/audit-clone/…/vra_raw_sample_2002.csv: CRLF= 0     bare LF= 3001  size= 232639
```

235,640 − 232,639 = 3,001 bytes, exactly the number of CR characters. The blob
stored in git already has LF, so **every** fresh checkout loses the CRLF —
including `actions/checkout` in the `test` job of `.github/workflows/ci.yml`,
which runs this exact command. The original tree still holds CRLF only because
that file predates the attribute taking effect.

This is not a cosmetic issue: `tests/conftest.py` states the intent explicitly —
the fixtures are *"cut byte for byte from the real ANAC files (so latin-1,
**CRLF**, `N/A` and the free-text 2010 layout are all exercised)"*. The
`.gitattributes` rule destroys the one property the 2002 fixture exists to
test, and `src/vra/io.py`'s declared layout for 2000-2009 (`crlf`) is therefore
unverified for anyone but the author.

### B-2 · Absolute paths into the private research archive are committed in `data/external/`

The check requested in the brief:

```
$ git grep -n -i "pesquisa-acervo\|proj18\|labtar\|nectarbase\|_recebidos"
```

Most hits are intentional prose (README, SECURITY.md, CLAUDE.md declaring the
private benchmark as an omission). Two are not:

```
$ git grep -oh "file:///Users/[^,\"]*" | sed 's|\(file:///Users/[^/]*/[^/]*/[^/]*\).*|\1|' | sort | uniq -c
  13 file:///Users/wbendinelli/Documents/airline-delays
  30 file:///Users/wbendinelli/Documents/pesquisa-acervo

$ git grep -oh "file:///Users/wbendinelli/Documents/pesquisa-acervo[^,\"]*" | sort -u
file:///Users/wbendinelli/Documents/pesquisa-acervo/01-atrasos-concentracao/_analises/avaliacao-vra-como-fonte.md
file:///Users/wbendinelli/Documents/pesquisa-acervo/01-atrasos-concentracao/_analises/especificacao.md
file:///Users/wbendinelli/Documents/pesquisa-acervo/01-atrasos-concentracao/_analises/reconstruir_vra_08_amostra3.py
file:///Users/wbendinelli/Documents/pesquisa-acervo/01-atrasos-concentracao/_analises/reconstruir_vra_13_validar.py
```

Distribution: 24 rows of `data/external/groups.csv` and 6 rows of
`data/external/events.csv` carry a `pesquisa-acervo` path in their `url`
column. A fifth private artefact is named in prose —
`data/external/README.md:40` cites `nectarbase_delays_v005.dta`'s `lab_j`
dummies and `proj18.dta`'s `pres_*` dummies. A further 13 rows point at
`file:///Users/wbendinelli/Documents/airline-delays/DECISIONS.md`, the author's
own machine.

Two consequences, one of confidentiality and one of provenance:

1. It contradicts the repository's own stated guarantee. `README.md:100-102`:
   *"`replication/gabarito/` reads it only from the `AIRLINE_DELAYS_PRIVATE_DIR`
   environment variable (never a path hardcoded in code)"*. That holds for
   code, but not for the committed reference tables, which publish the archive's
   directory layout and four of its filenames.
2. `just refs` validates that every row of `data/external/*.csv` carries a
   `source` and a `url`. For 30 rows that URL resolves only on one laptop, so
   the provenance guarantee the tutorial teaches (`docs/tutorial/02`) is not
   actually met for those rows.

Neither existing guard catches this. The `no-private-data` pre-commit hook
matches *staged path names*, never file contents:

```
$ sed -n '38p' .pre-commit-config.yaml
… git diff --cached --name-only … | grep -Ei "proj18|labtar|nectarbase|\.dta$|^data/(raw|staged|derived|private)/" …
```

and the only content-level assertion guards a different directory:

```
$ git grep -n "_recebidos"
tests/test_gabarito.py:66:        assert "_recebidos" not in text
```

`_recebidos` is the deliverables folder; the leaked paths are in the sibling
`_analises` folder, so the assertion passes while the leak stands.

---

## 2. Majors

### M-1 · README overstates the article's central result

`README.md:233-234`:

> No conclusion of the article changes — the sign inversion of both HHIs
> between OLS and 2SGMM, the article's central argument, replicates in all 12
> comparisons.

Recomputed from `reports/replication/private/results.json` (Table 6 = OLS,
Table 3 = 2SGMM, six columns, two HHIs each):

```
col1 rthhi:     OLSpub=-0.2086 GMMpub=+0.8050 inv=True  | OLSrep=-0.2080 GMMrep=+0.8843 inv=True
col1 maxcthhi:  OLSpub=+0.1614 GMMpub=-1.4772 inv=True  | OLSrep=+0.1540 GMMrep=-1.4551 inv=True
col2 rthhi:     OLSpub=-0.3126 GMMpub=+0.8192 inv=True  | OLSrep=-0.2914 GMMrep=+0.9028 inv=True
col2 maxcthhi:  OLSpub=+0.1057 GMMpub=-1.5144 inv=True  | OLSrep=+0.0938 GMMrep=-1.4839 inv=True
col3 rthhi:     OLSpub=+3.3899 GMMpub=+30.6290 inv=False | OLSrep=+3.2388 GMMrep=+25.0753 inv=False
col3 maxcthhi:  OLSpub=-2.4930 GMMpub=-19.4278 inv=False | OLSrep=-1.5739 GMMrep=-16.5621 inv=False
… (cols 4-6 likewise inv=False on both sides)
comparisons: 12   inversion replicates in: 4
```

An actual sign inversion occurs in **4** of the 12 comparisons — columns (1)
and (2), the ODDS regressand. In columns (3)-(6) (`MINS`, `MINS > 15`) OLS and
2SGMM carry the *same* sign in the published table and in the replication; only
the magnitude moves. What replicates in 12 of 12 is the OLS-vs-2SGMM sign
*pattern*, which is a weaker and different statement.

No script computes this number:

```
$ grep -rn -i "inver\|sign_flip" replication/ ml/ src/ scripts/
replication/kp.py:128:  def _sqrtm_psd(matrix, *, inverse: bool = False)   # unrelated
```

so it is hand-derived, which `README.md:325-327` itself forbids (*"a number
without a script behind it is a bug in this repository"*). The Portuguese
tutorial gets it right and confines the claim to column (1)
(`docs/tutorial/04-segundo-desenho.md:44-53`); only the English README
generalises it. Because this is the article's headline finding, the overstatement
is the single most consequential wording problem in the repository.

### M-2 · `reports/prediction/results.md` mislabels its "out of scope" column, so the README appears self-contradicting

`README.md:297-300` and `docs/declared-differences.md:308-309` state the
pre-2010 null rate as *"72.9% for the 5.1 million realised flights in scope
against 83.0% for the 313,368 out of it"*, citing
`reports/prediction/results.md`. Summing that file's own table:

```
$ # parsed from the "ADR-0017 accounting" table, years 2000-2009
sum realised      = 5,419,466
sum no_alteration = 3,720,757
sum out_of_scope  =   260,188      <-- README says 313,368
```

Both figures are correct, but they count different things. The
`out of scope` column is written from a different field:

```
$ grep -n "target_excluded_missing_actual" ml/run.py
ml/run.py:479:            f"{row['target_excluded_missing_actual']:,d} | "
```

so the column holds out-of-scope flights **that also have an empty actual
time** (260,188), while the prose above the table defines it as *all* realised
flights of `other`/unlabelled carriers (313,368). The README's figures
reconcile against a different artefact:

```
$ # reports/prediction/null_actual_by_carrier.csv, 2000-2009
in scope  : realised=5,106,122  null_arr=3,720,758  rate=0.7287   -> 72.9%
out scope : realised=  313,368  null_arr=  260,190  rate=0.8303   -> 83.0%
distinct out-of-scope carriers: 20
```

A reader following the README's own citation therefore finds an apparent
53,180-flight contradiction in the ADR-0017 accounting — the layer where the
repository most needs to be trusted, because it is the one place a definition
converts missing data into a zero.

### M-3 · Two committed artefacts disagree on the same population

The same 2000-2009 universe is counted twice, with three small mismatches:

| quantity | `null_actual_by_carrier.csv` | `results.md` | gap |
|---|---:|---:|---:|
| realised flights | 5,419,490 | 5,419,466 | 24 |
| in-scope null arrivals | 3,720,758 | 3,720,757 | 1 |
| out-of-scope null arrivals | 260,190 | 260,188 | 2 |

(`docs/declared-differences.md:414` quotes 260,190.) The gaps are numerically
trivial but they are exactly the kind of drift the repository's own standard is
designed to exclude, and there is no note explaining which count is
authoritative.

### M-4 · The `ml` runtime in the README is not printed by anything

`README.md:88-93` gives *"`ml` about 2,344 seconds end to end"*, cited to
`reports/prediction/results.md`. That file records only a generation timestamp;
no runtime appears in it or in any JSON. Summing every recorded `seconds`:

```
rolling.json  folds  : 1140.3 s
fixed.json    folds  : 1001.4 s
dataset.json         :   24.7 s
                       -------
                        2166.4 s      (README: about 2,344 s)
```

Every other timing in the same paragraph does check out against its cited
manifest (see §7), which makes this one the outlier. Either the figure includes
un-instrumented wall time (permutation importance, calibration, I/O) and should
say so, or it is stale.

### M-5 · Placeholder DOIs would ship in two published surfaces

```
$ sed -n '5p' README.md
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.XXXXXXX.svg)](https://doi.org/10.5281/zenodo.XXXXXXX)

$ uv run python -c "import json;print(json.load(open('datapackage.json'))['id'])"
https://doi.org/10.5281/zenodo.PENDING
```

The badge renders a dead DOI link at the top of the public landing page, and
`datapackage.json` publishes an invalid DOI as machine-readable metadata that
harvesters will read. Both are honestly declared as pending in `ROADMAP.md:67-73`,
so this is a sequencing requirement rather than a hidden defect: the Zenodo
deposit has to precede or accompany the first public push, not follow it.

---

## 3. Minors

- **m-1 · Stale paths in `docs/declared-differences.md`.** Line 24 cites
  `reports/replication/tables.md` and line 41 cites
  `reports/replication/sensitivity.json`; both are missing (the real files carry
  a `public/` or `private/` segment). `scripts/check_docs_paths.py:44` limits
  itself to `README.md` and `docs/tutorial/*.md`, so CI cannot catch this.
- **m-2 · README reading-A range is slightly wrong.** `README.md:308` gives
  `0.638-0.711` for the superseded reading over 2010-2013; the minimum in
  `reports/prediction/results.md:113` is `0.6358` (2011), not 0.6383 (2010).
- **m-3 · `panel_route_month.csv.gz` is not byte-reproducible.** Re-running the
  pipeline reproduced `panel_route_month.parquet`, the fact table and both city
  projections byte-for-byte, and the `.csv.gz` payload hashes identically
  (`65e0fa1f…` both ways), but the gzip header embeds an mtime
  (`1f 8b 08 08 02c49b6a` vs `1f 8b 08 08 7ad09b6a`), so a tracked file changes
  on every rebuild. `gzip -n` / `mtime=0` would close it.
- **m-4 · `just replicate` is not idempotent.** Its only diff against the
  committed output in the clone was the measured wall time it writes into the
  artefact itself (`"seconds": 0.3` → `0.2`; the same string in `tables.md`).
  Every other value was identical.
- **m-5 · CHANGELOG carries superseded numbers.** Lines 16-20 state
  `10,200,578 rows`, `4.97 M` targets and `about 33 seconds`; line 181 of the
  same `[Unreleased]` section corrects them to `10,200,560` and `8,686,697`,
  and the manifest records `24.73 s`.
- **m-6 · `docs/tutorial/12` expected number is off by one.** It predicts *"Duas
  ocorrências"* of `no-private-data`; `grep -c` returns `3`.
- **m-7 · Manifest commit stamps are behind HEAD and inconsistently formatted.**
  `data/derived/ml/manifest.json` and `reports/prediction/*.json` stamp
  `14d12b6` (HEAD~1) while HEAD is `d993b74`; `data/staged/manifest.json` uses a
  full 40-character SHA where the others use 7. None is `UNCOMMITTED`, so the
  brief's integrity requirement is met, but a reader cannot map the committed
  prediction artefacts onto the commit that contains them.
- **m-8 · README's data-availability table summarises 9 of 14 sources.**
  `docs/data-availability.md` documents 14; the README table lists 9 and omits
  two that this repository actually redistributes — OurAirports
  (`data/external/airports_br.csv`, 8,035 rows) and the federal holiday laws
  (`data/external/holidays.csv`, 92 rows). The README does label itself a
  summary, and the full statement is complete.
- **m-9 · `datapackage.json` describes 5 resources; the dictionary has 6
  layers.** The staged-flights layer has no resource entry.
- **m-10 · Ruff version drift.** `.pre-commit-config.yaml:21` pins
  `v0.16.4`; `uv.lock` resolves `0.16.6`. Both pass today
  (`All checks passed!`, `108 files already formatted`).
- **m-11 · `.sapians-doclint-baseline.json` is referenced but absent.**
  `.github/workflows/docs-lint.yml:12` lists it in `paths:`; the file does not
  exist. Harmless (the filter simply never matches on it).
- **m-12 · Inconsistent comparison order in `docs/declared-differences.md`.**
  Rows 2 and 3 of the replication table state *replicated against published*;
  row 7 states *published against replicated*. All eight values are correct;
  only the order flips.

---

## 4. Clone test — full transcript

All commands below ran in `…/scratchpad/audit-clone` with
`AIRLINE_DELAYS_PRIVATE_DIR` unset.

```
$ uv sync --group dev
… 0.14s user 0.28s system 79% cpu 0.530 total      (exit 0)

$ uv run pytest -q
1 failed, 335 passed, 5 skipped, 16 deselected, 1 warning in 14.29s   -> B-1

$ just demo
demo: not implemented yet                          (exit 0, declared placeholder)

$ just replicate
wrote …/audit-clone/reports/replication/public in 0.2 s
just replicate  0.66s user 0.13s system 105% cpu 0.750 total

$ git diff -U0 reports/replication/public/
-  "seconds": 0.3
+  "seconds": 0.2
-Generated by `uv run python -m replication.run` (`--source public`, 0.3 s). …
+Generated by `uv run python -m replication.run` (`--source public`, 0.2 s). …
```

`just replicate` in public mode works from the committed analysis tables with no
private directory and no network, exactly as `README.md:57-62` promises, and
every estimated value is reproduced identically — the only diff is the runtime
the script stamps into its own output (m-4).

The smallest documented reproduction on the fixture is `uv run pytest -q`
(`README.md:53-56` says `just demo` is still a placeholder and points here
instead). It fails in the clone — see B-1.

### 4.1 Registry regeneration (brief item c)

```
$ uv run vra dictionary && uv run vra datapackage && git diff --stat
dictionary: 584 columns across 6 layers -> …/audit-clone/docs/dictionary.md
datapackage: 5 resources -> …/audit-clone/datapackage.json
 reports/replication/public/results.json | 2 +-
 reports/replication/public/tables.md    | 2 +-
```

**Pass.** Neither `docs/dictionary.md` nor `datapackage.json` appears in the
diff; both regenerate byte-identically from `src/vra/registry.py`. (The two
listed files are the leftovers of the preceding `just replicate`.)

### 4.2 `gabarito` tests — original repository, variable set in the shell only

```
$ AIRLINE_DELAYS_PRIVATE_DIR=/Users/wbendinelli/Documents/pesquisa-acervo/01-atrasos-concentracao/_recebidos \
  uv run pytest -m gabarito -v
tests/test_gabarito.py::…::test_the_keys_line_up PASSED
tests/test_gabarito.py::…::test_no_column_regressed_against_its_measured_rate[dlccfu|f|fl_can|
   fl_odel|fsc_prdelarr|maxalccfu|olccfu|pr_connc|princident|prwheather] PASSED (10)
tests/test_gabarito.py::…::test_the_article_fsc_set_reproduces_better_than_the_fsc_class PASSED
tests/test_gabarito.py::…::test_taxas_is_written_without_a_single_benchmark_value PASSED
tests/test_gabarito.py::test_the_private_directory_is_readable_when_declared PASSED
tests/test_replication_kp.py::test_identification_statistics_against_the_published_table_3[1|3] PASSED
16 passed, 341 deselected in 2.83s
```

**Pass.** The private-directory contract works as documented: deselected by
`addopts = "-m 'not gabarito'"`, skipped rather than failed when the variable is
unset (`tests/conftest.py:30-38`), and all 16 pass when it is set.

---

## 5. Number verification (brief item a)

Fifty README and tutorial numbers were checked against the JSON/CSV/parquet they
cite. Forty-seven matched. The three that did not are M-1, M-4 and m-2.

| Claim (source) | Cited artefact | Measured | ✓ |
|---|---|---|---|
| 13,652,322 legs | `data/staged/manifest.json` | 13,652,322 | ✓ |
| 168 monthly files, 2.17 GB raw | `data/raw/manifest.json` | 168, 2,166,489,628 B | ✓ |
| 265 MB zstd parquet | staged manifest | 264.5 MB | ✓ |
| fact table 165,763 × 87 | `fact_group_route_month.parquet` | 165,763 × 87 | ✓ |
| panel 31,313 × 228 | `panel_route_month.parquet` | 31,313 × 228 | ✓ |
| 310 routes, 168 months, unique on `(route, ym)` | same | 310; 168 (200001-201312); unique | ✓ |
| city-month 21,231 / airline-city-month 49,801 | those parquets | 21,231 / 49,801 | ✓ |
| `rthhi`/`maxcthhi` present but entirely null | same | 0 non-null; `*_flights` present | ✓ |
| dictionary 584 columns, six layers | `docs/dictionary.md` | 584 rows, 6 `##` layers | ✓ |
| fetch ~17 min | raw manifest `retrieved_at` span | 17.0 min, all HTTP 200 | ✓ |
| stage ~8.4 s / features ~11.4 s / panel ~7.5 s | the three manifests | 8.31 / 11.43 / 7.46 | ✓ |
| replicate public ~0.3 s / private ~38.1 s | both `tables.md` | 0.3 / 38.1 | ✓ |
| `ml` ~2,344 s end to end | `reports/prediction/results.md` | 2,166.4 (summed) | **✗ M-4** |
| 25 s to build 10,200,560 rows | `data/derived/ml/manifest.json` | 24.73 s, 10,200,560 | ✓ |
| 24 models over 8 folds + fixed split | `rolling.json`, `fixed.json` | 24 | ✓ |
| 8.7 M arrival targets vs 5.0 M | `dataset.json` / `dataset_reading_A.json` | 8,686,697 / 4,965,966 | ✓ |
| 306 coefficients, 302 signs, 259 (85%) | `private/summary.json` | 306 / 302 / 259 (84.6%) | ✓ |
| largest gap 0.94 published s.e. | same | 0.9413 (Table 6) | ✓ |
| N 20,447-20,630 vs 19,408-19,590; 5.31% / 5.35% | same | exactly those 4 pairs; +5.3088-5.3092% / +5.3527-5.3535% | ✓ |
| median s.e. ratio 0.94-0.99 | same | 0.9411-0.9922 | ✓ |
| 22 of 24 J columns fail to reject; same 2 reject | `private/results.json` | 22/24; Table 4 cols 3 and 5 in both | ✓ |
| HHI sign inversion in all 12 comparisons | — | 12 comparisons, inversion in 4 | **✗ M-1** |
| Adj. R² 0.4833/0.4875/0.4715/0.4752 vs published | same | exact | ✓ |
| 51 of 60 s.e. below published, 0.79-1.14 | same | 51/60, 0.7902-1.1410 | ✓ |
| four sign disagreements, all ≤0.52 s.e. | same | exactly 4; max 0.52 | ✓ |
| F statistic not reproduced in any column | same | all `f_stat` null | ✓ |
| public panel: 21,566 obs, 207 routes | `public/tables.md` | 21,566 / 207 | ✓ |
| 7 of 13 Table 2 variables; other 6 missing | same | 7 computed, 6 blank | ✓ |
| `fsc_oddsarr` −1.3927 vs −1.38 | same | −1.3927 | ✓ |
| `MINS` 6.8632 vs 7.16, s.d. 8.79 vs 8.29 | same | 6.8632, 8.7852 | ✓ |
| LCC presence city-pair 0.7761 vs 0.90 | same | 0.7761 | ✓ |
| 24,551 comparable route-months | `data/analysis/taxas.csv` | n = 24,551 | ✓ |
| `f` 90.2% overall, 95.3% stable, 97.5% earlier | same | 0.902244 / 0.953436 / 0.975 | ✓ |
| `fl_odel` 87.9% vs `fl_ddel` 56.3% (stable) | same | 0.879119 / 0.563367 | ✓ |
| earlier reconstruction 92.4% / 59.8% | same | 0.924 / 59.8% in definition | ✓ |
| `prwheather` 92.0% stable | same | 0.920421 | ✓ |
| `fsc_prdelarr` 65.1% vs `fscc_prdelarr` 53.5% | same | 0.650643 (exp. 0.651) / 0.535090 | ✓ |
| `lcc`/`pres_*` 90.7%-93.6% stable | same | 0.907202-0.936468 | ✓ |
| `maxalccfu` 100% | same | 1.000000 | ✓ |
| 72.9% / 83.0% / 313,368 out of scope | `null_actual_by_carrier.csv` | 0.7287 / 0.8303 / 313,368, 20 carriers | ✓ (but M-2) |
| day-ahead AUC 0.715-0.741 | `rolling.json` | 0.7149-0.7411 | ✓ |
| at-gate AUC 0.757-0.824 | same | 0.7568-0.8242 | ✓ |
| route-prevalence baseline 0.60-0.67 | same | 0.6079-0.6728 | ✓ |
| linked subset 20-35%, at-gate 0.87-0.93 | same | 0.1984-0.3507; 0.8691-0.9340 | ✓ |
| reading B 2010-13 day-ahead 0.715-0.724 | `results.md` | 0.7149-0.7241 | ✓ |
| reading A 2010-13 day-ahead 0.638-0.711 | same | 0.6358-0.7113 | **✗ m-2** |
| outlier threshold 313.25 (117.10 alt.) | analysis manifest, `sensitivity.json` | 313.25; 117.10 present | ✓ |
| Viracopos node lifts `f` 86.8% → 97.4% | `DECISIONS.md` ADR-0001 | narrative evidence, no committed artefact | n/a |

Every `**Número esperado**` block in `docs/tutorial/*.md` was executed. Nine
blocks, eight exactly right (zero fare columns in the registry; `just refs`
clean with `groups.csv` at 50 rows all grade B; one capacity row, `SBSP` 33
mov/h from 2007-08, grade B; `grep -c "^| HHI city-pair"` → `6`; two
`prdelarr` entries; `test_replication_kp.py` 13 passed; the scorecard summing to
306/302/259; two `title:` lines in `CITATION.cff`). One is off by one — m-6.

---

## 6. Remaining brief items

### (b) `docs/declared-differences.md` consistency — pass with M-2/M-3/m-1/m-12

Against `data/analysis/taxas.csv`: all rate claims reconcile (§5). Against
`reports/replication/public/tables.md`: 21,566 / 207 routes / 144 months, the
7-of-13 split, and every quoted descriptive value match. Against
`reports/prediction/results.md`: the ADR-0017 figures reconcile only via
`null_actual_by_carrier.csv`, not via the file cited — M-2 — and the two
artefacts differ by 24/1/2 flights — M-3. Two internal path references are dead
(m-1) and one comparison order flips (m-12).

### (d) Private-path leak — **fail**, see B-2

`_recebidos` appears once, in a test assertion. `pesquisa-acervo` appears in 30
committed rows with a full absolute path.

### (e) Placeholder targets — pass

```
$ grep -n "not implemented yet" justfile
74:    @echo "report: not implemented yet"
77:    @echo "publish: not implemented yet"
93:    @echo "demo: not implemented yet"
```

All three are declared: `demo` in `README.md:53-56` (with the reason and the
working alternative), `report` in `ROADMAP.md:59-66`, `publish` in
`ROADMAP.md:67-73`. No undeclared placeholder exists.

### (f) CI without network to ANAC, and pinned reusables — pass

Tests are fixture-only: the `test` job runs `uv run pytest -q`, `addopts`
deselects `gabarito`, and no test touches `data/raw/`. Nothing in the workflows
downloads from ANAC. Third-party actions are pinned by commit SHA with the tag
in a comment. No `cron` anywhere, as `.sapians-repo.yml` requires.

Both reusable workflows resolve at the pinned tag:

```
$ gh api repos/wbendinelli/.github --jq '{private,visibility}'
{"private":false,"visibility":"public"}
$ gh api repos/wbendinelli/.github/git/ref/tags/v0.8.0 --jq '{ref,sha:.object.sha}'
{"ref":"refs/tags/v0.8.0","sha":"9a1212d9df466988781b0b3c4285d5dc61f58ea6"}
$ gh api "…/contents/.github/workflows/docs-lint.yml?ref=v0.8.0"   ->  1743 bytes
$ gh api "…/contents/.github/workflows/security.yml?ref=v0.8.0"    ->  2608 bytes
```

The inputs passed match the callees' `workflow_call` signatures (`config-ref`,
required and without a default, is supplied; `full-history` is a declared
boolean). The `lint`, `citation` and `docs-paths` jobs were reproduced locally
and pass. **The `test` job will fail** — B-1.

---

## 7. What passed

Recorded so the blockers are not read as a verdict on the whole repository.

- **SAPIANS doclint:** `node …/doclint.mjs . --format human` →
  `airline-delays · profile=research · tier=C class=Research · 0 erro(s) · 0 aviso(s)`.
- **`CITATION.cff`:** `uv run cffconvert --validate` →
  `Citation metadata are valid according to schema version 1.2.0.`
- **Lint:** `uv run ruff check .` → `All checks passed!`;
  `uv run ruff format --check .` → `108 files already formatted`.
- **Docs paths:** `uv run python scripts/check_docs_paths.py` →
  `16 file(s), 244 path candidate(s), 26 command(s) checked / all paths and commands resolved`.
- **Registry as single source:** dictionary and datapackage regenerate
  byte-identically in a clean clone (§4.1); `tests/test_registry.py` holds 18
  guards, including that every built column resolves, that no entry describes a
  non-existent column, that a proportion is never declared additive, and that an
  unknown measure raises rather than shipping undocumented.
- **Additivity (ADR-0004):** `tests/test_features.py` tests that hourly counts
  sum to flights, that route-month sums equal a direct count, that every
  additive measure survives projection, and that the airline-city grain sums back
  to the city grain.
- **Leakage (rolling-origin):** `uv run pytest tests/test_leakage.py -q` →
  `32 passed`; all nine checks in `reports/prediction/leakage.json` pass,
  including closed lag windows (1.0000 match t−1, 0.0000 match t over 1,535,464
  rows), nested horizons, no post-departure features, and no `p90` flag in the
  first year. Evaluation is genuinely rolling-origin (train ≤ y−2, early-stop on
  y−1, test on y) with two prevalence baselines.
- **Replication reports N and s.e. distances,** not only relative differences:
  the scorecard's decisive column is `diff/s.e.` in *published* standard errors,
  and per-column N is printed published-against-replicated.
- **No tuning to the benchmark:** `rthhi`/`maxcthhi` are shipped null and the
  near-equivalent `*_flights` indices are explicitly *not* substituted; the
  public run prints the variables each table is missing instead of estimating on
  a proxy; `test_taxas_is_written_without_a_single_benchmark_value` passes.
- **ADR coverage:** 18 ADRs (0000-0017); every declared difference traced in
  this audit points at one.
- **Manifest integrity:** `sha256`, `retrieved_at` and `http_status` present on
  all 168 raw files, all 200; no `git_commit` is `UNCOMMITTED` (but see m-7).
- **Pipeline determinism:** a full `fetch/stage/refs/features/panel` rerun
  reproduced `panel_route_month.parquet`, `fact_group_route_month.parquet`,
  `city_month.parquet` and `airline_city_month.parquet` byte-for-byte; only
  timestamps, measured seconds and the gzip header changed (m-3). *(This rerun
  was triggered by executing the tutorial's own command block; the working tree
  was restored to `d993b74` with `git checkout --` and verified clean.)*
- **Fixtures are small and committed:** 230 KB + 880 KB + 373 KB.
- **Staleness guard:** `uv run pytest -q -m analysis` → `9 passed` in the
  original tree; skips rather than fails in the clone, as ADR-0014 intends.
- **Licences per layer** are declared and the files exist: MIT for code,
  CC BY 4.0 for text and curated tables, ANAC attribution for the raw records.
  The full Data Availability Statement covers 14 sources, including every one
  used in code.

---

## 8. Verdict

**Not ready for a public first release or a Zenodo deposit today, but close —
the substance is sound and the defects are correctable in hours, not weeks.**
Two blockers must clear first. `uv run pytest -q` fails on any fresh clone
because `.gitattributes` normalises away the CRLF that the 2002 fixture exists
to prove, so the very first CI run on GitHub would be red and the first thing a
visitor does would fail; and 30 committed rows of `data/external/` publish
absolute `file:///Users/wbendinelli/Documents/pesquisa-acervo/…` paths naming
four private analysis files, with a fifth private base named in
`data/external/README.md` — a leak that both existing guards structurally miss,
and one that contradicts the confidentiality guarantee the README makes in its
own words. The majors are narrower but matter for a research artefact: the
README generalises the article's central HHI sign-inversion result from the 4
comparisons where it holds to all 12; the ADR-0017 accounting cannot be
reconciled against the file the README cites, because
`reports/prediction/results.md` labels a column with a different quantity than
its own prose defines; two artefacts count the same population differently; one
runtime is unsourced; and two placeholder DOIs would ship live. Against that,
what this audit could verify is unusually strong. Forty-seven of fifty quoted
numbers matched their cited artefact exactly, every tutorial exercise but one
produced its stated answer, the registry regenerates the dictionary and the
datapackage byte-identically from a clean clone, `just replicate` reproduces
every public estimate with no private directory and no network, all 16
`gabarito` tests pass when the benchmark is present, the leakage suite and the
rolling-origin design are real and passing, and the analysis tables rebuild
byte-for-byte. Crucially, the discipline the repository claims for itself —
declare the difference, never tune the definition — holds where it was tested:
`rthhi`/`maxcthhi` ship null rather than silently substituted, and the public
replication refuses to estimate rather than estimate on a proxy. Clear the two
blockers, restate M-1 to match what the data shows, reconcile M-2 and M-3, and
this is a publishable, citable artefact.

---

## 9. Fixes applied

Written by the remediation pass, not by the auditor. Every blocker and every
major is closed; the minors that cost less than ten minutes are closed too, and
the rest are listed in `ROADMAP.md` under "Open items, by phase" with this
report as their reference. `CHANGELOG.md`'s `Fixed` section carries the same
list in the repository's own voice.

| Finding | Status | What changed |
|---|---|---|
| **B-1** fixture line endings | fixed | `.gitattributes` gains `tests/fixtures/vra_raw_sample_*.csv -text`; both fixtures were `git rm --cached`-ed and re-added, so the stored blob now carries the bytes on disk (`git ls-files --eol tests/fixtures/` -> `i/crlf w/crlf attr/-text` for 2002, 235,640 bytes staged and on disk). `tests/test_io.py::TestMeasuredAgainstDeclared` asserts on the bytes of the file it reads; the new `TestFixtureBytes` fails with a message naming `.gitattributes` and this finding if a fixture arrives normalised. |
| **B-2** private paths in content | fixed | The 30 `file:///…/pesquisa-acervo/…/_analises/…` URLs in `data/external/groups.csv` and `events.csv` are gone: those rows now cite `author's research notes (private, not redistributed)`, with the public URL kept where the fact has one and an empty `url` where it does not. The 13 rows pointing at the author's checkout of this repository now cite `DECISIONS.md` relatively. `data/external/README.md` no longer names the two private bases; the absolute archive paths in `docs/data-availability.md` and `docs/notes/references.md` are neutralised too. New `scripts/check_no_private_paths.py` greps file **content** and is run by a new `no-private-data-content` pre-commit hook (staged blobs) and by `tests/test_no_private_paths.py` (every tracked text file, unmarked, so it runs in CI). |
| **M-1** "all 12 comparisons" | fixed | `replication.run.hhi_sign_inversions` computes the count from `results.json` and writes `hhi_sign_inversions` into `summary.json` with per-column detail; `tables.md` prints the cell-by-cell table. Measured: 12 comparisons, inversion in **4** (columns 1 and 2), all 4 replicate, pattern agrees 12/12 — the auditor's numbers exactly. `README.md` and `docs/notes/replication.md` now state that and cite the file. The tutorial's correct statement is untouched. |
| **M-2** mislabelled "out of scope" | fixed | See M-3. |
| **M-3** two artefacts, one population | fixed | `ml/run.py` writes one canonical `accounting` block into `reports/prediction/dataset.json` (per year: scheduled, realised, realised in/out of scope, `on_time_no_bav`, `actual_time_suspect`, targets available, exclusions by reason) plus a legacy-window summary; `results.md`, `README.md` and `docs/declared-differences.md` quote it under matching headers and compute nothing. The column that used to hold `target_excluded_missing_actual` under an "out of scope" header is now two separate columns. The residual gap against `null_actual_by_carrier.csv` (24 realised flights over 2000-2009) is stated where it appears: the CSV counts `data/staged/`, the block counts the flight table built from it, which drops flights whose schedule is unusable. |
| **M-4** unsourced `ml` runtime | fixed | `ml/run.py` writes a `runtime` block into `dataset.json` (total 2,344.2 s, dataset build 24.73 s, rolling folds 1,140.3 s, fixed folds 1,001.4 s) and says the total exceeds the fold sums because permutation importance, calibration and I/O are inside it and are not separately timed. The README cites that block. The figure was not stale: it was `fixed.json`'s `meta.seconds`, cited to the wrong file. |
| **M-5** placeholder DOIs | fixed | The badge reads "DOI pending Zenodo deposit" and links to `ROADMAP.md`; doclint still passes with zero errors. `registry.datapackage()` omits `id` unless a DOI is passed and carries `pending_doi: true` with a note; `CITATION.cff` explains in a comment why it has no `doi:`. |
| m-1 stale paths | fixed | Both now carry their `public/`/`private/` segment. |
| m-2 reading-A range | fixed | 0.636-0.711 in `README.md` and `CHANGELOG.md`. |
| m-3 gzip mtime | fixed | `src/vra/panel.py` writes the gzip header with `mtime=0`; the file was regenerated and its payload sha256 is unchanged (`65e0fa1f…`). |
| m-4 `just replicate` idempotence | **open** | `ROADMAP.md`. `--rescore` avoids re-measuring but does not remove the stamp. |
| m-5 CHANGELOG numbers | fixed | 10,200,560 rows, 4,965,966 -> 8,686,697 targets, 24.73 s. |
| m-6 tutorial 12 count | fixed | Five, and the block now describes both hooks. |
| m-7 manifest commit stamps | **open** | `ROADMAP.md`; needs a post-commit step. |
| m-8 availability summary | fixed | OurAirports and the federal holiday laws added; the text says 12 of 14 and names the two omitted. |
| m-9 5 resources vs 6 layers | **open** | `ROADMAP.md`; what the staged layer's `path` should say is a real question. |
| m-10 ruff drift | fixed | `v0.16.6`, the version `uv.lock` resolves. |
| m-11 missing doclint baseline | fixed | Dropped from the `docs-lint` path filter. |
| m-12 comparison order | fixed | Row 7 reads replicated-against-published. |
| *(not in the audit)* non-deterministic carrier labels | fixed | Found while checking that the regenerated artefacts are idempotent: `scripts/null_actual_by_carrier.py` picked each airline-year's group and class with DuckDB's `any_value()`, so five transition-year rows of the tracked CSV flipped between runs. The convention is now stated and deterministic (the label in force in the airline's last observed month of that year) and the file reproduces byte for byte. No total moves — `in_bav_scope` is identical on every row, so the 72.9% / 83.0% / 313,368 / 20-carrier figures of §5 still hold. |

**One deviation from the remediation brief, deliberate.** The brief asked that
`git grep -n -i "pesquisa-acervo\|proj18\|labtar\|nectarbase\|_recebidos\|_analises/"`
return nothing outside this report and the guard's pattern list. The first
three patterns of that class — the archive's *location and layout* — are indeed
gone everywhere. The benchmark's *file names* are not, and removing them would
be wrong: `README.md`, `SECURITY.md`, `CLAUDE.md`, `CONTRIBUTING.md` and
`docs/data-availability.md` name `proj18.dta` and the LABTAR/NECTAR bases in
order to **declare** them as the one non-public input, and
`replication/gabarito/compare.py` must name the file it opens through
`AIRLINE_DELAYS_PRIVATE_DIR`. Naming a file that is deliberately not
redistributed is transparency, not a leak. The guard therefore enforces two
tiers: tier 1 (`pesquisa-acervo`, `_recebidos`, `_analises/`, `file:///Users/`,
`/Users/<name>/Documents`) fails anywhere; tier 2 (`proj18`, `labtar`,
`nectarbase`, `.dta`) fails outside an explicit per-file allowlist that carries
a reason for each entry, is checked for stale entries, and contains no path
under `data/` except `data/private/README.md`. `git grep` over `data/external/`
— where the leak was — returns nothing.
