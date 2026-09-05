"""The figures of the theory layer, drawn with matplotlib in the SAPIANS style.

Figures 1-5 are the congestion-economics diagrams of the monograph's section
2, after Cohen and Coughlin (2003, *Federal Reserve Bank of St. Louis Review*
85, 9-25) and Cohen, Coughlin and Ott (2009, same journal, 91, 569-587).
Nothing is copied from either: each diagram is rebuilt from a few
piecewise-linear curves, so every labelled point, every welfare-loss triangle
and every toll is a number computed from the curve formulas and written to
``figures.json``. The curves are stylised, not calibrated.

Figures 6-11 show the model of section 4 and the bridge to the 2016 article:
the follower's reaction function, the tolls by market structure, the
comparative statics in cost curvature and demand slope, the low-cost entrant,
and the OLS-to-2SGMM sign inversion of the published coefficients. Their
numbers come from :mod:`theory.equilibrium` and :mod:`theory.bridge`, the
same functions that write ``model.json``.

Every figure carries an active title stating its finding and a subtitle with
the parameters (the SAPIANS convention, see :mod:`theory.sapians_style`).
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import numpy as np

from airline_delays.theory import bridge as bridge_module
from airline_delays.theory import equilibrium
from airline_delays.theory.families import LinearCost, Primitives, QuadraticCost
from airline_delays.theory.sapians_style import (
    COLORS,
    footnote,
    guide,
    insight_title,
    label_series,
    mark_point,
    new_figure,
    save,
)

Curve = Callable[[float], float]


SWAP_SEPARATORS = str.maketrans({",": ".", ".": ","})


def pt(x: float, d: int = 1, sign: bool = False) -> str:
    """A number in pt-BR notation: comma decimal, dot thousands, optional explicit sign."""
    text = f"{x:{'+' if sign else ''},.{d}f}"
    return text.translate(SWAP_SEPARATORS)


def ptg(x: float) -> str:
    """A short pt-BR number without trailing zeros (0,005; 0,03; 0)."""
    return format(x, "g").translate(SWAP_SEPARATORS)


XLABEL = "Voos no período de pico (Q)"
YLABEL = "Preço de um voo (P)"


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


def _tri_area(a: tuple[float, float], b: tuple[float, float], c: tuple[float, float]) -> float:
    return abs((b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1])) / 2.0


def _pl(
    ax: Any,
    fn: Curve,
    qs: list[float],
    color: str,
    label: str,
    dy: float = 0.0,
    dashed: bool = False,
    dx: float = 4.0,
    ha: str = "left",
) -> None:
    ax.plot(
        qs,
        [fn(q) for q in qs],
        color=color,
        linestyle="--" if dashed else "-",
        linewidth=1.6 if not dashed else 1.3,
    )
    label_series(ax, qs[-1], fn(qs[-1]), label, color, dx=dx, dy=dy, ha=ha)


def _economics_axes(ax: Any, qmax: float = 100.0, pmax: float = 120.0) -> None:
    ax.set_xlim(0, qmax + 14)
    ax.set_ylim(0, pmax)
    ax.set_xlabel(XLABEL)
    ax.set_ylabel(YLABEL)
    ax.grid(False)


def _ticks(ax: Any, xt: dict[float, str] | None = None, yt: dict[float, str] | None = None) -> None:
    if xt:
        ax.set_xticks(list(xt.keys()), labels=list(xt.values()))
    if yt:
        ax.set_yticks(list(yt.keys()), labels=list(yt.values()))


# ----------------------------------------------------- figures 1-5, economics
def fig1() -> tuple[Any, dict[str, Any]]:
    qc = 40.0
    P, S, B = cmgp(qc), cmgs(qc), bmg()
    q_p, q_s = intersect(P, B, qc, 100.0), intersect(S, B, qc, 100.0)
    A, C, Bp, D = (q_p, P(q_p)), (q_s, S(q_s)), (q_p, S(q_p)), (q_p, S(q_s))
    pigou = S(q_s) - P(q_s)
    area = _tri_area(A, Bp, C)
    fig, ax = new_figure()
    _economics_axes(ax)
    _pl(ax, P, [0, qc, 100], COLORS["blue"], "CMgP")
    _pl(ax, S, [qc, 92], COLORS["terracotta"], "CMgS")
    _pl(ax, B, [0, 100], COLORS["sage"], "BMg", dy=-8)
    ax.fill(
        [A[0], Bp[0], C[0]],
        [A[1], Bp[1], C[1]],
        color=COLORS["terracotta"],
        alpha=0.22,
        linewidth=0,
    )
    ax.annotate(
        f"perda ABC = {pt(area, 0)}",
        xy=((A[0] + C[0]) / 2 + 2, (A[1] + Bp[1]) / 2),
        xytext=(22, 18),
        textcoords="offset points",
        fontsize=7.5,
        color=COLORS["terracotta"],
        arrowprops={"arrowstyle": "-", "color": COLORS["muted_light"], "lw": 0.7},
    )
    ax.plot(
        [q_s, q_s],
        [P(q_s), S(q_s)],
        color=COLORS["terracotta"],
        linewidth=2.4,
        solid_capstyle="butt",
        zorder=5,
    )
    ax.annotate(
        f"tarifa pigouviana t* = {pt(pigou, 0)}",
        xy=(q_s, (P(q_s) + S(q_s)) / 2),
        xytext=(-70, -26),
        textcoords="offset points",
        fontsize=7.5,
        color=COLORS["terracotta"],
        arrowprops={"arrowstyle": "-", "color": COLORS["muted_light"], "lw": 0.7},
    )
    for q, p in ((qc, P(qc)), (q_s, C[1]), (q_p, A[1])):
        guide(ax, q, p, to_x=True, to_y=q != qc)
    mark_point(ax, *A, "A", dx=5, dy=-11)
    mark_point(ax, *Bp, "B", dx=5, dy=2)
    mark_point(ax, *C, "C", dx=-12, dy=4)
    mark_point(ax, *D, "D", dx=5, dy=-4)
    _ticks(ax, {qc: "$Q_c$", q_s: "$Q_S$", q_p: "$Q_P$"}, {A[1]: "$P_P$", C[1]: "$P_S$"})
    insight_title(
        ax,
        f"Sem tarifa, o mercado voa {pt(q_p - q_s, 0)} voos além do ótimo",
        f"CMgP plana até $Q_c$ = {pt(qc, 0)} e depois com inclinação 0,5; CMgS com inclinação 1,5; BMg = 100 − Q. Curvas estilizadas, não calibradas.",
    )
    footnote(
        fig,
        f"A = equilíbrio privado ({pt(q_p, 0)}, {pt(A[1], 0)}); C = ótimo social ({pt(q_s, 0)}, {pt(C[1], 0)}). O segmento AD do texto mede P_S − P_P = {pt(C[1] - A[1], 0)}; a tarifa pigouviana em Q_S mede {pt(pigou, 0)}.",
    )
    payload = {
        "file": "figures/fig1_nivel_eficiente.svg",
        "title": "Figura 1 — O nível eficiente de congestionamento",
        "insight": f"Sem tarifa, o mercado voa {pt(q_p - q_s, 0)} voos além do ótimo",
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
            "triangle_ABC_area": area,
            "toll_AD_equals_PS_minus_PP": C[1] - A[1],
            "toll_pigou_at_QS": pigou,
        },
        "note": "AD = P_S - P_P is what the monograph's text says; the Pigouvian toll t* = CMgS(Q_S) - CMgP(Q_S) coincides with it only when CMgP is flat between Q_S and Q_P.",
    }
    return fig, payload


def fig2() -> tuple[Any, dict[str, Any]]:
    qc = 40.0
    P, S = cmgp(qc), cmgs(qc)
    E, R = bmg(100.0), bmg(115.0)
    q_q = intersect(S, E, qc, 100.0)
    t_e = S(q_q) - P(q_q)
    Pt: Curve = lambda q: P(q) + t_e
    q_s, q_t = intersect(S, R, qc, 100.0), intersect(Pt, R, qc, 100.0)
    C = (q_s, S(q_s))
    A_, B_ = (q_q, R(q_q)), (q_q, S(q_q))
    E_, F_ = (q_t, S(q_t)), (q_t, R(q_t))
    area_abc, area_cef = _tri_area(A_, B_, C), _tri_area(C, E_, F_)
    fig, ax = new_figure()
    _economics_axes(ax)
    _pl(ax, P, [0, qc, 100], COLORS["blue"], "CMgP")
    _pl(ax, Pt, [qc, 100], COLORS["blue"], "CMgP + t", dashed=True, dy=6)
    _pl(ax, S, [qc, 92], COLORS["terracotta"], "CMgS")
    _pl(ax, E, [0, 100], COLORS["sage"], "BMg esperado", dy=-8)
    _pl(ax, R, [0, 100], COLORS["sage"], "BMg realizado", dashed=True, dy=6)
    ax.fill(
        [A_[0], B_[0], C[0]],
        [A_[1], B_[1], C[1]],
        color=COLORS["terracotta"],
        alpha=0.25,
        linewidth=0,
    )
    ax.fill(
        [C[0], E_[0], F_[0]], [C[1], E_[1], F_[1]], color=COLORS["blue"], alpha=0.25, linewidth=0
    )
    ax.annotate(
        f"cota: perda ABC = {pt(area_abc, 0)}",
        xy=(q_q + 1.5, (A_[1] + B_[1]) / 2),
        xytext=(-95, 30),
        textcoords="offset points",
        fontsize=7.5,
        color=COLORS["terracotta"],
        arrowprops={"arrowstyle": "-", "color": COLORS["muted_light"], "lw": 0.7},
    )
    ax.annotate(
        f"tarifa: perda CEF = {pt(area_cef, 0)}",
        xy=(q_t - 1.5, (E_[1] + F_[1]) / 2),
        xytext=(30, 34),
        textcoords="offset points",
        fontsize=7.5,
        color=COLORS["blue"],
        arrowprops={"arrowstyle": "-", "color": COLORS["muted_light"], "lw": 0.7},
    )
    for q, p in ((q_q, B_[1]), (q_s, C[1]), (q_t, F_[1])):
        guide(ax, q, p, to_x=True)
    mark_point(ax, *A_, "A", dx=-12, dy=2)
    mark_point(ax, *B_, "B", dx=-12, dy=-10)
    mark_point(ax, *C, "C", dx=4, dy=6)
    mark_point(ax, *E_, "E", dx=5, dy=2)
    mark_point(ax, *F_, "F", dx=5, dy=-10)
    _ticks(ax, {q_q: "$Q_Q$", q_s: "$Q_S$", q_t: "$Q_T$"})
    insight_title(
        ax,
        f"Quando o benefício surpreende, a tarifa perde menos que a cota ({pt(area_cef, 0)} contra {pt(area_abc, 0)})",
        f"Regulador fixa a tarifa t = {pt(t_e, 0)} ou a cota $Q_Q$ = {pt(q_q, 0)} sobre o BMg esperado (100 − Q); o realizado é 115 − Q. Inclinações: CMgS 1,5, BMg 1.",
    )
    footnote(
        fig,
        f"C = ótimo sob o benefício realizado ({pt(q_s, 0)}, {pt(C[1], 0)}). A tarifa leva o mercado a Q_T = {pt(q_t, 0)}; a cota o prende em Q_Q = {pt(q_q, 0)}. Quanto mais inclinado o custo marginal frente ao benefício, mais o preço vence.",
    )
    payload = {
        "file": "figures/fig2_incerteza.svg",
        "title": "Figura 2 — Benefício marginal em condições de incerteza",
        "insight": f"Quando o benefício surpreende, a tarifa perde menos que a cota ({pt(area_cef, 0)} contra {pt(area_abc, 0)})",
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
            "triangle_ABC_area_quantity_regulation": area_abc,
            "triangle_CEF_area_price_regulation": area_cef,
        },
        "note": "With these slopes (|CMgS'| = 1.5 > |BMg'| = 1) the price instrument loses less: CEF < ABC, the case the monograph's text concludes with.",
    }
    return fig, payload


def fig3() -> tuple[Any, dict[str, Any]]:
    qt, qtx = 40.0, 64.0
    P0, S0, P1, S1 = cmgp(qt), cmgs(qt), cmgp(qtx), cmgs(qtx)
    B = bmg()
    q_e0, q_e1, q_i = intersect(P0, B, qt, 100.0), intersect(P1, B, qtx, 100.0), 50.0
    fig, ax = new_figure()
    _economics_axes(ax)
    fig.subplots_adjust(bottom=0.25)
    _pl(ax, P0, [0, qt, 100], COLORS["blue"], "CMgP antes", dy=8)
    _pl(ax, S0, [qt, 80], COLORS["terracotta"], "CMgS antes")
    _pl(ax, P1, [0, qtx, 100], COLORS["blue"], "CMgP depois", dashed=True, dy=-8)
    _pl(ax, S1, [qtx, 100], COLORS["terracotta"], "CMgS depois", dashed=True)
    _pl(ax, B, [0, 100], COLORS["sage"], "BMg elástico", dy=-8)
    ax.plot([q_i, q_i], [0, 100], color=COLORS["sage"], linestyle=":", linewidth=1.4)
    label_series(ax, q_i, 100, "demanda inelástica", COLORS["sage"], dx=4, dy=0, va="bottom")
    for q, p in ((qt, P0(qt)), (qtx, P1(qtx)), (q_e0, B(q_e0)), (q_e1, B(q_e1))):
        guide(ax, q, p, to_x=True)
    mark_point(ax, q_e0, B(q_e0), "E", dx=5, dy=-11)
    mark_point(ax, q_e1, B(q_e1), "E′", dx=5, dy=-11)
    mark_point(ax, q_i, P0(q_i), "I", dx=5, dy=3)
    mark_point(ax, q_i, P1(q_i), "I′", dx=5, dy=-11)
    _ticks(ax, {qt: "$Q_T$", q_i: "$Q_I$", q_e0: "$Q_E$", qtx: "\n$Q_{TX}$", q_e1: "$Q_{E'}$"})
    insight_title(
        ax,
        "Expandir o aeroporto só descongestiona quem não responde ao preço",
        f"Curvas deslocadas em {pt(qtx - qt, 0)} voos: o limiar passa de $Q_T$ = {pt(qt, 0)} para $Q_{{TX}}$ = {pt(qtx, 0)}. Demanda elástica BMg = 100 − Q; inelástica fixa em $Q_I$ = {pt(q_i, 0)}.",
    )
    footnote(
        fig,
        f"Elástica: o equilíbrio vai de Q_E = {pt(q_e0, 0)} para Q_E′ = {pt(q_e1, 0)}, ainda além do novo limiar. Inelástica: Q_I = {pt(q_i, 0)} fica abaixo de Q_TX e o preço cai de {pt(P0(q_i), 0)} para {pt(P1(q_i), 0)}.",
    )
    payload = {
        "file": "figures/fig3_expansao.svg",
        "title": "Figura 3 — Custo marginal social e privado antes e depois de uma expansão",
        "insight": "Expandir o aeroporto só descongestiona quem não responde ao preço",
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
    return fig, payload


def fig4() -> tuple[Any, dict[str, Any]]:
    cmg = 30.0
    L, Sb = bmg(100.0), bmg(115.0)
    q0, q1 = intersect(L, lambda q: cmg, 0.0, 100.0), intersect(Sb, lambda q: cmg, 0.0, 100.0)
    subsidy = Sb(q1) - L(q1)
    fig, ax = new_figure()
    _economics_axes(ax)
    _pl(ax, lambda q: cmg, [0, 100], COLORS["blue"], "CMg")
    _pl(ax, L, [0, 100], COLORS["sage"], "BMg local", dy=-8)
    _pl(ax, Sb, [0, 100], COLORS["sage"], "BMg social", dashed=True, dy=6)
    ax.plot(
        [q1, q1],
        [L(q1), Sb(q1)],
        color=COLORS["terracotta"],
        linewidth=2.4,
        solid_capstyle="butt",
        zorder=5,
    )
    ax.annotate(
        f"subsídio = {pt(subsidy, 0)}",
        xy=(q1, (L(q1) + Sb(q1)) / 2),
        xytext=(-60, -30),
        textcoords="offset points",
        fontsize=7.5,
        color=COLORS["terracotta"],
        arrowprops={"arrowstyle": "-", "color": COLORS["muted_light"], "lw": 0.7},
    )
    for q in (q0, q1):
        guide(ax, q, cmg, to_x=True)
    mark_point(ax, q0, cmg, "", dx=0, dy=0)
    mark_point(ax, q1, cmg, "", dx=0, dy=0)
    _ticks(ax, {q0: "$Q_0$", q1: "$Q_1$"})
    insight_title(
        ax,
        f"O aeroporto-spoke para em {pt(q0, 0)} voos; a rede justifica {pt(q1, 0)}",
        "CMg constante em 30; BMg local = 100 − Q; BMg social = 115 − Q (a rede acrescenta 15 por voo). Um subsídio igual à diferença leva o aeroporto de Q₀ a Q₁.",
    )
    footnote(
        fig,
        "O benefício de um voo a mais no spoke inclui as conexões que ele alimenta no hub; o aeroporto que só vê o benefício local subinveste.",
    )
    payload = {
        "file": "figures/fig4_externalidade_de_rede.svg",
        "title": "Figura 4 — Expansão do aeroporto levando em conta as externalidades de rede",
        "insight": f"O aeroporto-spoke para em {pt(q0, 0)} voos; a rede justifica {pt(q1, 0)}",
        "curves": {"CMg": "30 (flat)", "BMg local": "100 - Q", "BMg social": "115 - Q"},
        "points": {"Q_0": (q0, cmg), "Q_1": (q1, cmg)},
        "quantities": {"Q_0": q0, "Q_1": q1, "subsidy_at_Q_1": subsidy},
        "note": "The spoke airport that sets flights where its local marginal benefit meets marginal cost stops at Q_0; the network-wide benefit justifies Q_1, reached with a subsidy equal to the gap between the two benefit curves.",
    }
    return fig, payload


def fig5() -> tuple[Any, dict[str, Any]]:
    qc = 40.0
    P, S = cmgp(qc), cmgs(qc)
    L, Sb = bmg(100.0), bmg(120.0)
    q0, q_s, q_n, q_star = (
        intersect(P, L, qc, 100.0),
        intersect(S, L, qc, 100.0),
        intersect(P, Sb, qc, 100.0),
        intersect(S, Sb, qc, 100.0),
    )
    fig, ax = new_figure()
    _economics_axes(ax)
    _pl(ax, P, [0, qc, 100], COLORS["blue"], "CMgP")
    _pl(ax, S, [qc, 92], COLORS["terracotta"], "CMgS")
    _pl(ax, L, [0, 100], COLORS["sage"], "BMg local", dy=-8)
    _pl(ax, Sb, [0, 100], COLORS["sage"], "BMg social", dashed=True, dy=6)
    for q, p in ((q_s, S(q_s)), (q_star, S(q_star))):
        guide(ax, q, p, to_x=True, to_y=q == q_star)
    mark_point(ax, q0, P(q0), "mercado", dx=6, dy=-12)
    mark_point(ax, q_star, S(q_star), "ótimo com as duas externalidades", dx=6, dy=4)
    mark_point(ax, q_s, S(q_s), "só congestionamento", dx=-6, dy=8, color=COLORS["terracotta"])
    _ticks(ax, {q_s: "$Q_S$", q_star: "$Q_0 = Q^*$"}, {S(q_star): "$P^*$"})
    insight_title(
        ax,
        "Quando congestionamento e rede se compensam, o mercado já está no ótimo",
        "BMg social = 120 − Q, desenhado para que o cruzamento de CMgS com o BMg social caia exatamente sobre o de CMgP com o BMg local, como a monografia descreve a sua Figura 5.",
    )
    footnote(
        fig,
        f"Só congestionamento: Q_S = {pt(q_s, 0)}. Só rede: {pt(q_n, 1)}. Os dois juntos: Q* = {pt(q_star, 0)} = Q₀. Fora desse caso especial, a prescrição depende de qual efeito é maior.",
    )
    payload = {
        "file": "figures/fig5_congestionamento_e_rede.svg",
        "title": "Figura 5 — Congestionamento e externalidades de rede",
        "insight": "Quando congestionamento e rede se compensam, o mercado já está no ótimo",
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
    return fig, payload


# ------------------------------------------------------- figures 6-11, the game
def fig6() -> tuple[Any, dict[str, Any]]:
    """The follower's reaction function in the linear example, with the four equilibria on it."""
    prim, cost = Primitives(), LinearCost()
    D, b = prim.A - cost.a, cost.b
    st = equilibrium.stackelberg(prim, cost)
    co = equilibrium.cournot(prim, cost)
    opt = equilibrium.social_optimum(prim, cost)
    atom = equilibrium.atomistic(prim, cost)
    f1s = np.linspace(0.0, D / b, 200)
    r2 = np.maximum((D - b * f1s) / (2 * b), 0.0)  # follower's reaction f2(f1)
    r1 = np.maximum(
        (D - b * f1s) / (2 * b), 0.0
    )  # firm 1's reaction, as a function of f2 (symmetric)
    fig, ax = new_figure()
    ax.plot(f1s, r2, color=COLORS["blue"], linewidth=1.8)
    label_series(
        ax,
        f1s[150],
        r2[150],
        "reação da seguidora $f_2(f_1)$",
        COLORS["blue"],
        dx=-4,
        dy=10,
        ha="right",
    )
    ax.plot(r1, f1s, color=COLORS["amber"], linewidth=1.3, linestyle="--")
    label_series(
        ax, r1[150], f1s[150], "reação da empresa 1 (jogo simultâneo)", COLORS["amber"], dx=6, dy=0
    )
    ax.plot(
        [0, atom["F"]], [atom["F"], 0], color=COLORS["muted_light"], linewidth=0.9, linestyle=":"
    )
    label_series(
        ax,
        atom["F"] * 0.62,
        atom["F"] * 0.38,
        f"total atomístico $F$ = {pt(atom['F'], 0)}",
        COLORS["muted"],
        dx=4,
        dy=4,
        weight="normal",
        size=7.5,
    )
    mark_point(ax, st.f1, st.f2, f"Stackelberg ({pt(st.f1, 0)}; {pt(st.f2, 1)})", dx=6, dy=6)
    mark_point(
        ax,
        co.f1,
        co.f2,
        f"Cournot ({pt(co.f1, 0)}; {pt(co.f2, 0)})",
        dx=6,
        dy=6,
        color=COLORS["amber"],
    )
    mark_point(
        ax,
        opt["f_star"],
        opt["f_star"],
        f"ótimo simétrico ({pt(opt['f_star'], 1)}; {pt(opt['f_star'], 1)})",
        dx=6,
        dy=-12,
        color=COLORS["sage"],
    )
    ax.set_xlim(0, D / b * 1.02)
    ax.set_ylim(0, D / (2 * b) * 1.15)
    ax.set_xlabel("Voos da empresa 1, $f_1$")
    ax.set_ylabel("Voos da empresa 2, $f_2$")
    insight_title(
        ax,
        "A seguidora corta metade de cada voo extra da líder",
        f"Custo linear c = {pt(cost.a, 0)} + {pt(cost.b, 0)}F; p = {pt(prim.p, 0)}, τ = {pt(prim.tau, 0)}, s = {pt(prim.s, 0)}. Reação: $f_2 = (D − b f_1)/2b$, declive −½ = −λ.",
    )
    footnote(
        fig,
        f"A líder escolhe f₁ sobre a reação da seguidora: f₁ = {pt(st.f1, 0)}, f₂ = {pt(st.f2, 1)}, total {pt(st.F, 1)}; Cournot dá {pt(co.F, 0)}, o ótimo {pt(opt['F_star'], 0)}, o atomístico {pt(atom['F'], 0)}.".replace(
            ".5", ",5"
        ),
    )
    payload = {
        "file": "figures/fig6_funcao_de_reacao.svg",
        "title": "Figura 6 — A função de reação da seguidora e os equilíbrios (exemplo linear)",
        "insight": "A seguidora corta metade de cada voo extra da líder",
        "points": {
            "stackelberg": (st.f1, st.f2),
            "cournot": (co.f1, co.f2),
            "social_symmetric": (opt["f_star"], opt["f_star"]),
        },
        "quantities": {
            "reaction_slope": -0.5,
            "F_stackelberg": st.F,
            "F_cournot": co.F,
            "F_star": opt["F_star"],
            "F_atomistic": atom["F"],
        },
        "note": "Linear example of model.json; the follower's reaction is f2 = (D - b f1)/(2b).",
    }
    return fig, payload


