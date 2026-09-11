"""The SAPIANS scientific figure style, vendored for the theory layer.

Source: ``sapians-design`` (https://github.com/wbendinelli/sapians-design, MIT),
``packages/python/sapians.mplstyle`` and ``sapians_plots/theme.py`` of its
v0.2.0 package, reduced to what this repository draws. The rules it encodes
come from the SAPIANS design system (Urban Institute and DeepMind
conventions): an *active insight title* stating the finding, a muted subtitle
carrying the parameters, direct labels at the end of each series instead of
a distant legend, top and right spines removed, faint dashed horizontal
gridlines, bar charts starting at zero, and the categorical palette blue,
terracotta, amber, sage, charcoal. Inter is the typeface when installed;
matplotlib falls back to Helvetica Neue, Arial or DejaVu Sans otherwise.

Every figure is written as SVG with the text kept as text (so it stays
searchable and re-renders in the reader's font when Inter is absent), with
a fixed hash salt and no date or creator metadata, so a second run on an
unchanged tree changes nothing.
"""

from __future__ import annotations

import glob
import os
import textwrap
import warnings
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.axes import Axes
from matplotlib.figure import Figure

COLORS: dict[str, str] = {
    "dark": "#161311",
    "paper": "#FFFFFF",
    "card_bg": "#F8F8FA",
    "terracotta": "#C96F3F",
    "blue": "#315B86",
    "amber": "#D9822B",
    "sage": "#4E8752",
    "muted": "#6D675F",
    "muted_light": "#A9A498",
    "line": "#E5E0D8",
    "grid": "#EBE7E1",
}
CATEGORICAL: tuple[str, ...] = ("#315B86", "#C96F3F", "#D9822B", "#4E8752", "#161311")
FONTS = ["Inter", "Helvetica Neue", "Arial", "DejaVu Sans"]

RC: dict[str, Any] = {
    "figure.facecolor": COLORS["paper"],
    "figure.edgecolor": COLORS["paper"],
    "figure.dpi": 150,
    "savefig.dpi": 300,
    "axes.facecolor": COLORS["paper"],
    "axes.edgecolor": COLORS["line"],
    "axes.linewidth": 0.8,
    "axes.grid": True,
    "axes.grid.which": "major",
    "axes.grid.axis": "y",
    "axes.titlesize": 11,
    "axes.titleweight": "bold",
    "axes.titlecolor": COLORS["dark"],
    "axes.titlelocation": "left",
    "axes.labelsize": 8.5,
    "axes.labelweight": "medium",
    "axes.labelcolor": COLORS["muted"],
    "axes.labelpad": 6,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.prop_cycle": matplotlib.cycler(color=list(CATEGORICAL)),
    "grid.color": COLORS["grid"],
    "grid.linestyle": "--",
    "grid.linewidth": 0.5,
    "grid.alpha": 0.8,
    "xtick.direction": "out",
    "ytick.direction": "out",
    "xtick.color": COLORS["muted"],
    "ytick.color": COLORS["muted"],
    "xtick.labelsize": 7.5,
    "ytick.labelsize": 7.5,
    "xtick.major.size": 3,
    "ytick.major.size": 3,
    "xtick.major.width": 0.8,
    "ytick.major.width": 0.8,
    "legend.frameon": False,
    "legend.fontsize": 7.5,
    "lines.linewidth": 1.6,
    "lines.solid_capstyle": "round",
    "lines.markersize": 5,
    "font.family": "sans-serif",
    "font.sans-serif": FONTS,
    "text.color": COLORS["dark"],
    "mathtext.fontset": "custom",
    "mathtext.rm": "Inter",
    "mathtext.it": "Inter:italic",
    "mathtext.bf": "Inter:bold",
    "mathtext.fallback": "stixsans",
    "svg.fonttype": "none",
    "svg.hashsalt": "airline-delays-theory",
    "path.simplify": False,
}


FONT_DIRS = ("~/Library/Fonts", "~/.local/share/fonts", "~/Documents/sapians-design/assets/fonts")


