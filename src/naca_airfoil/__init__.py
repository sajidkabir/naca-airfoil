"""naca-airfoil: NACA 4-digit airfoil generator and analyzer."""

from .airfoil import Airfoil, generate_airfoil, parse_designation
from .export import load_dat, write_csv, write_dat
from .panel import PanelResult, panel_method
from .plot import plot_airfoil
from .theory import TheoryResult, thin_airfoil_theory

__version__ = "1.1.0"

__all__ = [
    "Airfoil",
    "PanelResult",
    "TheoryResult",
    "generate_airfoil",
    "panel_method",
    "parse_designation",
    "thin_airfoil_theory",
    "write_dat",
    "write_csv",
    "load_dat",
    "plot_airfoil",
    "__version__",
]
