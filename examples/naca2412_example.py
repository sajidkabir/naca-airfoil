"""Example: generate the NACA 2412, summarize it, export it, plot it."""

from naca_airfoil import generate_airfoil, thin_airfoil_theory, write_dat
from naca_airfoil.plot import plot_airfoil

airfoil = generate_airfoil("2412", n_points=200, spacing="cosine")
theory = thin_airfoil_theory(airfoil)

print(f"{airfoil.name}")
print(f"  Max camber:    {airfoil.max_camber * 100:.2f} % chord "
      f"at x/c {airfoil.max_camber_x:.2f}")
print(f"  Max thickness: {airfoil.max_thickness * 100:.2f} % chord "
      f"at x/c {airfoil.max_thickness_x:.2f}")
print(f"  Zero-lift AoA: {theory.alpha_l0_deg:.2f} deg (thin-airfoil theory)")
print(f"  Cm (c/4):      {theory.cm_c4:.4f} (thin-airfoil theory)")

write_dat(airfoil, "naca2412.dat")
plot_airfoil(airfoil, "naca2412.png")
print("Wrote naca2412.dat and naca2412.png")
