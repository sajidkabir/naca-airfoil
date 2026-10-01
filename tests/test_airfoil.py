"""Geometry tests: parsing, thickness, camber, surfaces, ordering."""

import numpy as np
import pytest

from naca_airfoil import generate_airfoil, parse_designation


def test_parse_designation_2412():
    m, p, t = parse_designation("2412")
    assert m == pytest.approx(0.02)
    assert p == pytest.approx(0.4)
    assert t == pytest.approx(0.12)


@pytest.mark.parametrize(
    "bad", ["241", "24123", "abcd", "24a2", "", "0012x", "0000", "2012"]
)
def test_parse_rejects_bad_input(bad):
    # "0000" has zero thickness; "2012" puts max camber at the leading
    # edge, which divides by zero in the mean-line equations.
    with pytest.raises(ValueError):
        parse_designation(bad)


def test_symmetric_0012_zero_camber():
    af = generate_airfoil("0012")
    assert np.allclose(af.y_camber, 0.0)
    assert af.max_camber == pytest.approx(0.0, abs=1e-12)


def test_2412_max_thickness():
    # Published: 12 percent chord at 30 percent chord.
    af = generate_airfoil("2412")
    assert af.max_thickness == pytest.approx(0.12, abs=0.002)
    assert af.max_thickness_x == pytest.approx(0.30, abs=0.03)


def test_2412_max_camber():
    # Published: 2 percent chord at 40 percent chord (in the digits).
    af = generate_airfoil("2412")
    assert af.max_camber == pytest.approx(0.02, abs=0.001)
    assert af.max_camber_x == pytest.approx(0.40, abs=0.05)


def test_symmetric_surfaces_mirror():
    af = generate_airfoil("0012")
    assert np.allclose(af.x_upper, af.x_lower)
    assert np.allclose(af.y_upper, -af.y_lower)


def test_point_count():
    af = generate_airfoil("2412", n_points=120)
    assert len(af.x) == 120
    assert len(af.x_upper) == 120
    assert len(af.y_lower) == 120
    xs, ys = af.coordinates()
    assert len(xs) == 2 * 120 - 1
    assert len(ys) == 2 * 120 - 1


def test_loop_starts_and_ends_at_trailing_edge():
    af = generate_airfoil("2412")
    xs, ys = af.coordinates()
    # First point: upper trailing edge. Last point: lower trailing edge.
    assert xs[0] == pytest.approx(1.0, abs=0.01)
    assert xs[-1] == pytest.approx(1.0, abs=0.01)
    # The loop runs TE to LE along the top, then LE to TE along the
    # bottom, so x falls monotonically then rises monotonically. The
    # minimum sits at the leading edge (within a fraction of a percent
    # of chord: the perpendicular offset leans the first upper point a
    # hair past x = 0 where the thickness grows like sqrt(x)).
    i_le = int(np.argmin(xs))
    assert xs[i_le] == pytest.approx(0.0, abs=5e-4)
    assert xs[af.n_points - 1] == pytest.approx(0.0, abs=1e-9)
    assert np.all(np.diff(xs[: i_le + 1]) <= 1e-9)
    assert np.all(np.diff(xs[i_le:]) >= -1e-9)


def test_closed_trailing_edge():
    # With the -0.1015 coefficient the surfaces meet at the trailing
    # edge: the residual gap is a small fraction of a percent of chord.
    af = generate_airfoil("2412")
    gap = af.y_upper[-1] - af.y_lower[-1]
    assert gap == pytest.approx(0.0, abs=0.005)
    assert af.x_upper[-1] == pytest.approx(1.0, abs=0.01)


def test_cosine_spacing_clusters_leading_edge():
    n = 101
    cos = generate_airfoil("2412", n_points=n, spacing="cosine")
    lin = generate_airfoil("2412", n_points=n, spacing="linear")
    # The first cosine cell is far finer than the first linear cell.
    assert (cos.x[1] - cos.x[0]) < 0.2 * (lin.x[1] - lin.x[0])
    # And a mid-chord cosine cell is coarser than the linear cell.
    mid = n // 2
    assert (cos.x[mid + 1] - cos.x[mid]) > (lin.x[mid + 1] - lin.x[mid])
