# airline-delays -- task runner. Every target either calls the real command
# or, if that phase has not landed yet, prints a message and exits 0 -- a
# fresh clone should never fail just because a later phase is still
# scaffolding. See ROADMAP.md for what each phase depends on.

fetch:
    uv run airline-delays fetch

stage:
    uv run airline-delays stage

# Validate data/external: provenance on every row, plus the ADR-0003/0005 sets.
reference:
    uv run airline-delays reference

# The canonical fact table (group x route x month) and its city projections.
# One pass per year over data/staged; about 12 s on the full series.
fact:
    uv run airline-delays fact

# The public route-month panel, parquet and csv.gz, from the fact table.
# Regenerates the dictionary and datapackage, which are derived from the registry.
panel:
    uv run airline-delays panel
    uv run airline-delays dictionary
    uv run airline-delays datapackage

# ADR-0014 staleness guard: rebuilds the panel from the committed fact table
# in memory (data/analysis/fact_group_route_month.parquet plus the two
# data/derived/ intermediates `just fact` also writes) and compares it,
# shape and checksum, against the committed data/analysis/panel_route_month.parquet.
# Skips rather than fails when either side is missing -- run `just fact`
# first if this only ever skips locally.
check-analysis:
    uv run pytest -q -m analysis

# Tables 2-7 of Bendinelli, Bettini & Oliveira (2016). `just replicate` uses the
# public panel (data/analysis/panel_route_month.parquet, built by `just panel`);
# `just replicate private` uses the benchmark and needs AIRLINE_DELAYS_PRIVATE_DIR.
# Writes reports/replication/<source>/{results,summary,sensitivity}.json and tables.md.
replicate source="public":
    @if [ "{{source}}" = "public" ] && [ ! -f data/analysis/panel_route_month.parquet ]; then \
        echo "replicate: the public panel is not built yet (data/analysis/panel_route_month.parquet)."; \
        echo "           run 'just panel' first, or 'just replicate private' with AIRLINE_DELAYS_PRIVATE_DIR set."; \
    else \
        uv run airline-delays estimate --source {{source}}; \
    fi

# The flight-level modelling table: one DuckDB pass per calendar year over
# data/staged/, writing data/derived/ml/year=YYYY/part-0.parquet (about 25 s,
# 10.2 M rows, 320 MB -- never in git, ADR-0004). `just predict` also trains the
# rolling-origin folds and the fixed split and writes reports/prediction/;
# that part takes about 39 minutes under the ADR-0017 reading, which gives an
# arrival target to 8.7 M flights instead of 5.0 M. `just predict-dataset` stops
# after the table.
predict-dataset:
    uv run airline-delays predict-dataset

predict:
    uv run airline-delays predict --rebuild

# The Stackelberg congestion model of the author's 2013 monograph (after
# Brueckner and Van Dender 2008), derived with sympy and checked numerically,
# plus the five congestion-economics diagrams of its section 2 redrawn as SVG.
# Offline, deterministic, about a second. Writes reports/theory/{model,figures}.json,
# figures/*.svg and results.md; a second run on an unchanged tree changes nothing.
theory:
    uv run airline-delays theory

report:
    @echo "report: not implemented yet"

publish:
    @echo "publish: not implemented yet"

test:
    uv run pytest -q

lint:
    uv run ruff check .
    uv run ruff format --check .

check:
    uv run pre-commit run --all-files

# The smallest end-to-end reproduction: the committed fixture (three routes,
# 2004/2009/2012, about 20,000 staged legs) through features, panel and Table 2,
# offline, in about a second, into the git-ignored data/derived/demo/. It never
# touches data/analysis/ or reports/ -- see scripts/demo.py.
demo:
    uv run python scripts/demo.py
