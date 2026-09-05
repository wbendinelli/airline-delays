# Contributing

This repository reconstructs a public flight-delay dataset, replicates a
published econometric result on it, and trains a delay predictor on top of
it. The page below is the practical guide — it is also what CI checks on
every pull request, so nobody has to police it by hand.

Corrections and independent replications are welcome from anyone. The most
valuable thing you can send is a measurement showing that something here is
wrong.

## Your first contribution

1. **Fork** the repository and clone your fork.
2. **Set up the environment** (Python 3.12, managed by `uv`; never the
   system `python3` — it lacks pandas):

   ```bash
   uv sync
   uv run pre-commit install
   ```

3. **Run the smallest reproduction** (`just demo`, over the fixture
   committed in `tests/fixtures/`) to see the pipeline work without
   touching the network or `data/raw/`.
4. **Branch, change, open a pull request.** CI runs `ruff`, `pytest`
   against the fixture, and validates `CITATION.cff` — if something is
   wrong, it says exactly what, before anyone reviews by hand.

## The hard rules

1. **No column reaches a public table without an entry in
   `src/vra/registry.py`.** The dictionary, `datapackage.json`, and the
   registry-completeness test are all generated from it — never
   hand-write them.
2. **No number in prose (the README, `docs/`, the Typst reports) without a
   versioned script that prints it.** A number without a script behind it
   is a bug: either the script is missing, or the number should be.
3. **Never commit anything under `data/raw/`, `data/staged/`,
   `data/derived/` or `data/private/`**, except their `README.md` (and,
   for `data/raw/`, `manifest.json`). The private benchmark
   (`proj18.dta`, the LABTAR/NECTAR laboratory bases, `vra.dta`) is
   reached only through the `AIRLINE_DELAYS_PRIVATE_DIR` environment
   variable, by `replication/gabarito/` or a `scripts/verify*.py`, and
   only its derived agreement rate (`replication/gabarito/taxas.csv`) is
   ever committed.
4. **When a measurement contradicts prose, the prose changes and the old
   value stays in the text, marked corrected.** A divergence against the
   original article or the private benchmark is declared in
   `docs/declared-differences.md`, never resolved by adjusting a
   definition until the numbers match (see `CLAUDE.md`).
5. **Changing the replication universe, an outlier threshold, or the
   airline-grouping table is an ADR**, recorded in `DECISIONS.md` — not a
   parameter to tune until a benchmark cell agrees.

## Data availability while you work

`data/raw/`, `data/staged/` and `data/derived/` are git-ignored on purpose
— you regenerate them locally (`just fetch`, `just stage`, once those
phases land) instead of pulling them from git. `data/external/*.csv` is
the exception: small, hand-curated reference tables (the node map, airline
groups, the IAC 1504 taxonomy), each row citing its own source and URL,
committed because their diff is exactly what needs to stay reviewable in a
pull request.

## Style

Commit messages: `type(scope): summary`, scopes `vra data replication ml
docs ci`. A fix to a number already in prose is always `fix`, never
`docs`, even when the diff is only text.
