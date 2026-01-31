"""
Binary EquaLab - Exported Functions
Convenience re-exports for direct import usage.
"""

from .engine import (
    derivar, integrar, limite, sumatoria,
    simplificar, expandir, factorizar, resolver,
    van, tir, depreciar, interes_simple, interes_compuesto,
    media, mediana, desviacion, varianza
)

__all__ = [
    "derivar", "integrar", "limite", "sumatoria",
    "simplificar", "expandir", "factorizar", "resolver",
    "van", "tir", "depreciar", "interes_simple", "interes_compuesto",
    "media", "mediana", "desviacion", "varianza",
]
