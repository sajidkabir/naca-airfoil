"""Command-line interface for naca-airfoil.

Subcommands:
  gen     print the geometry and thin-airfoil summary for a section
  panel   run the vortex panel method at an angle of attack
  export  write coordinates to a .dat or .csv file
  plot    save a PNG plot of the section
"""

from __future__ import annotations

import argparse
from pathlib import Path

from .airfoil import generate_airfoil
from .export import write_csv, write_dat
from .panel import panel_method
from .plot import plot_airfoil
from .theory import thin_airfoil_theory


def _add_geometry_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "designation", help="NACA 4-digit designation, e.g. 2412"
    )
    parser.add_argument(
        "--points",
        type=int,
        default=200,
        help="Chord stations per surface (default 200)",
    )
    parser.add_argument(
        "--spacing",
        choices=["cosine", "linear"],
        default="cosine",
        help="Station spacing (default cosine)",
    )


def _cmd_gen(args: argparse.Namespace) -> int:
    airfoil = generate_airfoil(
        args.designation, n_points=args.points, spacing=args.spacing
    )
    theory = thin_airfoil_theory(airfoil)
    print(f"{airfoil.name} airfoil")
    print(
        f"  Max camber:      {airfoil.max_camber * 100:.2f} % chord "
        f"at x/c {airfoil.max_camber_x:.2f}"
    )
    print(
        f"  Max thickness:   {airfoil.max_thickness * 100:.2f} % chord "
        f"at x/c {airfoil.max_thickness_x:.2f}"
    )
    print(f"  Points:          {airfoil.n_points} per surface "
          f"({airfoil.spacing} spacing)")
    print("  Thin-airfoil theory:")
    print(f"    Zero-lift AoA:   {theory.alpha_l0_deg:.2f} deg")
    print(f"    Lift slope:      {theory.lift_slope_per_rad:.3f} /rad "
          f"({theory.lift_slope_per_deg:.4f} /deg)")
    print(f"    Cm (c/4):        {theory.cm_c4:.4f}")
    return 0


def _cmd_panel(args: argparse.Namespace) -> int:
    airfoil = generate_airfoil(
        args.designation, n_points=args.points, spacing=args.spacing
    )
    result = panel_method(airfoil, args.alpha)
    print(f"{airfoil.name} airfoil, vortex panel method "
          f"({result.n_panels} panels)")
    print(f"  Angle of attack: {result.alpha_deg:.2f} deg")
    print(f"  Lift coeff:      Cl = {result.cl:.4f}")
    print(f"  Moment coeff:    Cm_c4 = {result.cm_c4:.4f}")
    print(f"  Min Cp:          {result.cp.min():.3f} "
          f"(max {result.cp.max():.3f})")
    print("  Inviscid and incompressible; valid at small angles, "
          "well below stall.")
    return 0


def _cmd_export(args: argparse.Namespace) -> int:
    airfoil = generate_airfoil(
        args.designation, n_points=args.points, spacing=args.spacing
    )
    suffix = Path(args.out).suffix.lower()
    if suffix == ".dat":
        written = write_dat(airfoil, args.out)
    elif suffix == ".csv":
        written = write_csv(airfoil, args.out)
    else:
        raise SystemExit(
            f"Unsupported output format {suffix!r}: use .dat or .csv."
        )
    xs, _ = airfoil.coordinates()
    print(f"Wrote {len(xs)} coordinate points to {written}")
    return 0


def _cmd_plot(args: argparse.Namespace) -> int:
    airfoil = generate_airfoil(
        args.designation, n_points=args.points, spacing=args.spacing
    )
    written = plot_airfoil(airfoil, args.output)
    print(f"Wrote plot to {written}")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="naca-airfoil",
        description="NACA 4-digit airfoil generator and analyzer.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    gen = sub.add_parser("gen", help="Print a section summary")
    _add_geometry_args(gen)
    gen.set_defaults(func=_cmd_gen)

    panel = sub.add_parser(
        "panel", help="Vortex panel method at an angle of attack"
    )
    _add_geometry_args(panel)
    panel.add_argument(
        "--alpha",
        type=float,
        default=0.0,
        help="Angle of attack in degrees (default 0)",
    )
    panel.set_defaults(func=_cmd_panel)

    export = sub.add_parser("export", help="Write coordinates to a file")
    _add_geometry_args(export)
    export.add_argument(
        "--out", required=True, help="Output file (.dat or .csv)"
    )
    export.set_defaults(func=_cmd_export)

    plot = sub.add_parser("plot", help="Save a PNG plot of the section")
    _add_geometry_args(plot)
    plot.add_argument(
        "--output",
        default=None,
        help="Output PNG path (default naca<designation>.png)",
    )
    plot.set_defaults(func=_cmd_plot)

    args = parser.parse_args(argv)
    if args.command == "plot" and args.output is None:
        args.output = f"naca{args.designation}.png"
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
