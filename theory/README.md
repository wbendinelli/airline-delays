# theory/

The theory behind the replicated article, derived and checked (`DECISIONS.md`
ADR-0019). Run it with `just theory` (writes `reports/theory/`); it is offline,
deterministic and takes about a second.

| module | what it owns |
|---|---|
| `model.py` | the symbolic model (sympy): equations (1)-(12) of the author's 2013 monograph, section 4, after Brueckner and Van Dender (2008); the follower's reaction slope and its bounds; the tolls of Proposition 1; the Cournot, atomistic and monopoly benchmarks; the inelastic-demand case and the condition under which its bounds hold; `IDENTITIES` (every algebraic statement, with the callable that checks it) and `ASSUMPTIONS` (what is assumed, not proved). |
| `families.py` | concrete primitives for the numeric examples: linear and quadratic congestion cost, linear inverse demand. |
| `equilibrium.py` | numeric solutions by bracketed root-finding: social optimum, Stackelberg, Cournot, atomistic, monopoly, the tolls at the symmetric optimum, comparative statics over cost curvature and demand slope, and this repository's extension -- a Cournot game with a lower-cost entrant. |
| `figures.py` | the five congestion-economics diagrams of the monograph's section 2, redrawn as hand-written SVG from piecewise-linear curves; every labelled point, triangle area and toll is computed and written to `figures.json`. Nothing is copied from the source papers. |
| `bridge.py` | theory object -> article variable -> published sign, joined with `replication/published.json`. The mapping and the expected signs are judgment, recorded once; the coefficients are read, never typed. |
| `run.py` | drives all of it and writes `reports/theory/model.json`, `figures.json`, `figures/*.svg` and `results.md`. |

Three things to know before quoting a number out of this directory.

**Derived, restated and added are labelled apart.** Each identity carries an
`origin`: `monograph` (the monograph's own statement), `BVD` (Brueckner and
Van Dender 2008, restated), `Brueckner (2002)` (the benchmarks), or `here`
(what this derivation adds: `f1 = f2/(1 - lambda) >= 2 f2`, the leader's toll
at exactly three quarters of the marginal congestion damage under linear cost,
the condition `c''/s >= s^2 d''` for the inelastic-demand bounds, the linear
closed forms, and the low-cost entrant). The Portuguese chapters keep the same
three labels.

**sympy checks algebra, not economics.** An identity holding means the
statement follows from the declared assumptions (`model.json["assumptions"]`);
it says nothing about whether airlines behave as the model assumes. Nothing
here is estimated on data; the econometrics of reference is the 2016 article's,
replicated under `replication/`.

**The report is a pure function of the code.** `model.json` and the figures
carry no timestamp or commit, so `tests/test_theory.py` rebuilds them in memory
and fails when the committed copy is stale, naming `just theory`.
