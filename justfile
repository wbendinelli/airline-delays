# airline-delays -- task runner. Every target either calls the real command
# or, if that phase has not landed yet, prints a message and exits 0 -- a
# fresh clone should never fail just because a later phase is still
# scaffolding. See ROADMAP.md for what each phase depends on.

fetch:
    uv run python scripts/fetch.py

stage:
    uv run vra stage

# Validate data/external: provenance on every row, plus the ADR-0003/0005 sets.
refs:
    uv run vra refs

# The canonical fact table (group x route x month) and its city projections.
# One pass per year over data/staged; about 12 s on the full series.
features:
    uv run vra features

# The public route-month panel, parquet and csv.gz, from the fact table.
# Regenerates the dictionary and datapackage, which are derived from the registry.
panel:
    uv run vra panel
    uv run vra dictionary
    uv run vra datapackage

# ADR-0014 staleness guard: rebuilds the panel from the committed fact table
# in memory (data/analysis/fact_group_route_month.parquet plus the two
# data/derived/ intermediates `just features` also writes) and compares it,
# shape and checksum, against the committed data/analysis/panel_route_month.parquet.
# Skips rather than fails when either side is missing -- run `just features`
# first if this only ever skips locally.
check-analysis:
    uv run pytest -q -m analysis

# Column-by-column agreement of the public panel against the private benchmark.
# Needs AIRLINE_DELAYS_PRIVATE_DIR exported in the shell; writes
# data/analysis/taxas.csv and the generated block of docs/declared-differences.md.
# Exits non-zero while any column sits below the rate the earlier reconstruction
# measured -- today seven do, because the raw files changed between the 2019
# vintage the benchmark was built from and the ones ANAC publishes now. That is
# a standing, declared difference (docs/declared-differences.md), not a broken
# build: the files are written either way.
gabarito:
    uv run python -m replication.gabarito.compare

# Tables 2-7 of Bendinelli, Bettini & Oliveira (2016). `just replicate` uses the
# public panel (data/analysis/panel_route_month.parquet, built by `just panel`);
# `just replicate private` uses the benchmark and needs AIRLINE_DELAYS_PRIVATE_DIR.
# Writes reports/replication/<source>/{results,summary,sensitivity}.json and tables.md.
replicate source="public":
    @if [ "{{source}}" = "public" ] && [ ! -f data/analysis/panel_route_month.parquet ]; then \
        echo "replicate: the public panel is not built yet (data/analysis/panel_route_month.parquet)."; \
        echo "           run 'just panel' first, or 'just replicate private' with AIRLINE_DELAYS_PRIVATE_DIR set."; \
    else \
        uv run python -m replication.run --source {{source}}; \
    fi

ml:
    @echo "ml: not implemented yet"

report:
    @echo "report: not implemented yet"

publish:
    @echo "publish: not implemented yet"

verify:
    uv run python scripts/verify_reconcile.py

test:
    uv run pytest -q

lint:
    uv run ruff check .
    uv run ruff format --check .

check:
    uv run pre-commit run --all-files

demo:
    @echo "demo: not implemented yet"
