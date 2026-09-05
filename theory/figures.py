"""The five congestion-economics diagrams of the monograph's section 2, redrawn as SVG.

The monograph reproduces the figures of Cohen and Coughlin (2003, *Federal
Reserve Bank of St. Louis Review* 85, 9-25) and Cohen, Coughlin and Ott (2009,
same journal, 91, 569-587). Nothing is copied from either: each diagram is
rebuilt here from a few piecewise-linear curves on a fixed canvas, so every
labelled point, every welfare-loss triangle and every toll is a number computed
from the curve formulas and written to ``figures.json`` next to the drawing.
The curves are stylised, not calibrated -- their only job is to make the
geometry the text describes exact.

Coordinates: ``Q`` (flights) on the horizontal axis, ``P`` (price of a flight)
on the vertical one; ``X = 60 + 4 Q``, ``Y = 320 - 2.5 P`` on a 500 x 350
canvas. Labels are the monograph's: CMgP (custo marginal privado), CMgS
(custo marginal social), BMg (benefício marginal).
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

WIDTH, HEIGHT = 500, 350
X0, Y0 = 60.0, 320.0
SX, SY = 4.0, 2.5
INK = "#222222"
GREY = "#777777"
BLUE = "#1f5fa8"
RED = "#b03a2e"
GREEN = "#2e7d4f"
FILL_LOSS = "#b03a2e"
FILL_ALT = "#1f5fa8"

Curve = Callable[[float], float]


def X(q: float) -> float:
    return X0 + SX * q


def Y(p: float) -> float:
    return Y0 - SY * p


def _f(v: float) -> str:
    return f"{v:.1f}"


# ------------------------------------------------------------------ curves
def cmgp(qc: float = 40.0, base: float = 30.0, slope: float = 0.5) -> Curve:
    """Private marginal cost: flat up to ``qc``, then rising."""
    return lambda q: base if q <= qc else base + slope * (q - qc)


def cmgs(qc: float = 40.0, base: float = 30.0, slope: float = 1.5) -> Curve:
    """Social marginal cost: coincides with CMgP up to ``qc``, then rises faster."""
    return lambda q: base if q <= qc else base + slope * (q - qc)


def bmg(intercept: float = 100.0, slope: float = 1.0) -> Curve:
    """Marginal benefit (demand): ``intercept - slope Q``."""
    return lambda q: intercept - slope * q


def intersect(f: Curve, g: Curve, lo: float, hi: float) -> float:
    """``Q`` with ``f(Q) = g(Q)`` for two curves linear on ``[lo, hi]``."""
    a, b = f(lo) - g(lo), f(hi) - g(hi)
    if a == b:
        raise ValueError("parallel on the bracket")
    return lo + (hi - lo) * a / (a - b)


# ---------------------------------------------------------------- svg bits
def _sub(base: str, sub: str) -> str:
    return f'{base}<tspan dy="3" font-size="9">{sub}</tspan><tspan dy="-3"> </tspan>'


def text(
    x: float, y: float, label: str, anchor: str = "start", size: int = 11, fill: str = INK
) -> str:
    return (
        f'<text x="{_f(x)}" y="{_f(y)}" font-family="serif" font-size="{size}" '
        f'text-anchor="{anchor}" fill="{fill}">{label}</text>'
    )


def line(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    color: str = INK,
    width: float = 1.3,
    dashed: bool = False,
) -> str:
    dash = ' stroke-dasharray="4 3"' if dashed else ""
    return (
        f'<line x1="{_f(x1)}" y1="{_f(y1)}" x2="{_f(x2)}" y2="{_f(y2)}" '
        f'stroke="{color}" stroke-width="{width}"{dash}/>'
    )


def curve(
    points: list[tuple[float, float]],
    color: str,
    label: str,
    dx: float = 4.0,
    dy: float = 0.0,
    dashed: bool = False,
    anchor: str = "start",
) -> str:
    pts = " ".join(f"{_f(X(q))},{_f(Y(p))}" for q, p in points)
    dash = ' stroke-dasharray="5 3"' if dashed else ""
    q_end, p_end = points[-1]
    return (
        f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="1.6"{dash}/>'
        + text(X(q_end) + dx, Y(p_end) + dy, label, anchor=anchor, fill=color)
    )


def point(q: float, p: float, name: str, dx: float = 5.0, dy: float = -5.0) -> str:
    return f'<circle cx="{_f(X(q))}" cy="{_f(Y(p))}" r="2.8" fill="{INK}"/>' + text(
        X(q) + dx, Y(p) + dy, name, size=11
    )


def guide(
    q: float, p: float, xlabel: str | None = None, ylabel: str | None = None, row: int = 0
) -> str:
    out = []
    if xlabel is not None:
        out.append(line(X(q), Y(p), X(q), Y0, color=GREY, width=0.8, dashed=True))
        out.append(text(X(q), Y0 + 14 + 11 * row, xlabel, anchor="middle", size=10))
    if ylabel is not None:
        out.append(line(X0, Y(p), X(q), Y(p), color=GREY, width=0.8, dashed=True))
        out.append(text(X0 - 4, Y(p) + 4, ylabel, anchor="end", size=10))
    return "".join(out)


def polygon(points: list[tuple[float, float]], fill: str = FILL_LOSS, opacity: float = 0.28) -> str:
    pts = " ".join(f"{_f(X(q))},{_f(Y(p))}" for q, p in points)
    return f'<polygon points="{pts}" fill="{fill}" fill-opacity="{opacity}" stroke="none"/>'


def axes() -> str:
    return (
        line(X0, Y0, WIDTH - 20, Y0, width=1.2)
        + line(X0, Y0, X0, 14, width=1.2)
        + f'<polygon points="{WIDTH - 20},{_f(Y0 - 4)} {WIDTH - 10},{_f(Y0)} {WIDTH - 20},{_f(Y0 + 4)}" fill="{INK}"/>'
        + f'<polygon points="{_f(X0 - 4)},14 {_f(X0)},4 {_f(X0 + 4)},14" fill="{INK}"/>'
        + text(WIDTH - 12, Y0 + 26, "Q (voos)", anchor="end")
        + text(X0 + 8, 12, "P (preço)")
    )


def svg(body: str, title: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" '
        f'width="{WIDTH}" height="{HEIGHT}">'
        f"<title>{title}</title>"
        f'<rect x="0" y="0" width="{WIDTH}" height="{HEIGHT}" fill="white"/>' + body + "</svg>\n"
    )


def _tri_area(a: tuple[float, float], b: tuple[float, float], c: tuple[float, float]) -> float:
    return abs((b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1])) / 2.0


# ----------------------------------------------------------------- figures
def fig1() -> tuple[str, dict[str, Any]]:
    """Figure 1 -- the efficient level of congestion."""
    qc = 40.0
    P, S, B = cmgp(qc), cmgs(qc), bmg()
    q_p = intersect(P, B, qc, 100.0)  # A: private equilibrium
    q_s = intersect(S, B, qc, 100.0)  # C: efficient
    A = (q_p, P(q_p))
    C = (q_s, S(q_s))
    Bp = (q_p, S(q_p))
    D = (q_p, C[1])  # "AD = P_S - P_P", as the monograph's text reads
    pigou = S(q_s) - P(q_s)
    body = (
        axes()
        + curve([(0, P(0)), (qc, P(qc)), (100, P(100))], BLUE, "CMgP")
        + curve([(qc, S(qc)), (93, S(93))], RED, "CMgS")
        + curve([(0, B(0)), (100, B(100))], GREEN, "BMg", dx=-4, dy=14)
        + polygon([A, Bp, C])
        + line(X(q_s), Y(P(q_s)), X(q_s), Y(S(q_s)), color=RED, width=2.2)
        + text(X(q_s) - 6, Y((P(q_s) + S(q_s)) / 2) + 4, "t*", anchor="end", size=10, fill=RED)
        + guide(qc, P(qc), xlabel=_sub("Q", "c"))
        + guide(q_s, C[1], xlabel=_sub("Q", "S"), ylabel=_sub("P", "S"))
        + guide(q_p, A[1], xlabel=_sub("Q", "P"), ylabel=_sub("P", "P"))
        + point(*A, "A", dx=6, dy=12)
        + point(*Bp, "B", dx=6, dy=-4)
        + point(*C, "C", dx=-12, dy=-6)
        + point(*D, "D", dx=6, dy=4)
    )
    payload = {
        "file": "figures/fig1_nivel_eficiente.svg",
        "title": "Figura 1 — O nível eficiente de congestionamento",
        "curves": {
            "CMgP": "30 for Q <= 40, 30 + 0.5 (Q - 40) beyond",
            "CMgS": "30 + 1.5 (Q - 40) for Q >= 40",
            "BMg": "100 - Q",
        },
        "points": {"A": A, "B": Bp, "C": C, "D": D},
        "quantities": {
            "Q_c": qc,
            "Q_P": q_p,
            "P_P": A[1],
            "Q_S": q_s,
            "P_S": C[1],
            "triangle_ABC_area": _tri_area(A, Bp, C),
            "toll_AD_equals_PS_minus_PP": C[1] - A[1],
            "toll_pigou_at_QS": pigou,
        },
        "note": "AD = P_S - P_P is what the monograph's text says; the Pigouvian toll t* = CMgS(Q_S) - CMgP(Q_S) coincides with it only when CMgP is flat between Q_S and Q_P.",
    }
    return svg(body, payload["title"]), payload


def fig2() -> tuple[str, dict[str, Any]]:
    """Figure 2 -- price versus quantity regulation when the marginal benefit is uncertain."""
    qc = 40.0
    P, S = cmgp(qc), cmgs(qc)
    E, R = bmg(100.0), bmg(115.0)
    q_q = intersect(S, E, qc, 100.0)  # the quota, set on the expected benefit
    t_e = S(q_q) - P(q_q)  # the toll, set on the expected benefit
    Pt: Curve = lambda q: P(q) + t_e
    q_s = intersect(S, R, qc, 100.0)  # efficient under the realised benefit
    q_t = intersect(Pt, R, qc, 100.0)  # what the toll yields
    C = (q_s, S(q_s))
    A_, B_ = (q_q, R(q_q)), (q_q, S(q_q))
    E_, F_ = (q_t, S(q_t)), (q_t, R(q_t))
    body = (
        axes()
        + curve([(0, P(0)), (qc, P(qc)), (100, P(100))], BLUE, "CMgP")
        + curve([(qc, Pt(qc)), (100, Pt(100))], BLUE, "CMgP + t", dashed=True, dy=-8)
        + curve([(qc, S(qc)), (93, S(93))], RED, "CMgS")
        + curve([(0, E(0)), (100, E(100))], GREEN, "BMgE", dx=-2, dy=14, anchor="end")
        + curve([(0, R(0)), (100, R(100))], GREEN, "BMgR", dx=-2, dy=-6, dashed=True, anchor="end")
        + polygon([A_, B_, C])
        + polygon([C, E_, F_], fill=FILL_ALT)
        + guide(q_q, B_[1], xlabel=_sub("Q", "Q"))
        + guide(q_s, C[1], xlabel=_sub("Q", "S"), ylabel=_sub("P", "S"))
        + guide(q_t, F_[1], xlabel=_sub("Q", "T"), row=1)
        + point(*A_, "A", dx=-12, dy=-4)
        + point(*B_, "B", dx=-12, dy=12)
        + point(*C, "C", dx=4, dy=-6)
        + point(*E_, "E", dx=6, dy=-4)
        + point(*F_, "F", dx=6, dy=12)
    )
    payload = {
        "file": "figures/fig2_incerteza.svg",
        "title": "Figura 2 — Benefício marginal em condições de incerteza",
        "curves": {
            "CMgP": "as Figure 1",
            "CMgS": "as Figure 1",
            "BMgE": "100 - Q (expected)",
            "BMgR": "115 - Q (realised)",
            "CMgP + t": "CMgP shifted up by the toll set on BMgE",
        },
        "points": {"A": A_, "B": B_, "C": C, "E": E_, "F": F_},
        "quantities": {
            "toll_set_on_expectations": t_e,
            "Q_Q_quota": q_q,
            "Q_S_efficient_under_BMgR": q_s,
            "P_S": C[1],
            "Q_T_under_the_toll": q_t,
            "triangle_ABC_area_quantity_regulation": _tri_area(A_, B_, C),
            "triangle_CEF_area_price_regulation": _tri_area(C, E_, F_),
        },
        "note": "With these slopes (|CMgS'| = 1.5 > |BMg'| = 1) the price instrument loses less: CEF < ABC, the case the monograph's text concludes with.",
    }
    return svg(body, payload["title"]), payload


def fig3() -> tuple[str, dict[str, Any]]:
    """Figure 3 -- expanding the airport shifts both cost curves to the right."""
    qt, qtx = 40.0, 64.0
    P0, S0, P1, S1 = cmgp(qt), cmgs(qt), cmgp(qtx), cmgs(qtx)
    B = bmg()
    q_e0, q_e1 = intersect(P0, B, qt, 100.0), intersect(P1, B, qtx, 100.0)
    q_i = 50.0
    body = (
        axes()
        + curve([(0, P0(0)), (qt, P0(qt)), (100, P0(100))], BLUE, "CMgP")
        + curve([(qt, S0(qt)), (80, S0(80))], RED, "CMgS")
        + curve([(0, P1(0)), (qtx, P1(qtx)), (100, P1(100))], BLUE, "CMgP'", dashed=True, dy=12)
        + curve([(qtx, S1(qtx)), (100, S1(100))], RED, "CMgS'", dashed=True)
        + curve([(0, B(0)), (100, B(100))], GREEN, "BMg", dx=-4, dy=14)
        + line(X(q_i), Y0, X(q_i), Y(100), color=GREEN, width=1.4, dashed=True)
        + text(X(q_i) + 4, Y(96), "demanda inelástica", size=10, fill=GREEN)
        + guide(qt, P0(qt), xlabel=_sub("Q", "T"))
        + guide(qtx, P1(qtx), xlabel=_sub("Q", "TX"), row=1)
        + guide(q_i, P0(q_i), xlabel=_sub("Q", "I"))
        + guide(q_e0, B(q_e0), xlabel=_sub("Q", "E"))
        + guide(q_e1, B(q_e1), xlabel=_sub("Q", "E'"))
        + point(q_e0, B(q_e0), "E", dx=6, dy=12)
        + point(q_e1, B(q_e1), "E'", dx=6, dy=12)
        + point(q_i, P0(q_i), "I", dx=6, dy=-4)
        + point(q_i, P1(q_i), "I'", dx=6, dy=12)
    )
    payload = {
        "file": "figures/fig3_expansao.svg",
        "title": "Figura 3 — Custo marginal social e privado antes e depois de uma expansão",
        "curves": {
            "before": "CMgP/CMgS as Figure 1 with the congestion threshold at Q_T = 40",
            "after": "the same curves shifted right by 24 (threshold Q_TX = 64)",
            "BMg": "100 - Q (elastic demand)",
            "inelastic demand": "vertical at Q_I = 50",
        },
        "points": {
            "E": (q_e0, B(q_e0)),
            "E'": (q_e1, B(q_e1)),
            "I": (q_i, P0(q_i)),
            "I'": (q_i, P1(q_i)),
        },
        "quantities": {
            "Q_T": qt,
            "Q_TX": qtx,
            "Q_E_before": q_e0,
            "Q_E_after": q_e1,
            "elastic_still_congested_after": q_e1 > qtx,
            "Q_I": q_i,
            "P_I_before": P0(q_i),
            "P_I_after": P1(q_i),
            "inelastic_uncongested_after": q_i < qtx,
        },
        "note": "Elastic demand: the equilibrium moves from Q_E to Q_E' and stays beyond the new threshold, so congestion persists. Inelastic demand: Q_I is below the new threshold, so the expansion removes congestion.",
    }
    return svg(body, payload["title"]), payload


def fig4() -> tuple[str, dict[str, Any]]:
    """Figure 4 -- a network externality: local versus social marginal benefit."""
    cmg = 30.0
    L, Sb = bmg(100.0), bmg(115.0)
    q0 = intersect(L, lambda q: cmg, 0.0, 100.0)
    q1 = intersect(Sb, lambda q: cmg, 0.0, 100.0)
    subsidy = Sb(q1) - L(q1)
    body = (
        axes()
        + curve([(0, cmg), (100, cmg)], BLUE, "CMg")
        + curve([(0, L(0)), (100, L(100))], GREEN, "BMg local", dx=-2, dy=14, anchor="end")
        + curve(
            [(0, Sb(0)), (100, Sb(100))],
            GREEN,
            "BMg social",
            dx=-2,
            dy=-6,
            dashed=True,
            anchor="end",
        )
        + line(X(q1), Y(L(q1)), X(q1), Y(Sb(q1)), color=RED, width=2.2)
        + text(X(q1) + 6, Y((L(q1) + Sb(q1)) / 2) + 4, "subsídio", size=10, fill=RED)
        + guide(q0, cmg, xlabel=_sub("Q", "0"))
        + guide(q1, cmg, xlabel=_sub("Q", "1"))
        + point(q0, cmg, "", dx=0, dy=0)
        + point(q1, cmg, "", dx=0, dy=0)
    )
    payload = {
        "file": "figures/fig4_externalidade_de_rede.svg",
        "title": "Figura 4 — Expansão do aeroporto levando em conta as externalidades de rede",
        "curves": {"CMg": "30 (flat)", "BMg local": "100 - Q", "BMg social": "115 - Q"},
        "points": {"Q_0": (q0, cmg), "Q_1": (q1, cmg)},
        "quantities": {"Q_0": q0, "Q_1": q1, "subsidy_at_Q_1": subsidy},
        "note": "The spoke airport that sets flights where its local marginal benefit meets marginal cost stops at Q_0; the network-wide benefit justifies Q_1, reached with a subsidy equal to the gap between the two benefit curves.",
    }
    return svg(body, payload["title"]), payload


def fig5() -> tuple[str, dict[str, Any]]:
    """Figure 5 -- congestion and network externalities together, drawn to offset exactly."""
    qc = 40.0
    P, S = cmgp(qc), cmgs(qc)
    L, Sb = bmg(100.0), bmg(120.0)
    q0 = intersect(P, L, qc, 100.0)
    q_s = intersect(S, L, qc, 100.0)
    q_n = intersect(P, Sb, qc, 100.0)
    q_star = intersect(S, Sb, qc, 100.0)
    body = (
        axes()
        + curve([(0, P(0)), (qc, P(qc)), (100, P(100))], BLUE, "CMgP")
        + curve([(qc, S(qc)), (93, S(93))], RED, "CMgS")
        + curve([(0, L(0)), (100, L(100))], GREEN, "BMg local", dx=-2, dy=14, anchor="end")
        + curve(
            [(0, Sb(0)), (100, Sb(100))],
            GREEN,
            "BMg social",
            dx=-2,
            dy=-6,
            dashed=True,
            anchor="end",
        )
        + guide(q_s, S(q_s), xlabel=_sub("Q", "S"))
        + guide(q_star, S(q_star), xlabel=_sub("Q", "0") + " = Q*", ylabel="P*")
        + point(q0, P(q0), "", dx=0, dy=0)
        + point(q_star, S(q_star), "", dx=0, dy=0)
        + point(q_s, S(q_s), "", dx=0, dy=0)
    )
    payload = {
        "file": "figures/fig5_congestionamento_e_rede.svg",
        "title": "Figura 5 — Congestionamento e externalidades de rede",
        "curves": {
            "CMgP": "as Figure 1",
            "CMgS": "as Figure 1",
            "BMg local": "100 - Q",
            "BMg social": "120 - Q",
        },
        "points": {
            "market": (q0, P(q0)),
            "congestion_only": (q_s, S(q_s)),
            "network_only": (q_n, P(q_n)),
            "both": (q_star, S(q_star)),
        },
        "quantities": {
            "Q_0": q0,
            "Q_S_congestion_only": q_s,
            "Q_N_network_only": q_n,
            "Q_star": q_star,
            "P_star": S(q_star),
            "Q_star_equals_Q_0": abs(q_star - q0) < 1e-9,
        },
        "note": "Drawn as the monograph describes its Figure 5: the two externalities offset each other exactly, so the market quantity Q_0 is already the efficient Q* and no intervention is needed.",
    }
    return svg(body, payload["title"]), payload


FIGURES: dict[str, Callable[[], tuple[str, dict[str, Any]]]] = {
    "fig1": fig1,
    "fig2": fig2,
    "fig3": fig3,
    "fig4": fig4,
    "fig5": fig5,
}


def _round(value: Any) -> Any:
    if isinstance(value, bool):
        return value
    if isinstance(value, float):
        return float(f"{value:.6g}")
    if isinstance(value, tuple | list):
        return [_round(v) for v in value]
    if isinstance(value, dict):
        return {k: _round(v) for k, v in value.items()}
    return value


def draw_all(outdir: Path) -> dict[str, Any]:
    """Write the five SVG files under ``outdir/figures`` and return the ``figures.json`` payload."""
    outdir = Path(outdir)
    (outdir / "figures").mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "canvas": {"width": WIDTH, "height": HEIGHT, "X": "60 + 4 Q", "Y": "320 - 2.5 P"},
        "source": "Redrawn from piecewise-linear curves; nothing copied from Cohen and Coughlin (2003), Cohen, Coughlin and Ott (2009) or the monograph. Stylised, not calibrated.",
        "figures": {},
    }
    for key, fn in FIGURES.items():
        markup, info = fn()
        (outdir / info["file"]).write_text(markup, encoding="utf-8")
        payload["figures"][key] = _round(info)
    return payload
