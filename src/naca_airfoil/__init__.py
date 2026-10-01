"""naca-airfoil: NACA 4-digit airfoil generator and analyzer."""

from .airfoil import Airfoil, generate_airfoil, parse_designation
from .export import load_dat, write_csv, write_dat
from .plot import plot_airfoil
from .theory import TheoryResult, thin_airfoil_theory

__version__ = "1.0.0"

__all__ = [
    "Airfoil",
    "TheoryResult",
    "generate_airfoil",
    "parse_designation",
    "thin_airfoil_theory",
    "write_dat",
    "write_csv",
    "load_dat",
    "plot_airfoil",
    "__version__",
]
