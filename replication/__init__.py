"""Replication of Tables 2-7 of Bendinelli, Bettini and Oliveira (2016).

The article -- *Airline delays, congestion internalization and non-price
spillover effects of low cost carrier entry*, Transportation Research Part A 85,
39-52, `doi:10.1016/j.tra.2016.01.001` -- is reproduced here column by column
from a route-month panel, against the numbers parsed out of the published text
into :mod:`replication.published`.

Layout
------
``common``
    The :class:`~replication.common.Source` switch (private benchmark vs the
    public panel this repository rebuilds), the sample filters, the regressor
    and instrument lists, the dummies, the HAC settings and :func:`fit`.
``kp``
    Kleibergen-Paap rk LM and rk Wald F, plus Cragg-Donald. Written from the
    paper because no Python package implements them.
``published``
    The published numbers, parsed once out of the article text.
``table2`` .. ``table7``
    One module per published table.
``sensitivity``
    ADR-0008: the main coefficients across outlier thresholds and with or
    without the seasonality dummies.
``run``
    Runs everything and writes ``reports/replication/``.

Nothing here is ever tuned to make a number match. Where the replication and
the article disagree, the disagreement is measured and written down -- in
``docs/declared-differences.md`` and ``docs/notes/replication.md``.
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
