"""Write ``reports/theory/``: ``model.json``, ``figures.json``, the SVG figures and ``results.md``.

Everything the Portuguese chapters under ``docs/study/`` quote about the
model comes out of this script. It is deterministic and offline: no
timestamp, no git commit and no wall time reaches the files (the elapsed
time goes to stdout only), so a second run on an unchanged tree changes
nothing under ``reports/theory/`` -- which is what lets
``tests/test_theory.py`` fail when the committed report is stale.

Usage::

    uv run airline-delays theory
    uv run airline-delays theory --outdir /tmp/theory
"""

from __future__ import annotations

import argparse
import json
import math
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

import sympy

from airline_delays import paths
from airline_delays.theory import bridge as bridge_module
from airline_delays.theory import equilibrium, figures, model
from airline_delays.theory import primer as primer_module

REPO_ROOT = paths.REPO_ROOT
REPORT_DIR = REPO_ROOT / "reports" / "theory"
GENERATED_BY = "airline-delays theory"
SOURCE = (
    "Bendinelli (2013), undergraduate monograph, USP, section 4, following Brueckner "
    "and Van Dender (2008, Journal of Urban Economics 64, 288-295) and Brueckner (2002, "
    "American Economic Review 92, 1357-1375); figures after Cohen and Coughlin (2003) and "
    "Cohen, Coughlin and Ott (2009), redrawn"
)
EXAMPLES = ("linear", "quadratic", "inelastic_linear_demand")
RESIDUAL_TOLERANCE = 1e-8


# ---------------------------------------------------------------- cleaning
def _clean(value: Any) -> Any:
    """Round floats to 10 significant digits, map NaN/inf to null, keep everything else."""
    if isinstance(value, bool):
        return value
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        return float(f"{value:.10g}")
    if isinstance(value, dict):
        out = {}
        for key, item in value.items():
            if key == "foc_residuals":
                worst = max(abs(v) for v in item.values())
                out["foc_residuals_ok"] = worst < RESIDUAL_TOLERANCE
                out["foc_residual_tolerance"] = RESIDUAL_TOLERANCE
            else:
                out[key] = _clean(item)
        return out
    if isinstance(value, list | tuple):
        return [_clean(v) for v in value]
    return value


def _sym(expr: Any) -> str:
    return str(expr)


