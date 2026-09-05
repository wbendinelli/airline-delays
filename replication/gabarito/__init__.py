"""The only package allowed to read the private benchmark.

Everything here is reached through the ``AIRLINE_DELAYS_PRIVATE_DIR``
environment variable and nothing here writes a private value anywhere: the one
artefact it produces, ``data/analysis/taxas.csv``, holds agreement rates,
median and p90 absolute differences and row counts — statistics *about* the
comparison, never the benchmark's own numbers. See `SECURITY.md` and
`CLAUDE.md`.
"""
