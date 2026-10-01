"""Thin-airfoil theory tests against published reference values."""

import numpy as np
import pytest

from naca_airfoil import generate_airfoil, thin_airfoil_theory


def test_symmetric_alpha_l0_zero():
    theory = thin_airfoil_theory(generate_airfoil("0012"))
    assert theory.alpha_l0_deg == pytest.approx(0.0, abs=1e-9)
    assert theory.cm_c4 == pytest.approx(0.0, abs=1e-9)
    assert theory.lift_coefficient(0.0) == pytest.approx(0.0)


def test_2412_alpha_l0():
    # Published thin-airfoil value for the NACA 2412: about -2.1 deg.
    theory = thin_airfoil_theory(generate_airfoil("2412"))
    assert theory.alpha_l0_deg == pytest.approx(-2.1, abs=0.3)


def test_2412_cm_c4():
    # Thin-airfoil theory for the 2412 camber line: about -0.053.
    # The often quoted -0.09 to -0.10 is the measured section value;
    # thin-airfoil theory (camber line only, zero thickness, inviscid)
    # underpredicts the moment magnitude, a known limitation.
    theory = thin_airfoil_theory(generate_airfoil("2412"))
    assert theory.cm_c4 == pytest.approx(-0.053, abs=0.01)


def test_lift_slope_is_two_pi():
    theory = thin_airfoil_theory(generate_airfoil("2412"))
    assert theory.lift_slope_per_rad == pytest.approx(2.0 * np.pi)
    assert theory.lift_slope_per_deg == pytest.approx(
        2.0 * np.pi * np.pi / 180.0
    )


def test_lift_coefficient_zero_at_alpha_l0():
    theory = thin_airfoil_theory(generate_airfoil("4415"))
    assert theory.lift_coefficient(theory.alpha_l0_deg) == pytest.approx(
        0.0, abs=1e-9
    )
    # At 4 deg above the zero-lift angle the lift is positive and
    # follows the 2 pi slope.
    cl = theory.lift_coefficient(theory.alpha_l0_deg + 4.0)
    assert cl == pytest.approx(2.0 * np.pi * np.radians(4.0), rel=1e-9)