def fig7() -> tuple[Any, dict[str, Any]]:
    """Tolls at the symmetric optimum, as shares of MCD*, by market structure."""
    prim = Primitives()
    lin = equilibrium.tolls_at_symmetric_optimum(prim, LinearCost())
    quad = equilibrium.tolls_at_symmetric_optimum(prim, QuadraticCost())
    labels = [
        "monopólio",
        "Cournot\n(e seguidora)",
        "líder de Stackelberg\ncusto linear",
        "líder de Stackelberg\ncusto quadrático",
        "atomística",
    ]
    values = [
        0.0,
        lin["T2_star"] / lin["MCD_star"],
        lin["T1_star_over_MCD"],
        quad["T1_star_over_MCD"],
        1.0,
    ]
    colors = [
        COLORS["muted_light"],
        COLORS["blue"],
        COLORS["terracotta"],
        COLORS["terracotta"],
        COLORS["dark"],
    ]
    fig, ax = new_figure(6.4, 4.2)
    bars = ax.bar(labels, values, color=colors, width=0.62)
    for bar, v in zip(bars, values, strict=True):
        ax.annotate(
            f"{pt(v, 2)}",
            xy=(bar.get_x() + bar.get_width() / 2, v),
            xytext=(0, 4),
            textcoords="offset points",
            ha="center",
            fontsize=8.5,
            fontweight="bold",
            color=bar.get_facecolor(),
        )
    ax.set_ylim(0, 1.15)
    ax.set_ylabel("Tarifa por voo ÷ dano marginal MCD*")
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0], labels=["0", "0,25", "0,50", "0,75", "1,00"])
    ax.tick_params(axis="x", labelsize=7.5)
    insight_title(
        ax,
        "A líder de Stackelberg paga três quartos do dano marginal sob custo linear",
        f"Tarifa que restaura o ótimo, avaliada em f₁ = f₂ = f*, como fração de MCD* = F* c′. Quadrático: c = 1000 + 50F + F² (λ* = {pt(quad['lambda_star'], 4)}).".replace(
            "0.5670", "0,5670"
        ),
    )
    footnote(
        fig,
        "Quem internaliza tudo (monopólio) não precisa de tarifa; quem internaliza só a própria parcela (Cournot) paga metade; quem não internaliza nada (atomística) paga o dano inteiro.",
    )
    payload = {
        "file": "figures/fig7_tarifas_por_estrutura.svg",
        "title": "Figura 7 — Tarifas no ótimo simétrico por estrutura de mercado",
        "insight": "A líder de Stackelberg paga três quartos do dano marginal sob custo linear",
        "quantities": {
            "monopoly": 0.0,
            "cournot_and_follower": values[1],
            "stackelberg_leader_linear": values[2],
            "stackelberg_leader_quadratic": values[3],
            "atomistic": 1.0,
            "lambda_star_quadratic": quad["lambda_star"],
        },
        "note": "Proposition 1 of Brueckner and Van Dender (2008) as numbers; the quadratic bar is where lambda* > 1/2 lifts the leader's toll above three quarters.",
    }
    return fig, payload


