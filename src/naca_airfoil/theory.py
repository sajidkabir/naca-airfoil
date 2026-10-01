"""Thin-airfoil theory estimates for a NACA 4-digit section.

Thin-airfoil theory models the camber line as a vortex sheet and gives
closed-form estimates for the zero-lift angle of attack, the lift-curve
slope, and the quarter-chord pitching moment. With x mapped to
x = (1 - cos(theta)) / 2, the camber slope dz/dx has the Fourier
coefficients

    A1 = (2/pi) * integral of (dz/dx) * cos(theta) dtheta
    A2 = (2/pi) * integral of (dz/dx) * cos(2 * theta) dtheta

and the standard results are

    alpha_L0 = (1/pi) * integral of (dz/dx) * (1 - cos(theta)) dtheta
    cl       = 2 * pi * (alpha - alpha_L0)
    cm_c4    = (pi/4) * (A2 - A1)

This module evaluates those integrals numerically on a fine theta grid,
so the same code path covers any 4-digit camber line. For the NACA 2412
the integrals give alpha_L0 = -2.08 deg (published: about -2.1 deg) and
cm_c4 = -0.053. The measured section moment for the 2412 is larger in
magnitude (about -0.09 to -0.10): thin-airfoil theory models the camber
line only, with no thickness and no viscosity, and underpredicting the
quarter-chord moment is a known limitation of the theory.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .airfoil import Airfoil, camber_gradient

_trapezoid = np.trapezoid if hasattr(np, "trapezoid") else np.trapz

# Grid size for the Fourier integrals. The camber slope has a kink at
# the max camber point, so a fine grid keeps the trapezoid error far
# below the precision of the published reference values.
_GRID = 20001


@dataclass(eq=False)
class TheoryResult:
    """Thin-airfoil theory estimates for one section."""

    alpha_l0_deg: float
    lift_slope_per_rad: float
    cm_c4: float
    a1: float
    a2: float

    @property
    def lift_slope_per_deg(self) -> float:
        return self.lift_slope_per_rad * np.pi / 180.0

    def lift_coefficient(self, alpha_deg: float) -> float:
        """Section lift coefficient at angle of attack alpha_deg."""
        alpha = np.radians(alpha_deg)
        return self.lift_slope_per_rad * (alpha - np.radians(self.alpha_l0_deg))


def thin_airfoil_theory(airfoil: Airfoil) -> TheoryResult:
    """Thin-airfoil estimates for a generated Airfoil.

    A symmetric section (m = 0) short-circuits to alpha_L0 = 0 and
    cm_c4 = 0, which the integrals would return anyway.
    """
    if airfoil.m == 0.0:
        return TheoryResult(
            alpha_l0_deg=0.0,
            lift_slope_per_rad=2.0 * np.pi,
            cm_c4=0.0,
            a1=0.0,
            a2=0.0,
        )

    theta = np.linspace(0.0, np.pi, _GRID)
    x = 0.5 * (1.0 - np.cos(theta))
    dzdx = camber_gradient(x, airfoil.m, airfoil.p)

    int_slope = _trapezoid(dzdx, theta)
    a1 = (2.0 / np.pi) * _trapezoid(dzdx * np.cos(theta), theta)
    a2 = (2.0 / np.pi) * _trapezoid(dzdx * np.cos(2.0 * theta), theta)

    alpha_l0_rad = (int_slope - 0.5 * np.pi * a1) / np.pi
    cm_c4 = (np.pi / 4.0) * (a2 - a1)

    return TheoryResult(
        alpha_l0_deg=float(np.degrees(alpha_l0_rad)),
        lift_slope_per_rad=2.0 * np.pi,
        cm_c4=float(cm_c4),
        a1=float(a1),
        a2=float(a2),
    )
