"""The theory layer: the algebra holds, the numbers agree, the figures are exact, the report is fresh.

Four things are checked, none of which needs data or the network:

1. every identity in ``theory.model.IDENTITIES`` holds, plus the four the
   tutorial quotes by name;
2. the numeric examples agree with the closed forms (linear cost) and with an
   independent ``sympy.nsolve`` solution (quadratic cost), and the orderings the
   monograph states -- ``f1 > f2``, ``1/2 <= lambda < 1``, the leader's toll
   between the Cournot and the atomistic toll -- come out of the numbers;
3. the five SVG figures parse, carry the monograph's labels, and every labelled
   point lies on the curves that define it;
4. ``reports/theory/`` is what today's code produces: ``model.json`` (meta
   aside), ``figures.json``, the SVG files and ``results.md`` are rebuilt in
   memory and compared, so a ``airline_delays.theory`` edit without ``just theory`` fails here.
"""

from __future__ import annotations

import json
import math
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import pytest
import sympy as sp

from airline_delays.theory import equilibrium, figures, model, primer, run
from airline_delays.theory.families import LinearCost, LinearDemand, Primitives, QuadraticCost

ROOT = Path(__file__).resolve().parents[1]

REPORT = ROOT / "reports" / "theory"
MODEL_KEYS = {
    "meta",
    "assumptions",
    "identities",
    "reaction_slope",
    "leader_follower",
    "tolls",
    "benchmarks",
    "linear_closed_forms",
    "inelastic",
    "examples",
    "comparative_statics",
    "extension_lcc",
    "bridge",
    "primer",
}
SVG_TAG = "{http://www.w3.org/2000/svg}svg"


# ------------------------------------------------------------ 1. identities
class TestSymbolicIdentities:
    @pytest.mark.parametrize("identity", model.IDENTITIES, ids=lambda item: item.id)
    def test_holds(self, identity: model.Identity) -> None:
        assert identity.check(), identity.statement

    def test_every_identity_names_its_origin(self) -> None:
        origins = {item.origin for item in model.IDENTITIES}
        assert origins == {"monograph", "BVD", "Brueckner (2002)", "here"}
        assert len({item.id for item in model.IDENTITIES}) == len(model.IDENTITIES)

    def test_reaction_slope_is_minus_one_half_under_linear_cost(self) -> None:
        assert sp.simplify(model.reaction_slope().subs(model.c2, 0)) == -sp.Rational(1, 2)

    def test_leader_toll_at_symmetric_optimum_is_three_quarters_of_mcd_under_linear_cost(
        self,
    ) -> None:
        share = model.tolls_symmetric()["leader"].subs(model.lam, sp.Rational(1, 2))
        assert share == sp.Rational(3, 4)
        assert model.tolls_symmetric()["cournot"] < share < model.tolls_symmetric()["atomistic"]

    def test_follower_toll_has_the_cournot_form(self) -> None:
        # F c' - f2 c' = f1 c': the follower pays the rival's flights times c'.
        assert (
            sp.simplify(
                (model.f1 + model.f2) * model.c1 - model.f2 * model.c1 - model.toll_follower()
            )
            == 0
        )

    def test_inelastic_slope_bounds_hold_under_linear_demand(self) -> None:
        slope = model.reaction_slope_inelastic().subs(model.d2, 0)
        k = model.c1 - model.s**2 * model.d1
        # -1 < slope: slope + 1 = k/(2k + f2 c'') > 0; slope <= -1/2: -slope - 1/2 = f2 c''/(2(2k + f2 c'')) >= 0
        assert sp.simplify(slope + 1 - k / (2 * k + model.f2 * model.c2)) == 0
        assert (
            sp.simplify(
                -slope
                - sp.Rational(1, 2)
                - model.f2 * model.c2 / (2 * (2 * k + model.f2 * model.c2))
            )
            == 0
        )
        assert bool(k.is_positive)


