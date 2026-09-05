# airline-delays -- task runner. Every target either calls the real command
# or, if that phase has not landed yet, prints a message and exits 0 -- a
# fresh clone should never fail just because a later phase is still
# scaffolding. See ROADMAP.md for what each phase depends on.

fetch:
    uv run python scripts/fetch.py

stage:
    uv run vra stage

refs:
    @echo "refs: not implemented yet"

features:
    @echo "features: not implemented yet"

panel:
    @echo "panel: not implemented yet"

replicate:
    @echo "replicate: not implemented yet"

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
