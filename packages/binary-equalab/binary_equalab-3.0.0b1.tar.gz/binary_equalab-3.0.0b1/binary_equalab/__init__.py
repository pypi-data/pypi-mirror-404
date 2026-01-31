"""
Binary EquaLab CLI
Command-line CAS calculator with Spanish math functions.
"""

__version__ = "1.0.0"
__author__ = "BinaryEquaLab Team"

from .engine import MathEngine
from .functions import (
    derivar, integrar, limite, sumatoria,
    simplificar, expandir, factorizar, resolver,
    van, tir, depreciar, interes_simple, interes_compuesto,
    media, mediana, desviacion, varianza
)

__all__ = [
    "MathEngine",
    "derivar", "integrar", "limite", "sumatoria",
    "simplificar", "expandir", "factorizar", "resolver",
    "van", "tir", "depreciar", "interes_simple", "interes_compuesto",
    "media", "mediana", "desviacion", "varianza",
]
