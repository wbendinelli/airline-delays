"""`vra` — reconstruction of Brazilian airline delay data from ANAC's VRA files.

The package is layered: `io` fetches and describes the raw monthly CSVs,
`stage` parses them into one canonical flight table, `keys` builds nodes and
routes, `universe` applies the replication and prediction filters, `delays`
computes signed delays and thresholds, and `registry` is the single source of
truth for every column that reaches a public table.
"""

__all__ = ["__version__"]

__version__ = "0.1.0"
