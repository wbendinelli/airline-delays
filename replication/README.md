# replication/

Reproduces Tables 2-7 of Bendinelli, Bettini & Oliveira (2016,
*Transportation Research Part A*, `10.1016/j.tra.2016.01.001`) from public
data only: `table2.py` through `table7.py`, plus `especificacao.md`
(the specification notes carried over from the archive's reconstruction
work).

`gabarito/` is the **only** module in this repository allowed to read the
private benchmark, and only through the `AIRLINE_DELAYS_PRIVATE_DIR`
environment variable (see `CLAUDE.md`, `SECURITY.md`). It commits a single
derived file, `taxas.csv` -- the agreement rate against the benchmark --
never the benchmark itself. Every test that depends on `gabarito/` carries
the pytest marker `gabarito` and is skipped when the environment variable
is unset.

Nothing under this directory exists yet; it lands with the replication
phase (see `ROADMAP.md`).