# ------------------------------------------------------------------- build
def build() -> dict[str, Any]:
    """The whole ``model.json`` payload, computed in memory; raises if an identity fails."""
    identities = model.verify_identities()
    failed = [item["id"] for item in identities if not item["holds"]]
    if failed:
        raise RuntimeError(f"identities of theory.model do not hold: {failed}")
    lin = model.linear_closed_forms()
    inel = model.inelastic_linear_closed_forms()
    tolls = model.tolls_symmetric()
    leader_toll = model.toll_leader()
    pieces = model.inelastic_slope_pieces()
    limits = model.inelastic_limits()
    bounds = model.lambda_bounds()
    payload: dict[str, Any] = {
        "meta": {
            "generated_by": GENERATED_BY,
            "source": SOURCE,
            "sympy": sympy.__version__,
            "n_identities": len(identities),
            "equations": "numbered as in the monograph, (1) to (12)",
        },
        "assumptions": [asdict(item) for item in model.ASSUMPTIONS],
        "identities": identities,
        "reaction_slope": {
            "expression": _sym(model.reaction_slope()),
            "x": "f2 c''/c'",
            "lambda_of_x": _sym(model.lambda_of_x()),
            "lambda_minus_half": _sym(bounds["lambda_minus_half"]),
            "one_minus_lambda": _sym(bounds["one_minus_lambda"]),
            "lambda_lower": 0.5,
            "lambda_upper_exclusive": 1.0,
            "lambda_linear_cost": 0.5,
        },
        "leader_follower": {
            "f1": _sym(model.leader_follower_ratio()),
            "f1_minus_2_f2": "f2 x",
            "statement": "f1 = f2/(1 - lambda) >= 2 f2; equality under linear cost",
        },
        "tolls": {
            "MCD": "(f1 + f2) c'",
            "leader_difference_form": _sym(leader_toll["difference_form"]),
            "leader_share_form": _sym(leader_toll["share_form"]),
            "follower": _sym(model.toll_follower()),
            "leader_symmetric_share": _sym(tolls["leader"]),
            "leader_over_MCD_linear": float(tolls["leader_linear_cost"]),
            "leader_over_MCD_linear_exact": _sym(tolls["leader_linear_cost"]),
            "follower_over_MCD": float(tolls["follower"]),
            "cournot_over_MCD": float(tolls["cournot"]),
            "atomistic_over_MCD": float(tolls["atomistic"]),
            "monopoly_over_MCD": float(tolls["monopoly"]),
        },
        "benchmarks": {name: _sym(expr) for name, expr in model.benchmarks().items()},
        "linear_closed_forms": {
            **{name: _sym(expr) for name, expr in lin.items()},
            "loss_share_cournot_float": float(lin["loss_share_cournot"]),
            "loss_share_stackelberg_float": float(lin["loss_share_stackelberg"]),
            "loss_share_atomistic_float": float(lin["loss_share_atomistic"]),
        },
        "inelastic": {
            "leader_foc": _sym(model.foc_leader_inelastic()),
            "social_foc": _sym(model.foc_social_inelastic()),
            "limit_slope_minus_one": _sym(limits["slope_minus_one"]),
            "limit_slope_minus_half": _sym(limits["slope_minus_half"]),
            "market_power_term_at_minus_half": _sym(limits["market_power_term_at_minus_half"]),
            "uninternalised_term_at_minus_half": _sym(limits["uninternalised_term_at_minus_half"]),
            "atomistic_toll_per_seat": _sym(limits["atomistic_toll_per_seat"]),
            "slope_general": _sym(pieces["slope"]),
            "slope_A": _sym(pieces["A"]),
            "slope_B": _sym(pieces["B"]),
            "slope_bounds_condition": "c''/s >= s^2 d''",
            "slope_linear_demand": _sym(model.reaction_slope_linear_demand()),
            "closed_forms": {name: _sym(expr) for name, expr in inel.items()},
        },
        "examples": {name: equilibrium.example(name) for name in EXAMPLES},
        "comparative_statics": equilibrium.comparative_statics(),
        "extension_lcc": equilibrium.lcc_extension(),
        "bridge": bridge_module.bridge(),
        "primer": primer_module.primer(),
    }
    return _clean(payload)


# ---------------------------------------------------------------- markdown
def _n(value: Any, digits: int = 4) -> str:
    if value is None:
        return "-"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, int):
        return f"{value:,}"
    if isinstance(value, float):
        if value == int(value) and abs(value) < 1e6:
            return f"{value:,.0f}" if abs(value) >= 1000 else f"{value:.0f}"
        return f"{value:,.{digits}f}"
    return str(value)