class TestReactionSlopeBounds:
    def test_lambda_between_half_and_one_on_a_grid(self) -> None:
        expr = -model.reaction_slope()
        for c1 in (1.0, 50.0, 300.0):
            for c2 in (0.0, 0.5, 2.0, 40.0):
                for f2 in (0.1, 10.0, 200.0):
                    lam = float(expr.subs({model.c1: c1, model.c2: c2, model.f2: f2}))
                    assert 0.5 <= lam < 1.0
                    if c2 == 0.0:
                        assert lam == pytest.approx(0.5)

    def test_leader_flies_at_least_twice_the_follower(self) -> None:
        ratio = model.leader_follower_ratio()
        for lam in (0.5, 0.6, 0.9, 0.99):
            f1 = float(ratio.subs({model.f2: 1.0, model.lam: lam}))
            assert f1 >= 2.0 - 1e-12


# ------------------------------------------------------- 2. numeric examples
class TestNumericExamples:
    @staticmethod
    @pytest.fixture(scope="class")
    def examples() -> dict[str, Any]:
        return {name: equilibrium.example(name) for name in run.EXAMPLES}

    def test_linear_matches_the_closed_forms(self, examples: dict[str, Any]) -> None:
        prim, cost = Primitives(), LinearCost()
        D, b = prim.A - cost.a, cost.b
        ex = examples["linear"]
        st = ex["stackelberg"]
        assert ex["social_optimum"]["F_star"] == pytest.approx(D / (2 * b), rel=1e-9)
        assert st["f1"] == pytest.approx(D / (2 * b), rel=1e-9)
        assert st["f2"] == pytest.approx(D / (4 * b), rel=1e-9)
        assert ex["cournot"]["f1"] == pytest.approx(D / (3 * b), rel=1e-9)
        assert ex["atomistic"]["F"] == pytest.approx(D / b, rel=1e-9)
        assert ex["monopoly"]["F"] == pytest.approx(ex["social_optimum"]["F_star"], rel=1e-9)
        assert ex["cournot"]["loss_share"] == pytest.approx(1 / 9, rel=1e-9)
        assert st["loss_share"] == pytest.approx(1 / 4, rel=1e-9)
        assert ex["atomistic"]["loss_share"] == pytest.approx(1.0, rel=1e-9)
        assert ex["tolls_at_symmetric_optimum"]["T1_star_over_MCD"] == pytest.approx(0.75)
        assert st["T1"] == pytest.approx(st["T2"])  # T1 = T2 = f1 c' at any Stackelberg point

    @pytest.mark.parametrize("name", run.EXAMPLES)
    def test_the_monographs_orderings(self, examples: dict[str, Any], name: str) -> None:
        ex = examples[name]
        st, tolls = ex["stackelberg"], ex["tolls_at_symmetric_optimum"]
        assert st["f1"] > st["f2"]
        assert st["f1"] / st["f2"] == pytest.approx(1.0 / (1.0 - st["lam"]), rel=1e-9)
        assert 0.5 <= st["lam"] < 1.0
        assert 0.5 < st["T1_over_MCD"] < 1.0
        assert 0.5 < tolls["T1_star_over_MCD"] < 1.0
        assert tolls["T2_star"] == pytest.approx(0.5 * tolls["MCD_star"])
        assert max(abs(v) for v in st["foc_residuals"].values()) < 1e-8
        assert st["soc_leader"] < 0 and st["soc_follower"] < 0
        assert st["loss"] > 0

    def test_quadratic_agrees_with_an_independent_nsolve(self, examples: dict[str, Any]) -> None:
        prim, cost = Primitives(), QuadraticCost()
        x1, x2 = sp.symbols("x1 x2", positive=True)
        Fs = x1 + x2
        c = cost.a + cost.b * Fs + cost.q * Fs**2
        c1 = sp.diff(c, x1)
        c2 = sp.diff(c1, x1)
        follower = prim.A - c - x2 * c1
        slope = -(c1 + x2 * c2) / (2 * c1 + x2 * c2)
        leader = prim.A - c - x1 * c1 * (1 + slope)
        sol = sp.nsolve([follower, leader], [x1, x2], [30.0, 20.0], tol=1e-14)
        st = examples["quadratic"]["stackelberg"]
        assert float(sol[0]) == pytest.approx(st["f1"], abs=1e-8)
        assert float(sol[1]) == pytest.approx(st["f2"], abs=1e-8)
        assert examples["quadratic"]["tolls_at_symmetric_optimum"]["lambda_star"] > 0.5

    def test_inelastic_terms_of_equation_12(self, examples: dict[str, Any]) -> None:
        ex = examples["inelastic_linear_demand"]
        prim, cost, demand = Primitives(), LinearCost(), LinearDemand()
        terms = ex["equation_12_terms_at_stackelberg"]
        st = ex["stackelberg"]
        s = prim.s
        assert terms["market_power_term"] == pytest.approx(s * st["f1"] * demand.d1(0.0) * 0.5)
        assert terms["market_power_term"] < 0 < terms["uninternalised_term"]
        assert terms["uninternalised_term"] == pytest.approx(st["f1"] * cost.c1(st["F"]) * 0.5 / s)
        assert st["F"] > ex["social_optimum"]["F_star"]

    def test_lcc_extension_shares(self) -> None:
        ext = equilibrium.lcc_extension()
        shares = ext["triopoly"]["internalised_share"]
        assert sum(shares) == pytest.approx(1.0)
        assert shares[0] > shares[1] == pytest.approx(shares[2])
        assert ext["triopoly"]["F"] > ext["duopoly_cournot"]["F"]

    def test_comparative_statics_are_monotone_in_curvature(self) -> None:
        rows = equilibrium.comparative_statics()["cost_curvature"]
        lam = [row["lambda_star"] for row in rows]
        toll = [row["T1_star_over_MCD"] for row in rows]
        assert lam == sorted(lam) and toll == sorted(toll)
        assert lam[0] == pytest.approx(0.5) and toll[0] == pytest.approx(0.75)


