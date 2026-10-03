"""Example: vortex panel analysis of the NACA 2412 at several angles."""

from naca_airfoil import generate_airfoil, panel_method, thin_airfoil_theory

airfoil = generate_airfoil("2412", n_points=200, spacing="cosine")
theory = thin_airfoil_theory(airfoil)

print(f"{airfoil.name}: panel method vs thin-airfoil theory")
print(f"  {'alpha':>5} {'Cl_panel':>8} {'Cl_theory':>9} {'Cm_panel':>8}")
for alpha in [0.0, 2.0, 4.0, 6.0]:
    panel = panel_method(airfoil, alpha)
    cl_theory = theory.lift_coefficient(alpha)
    print(f"  {alpha:5.1f} {panel.cl:8.4f} {cl_theory:9.4f} "
          f"{panel.cm_c4:8.4f}")
print("Thin-airfoil Cm_c4:", f"{theory.cm_c4:.4f}")
