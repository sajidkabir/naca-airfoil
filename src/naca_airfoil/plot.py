"""Airfoil plotting: save a shape plot to a PNG file."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from .airfoil import Airfoil  # noqa: E402


def plot_airfoil(airfoil: Airfoil, output, show_camber: bool = True) -> str:
    """Plot the section outline (and camber line) and save a PNG.

    Returns the output path. The axes use equal aspect so the shape
    on screen is the shape in the file: no vertical exaggeration.
    """
    output = Path(output)
    xs, ys = airfoil.coordinates()
    fig, ax = plt.subplots(figsize=(8.0, 2.8))
    ax.plot(xs, ys, color="black", linewidth=1.2, label="Surface")
    ax.fill(xs, ys, color="steelblue", alpha=0.15)
    if show_camber and airfoil.m > 0.0:
        ax.plot(
            airfoil.x,
            airfoil.y_camber,
            color="firebrick",
            linestyle="--",
            linewidth=1.0,
            label="Camber line",
        )
    ax.set_aspect("equal")
    ax.set_xlim(-0.05, 1.05)
    ax.set_xlabel("x / c")
    ax.set_ylabel("y / c")
    ax.set_title(airfoil.name)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="lower right", fontsize=8)
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    plt.close(fig)
    return str(output)