# ---------------------------------------------------------- 2b. the primer
class TestPrimer:
    """The 2 x 2 game of the study's chapter 2 is cut out of the linear example, and says what it claims."""

    @staticmethod
    @pytest.fixture(scope="class")
    def block() -> dict[str, Any]:
        return primer.primer()

    @staticmethod
    @pytest.fixture(scope="class")
    def linear() -> dict[str, Any]:
        return equilibrium.example("linear")

    def test_the_strategies_are_the_efficient_and_the_cournot_volumes(
        self, block: dict[str, Any], linear: dict[str, Any]
    ) -> None:
        game = block["two_by_two"]
        assert game["strategies"]["low"]["volume"] == pytest.approx(
            linear["social_optimum"]["f_star"]
        )
        assert game["strategies"]["high"]["volume"] == pytest.approx(linear["cournot"]["f1"])
        cells = game["cells"]
        assert cells["low_low"]["total_profit"] == pytest.approx(
            linear["social_optimum"]["welfare_star"]
        )
        assert cells["high_high"]["profit1"] == pytest.approx(linear["cournot"]["profit1"])
        assert cells["high_high"]["profit2"] == pytest.approx(linear["cournot"]["profit2"])
        assert cells["high_low"]["profit1"] == cells["low_high"]["profit2"]  # symmetric game

    def test_the_game_is_a_prisoners_dilemma_whose_nash_cell_is_cournot(
        self, block: dict[str, Any]
    ) -> None:
        game = block["two_by_two"]
        o = game["ordering"]
        assert o["temptation"] > o["reward"] > o["punishment"] > o["sucker"]
        assert game["is_prisoners_dilemma"] is True
        assert game["best_response_of_airline_1"] == {"to_low": "high", "to_high": "high"}
        assert game["dominant_strategy"] == "high"
        assert game["nash"] == "high_high" and game["nash_cells"] == ["high_high"]
        assert game["cooperative"] == "low_low"
        dev = game["deviation_from_cooperation"]
        assert dev["gain_to_deviator"] > 0 > dev["change_in_total_profit"]
        assert dev["loss_to_rival"] == pytest.approx(
            dev["loss_to_rival_as_extra_cost_times_rival_flights"]
        )
        assert dev["gain_to_deviator"] - dev["loss_to_rival"] == pytest.approx(
            dev["change_in_total_profit"]
        )

    def test_the_toll_moves_the_nash_cell_to_the_cooperative_cell(
        self, block: dict[str, Any], linear: dict[str, Any]
    ) -> None:
        tolled = block["two_by_two"]["with_toll"]
        assert tolled["toll_per_flight"] == pytest.approx(
            linear["tolls_at_symmetric_optimum"]["T2_star"]
        )
        assert tolled["best_response_of_airline_1"] == {"to_low": "low", "to_high": "low"}
        assert tolled["dominant_strategy"] == "low"
        assert tolled["nash"] == "low_low"
        # the toll is a transfer: profits plus toll revenue equal the untolled total in every cell
        plain = block["two_by_two"]["cells"]
        for key, cell in tolled["cells"].items():
            assert cell["total_profit"] + cell["toll_revenue"] == pytest.approx(
                plain[key]["total_profit"]
            )

    def test_reaction_points_and_the_leaders_profit_match_the_closed_forms(
        self, block: dict[str, Any], linear: dict[str, Any]
    ) -> None:
        prim, cost = Primitives(), LinearCost()
        D, b = prim.A - cost.a, cost.b
        reaction = block["reaction_function"]
        assert reaction["slope"] == pytest.approx(-0.5)
        assert reaction["intercept"] == pytest.approx(D / (2 * b))
        for point in reaction["points"]:
            assert point["f2"] == pytest.approx(max(0.0, (D - b * point["f1"]) / (2 * b)))
        along = block["leader_profit_along_reaction"]
        best = max(along, key=lambda row: row["profit1"])
        st = linear["stackelberg"]
        assert best["f1"] == pytest.approx(st["f1"]) and best["f2"] == pytest.approx(st["f2"])
        assert best["profit1"] == pytest.approx(st["profit1"])
        assert best["profit2"] == pytest.approx(st["profit2"])

    def test_internalised_shares_are_one_minus_the_tolls(
        self, block: dict[str, Any], linear: dict[str, Any]
    ) -> None:
        shares = block["internalised_share_of_MCD"]
        st = linear["stackelberg"]
        assert shares["monopoly"] == 1.0 and shares["atomistic"] == 0.0
        assert shares["cournot_symmetric"] == pytest.approx(1 - linear["cournot"]["T1_over_MCD"])
        assert shares["stackelberg_leader_at_equilibrium"] == pytest.approx(1 - st["T1_over_MCD"])
        assert shares["stackelberg_follower_at_equilibrium"] == pytest.approx(1 - st["T2_over_MCD"])


