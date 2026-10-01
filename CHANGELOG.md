# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/), and versions follow
[Semantic Versioning](https://semver.org/).

## [1.0.0] - 2026-10-01

First stable release.

### Added

- Designation parser (`parse_designation`) turning any NACA 4-digit code
  into max camber, camber position, and thickness, with validation of
  malformed input.
- Geometry generation (`generate_airfoil`): the standard thickness
  polynomial with the -0.1015 closed trailing edge coefficient, the
  two-parabola camber line, and surfaces built by laying the thickness
  off perpendicular to the camber line. Cosine spacing (leading edge
  clustering) or linear spacing, at a configurable point count.
- Headline geometry from the generated surfaces: max thickness and its
  chord position, max camber and its chord position, plus a single
  ordered coordinate loop (Selig ordering, trailing edge to trailing
  edge).
- Thin-airfoil theory (`thin_airfoil_theory`): zero-lift angle of
  attack, lift-curve slope, and quarter-chord moment coefficient from
  numerical Fourier integration of the camber slope. For the NACA 2412
  it gives alpha_L0 = -2.08 deg (published: about -2.1 deg) and
  cm_c4 = -0.053 (thin-airfoil value; measured section data reports
  about -0.09 to -0.10, a documented limitation of the theory).
- Export to Selig-style .dat and CSV at six decimal places, with a
  .dat reader (`load_dat`) for round trips.
- Equal-aspect PNG plotting of the section and its camber line.
- Command-line interface with `gen`, `export`, and `plot`
  subcommands.
- Test suite of 25 checks covering the published 2412 reference values,
  plus GitHub Actions CI on Python 3.12.
- Example: generate, summarize, export, and plot the NACA 2412.