def register_inter() -> bool:
    """Register the Inter files found in the usual user font directories; True if any."""
    found = False
    for directory in FONT_DIRS:
        for pattern in ("Inter-*.otf", "Inter-*.ttf"):
            for path in sorted(glob.glob(os.path.join(os.path.expanduser(directory), pattern))):
                try:
                    font_manager.fontManager.addfont(path)
                except (OSError, RuntimeError, ValueError) as exc:  # pragma: no cover
                    warnings.warn(f"skipping font file {path}: {exc}", stacklevel=2)
                else:
                    found = True
    return found


def apply() -> None:
    """Install the SAPIANS style into matplotlib's rcParams (idempotent)."""
    register_inter()
    plt.rcParams.update(RC)


def new_figure(width: float = 6.4, height: float = 4.0) -> tuple[Figure, Axes]:
    apply()
    fig, ax = plt.subplots(figsize=(width, height))
    fig.subplots_adjust(left=0.11, right=0.97, top=0.78, bottom=0.21)
    return fig, ax


def insight_title(ax: Axes, title: str, subtitle: str | None = None) -> None:
    """The active insight title (bold, left) and the muted metadata subtitle under it, wrapped."""
    scale = ax.get_position().width / 0.86  # wrap widths are calibrated for the default axes width
    title = "\n".join(textwrap.wrap(title, max(30, int(70 * scale))))
    if subtitle:
        lines = textwrap.wrap(subtitle, max(40, int(100 * scale)))
        ax.set_title(title, loc="left", pad=14 + 11 * len(lines))
        ax.text(
            0.0,
            1.04,
            "\n".join(lines),
            transform=ax.transAxes,
            fontsize=8,
            color=COLORS["muted"],
            va="bottom",
            ha="left",
            linespacing=1.35,
        )
    else:
        ax.set_title(title, loc="left", pad=10)


def label_series(
    ax: Axes,
    x: float,
    y: float,
    text: str,
    color: str,
    dx: float = 4.0,
    dy: float = 0.0,
    ha: str = "left",
    va: str = "center",
    size: float = 8.0,
    weight: str = "bold",
) -> None:
    """Label a series directly at a point of it, instead of a legend."""
    ax.annotate(
        text,
        xy=(x, y),
        xytext=(dx, dy),
        textcoords="offset points",
        color=color,
        fontsize=size,
        fontweight=weight,
        ha=ha,
        va=va,
    )


def mark_point(
    ax: Axes,
    x: float,
    y: float,
    name: str | None = None,
    dx: float = 4.0,
    dy: float = 4.0,
    color: str | None = None,
) -> None:
    color = color or COLORS["dark"]
    ax.plot([x], [y], marker="o", markersize=4.2, color=color, zorder=6, linestyle="none")
    if name:
        ax.annotate(
            name,
            xy=(x, y),
            xytext=(dx, dy),
            textcoords="offset points",
            fontsize=8.5,
            fontweight="bold",
            color=color,
            zorder=7,
        )


def guide(ax: Axes, x: float, y: float, to_x: bool = True, to_y: bool = False) -> None:
    """Dotted guides from a point to the axes."""
    style = {"color": COLORS["muted_light"], "linewidth": 0.7, "linestyle": ":", "zorder": 1}
    if to_x:
        ax.plot([x, x], [0, y], **style)
    if to_y:
        ax.plot([0, x], [y, y], **style)


def footnote(fig: Figure, text: str) -> None:
    """A muted caption line under the axes, wrapped."""
    wrapped = "\n".join(textwrap.wrap(text, 116))
    fig.text(
        0.11,
        0.015,
        wrapped,
        fontsize=7,
        color=COLORS["muted"],
        ha="left",
        va="bottom",
        linespacing=1.35,
    )


def save(fig: Figure, path: Path) -> None:
    """Write an SVG with no date, no creator and a fixed hash salt, normalised line by line.

    matplotlib emits no final newline and some trailing spaces; the repository's
    pre-commit hooks would rewrite both, so the file is normalised here instead --
    a second ``just theory`` must leave the tree untouched.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(
        path, format="svg", metadata={"Date": None, "Creator": None}, facecolor=COLORS["paper"]
    )
    plt.close(fig)
    lines = path.read_text(encoding="utf-8").splitlines()
    path.write_text("\n".join(line.rstrip() for line in lines) + "\n", encoding="utf-8")