def fig8() -> tuple[Any, dict[str, Any]]:
    """Comparative statics in cost curvature: lambda* and the leader's toll share."""
    rows = equilibrium.comparative_statics()["cost_curvature"]
    q = [r["q"] for r in rows]
    lam = [r["lambda_star"] for r in rows]
    toll = [r["T1_star_over_MCD"] for r in rows]
    ratio = [r["f1_over_f2"] for r in rows]
    fig, ax = new_figure()
    ax.plot(q, lam, marker="o", color=COLORS["blue"])
    label_series(ax, q[-1], lam[-1], "λ*: reação da seguidora", COLORS["blue"], dx=6)
    ax.plot(q, toll, marker="o", color=COLORS["terracotta"])
    label_series(ax, q[-1], toll[-1], "T₁*/MCD*: tarifa da líder", COLORS["terracotta"], dx=6)
    ax.axhline(0.5, color=COLORS["muted_light"], linewidth=0.8, linestyle=":")
    ax.axhline(0.75, color=COLORS["muted_light"], linewidth=0.8, linestyle=":")
    ax.text(
        0.3,
        0.425,
        "linhas pontilhadas: 0,50 (Cournot) e 0,75 (líder sob custo linear)",
        fontsize=7.5,
        color=COLORS["muted"],
    )
    ax.set_xlim(-0.2, 5.2)
    ax.set_ylim(0.4, 0.9)
    ax.set_xlabel("Curvatura q em c(F) = 1000 + 50F + qF²")
    ax.set_ylabel("Fração")
    insight_title(
        ax,
        "Custo marginal mais curvo: a seguidora reage menos e a líder paga mais",
        f"Ótimo simétrico para q de {pt(q[0], 0)} a {pt(q[-1], 0)}; λ* sobe de {pt(lam[0], 2)} para {pt(lam[-1], 2)} e a tarifa da líder de {pt(toll[0], 2)} para {pt(toll[-1], 2)} do dano marginal.",
    )
    footnote(
        fig,
        f"No equilíbrio de Stackelberg a razão f₁/f₂ = 1/(1 − λ) vai de {pt(ratio[0], 2)} para {pt(ratio[-1], 2)}: a líder voa cada vez mais que a seguidora.",
    )
    payload = {
        "file": "figures/fig8_estatica_curvatura.svg",
        "title": "Figura 8 — Estática comparativa na curvatura do custo de congestionamento",
        "insight": "Custo marginal mais curvo: a seguidora reage menos e a líder paga mais",
        "quantities": {"q": q, "lambda_star": lam, "T1_star_over_MCD": toll, "f1_over_f2": ratio},
        "note": "From model.json comparative_statics.cost_curvature.",
    }
    return fig, payload


