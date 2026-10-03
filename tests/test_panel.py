"""Vortex panel method tests against reference values.

The panel method is inviscid and incompressible. Reference checks:
- A symmetric section at zero angle has zero lift and zero moment.
- The lift-curve slope of a thin section is near 2 pi per radian; the
  panel method resolves the thickness, so it comes out a few percent
  higher (published viscous CFD for the NACA 0012 at 4 deg gives
  Cl = 0.472; thin-airfoil theory gives 0.439).
- The NACA 2412 at zero angle carries camber lift near the thin-airfoil
  value of 0.228, and its quarter-chord moment is near the thin-airfoil
  -0.053.
"""

import numpy as np
import pytest

from naca_airfoil import generate_airfoil, panel_method


def test_symmetric_zero_alpha():
    result = panel_method(generate_airfoil("0012"), 0.0)
    assert result.cl == pytest.approx(0.0, abs=1e-6)
    assert result.cm_c4 == pytest.approx(0.0, abs=1e-6)


def test_symmetric_lift_slope_near_two_pi():
    # Inviscid lift slope of the 12 % thick section: a few percent above
    # the thin-airfoil 2 pi because the panel method resolves the
    # thickness. Published viscous CFD gives Cl = 0.472 at 4 deg.
    airfoil = generate_airfoil("0012", n_points=200)
    cl_4 = panel_method(airfoil, 4.0).cl
    assert cl_4 == pytest.approx(0.472, abs=0.02)
    slope = (cl_4 - panel_method(airfoil, 0.0).cl) / np.radians(4.0)
    assert slope == pytest.approx(2.0 * np.pi, rel=0.09)


def test_2412_camber_lift_at_zero_alpha():
    # Thin-airfoil theory: Cl = 2 pi * 2.08 deg = 0.228 at zero angle.
    result = panel_method(generate_airfoil("2412", n_points=200), 0.0)
    assert result.cl == pytest.approx(0.228, abs=0.04)


def test_2412_quarter_chord_moment():
    # Thin-airfoil theory gives cm_c4 = -0.053 for the 2412 camber line;
    # the panel method (inviscid, with thickness) lands nearby.
    result = panel_method(generate_airfoil("2412", n_points=200), 2.0)
    assert result.cm_c4 == pytest.approx(-0.053, abs=0.015)


def test_zero_lift_angle_2412():
    # Zero-lift angle from a two-point interpolation of panel Cl.
    airfoil = generate_airfoil("2412", n_points=120)
    cl0 = panel_method(airfoil, 0.0).cl
    cl4 = panel_method(airfoil, 4.0).cl
    alpha_l0 = -cl0 / (cl4 - cl0) * 4.0
    assert alpha_l0 == pytest.approx(-2.1, abs=0.3)


def test_panel_refinement_converges():
    # Finer paneling changes Cl by less than 2 % (first-order method,
    # converges slowly).
    coarse = panel_method(generate_airfoil("0012", n_points=50), 4.0).cl
    fine = panel_method(generate_airfoil("0012", n_points=200), 4.0).cl
    assert fine == pytest.approx(coarse, rel=0.02)


def test_cp_physical():
    # Stagnation Cp near 1 at the leading edge, suction (negative Cp)
    # on the upper surface at positive alpha, all finite.
    result = panel_method(generate_airfoil("2412", n_points=120), 4.0)
    assert np.all(np.isfinite(result.cp))
    assert result.cp.max() == pytest.approx(1.0, abs=0.05)
    assert result.cp.min() < -0.5


def test_too_coarse_raises():
    with pytest.raises(ValueError, match="at least"):
        panel_method(generate_airfoil("0012", n_points=5), 2.0)


def test_result_summary():
    result = panel_method(generate_airfoil("0012", n_points=60), 4.0)
    assert result.n_panels == 2 * 60 - 1
    assert "0012" in result.summary()
    assert "Cl" in result.summary()
