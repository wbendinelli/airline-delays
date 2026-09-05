# airline-delays -- task runner. `just` lists the recipes by pipeline stage.
# `just pipeline` runs stages 3-9 from data/staged/ (no network, nothing
# refitted, about two minutes); `just pipeline-full` adds the download, the
# parse and the 39-minute prediction step. Every recipe is a thin wrapper over
# `uv run airline-delays <stage>`; see `uv run airline-delays --help`.

default:
    @just --list

# Stages 3-9 from data/staged/: reference, fact, panel, estimate, theory, summary, check.
pipeline: reference fact panel estimate theory summary check-analysis

# Everything, from ANAC's servers to the compiled reports (about 45 minutes).
pipeline-full: fetch stage reference fact panel estimate predict theory summary report

[group('1-ingest')]
[doc('Download the monthly ANAC VRA CSVs into data/raw/ and write manifest.json (about 17 min, 2.2 GB)')]
fetch:
    uv run airline-delays fetch

[group('2-staging')]
[doc('Parse and clean the raw CSVs into data/staged/year=YYYY/part-0.parquet, one year at a time')]
stage:
    uv run airline-delays stage

[group('3-reference')]
[doc('Validate data/external: provenance on every row, and the ADR sets the tables encode')]
reference:
    uv run airline-delays reference

[group('4-fact')]
[doc('The group x route x month fact table and its city projections (about 12 s on the full series)')]
fact:
    uv run airline-delays fact

[group('5-panel')]
[doc('The route-month reconstruction panel, then the dictionary and the datapackage')]
panel:
    uv run airline-delays panel
    uv run airline-delays dictionary
    uv run airline-delays datapackage

[group('5-panel')]
[doc('ADR-0014: rebuild the committed tables in memory and diff them; skips what data/derived/ lacks')]
check-analysis:
    uv run pytest -q -m analysis

[group('6-estimation')]
[doc("Curate the authors' final base into data/analysis/article_panel_route_month.* (ADR-0020; owner's machine)")]
article-panel source:
    uv run airline-delays article-panel --source "{{source}}"

[group('6-estimation')]
[doc('Tables 2-7 re-estimated on the article panel and compared with the published values -> reports/replication/')]
estimate *args:
    uv run airline-delays estimate {{args}}

[group('7-prediction')]
[doc('The flight-level modelling table -> data/derived/ml/ (one DuckDB scan per year, about 25 s)')]
predict-dataset:
    uv run airline-delays predict-dataset

[group('7-prediction')]
[doc('Rolling-origin XGBoost, both horizons, about 39 minutes -> reports/prediction/')]
predict *args:
    uv run airline-delays predict --rebuild {{args}}

[group('8-theory')]
[doc('The congestion model derived and checked, eleven figures -> reports/theory/ (about 1 s)')]
theory:
    uv run airline-delays theory

[group('9-reporting')]
[doc('reports/summary.json: every headline number the READMEs quote')]
summary:
    uv run airline-delays summary

[group('9-reporting')]
[doc('Compile the three Typst reports into reports/build/')]
report:
    uv run airline-delays report

[group('9-reporting')]
[doc('Check the publication metadata (datapackage, dictionary, CITATION) and print the release checklist')]
publish: summary report
    uv run airline-delays datapackage --check
    uv run airline-delays dictionary --check
    uv run cffconvert --validate
    @echo "publish: metadata consistent. Next: tag the release (see ROADMAP.md), Zenodo archives it and mints the DOI."

[group('dev')]
[doc('The smallest end-to-end reproduction on the committed fixture, offline, about a second')]
demo:
    uv run python scripts/demo.py

[group('dev')]
test:
    uv run pytest -q

[group('dev')]
lint:
    uv run ruff check .
    uv run ruff format --check .

[group('dev')]
[doc('pre-commit over the whole tree, plus every path and command quoted in the docs')]
check:
    uv run pre-commit run --all-files
    uv run python scripts/check_docs_paths.py