def fig9() -> tuple[Any, dict[str, Any]]:
    """Inelastic demand: Stackelberg total against the optimum as demand steepens."""
    rows = equilibrium.comparative_statics()["demand_slope"]
    dd = [r["dd"] for r in rows]
    F = [r["F"] for r in rows]
    Fs = [r["F_star"] for r in rows]
    mp = [r["market_power_term"] for r in rows]
    un = [r["uninternalised_term"] for r in rows]
    fig, ax = new_figure()
    ax.plot(dd, F, marker="o", color=COLORS["blue"])
    label_series(ax, dd[-1], F[-1], "F de Stackelberg", COLORS["blue"], dx=6, dy=-6)
    ax.plot(dd, Fs, marker="o", color=COLORS["sage"], linestyle="--")
    label_series(ax, dd[-1], Fs[-1], "F* eficiente", COLORS["sage"], dx=6, dy=7)
    for x, a, b_ in zip(dd, F, Fs, strict=True):
        ax.plot([x, x], [a, b_], color=COLORS["muted_light"], linewidth=0.8, linestyle=":")
    ax.annotate(
        "acima do ótimo:\nfalha em internalizar",
        xy=(dd[1], (F[1] + Fs[1]) / 2),
        xytext=(12, 10),
        textcoords="offset points",
        fontsize=7.5,
        color=COLORS["muted"],
    )
    ax.annotate(
        "abaixo do ótimo:\npoder de mercado",
        xy=(dd[3], (F[3] + Fs[3]) / 2),
        xytext=(-118, 34),
        textcoords="offset points",
        fontsize=7.5,
        color=COLORS["muted"],
    )
    ax.set_xlim(-0.002, 0.036)
    ax.set_xticks(dd, labels=[ptg(x) for x in dd])
    ax.set_xlabel("Inclinação da demanda dd em d(Q) = 400 − dd·Q (0 = perfeitamente elástica)")
    ax.set_ylabel("Voos no total, F")
    insight_title(
        ax,
        "Com demanda inclinada, o tráfego de Stackelberg cai abaixo do ótimo",
        f"Custo linear c = 1000 + 100F. Termos de (12) no ponto de Stackelberg: poder de mercado {pt(mp[2], 1)} e não internalizado {pt(un[2], 0)} em dd = 0,015; {pt(mp[3], 1)} e {pt(un[3], 1)} em dd = 0,03.",
    )
    footnote(
        fig,
        "As duas distorções de (12) puxam em sentidos opostos: a que retém tráfego (poder de mercado) e a que o excede (o dano não internalizado).",
    )
    payload = {
        "file": "figures/fig9_demanda_inelastica.svg",
        "title": "Figura 9 — Demanda inelástica: o total de Stackelberg contra o ótimo",
        "insight": "Com demanda inclinada, o tráfego de Stackelberg cai abaixo do ótimo",
        "quantities": {
            "dd": dd,
            "F_stackelberg": F,
            "F_star": Fs,
            "market_power_term": mp,
            "uninternalised_term": un,
        },
        "note": "From model.json comparative_statics.demand_slope.",
    }
    return fig, payload


