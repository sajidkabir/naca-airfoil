"""Coordinate file export and import.

The .dat writer uses the Selig-style single-loop format: a name line,
then one "x y" pair per line running from the trailing edge along the
upper surface to the leading edge and back along the lower surface.
This is the format used by the UIUC airfoil database and read by most
tools (XFOIL, Airfoil Tools, JavaFoil). The CSV writer emits the same
loop with an "x,y" header row.

Coordinates are normalized by chord and written to six decimal
places, so a file read back with load_dat reproduces the generated
coordinates to within 1e-6.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from .airfoil import Airfoil


def write_dat(airfoil: Airfoil, path) -> str:
    """Write the ordered coordinate loop to a Selig-style .dat file."""
    path = Path(path)
    xs, ys = airfoil.coordinates()
    lines = [airfoil.name]
    lines += [f"{xv:.6f} {yv:.6f}" for xv, yv in zip(xs, ys)]
    path.write_text("\n".join(lines) + "\n")
    return str(path)


def write_csv(airfoil: Airfoil, path) -> str:
    """Write the ordered coordinate loop to a CSV file with x,y header."""
    path = Path(path)
    xs, ys = airfoil.coordinates()
    lines = ["x,y"]
    lines += [f"{xv:.6f},{yv:.6f}" for xv, yv in zip(xs, ys)]
    path.write_text("\n".join(lines) + "\n")
    return str(path)


def load_dat(path) -> tuple[np.ndarray, np.ndarray]:
    """Read a .dat coordinate file back into (x, y) arrays.

    Skips the name line and any blank or non-numeric lines, so files
    from other Selig-format sources load as well.
    """
    xs, ys = [], []
    for line in Path(path).read_text().splitlines():
        parts = line.split()
        if len(parts) != 2:
            continue
        try:
            xv, yv = float(parts[0]), float(parts[1])
        except ValueError:
            continue
        xs.append(xv)
        ys.append(yv)
    return np.array(xs), np.array(ys)