# ---------------------------------------------------------------- 3. figures
class TestFigures:
    @staticmethod
    @pytest.fixture(scope="class")
    def drawn(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, dict[str, Any]]:
        out = tmp_path_factory.mktemp("figures")
        return out, figures.draw_all(out)

    def test_svgs_parse_and_carry_the_monographs_labels(
        self, drawn: tuple[Path, dict[str, Any]]
    ) -> None:
        out, payload = drawn
        assert set(payload["figures"]) == set(figures.FIGURES) and len(figures.FIGURES) == 11
        for key, info in payload["figures"].items():
            markup = (out / info["file"]).read_text(encoding="utf-8")
            root = ET.fromstring(markup)
            assert root.tag == SVG_TAG, key
            assert info["insight"] and info["title"] and info["quantities"], key
        economics = (out / "figures/fig1_nivel_eficiente.svg").read_text(encoding="utf-8")
        assert "CMgS" in economics and "CMgP" in economics and "BMg" in economics

    def test_points_lie_on_their_curves(self, drawn: tuple[Path, dict[str, Any]]) -> None:
        _, payload = drawn
        P, S, B = figures.cmgp(), figures.cmgs(), figures.bmg()
        pts = payload["figures"]["fig1"]["points"]
        qa, pa = pts["A"]
        qc, pc = pts["C"]
        assert pa == pytest.approx(P(qa)) and pa == pytest.approx(B(qa))
        assert pc == pytest.approx(S(qc)) and pc == pytest.approx(B(qc))
        assert pts["B"][1] == pytest.approx(S(qa)) and pts["D"] == [qa, pc]
        f5 = payload["figures"]["fig5"]["quantities"]
        assert f5["Q_star_equals_Q_0"] is True

    def test_the_areas_and_tolls_the_text_relies_on(
        self, drawn: tuple[Path, dict[str, Any]]
    ) -> None:
        _, payload = drawn
        q1 = payload["figures"]["fig1"]["quantities"]
        assert q1["triangle_ABC_area"] == pytest.approx(80.0)
        assert q1["toll_pigou_at_QS"] > q1["toll_AD_equals_PS_minus_PP"]
        q2 = payload["figures"]["fig2"]["quantities"]
        assert (
            q2["triangle_CEF_area_price_regulation"] < q2["triangle_ABC_area_quantity_regulation"]
        )
        q3 = payload["figures"]["fig3"]["quantities"]
        assert q3["elastic_still_congested_after"] and q3["inelastic_uncongested_after"]


