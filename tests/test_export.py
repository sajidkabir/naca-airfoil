"""Export and plotting tests: files round-trip the generated numbers."""

import numpy as np
import pytest

from naca_airfoil import generate_airfoil, load_dat, write_csv, write_dat
from naca_airfoil.plot import plot_airfoil


def test_dat_round_trip(tmp_path):
    af = generate_airfoil("2412")
    out = write_dat(af, tmp_path / "naca2412.dat")
    xs, ys = load_dat(out)
    want_x, want_y = af.coordinates()
    assert len(xs) == len(want_x)
    # Written to six decimals, so the round trip agrees to 1e-6.
    assert np.allclose(xs, want_x, atol=1e-6)
    assert np.allclose(ys, want_y, atol=1e-6)


def test_csv_round_trip(tmp_path):
    af = generate_airfoil("4412")
    out = write_csv(af, tmp_path / "naca4412.csv")
    data = np.loadtxt(out, delimiter=",", skiprows=1)
    want_x, want_y = af.coordinates()
    assert data.shape == (len(want_x), 2)
    assert np.allclose(data[:, 0], want_x, atol=1e-6)
    assert np.allclose(data[:, 1], want_y, atol=1e-6)


def test_plot_writes_png(tmp_path):
    af = generate_airfoil("2412")
    out = plot_airfoil(af, tmp_path / "naca2412.png")
    path = tmp_path / "naca2412.png"
    assert path.exists()
    assert path.stat().st_size > 0
    # PNG magic bytes.
    assert path.read_bytes()[:4] == b"\x89PNG"
    assert out == str(path)
