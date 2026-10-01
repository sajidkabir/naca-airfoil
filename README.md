# naca-airfoil

[![CI](https://github.com/sajidkabir/naca-airfoil/actions/workflows/ci.yml/badge.svg)](https://github.com/sajidkabir/naca-airfoil/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23077767.svg)](https://doi.org/10.5281/zenodo.23077767)

A NACA 4-digit airfoil generator and analyzer. Give it a designation like
`2412` and it builds the section coordinates from the classic NACA
definitions, reports the geometry (max camber, max thickness, and where
they sit on the chord), estimates the aerodynamics with thin-airfoil
theory, and exports the coordinates in the formats the airfoil world
actually uses.

Every student of aerodynamics meets these sections, usually as a table of
numbers copied from a textbook. This package exists so the numbers are
never a black box again: small modules, the published equations, and tests
that check the results against the published values for the NACA 2412.

## Features

- **Designation parser**: any 4-digit code into max camber, camber
  position, and thickness, with clear errors for invalid input.
- **Exact classic geometry**: the standard thickness polynomial with the
  -0.1015 closed trailing edge coefficient, the two-parabola NACA camber
  line, and surfaces built by laying the thickness off perpendicular to
  the camber line.
- **Cosine or linear spacing**: cosine spacing clusters stations at the
  leading edge, where the surface curves fastest and panel methods and
  CFD meshes need the resolution.
- **Headline geometry**: max thickness and its chord position, max
  camber and its chord position, computed from the generated surfaces.
- **Thin-airfoil theory**: zero-lift angle of attack and quarter-chord
  moment coefficient from the Fourier integrals of the camber slope,
  evaluated numerically so any 4-digit camber line works, plus the
  classic 2 pi lift-curve slope and a lift coefficient function.
- **Export**: Selig-style .dat files (the UIUC database format) and CSV,
  written to six decimals, with a matching reader for round trips.
- **Plotting**: equal-aspect PNG of the section with its camber line.
- **CLI**: `gen`, `export`, and `plot` subcommands, plus a Python API.

## Installation

Requires Python 3.10 or newer.

```bash
git clone https://github.com/sajidkabir/naca-airfoil.git
cd naca-airfoil
pip install -e .
```

For development (adds the test runner):

```bash
pip install -e . pytest
pytest -q
```

## Quickstart

### Command line

Summarize the NACA 2412:

```bash
naca-airfoil gen 2412
```

```text
NACA 2412 airfoil
  Max camber:      2.00 % chord at x/c 0.40
  Max thickness:   12.00 % chord at x/c 0.30
  Points:          200 per surface (cosine spacing)
  Thin-airfoil theory:
    Zero-lift AoA:   -2.08 deg
    Lift slope:      6.283 /rad (0.1097 /deg)
    Cm (c/4):        -0.0531
```

Export coordinates and a plot:

```bash
naca-airfoil export 2412 --out naca2412.dat
naca-airfoil export 2412 --out naca2412.csv
naca-airfoil plot 2412 --output naca2412.png
```

### Python API

```python
from naca_airfoil import generate_airfoil, thin_airfoil_theory, write_dat

airfoil = generate_airfoil("2412", n_points=200, spacing="cosine")
print(f"Max thickness: {airfoil.max_thickness * 100:.2f} % chord "
      f"at x/c {airfoil.max_thickness_x:.2f}")

theory = thin_airfoil_theory(airfoil)
print(f"Zero-lift AoA: {theory.alpha_l0_deg:.2f} deg")
print(f"Cl at 4 deg:   {theory.lift_coefficient(4.0):.3f}")

write_dat(airfoil, "naca2412.dat")
xs, ys = airfoil.coordinates()  # one ordered loop, TE to TE
```

## How it works

| Module | Responsibility |
| --- | --- |
| `airfoil.py` | Designation parsing, thickness and camber line, surface construction |
| `theory.py` | Thin-airfoil theory: Fourier integrals of the camber slope |
| `export.py` | Selig-style .dat and CSV writers, .dat reader |
| `plot.py` | Equal-aspect PNG plotting (matplotlib, Agg backend) |
| `cli.py` | Command-line interface |

Key relations (chord-normalized, x from 0 at the leading edge to 1 at
the trailing edge):

- Half-thickness: yt = 5 * t * (0.2969 * sqrt(x) - 0.1260 * x
  - 0.3516 * x^2 + 0.2843 * x^3 - 0.1015 * x^4). The final coefficient
  is the closed trailing edge form.
- Camber line: two parabolas joined at x = p, peaking at yc = m.
- Surfaces: the half-thickness is laid off perpendicular to the camber
  line, so xu = x - yt * sin(theta), yu = yc + yt * cos(theta), with
  theta the camber slope angle, and mirror signs for the lower surface.
- Zero-lift angle: alpha_L0 = (1/pi) * integral of (dz/dx)
  * (1 - cos(theta)) dtheta, with x = (1 - cos(theta)) / 2.
- Lift: cl = 2 * pi * (alpha - alpha_L0).
- Quarter-chord moment: cm_c4 = (pi/4) * (A2 - A1), where A1 and A2 are
  the first two Fourier coefficients of the camber slope.

## Validation and sanity checks

The test suite (25 checks) tests the aerodynamics, not just the plumbing:

- The 2412 generates max thickness 12.00 percent at x/c 0.30 and max
  camber 2.00 percent at x/c 0.40, the values in its own designation.
- Thin-airfoil integration gives alpha_L0 = -2.08 deg for the 2412,
  against the published value of about -2.1 deg.
- A symmetric 0012 has zero camber everywhere, mirror-image surfaces,
  and zero-lift angle and moment of exactly zero.
- The coordinate loop starts and ends at the trailing edge, passes the
  leading edge once, and is monotonic along each surface.
- Exported .dat and .csv files read back to the generated numbers
  within 1e-6.
- The parser rejects malformed designations (wrong length, non-digits,
  zero thickness, camber peaking at the leading edge).

One deliberate note on the moment coefficient: thin-airfoil theory gives
cm_c4 = -0.053 for the 2412, while wind-tunnel section data reports
about -0.09 to -0.10. Both numbers are in the tests and docs on purpose.
Thin-airfoil theory models the camber line only (no thickness, no
viscosity), and underpredicting the moment is a known limitation of the
theory, not a bug in the integration.

## Honest limitations

- Thin-airfoil theory only: inviscid, incompressible, two-dimensional,
  small angles. No stall, no Reynolds number effects, no drag.
- 4-digit sections only (for now): no 5-digit or 6-series sections.
- Geometry is the analytic NACA definition, not measured coordinates;
  real manufactured sections differ slightly.
- The perpendicular offset construction puts the trailing edge surface
  points a hair past x/c = 1 (under 0.01 percent of chord). Harmless for
  plotting, export, and panel codes, and left visible rather than
  silently clipped.

## Roadmap and room for exploration

Ideas are welcome. Roughly in order of expected value:

- **Vortex panel method**: a Hess and Smith style panel solver for
  pressure distributions and lift with thickness effects, which should
  close most of the moment gap described above.
- **Viscous coupling**: a simple boundary-layer correction, or an
  optional XFOIL bridge, for drag polars and stall estimates.
- **More families**: NACA 5-digit and 6-series sections, which need
  different camber lines and thickness forms.
- **Database comparison**: fetch UIUC coordinates for a designation and
  diff them against the generated section.
- **Design sweeps**: batch generation over camber and thickness to map
  alpha_L0 and cm across the whole 4-digit space.
- **CST parameterization**: fit class-shape transformation coefficients
  to generated sections for use in optimization loops.
- **Wing-level examples**: pair a section with a planform and estimate
  wing lift slope, a natural companion to solar-uav-sim.

If you build one of these, open an issue or a pull request. Design notes
in the PR description are appreciated: what assumption changed, and what
it did to the 2412 reference numbers.

## Project structure

```text
src/naca_airfoil/    the package (airfoil, theory, export, plot, cli)
tests/               pytest suite, published-value checks included
examples/            runnable example: generate, export, plot a 2412
.github/workflows/   CI: install and run the test suite on every push
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). The short version: fork, branch,
test, pull request. Every change should keep `pytest -q` green and should
not move the validated numbers without explaining why in the PR.

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

## Citation

If you use this project in research, please cite the archived release:

Sajid Kabir Saji (2026). naca-airfoil (v1.0.1) [Software]. Zenodo. https://doi.org/10.5281/zenodo.23077768

The concept DOI https://doi.org/10.5281/zenodo.23077767 always resolves to the latest version.

## License

MIT. See [LICENSE](LICENSE).

## Author

Sajid Kabir Saji, aeronautical engineer. Research interests: onboard
autonomous decision-making for UAVs and solar-electric flight endurance.
More at [sajidkabir.com](https://sajidkabir.com).