def write_markdown(payload: dict[str, Any], figs: dict[str, Any]) -> str:
    lines: list[str] = []
    add = lines.append
    add("# The theory layer - results")
    add("")
    add(
        f"Generated by `{GENERATED_BY}` from `airline_delays.theory`. Source: {payload['meta']['source']}. "
        "No number below is typed by hand; the Portuguese chapters under `docs/study/` quote "
        "this file's inputs (`model.json`, `figures.json`) by key."
    )
    add("")
    add("## 1. Identities")
    add("")
    add(
        f"{payload['meta']['n_identities']} algebraic statements, each checked with sympy "
        f"{payload['meta']['sympy']}. `origin` says whose statement it is: the monograph's, "
        "Brueckner and Van Dender's (BVD), Brueckner (2002)'s, or this repository's (`here`)."
    )
    add("")
    add("| id | equation | origin | holds | statement |")
    add("|---|---|---|---|---|")
    for item in payload["identities"]:
        add(
            f"| `{item['id']}` | {item['equation']} | {item['origin']} | {_n(item['holds'])} | {item['statement']} |"
        )
    add("")
    add("## 2. The follower's reaction and the leader's advantage")
    add("")
    rs = payload["reaction_slope"]
    add(
        f"- Equation (8): `df2/df1 = {rs['expression']}`; with `x = {rs['x']}`, `lambda = {rs['lambda_of_x']}`."
    )
    add(
        f"- `lambda - 1/2 = {rs['lambda_minus_half']}` and `1 - lambda = {rs['one_minus_lambda']}`, so `{rs['lambda_lower']} <= lambda < {rs['lambda_upper_exclusive']:.0f}`; `lambda = {rs['lambda_linear_cost']}` under linear cost."
    )
    add(
        f"- `[here]` {payload['leader_follower']['statement']} (`f1 = {payload['leader_follower']['f1']}`)."
    )
    add("")
    add("## 3. Proposition 1: the tolls at the symmetric optimum, as shares of MCD*")
    add("")
    t = payload["tolls"]
    add("| structure | toll / MCD* |")
    add("|---|---|")
    add(f"| monopoly | {_n(t['monopoly_over_MCD'])} |")
    add(f"| Cournot duopolist, and the Stackelberg follower | {_n(t['follower_over_MCD'])} |")
    add(
        f"| Stackelberg leader | `{t['leader_symmetric_share']}`; {_n(t['leader_over_MCD_linear'])} (= {t['leader_over_MCD_linear_exact']}) under linear cost |"
    )
    add(f"| atomistic | {_n(t['atomistic_over_MCD'])} |")
    add("")
    add(
        f"`MCD = {t['MCD']}`; `T1 = {t['leader_difference_form']} = {t['leader_share_form']}`; `T2 = {t['follower']}`."
    )
    add("")
    add("## 4. Numeric examples")
    add("")
    for name, ex in payload["examples"].items():
        st, opt, tl = ex["stackelberg"], ex["social_optimum"], ex["tolls_at_symmetric_optimum"]
        cost = ", ".join(f"{k} = {_n(v)}" for k, v in ex["cost"].items() if k != "family")
        demand = (
            "perfectly elastic"
            if ex["demand"] is None
            else ", ".join(f"{k} = {_n(v)}" for k, v in ex["demand"].items() if k != "family")
        )
        add(f"### {name}")
        add("")
        add(
            f"Primitives p = {_n(ex['primitives']['p'])}, tau = {_n(ex['primitives']['tau'])}, s = {_n(ex['primitives']['s'])}; cost {ex['cost']['family']} ({cost}); demand {demand}."
        )
        add("")
        add("| quantity | value |")
        add("|---|---|")
        add(f"| F* (efficient total), W* | {_n(opt['F_star'])}, {_n(opt['welfare_star'])} |")
        add(
            f"| lambda*, T1*/MCD*, T1*, T2* | {_n(tl['lambda_star'])}, {_n(tl['T1_star_over_MCD'])}, {_n(tl['T1_star'])}, {_n(tl['T2_star'])} |"
        )
        add(f"| Stackelberg f1, f2, F | {_n(st['f1'])}, {_n(st['f2'])}, {_n(st['F'])} |")
        add(
            f"| Stackelberg lambda, f1/f2, T1/MCD, T1, T2 | {_n(st['lam'])}, {_n(st['f1'] / st['f2'])}, {_n(st['T1_over_MCD'])}, {_n(st['T1'])}, {_n(st['T2'])} |"
        )
        add(
            f"| Stackelberg profits, welfare, loss share | {_n(st['profit1'])}, {_n(st['profit2'])}, {_n(st['welfare'])}, {_n(st['loss_share'])} |"
        )
        add(
            f"| Cournot f, F, loss share | {_n(ex['cournot']['f1'])}, {_n(ex['cournot']['F'])}, {_n(ex['cournot']['loss_share'])} |"
        )
        add(
            f"| atomistic F, loss share | {_n(ex['atomistic']['F'])}, {_n(ex['atomistic']['loss_share'])} |"
        )
        add(f"| monopoly F | {_n(ex['monopoly']['F'])} |")
        if "equation_12_terms_at_stackelberg" in ex:
            e12 = ex["equation_12_terms_at_stackelberg"]
            add(
                f"| equation (12) at the Stackelberg point: market-power term, uninternalised term, atomistic toll per seat | {_n(e12['market_power_term'])}, {_n(e12['uninternalised_term'])}, {_n(e12['atomistic_toll_per_seat'])} |"
            )
        add("")
    add("## 5. Comparative statics `[here]`")
    add("")
    add("Cost curvature `q` in `c = 1000 + 50 F + q F^2`, perfectly elastic demand:")
    add("")
    add("| q | F* | lambda* | T1*/MCD* | Stackelberg lambda | f1/f2 | T1/MCD | loss share |")
    add("|---|---|---|---|---|---|---|---|")
    for row in payload["comparative_statics"]["cost_curvature"]:
        add(
            f"| {_n(row['q'])} | {_n(row['F_star'])} | {_n(row['lambda_star'])} | {_n(row['T1_star_over_MCD'])} | {_n(row['stackelberg_lambda'])} | {_n(row['f1_over_f2'])} | {_n(row['T1_over_MCD'])} | {_n(row['loss_share'])} |"
        )
    add("")
    add(
        "Demand slope `dd` in `d(Q) = 400 - dd Q`, linear cost `1000 + 100 F` (`dd = 0` is the perfectly elastic case):"
    )
    add("")
    add("| dd | f1 | f2 | F | F* | price | market-power term | uninternalised term | loss share |")
    add("|---|---|---|---|---|---|---|---|---|")
    for row in payload["comparative_statics"]["demand_slope"]:
        add(
            f"| {_n(row['dd'])} | {_n(row['f1'])} | {_n(row['f2'])} | {_n(row['F'])} | {_n(row['F_star'])} | {_n(row['price'])} | {_n(row['market_power_term'])} | {_n(row['uninternalised_term'])} | {_n(row['loss_share'])} |"
        )
    add("")
    add("## 6. Extension of this repository: a low-cost entrant in a Cournot game")
    add("")
    lcc = payload["extension_lcc"]
    tri = lcc["triopoly"]
    add(
        f"{lcc['label'].capitalize()}. Two incumbents at tau = {_n(lcc['incumbent_tau'])} and an entrant at tau = {_n(lcc['entrant_tau'])}, linear cost."
    )
    add("")
    add("| quantity | value |")
    add("|---|---|")
    add(
        f"| total flights F | {_n(tri['F'])} (Cournot duopoly of incumbents: {_n(lcc['duopoly_cournot']['F'])}; Stackelberg duopoly: {_n(lcc['stackelberg_duopoly_F'])}) |"
    )
    add(
        f"| flights: entrant, incumbents | {_n(tri['flights'][0])}, {_n(tri['flights'][1])}, {_n(tri['flights'][2])} |"
    )
    add(
        f"| internalised share of MCD: entrant, incumbents | {_n(tri['internalised_share'][0])}, {_n(tri['internalised_share'][1])}, {_n(tri['internalised_share'][2])} |"
    )
    add("")
    add("## 7. Bridge to the 2016 article (published signs, Table 3 column 2 and Table 6 column 2)")
    add("")
    add(
        "| variable | theory object | expected | Table 3 (2): b, stars | Table 6 (2): b, stars | pattern over the six columns of Table 3 |"
    )
    add("|---|---|---|---|---|---|")
    br = payload["bridge"]
    labels = {row["variable"]: row["theory_object"] for row in br["rows"]}
    for var, info in br["tables"]["table3"]["variables"].items():
        c3 = info["columns"]["2"]
        c6 = br["tables"]["table6"]["variables"][var]["columns"]["2"]
        pat = info["pattern"]
        add(
            f"| `{var}` | {labels[var]} | {info['expected_sign'] or '-'} | {_n(c3['b'])} {c3['stars'] or ''} | {_n(c6['b'])} {c6['stars'] or ''} | +{pat['positive']} / -{pat['negative']} / absent {pat['absent']} |"
        )
    add("")
    add("## 8. The five figures")
    add("")
    for info in figs["figures"].values():
        add(f"### {info['title']}")
        add("")
        add(f"![{info['title']}]({info['file']})")
        add("")
        add("| quantity | value |")
        add("|---|---|")
        for name, value in info["quantities"].items():
            add(f"| {name} | {_n(value)} |")
        add("")
        add(f"{info['note']}")
        add("")
    add("## 9. The primer's 2 x 2 game `[here]`")
    add("")
    pr = payload["primer"]
    game = pr["two_by_two"]
    low, high = game["strategies"]["low"]["volume"], game["strategies"]["high"]["volume"]
    add(
        f"{pr['label'].capitalize()}. Each airline flies either f* = {_n(low)} (the efficient per-firm volume) "
        f"or {_n(high)} (the Cournot volume); cells are (airline 1's profit, airline 2's profit)."
    )
    add("")
    for label, block in (
        ("no toll", game),
        (f"toll {_n(game['with_toll']['toll_per_flight'])} per flight", game["with_toll"]),
    ):
        cells = block["cells"]
        add(f"| {label} | airline 2 flies {_n(low)} | airline 2 flies {_n(high)} |")
        add("|---|---|---|")
        for s1, f in (("low", low), ("high", high)):
            row = [
                f"{_n(cells[f'{s1}_{s2}']['profit1'])}, {_n(cells[f'{s1}_{s2}']['profit2'])}"
                for s2 in ("low", "high")
            ]
            add(f"| airline 1 flies {_n(f)} | {row[0]} | {row[1]} |")
        add("")
        add(f"Dominant strategy: {block['dominant_strategy']}; Nash cell: `{block['nash']}`.")
        add("")
    dev = game["deviation_from_cooperation"]
    add(
        f"Prisoner's dilemma: {_n(game['is_prisoners_dilemma'])}. One deviation from the cooperative cell adds "
        f"{_n(dev['extra_flights'])} flights, raises c by {_n(dev['extra_cost_per_flight'])} per flight, "
        f"gains the deviator {_n(dev['gain_to_deviator'])} and costs the rival {_n(dev['loss_to_rival'])}."
    )
    add("")
    add("| f1 | follower's reaction f2 | leader's profit along the reaction |")
    add("|---|---|---|")
    along = {row["f1"]: row for row in pr["leader_profit_along_reaction"]}
    for point in pr["reaction_function"]["points"]:
        profit = along.get(point["f1"])
        add(
            f"| {_n(point['f1'])} | {_n(point['f2'])} | {_n(profit['profit1']) if profit else '-'} |"
        )
    add("")
    shares = pr["internalised_share_of_MCD"]
    add(
        "Internalised share of MCD: "
        + ", ".join(f"{name.replace('_', ' ')} {_n(value)}" for name, value in shares.items())
        + "."
    )
    return "\n".join(lines).rstrip() + "\n"