def fig10() -> tuple[Any, dict[str, Any]]:
    """The low-cost entrant: internalised shares of the marginal damage."""
    ext = equilibrium.lcc_extension()
    tri = ext["triopoly"]
    duo = ext["duopoly_cournot"]
    labels = [
        "duopólio\nincumbente 1",
        "duopólio\nincumbente 2",
        "triopólio\nentrante LCC",
        "triopólio\nincumbente 1",
        "triopólio\nincumbente 2",
    ]
    values = [*duo["internalised_share"], *tri["internalised_share"]]
    colors = [
        COLORS["muted_light"],
        COLORS["muted_light"],
        COLORS["terracotta"],
        COLORS["blue"],
        COLORS["blue"],
    ]
    fig, ax = new_figure(6.4, 4.2)
    bars = ax.bar(labels, values, color=colors, width=0.62)
    for bar, v in zip(bars, values, strict=True):
        ax.annotate(
            f"{pt(v, 2)}",
            xy=(bar.get_x() + bar.get_width() / 2, v),
            xytext=(0, 4),
            textcoords="offset points",
            ha="center",
            fontsize=8.5,
            fontweight="bold",
            color=bar.get_facecolor(),
        )
    ax.set_ylim(0, 0.75)
    ax.set_ylabel("Parcela do dano marginal internalizada, $f_i / F$")
    ax.tick_params(axis="x", labelsize=7)
    insight_title(
        ax,
        f"A entrante de baixo custo internaliza {tri['internalised_share'][0]:.0%} do dano marginal; cada incumbente, {tri['internalised_share'][1]:.0%}",
        f"Cournot com custo linear c = 1000 + 100F; τ = {pt(ext['entrant_tau'], 0)} para a entrante, {pt(ext['incumbent_tau'], 0)} para as incumbentes. Total F: {pt(duo['F'], 0)} no duopólio, {pt(tri['F'], 0)} no triopólio.",
    )
    footnote(
        fig,
        "Extensão deste repositório, não da monografia: a entrante voa mais porque custa menos, e internaliza mais porque voa mais. Sem tempo, sem escolha de aeroporto, sem preços.",
    )
    payload = {
        "file": "figures/fig10_entrante_lcc.svg",
        "title": "Figura 10 — A entrante de baixo custo e a parcela internalizada",
        "insight": "A entrante de baixo custo internaliza a maior parcela do dano marginal",
        "quantities": {
            "duopoly_shares": duo["internalised_share"],
            "triopoly_shares": tri["internalised_share"],
            "F_duopoly": duo["F"],
            "F_triopoly": tri["F"],
        },
        "note": "From model.json extension_lcc; labelled as this repository's extension.",
    }
    return fig, payload


