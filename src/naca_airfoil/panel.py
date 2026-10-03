"""Vortex panel method for a NACA 4-digit section.

This module implements the classic constant-strength source / constant-strength
vortex panel method (the formulation in Kuethe and Chow, "Foundations of
Aerodynamics"): the airfoil contour is divided into straight panels, each
carrying an unknown constant source strength, plus one unknown vortex strength
shared by every panel. The flow-tangency condition (zero normal velocity) is
enforced at each panel midpoint, and the Kutta condition (equal and opposite
tangential velocity at the trailing edge) closes the system. Solving the
(N + 1) by (N + 1) linear system gives the singularity strengths, from which
the surface pressure distribution, lift coefficient, and quarter-chord
moment coefficient follow by direct pressure integration.

The method is inviscid and incompressible, so it is valid at small angles of
attack, well below stall. Unlike thin-airfoil theory it accounts for the
actual thickness distribution, which is why the lift-curve slope comes out
a few percent above 2 pi (matching published CFD) and the quarter-chord
moment lands close to the thin-airfoil value for cambered sections.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .airfoil import Airfoil

_TWO_PI = 2.0 * np.pi

# Fewer panels than this and the contour is too coarse to represent the
# leading edge curvature; the linear system stays solvable but the
# answers are not trustworthy.
_MIN_PANELS = 16


@dataclass(eq=False)
class PanelResult:
    """Inviscid panel-method solution for one section at one angle."""

    designation: str
    alpha_deg: float
    n_panels: int
    cl: float
    cm_c4: float
    cp: np.ndarray = field(repr=False)
    gamma: float = 0.0

    def summary(self) -> str:
        """One-line human-readable summary of the solution."""
        return (
            f"{self.designation} at {self.alpha_deg:.1f} deg: "
            f"Cl = {self.cl:.4f}, Cm_c4 = {self.cm_c4:.4f} "
            f"({self.n_panels} panels)"
        )


def _panel_nodes(airfoil: Airfoil) -> tuple[np.ndarray, np.ndarray]:
    """Closed, counter-clockwise node loop for the panel discretization.

    Uses the Selig-ordered coordinate loop as-is: it starts at the upper
    trailing edge and ends at the lower trailing edge, and the contour
    is closed by a short panel across the trailing edge gap (the closed
    trailing edge form leaves a residual gap of about 0.2 % chord, so
    the two trailing edge points are kept distinct and the panels follow
    the true surface right up to the edge). The loop is flipped to
    counter-clockwise if needed, keeping the upper trailing edge first.
    """
    xs, ys = airfoil.coordinates()
    nx, ny = np.array(xs), np.array(ys)
    # Signed area: positive means counter-clockwise.
    area = 0.5 * np.sum(nx * np.roll(ny, -1) - np.roll(nx, -1) * ny)
    if area < 0.0:
        # Reverse, then rotate so the upper trailing edge is node 0.
        nx = np.roll(nx[::-1], 1)
        ny = np.roll(ny[::-1], 1)
    return nx, ny


def panel_method(airfoil: Airfoil, alpha_deg: float = 0.0) -> PanelResult:
    """Inviscid lift and moment of a generated Airfoil at an angle.

    Builds constant-strength source/vortex panels on the airfoil
    contour, solves for the singularity strengths with the Kutta
    condition, and integrates the surface pressures.

    Args:
        airfoil: a section from generate_airfoil.
        alpha_deg: angle of attack in degrees (small angles only; the
            method is inviscid and knows nothing of stall).

    Returns:
        A PanelResult with cl, cm_c4 (about the quarter chord), the
        panel pressure coefficients, and the solved vortex strength.
    """
    nx, ny = _panel_nodes(airfoil)
    n = len(nx)
    if n < _MIN_PANELS:
        raise ValueError(
            f"Panel method needs at least {_MIN_PANELS} panels, "
            f"got {n}: generate the airfoil with more points."
        )

    # Panel geometry: start/end points, length, unit tangent, and the
    # outward unit normal (counter-clockwise ordering, so the outward
    # normal is the tangent rotated -90 degrees).
    sx, sy = nx, ny
    ex, ey = np.roll(nx, -1), np.roll(ny, -1)
    dx, dy = ex - sx, ey - sy
    length = np.hypot(dx, dy)
    tx, ty = dx / length, dy / length
    out_nx, out_ny = ty, -tx

    # Control points at panel midpoints.
    cx, cy = 0.5 * (sx + ex), 0.5 * (sy + ey)

    alpha = np.radians(alpha_deg)
    v_inf = np.array([np.cos(alpha), np.sin(alpha)])

    # Local frame of panel j: x along the panel, z 90 deg
    # counter-clockwise from it. For every (control point i, panel j)
    # pair, the velocity induced by a unit-strength source panel is
    #
    #   u = 1/(4 pi) * ln(r_start^2 / r_end^2)
    #   w = 1/(2 pi) * (theta_end - theta_start)
    #
    # and by a unit-strength vortex panel (positive counter-clockwise)
    #
    #   u = -1/(2 pi) * (theta_end - theta_start)
    #   w =  1/(4 pi) * ln(r_start^2 / r_end^2)
    #
    # in that local frame. The diagonal (self-induced) terms are set
    # explicitly because atan2 is ambiguous exactly on the panel, and
    # they use the EXTERIOR side of the sheet: the local +z axis points
    # 90 deg counter-clockwise from the panel tangent, which is the
    # interior side for a counter-clockwise contour. Hence the source
    # self term is -1/2 in the local frame (it is +1/2 blowing outward),
    # and the vortex self term is +1/2 in the local tangent direction.
    # The tangential velocity is continuous across a source sheet and
    # the normal velocity across a vortex sheet, so those self terms
    # are 0.
    ddx = cx[:, None] - sx[None, :]
    ddy = cy[:, None] - sy[None, :]
    xloc = ddx * tx[None, :] + ddy * ty[None, :]
    zloc = -ddx * ty[None, :] + ddy * tx[None, :]
    lj = length[None, :]
    rsq = xloc**2 + zloc**2
    re_sq = (xloc - lj) ** 2 + zloc**2
    theta_s = np.arctan2(zloc, xloc)
    theta_e = np.arctan2(zloc, xloc - lj)
    dtheta = theta_e - theta_s
    log_ratio = np.log(rsq / re_sq)

    us = log_ratio / (4.0 * np.pi)
    ws = dtheta / _TWO_PI
    uv = -dtheta / _TWO_PI
    wv = log_ratio / (4.0 * np.pi)

    diag = np.arange(n)
    us[diag, diag] = 0.0
    ws[diag, diag] = -0.5
    uv[diag, diag] = 0.5
    wv[diag, diag] = 0.0

    # Rotate the local influence vectors back to global coordinates.
    # Panel-j frame axes in global coords: t = (tx, ty), z = (-ty, tx).
    vsx = us * tx[None, :] - ws * ty[None, :]
    vsy = us * ty[None, :] + ws * tx[None, :]
    vvx = uv * tx[None, :] - wv * ty[None, :]
    vvy = uv * ty[None, :] + wv * tx[None, :]

    # System: N flow-tangency rows plus the Kutta row. Unknowns are the
    # N source strengths and the single vortex strength.
    a_mat = np.zeros((n + 1, n + 1))
    rhs = np.zeros(n + 1)
    a_mat[:n, :n] = vsx * out_nx[:, None] + vsy * out_ny[:, None]
    a_mat[:n, n] = np.sum(vvx * out_nx[:, None] + vvy * out_ny[:, None], axis=1)
    rhs[:n] = -(v_inf[0] * out_nx + v_inf[1] * out_ny)

    # Kutta: tangential velocity equal and opposite at the two surface
    # panels meeting at the trailing edge. Panel 0 starts at the upper
    # trailing edge; panel N - 2 ends at the lower trailing edge (panel
    # N - 1 is the short panel closing the trailing edge gap, not a
    # surface panel, so it is excluded here).
    i_te_up, i_te_lo = 0, n - 2
    t0x, t0y = tx[i_te_up], ty[i_te_up]
    tnx, tny = tx[i_te_lo], ty[i_te_lo]
    v0x, v0y = vsx[i_te_up, :], vsy[i_te_up, :]
    vnx, vny = vsx[i_te_lo, :], vsy[i_te_lo, :]
    a_mat[n, :n] = v0x * t0x + v0y * t0y + vnx * tnx + vny * tny
    a_mat[n, n] = np.sum(
        vvx[i_te_up, :] * t0x
        + vvy[i_te_up, :] * t0y
        + vvx[i_te_lo, :] * tnx
        + vvy[i_te_lo, :] * tny
    )
    rhs[n] = -(v_inf[0] * (t0x + tnx) + v_inf[1] * (t0y + tny))

    solution = np.linalg.solve(a_mat, rhs)
    lam = solution[:n]
    gamma = float(solution[n])

    # Tangential velocity and pressure on each panel.
    vtx = v_inf[0] + vsx @ lam + gamma * np.sum(vvx, axis=1)
    vty = v_inf[1] + vsy @ lam + gamma * np.sum(vvy, axis=1)
    vt = vtx * tx + vty * ty
    v_inf_mag = float(np.hypot(v_inf[0], v_inf[1]))
    cp = 1.0 - (vt / v_inf_mag) ** 2

    # Pressure integration for lift and quarter-chord moment. Chord is
    # the x-extent of the contour (1.0 for a generated section). The
    # moment uses the aerodynamic sign convention: positive Cm pitches
    # the nose up, which is the negative of the right-hand-rule moment
    # about the z axis.
    chord = float(np.max(nx) - np.min(nx))
    q = -cp * length
    cl = float(np.sum(q * out_ny) / chord)
    xc = cx - 0.25 * chord
    cm_c4 = -float(np.sum(q * (xc * out_ny - cy * out_nx)) / chord**2)

    return PanelResult(
        designation=airfoil.designation,
        alpha_deg=float(alpha_deg),
        n_panels=n,
        cl=cl,
        cm_c4=cm_c4,
        cp=cp,
        gamma=gamma,
    )