# --------------------------------------------------------------------- run
def _dump(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def run(outdir: Path = REPORT_DIR) -> dict[str, Any]:
    """Write the four kinds of output under ``outdir`` and return what was written."""
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    payload = build()
    figs = figures.draw_all(outdir)
    (outdir / "model.json").write_text(_dump(payload), encoding="utf-8")
    (outdir / "figures.json").write_text(_dump(figs), encoding="utf-8")
    (outdir / "results.md").write_text(write_markdown(payload, figs), encoding="utf-8")
    return {"model": payload, "figures": figs, "outdir": outdir}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Derive, check and print the theory layer")
    parser.add_argument("--outdir", default=None, help=f"where to write (default: {REPORT_DIR})")
    args = parser.parse_args(argv)
    started = time.perf_counter()
    written = run(Path(args.outdir) if args.outdir else REPORT_DIR)
    payload = written["model"]
    tolls = payload["tolls"]
    linear = payload["examples"]["linear"]["stackelberg"]
    print(
        f"theory: {payload['meta']['n_identities']} identities hold; "
        f"leader's toll under linear cost = {tolls['leader_over_MCD_linear']} MCD*; "
        f"linear Stackelberg f1 = {linear['f1']:g}, f2 = {linear['f2']:g}; "
        f"{len(written['figures']['figures'])} figures; "
        f"{time.perf_counter() - started:.1f} s"
    )
    print(f"wrote {written['outdir'] / 'model.json'}, figures.json, figures/*.svg, results.md")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
