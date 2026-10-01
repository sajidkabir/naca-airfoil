"""NACA 4-digit airfoil geometry: parsing, coordinates, and surface data.

The geometry follows the classic NACA definitions (Abbott and Von
Doenhoff, "Theory of Wing Sections"):

- The thickness distribution is the standard polynomial with the
  -0.1015 final coefficient, the closed trailing edge form: the
  half-thickness at the trailing edge is zero for practical purposes
  (a residual of about 0.1 percent chord comes from the rounded
  coefficients, and the upper and lower surfaces meet there).
- The camber line is the two-parabola NACA mean line, joined at the
  point of maximum camber.
- Surface points are built by laying the half-thickness off
  perpendicular to the camber line, the standard construction.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def parse_designation(designation) -> tuple[float, float, float]:
    """Parse a NACA 4-digit designation into (m, p, t).

    Example: "2412" gives m = 0.02 (max camber, fraction of chord),
    p = 0.4 (position of max camber, fraction of chord), and
    t = 0.12 (max thickness, fraction of chord).

    Accepts a string or an int. Raises ValueError on anything that is
    not exactly four digits, on a zero thickness, or on a cambered
    section with its max camber at the leading edge (p = 0 divides by
    zero in the mean-line equations).
    """
    text = str(designation).strip()
    if len(text) != 4 or not text.isdigit():
        raise ValueError(
            f"Invalid NACA designation {designation!r}: "
            "expected exactly four digits, e.g. '2412'."
        )
    m = int(text[0]) / 100.0
    p = int(text[1]) / 10.0
    t = int(text[2:4]) / 100.0
    if t <= 0.0:
        raise ValueError(
            f"Invalid NACA designation {designation!r}: "
            "thickness must be greater than zero."
        )
    if m > 0.0 and p <= 0.0:
        raise ValueError(
            f"Invalid NACA designation {designation!r}: "
            "a cambered section needs its max camber position "
            "behind the leading edge."
        )
    return m, p, t


def thickness_half(x: np.ndarray, t: float) -> np.ndarray:
    """Half-thickness of a NACA 4-digit section at chord stations x.

    yt = 5 * t * (0.2969 * sqrt(x) - 0.1260 * x - 0.3516 * x^2
                  + 0.2843 * x^3 - 0.1015 * x^4)

    The final coefficient -0.1015 is the closed trailing edge form.
    """
    x = np.asarray(x, dtype=float)
    return 5.0 * t * (
        0.2969 * np.sqrt(x)
        - 0.1260 * x
        - 0.3516 * x**2
        + 0.2843 * x**3
        - 0.1015 * x**4
    )


def camber_line(x: np.ndarray, m: float, p: float) -> np.ndarray:
    """Camber line ordinate yc at chord stations x.

    Two parabolas joined at x = p. A symmetric section (m = 0) has a
    camber line on the chord line everywhere.
    """
    x = np.asarray(x, dtype=float)
    if m == 0.0:
        return np.zeros_like(x)
    fore = m / p**2 * (2.0 * p * x - x**2)
    aft = m / (1.0 - p) ** 2 * ((1.0 - 2.0 * p) + 2.0 * p * x - x**2)
    return np.where(x < p, fore, aft)


def camber_gradient(x: np.ndarray, m: float, p: float) -> np.ndarray:
    """Slope dyc/dx of the camber line at chord stations x."""
    x = np.asarray(x, dtype=float)
    if m == 0.0:
        return np.zeros_like(x)
    fore = 2.0 * m / p**2 * (p - x)
    aft = 2.0 * m / (1.0 - p) ** 2 * (p - x)
    return np.where(x < p, fore, aft)


def _stations(n_points: int, spacing: str) -> np.ndarray:
    """Chord stations from 0 to 1.

    Cosine spacing clusters points at the leading and trailing edges,
    where the surface curves fastest. Linear spacing is uniform.
    """
    if n_points < 5:
        raise ValueError("n_points must be at least 5.")
    if spacing == "cosine":
        beta = np.linspace(0.0, np.pi, n_points)
        return 0.5 * (1.0 - np.cos(beta))
    if spacing == "linear":
        return np.linspace(0.0, 1.0, n_points)
    raise ValueError(
        f"Unknown spacing {spacing!r}: use 'cosine' or 'linear'."
    )


@dataclass(eq=False)
class Airfoil:
    """A generated NACA 4-digit airfoil and its headline geometry.

    Surface coordinates come in matching arrays: x_upper with y_upper
    and x_lower with y_lower, both running from the leading edge (x = 0)
    to the trailing edge (x = 1). Use coordinates() for a single ordered
    loop around the section.
    """

    designation: str
    m: float
    p: float
    t: float
    n_points: int
    spacing: str
    x: np.ndarray
    y_camber: np.ndarray
    y_thickness: np.ndarray
    x_upper: np.ndarray
    y_upper: np.ndarray
    x_lower: np.ndarray
    y_lower: np.ndarray
    max_thickness: float
    max_thickness_x: float
    max_camber: float
    max_camber_x: float

    def coordinates(self) -> tuple[np.ndarray, np.ndarray]:
        """One ordered loop around the section.

        Starts at the trailing edge, runs along the upper surface to
        the leading edge, then back along the lower surface to the
        trailing edge (the Selig ordering used by most airfoil data
        files). The leading edge point appears once, so the loop has
        2 * n_points - 1 points.
        """
        xs = np.concatenate([self.x_upper[::-1], self.x_lower[1:]])
        ys = np.concatenate([self.y_upper[::-1], self.y_lower[1:]])
        return xs, ys

    @property
    def name(self) -> str:
        return f"NACA {self.designation}"


def generate_airfoil(
    designation, n_points: int = 200, spacing: str = "cosine"
) -> Airfoil:
    """Generate an Airfoil from a 4-digit designation.

    n_points is the number of chord stations per surface. Cosine
    spacing (the default) clusters stations near the leading edge.
    """
    m, p, t = parse_designation(designation)
    text = str(designation).strip()
    x = _stations(n_points, spacing)
    yt = thickness_half(x, t)
    yc = camber_line(x, m, p)
    dyc = camber_gradient(x, m, p)

    theta = np.arctan(dyc)
    x_upper = x - yt * np.sin(theta)
    y_upper = yc + yt * np.cos(theta)
    x_lower = x + yt * np.sin(theta)
    y_lower = yc - yt * np.cos(theta)

    # Thickness as the vertical surface distance at each station. For
    # the gentle camber slopes of 4-digit sections this tracks the true
    # perpendicular thickness 2 * yt to within a fraction of a percent.
    thickness = y_upper - y_lower
    i_thick = int(np.argmax(thickness))
    i_camber = int(np.argmax(yc))

    return Airfoil(
        designation=text,
        m=m,
        p=p,
        t=t,
        n_points=n_points,
        spacing=spacing,
        x=x,
        y_camber=yc,
        y_thickness=yt,
        x_upper=x_upper,
        y_upper=y_upper,
        x_lower=x_lower,
        y_lower=y_lower,
        max_thickness=float(thickness[i_thick]),
        max_thickness_x=float(x[i_thick]),
        max_camber=float(yc[i_camber]),
        max_camber_x=float(x[i_camber]),
    )