def fig11() -> tuple[Any, dict[str, Any]]:
    """The published coefficients: OLS against 2SGMM for the four market-structure regressors."""
    br = bridge_module.bridge()
    variables = ["rthhi", "maxcthhi", "lcc", "maxalccfu"]
    names = {
        "rthhi": "HHI da rota (rthhi)",
        "maxcthhi": "HHI máx. das cidades (maxcthhi)",
        "lcc": "LCC na rota (lcc)",
        "maxalccfu": "LCC nas cidades (maxalccfu)",
    }
    ols = [br["tables"]["table6"]["variables"][v]["columns"]["2"]["b"] for v in variables]
    gmm = [br["tables"]["table3"]["variables"][v]["columns"]["2"]["b"] for v in variables]
    stars = [
        br["tables"]["table3"]["variables"][v]["columns"]["2"]["stars"] or "" for v in variables
    ]
    y = np.arange(len(variables))[::-1]
    fig, ax = new_figure(6.4, 3.8)
    fig.subplots_adjust(left=0.30)
    ax.axvline(0, color=COLORS["dark"], linewidth=0.9)
    for yi, o, g, s in zip(y, ols, gmm, stars, strict=True):
        ax.plot([o, g], [yi, yi], color=COLORS["muted_light"], linewidth=1.0, zorder=1)
        ax.plot(
            [o], [yi], marker="o", color=COLORS["muted"], markersize=6, linestyle="none", zorder=3
        )
        ax.plot(
            [g],
            [yi],
            marker="o",
            color=COLORS["terracotta"] if g < 0 else COLORS["blue"],
            markersize=7,
            linestyle="none",
            zorder=4,
        )
        ax.annotate(
            f"{pt(g, 3, sign=True)}{s}",
            xy=(g, yi),
            xytext=(0, 9),
            textcoords="offset points",
            ha="center",
            fontsize=7.5,
            fontweight="bold",
            color=COLORS["terracotta"] if g < 0 else COLORS["blue"],
        )
        ax.annotate(
            f"OLS {pt(o, 3, sign=True)}",
            xy=(o, yi),
            xytext=(0, -13),
            textcoords="offset points",
            ha="center",
            fontsize=7,
            color=COLORS["muted"],
        )
    ax.set_yticks(y, labels=[names[v] for v in variables])
    ax.set_xlabel("Coeficiente publicado sobre ODDS dos atrasos de chegada das FSC")
    ax.grid(False)
    ax.set_xlim(-2.0, 1.4)
    insight_title(
        ax,
        "O 2SGMM inverte o sinal das duas concentrações",
        "Tabela 3 col. (2), 2SGMM (pontos coloridos) contra Tabela 6 col. (2), OLS (cinza); coeficientes publicados em src/airline_delays/estimation/published.json. A presença de LCC fica negativa nos dois estimadores.",
    )
    footnote(
        fig,
        "Azul: positivo (concentração na rota, canal concorrência–qualidade). Terracota: negativo (concentração no aeroporto, internalização; presença de LCC).",
    )
    payload = {
        "file": "figures/fig11_inversao_de_sinal.svg",
        "title": "Figura 11 — OLS contra 2SGMM nos regressores de estrutura de mercado",
        "insight": "O 2SGMM inverte o sinal das duas concentrações",
        "quantities": {
            "variables": variables,
            "ols_table6_col2": ols,
            "gmm_table3_col2": gmm,
            "stars_table3_col2": stars,
        },
        "note": "Published coefficients only (src/airline_delays/estimation/published.json); nothing re-estimated.",
    }
    return fig, payload


FIGURES: dict[str, Callable[[], tuple[Any, dict[str, Any]]]] = {
    "fig1": fig1,
    "fig2": fig2,
    "fig3": fig3,
    "fig4": fig4,
    "fig5": fig5,
    "fig6": fig6,
    "fig7": fig7,
    "fig8": fig8,
    "fig9": fig9,
    "fig10": fig10,
    "fig11": fig11,
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
    """Write the SVG files under ``outdir/figures`` and return the ``figures.json`` payload."""
    outdir = Path(outdir)
    (outdir / "figures").mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "style": "SAPIANS scientific figure style (sapians-latex, MIT), see src/airline_delays/theory/sapians_style.py",
        "source": "Figures 1-5 redrawn from piecewise-linear curves after Cohen and Coughlin (2003) and Cohen, Coughlin and Ott (2009); nothing copied. Figures 6-11 from theory/equilibrium.py and theory/bridge.py. Stylised, not calibrated.",
        "figures": {},
    }
    for key, fn in FIGURES.items():
        fig, info = fn()
        save(fig, outdir / info["file"])
        payload["figures"][key] = _round(info)
    return payload
