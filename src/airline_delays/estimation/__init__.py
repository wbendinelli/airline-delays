"""Stage 6 -- estimation: Tables 2-7 of Bendinelli, Bettini & Oliveira (2016), re-estimated on
the article's own panel and compared with the published values (`airline-delays estimate`).

``article_panel``
    Curates the authors' final base into ``data/analysis/article_panel_route_month.parquet``
    (ADR-0020). Run once, on the author's machine; the output is committed.
``specification``
    Regressors, instruments, regressands, the column contract, the HAC settings.
``loader`` / ``sample``
    Reads the panel, rebuilds the route, time and seasonality dummies, applies the
    do-files' sample filters, builds the design matrix.
``estimators``
    2SGMM, LIML and OLS with the Bartlett HAC kernel; Hansen J; the Kleibergen-Paap
    statistics of ``kp``.
``table2`` ... ``table7``
    One module per published table, one ``ColumnSpec`` per column.
``published``
    The published tables parsed from the article's text into ``published.json``.
``compare`` / ``report`` / ``sensitivity`` / ``run``
    The comparison with the published values, the Markdown report, the seasonality grid and
    the orchestrator that writes ``reports/replication/``.

Every re-estimated coefficient is compared with the published one and the comparison is
written down in ``reports/replication/`` and ``docs/notes/replication.md``.
"""

from __future__ import annotations

__all__ = [
    "common",
    "kp",
    "published",
    "run",
    "sensitivity",
    "table2",
    "table3",
    "table4",
    "table5",
    "table6",
    "table7",
]