# ------------------------------------------------------------- 4. the report
def _close(left: Any, right: Any, path: str = "") -> None:
    if isinstance(left, float) or isinstance(right, float):
        assert isinstance(left, int | float) and isinstance(right, int | float), path
        assert math.isclose(left, right, rel_tol=1e-9, abs_tol=1e-12), (path, left, right)
    elif isinstance(left, dict):
        assert isinstance(right, dict) and left.keys() == right.keys(), (
            path,
            left.keys() ^ right.keys(),
        )
        for key in left:
            _close(left[key], right[key], f"{path}.{key}")
    elif isinstance(left, list):
        assert isinstance(right, list) and len(left) == len(right), path
        for i, (a, b) in enumerate(zip(left, right, strict=True)):
            _close(a, b, f"{path}[{i}]")
    else:
        assert left == right, (path, left, right)


class TestRunWritesTheReport:
    def test_writes_every_file_with_stable_keys(self, tmp_path: Path) -> None:
        written = run.run(outdir=tmp_path)
        assert set(written["model"]) == MODEL_KEYS
        for name in ("model.json", "figures.json", "results.md"):
            assert (tmp_path / name).exists()
        assert len(list((tmp_path / "figures").glob("*.svg"))) == 11
        text = (tmp_path / "model.json").read_text(encoding="utf-8")
        assert "NaN" not in text and "Infinity" not in text
        assert all(item["holds"] for item in written["model"]["identities"])

    def test_the_committed_report_is_untouched_by_a_run_elsewhere(self, tmp_path: Path) -> None:
        run.run(outdir=tmp_path)
        status = subprocess.run(
            ["git", "status", "--porcelain", "--", "reports/theory"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert all(not line.startswith("??") for line in status.stdout.splitlines() if line.strip())


class TestTheCommittedReportIsNotStale:
    """`just theory` and commit the result -- a theory/ edit without it fails here."""

    def test_model_json(self) -> None:
        committed = json.loads((REPORT / "model.json").read_text(encoding="utf-8"))
        fresh = run.build()
        committed.pop("meta")
        fresh.pop("meta")
        _close(fresh, committed, "model")

    def test_figures_json_and_svgs(self, tmp_path: Path) -> None:
        fresh = figures.draw_all(tmp_path)
        committed = json.loads((REPORT / "figures.json").read_text(encoding="utf-8"))
        assert fresh == committed, "run `just theory` and commit the result"
        for info in fresh["figures"].values():
            markup = (REPORT / info["file"]).read_text(encoding="utf-8")
            assert ET.fromstring(markup).tag == SVG_TAG, info["file"]

    def test_results_md(self) -> None:
        committed_figures = json.loads((REPORT / "figures.json").read_text(encoding="utf-8"))
        fresh = run.write_markdown(run.build(), committed_figures)
        assert fresh == (REPORT / "results.md").read_text(encoding="utf-8"), (
            "run `just theory` and commit the result"
        )
