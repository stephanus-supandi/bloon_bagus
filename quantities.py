"""Physical quantities and constants — the FINE-FM domain vocabulary.

FINE-FM is unit-explicit but unit-simple: everything is SI. There is no
units/dimensions algebra layer (see README: documented limitation — BLOON's
public surface does not expose one, and inventing a parallel framework is
forbidden by the task constraints).
"""

from dataclasses import dataclass

@dataclass(frozen=True)
class Quantity:
    """A named physical quantity in SI units."""

    symbol: str
    value: float
    unit: str

    def __str__(self) -> str:
        return f"{self.value:g} {self.unit}"

# Standard reference constants (SI, exact definitions)
RHO_WATER = 1000.0        # kg/m^3, liquid water at ~4 degC
G_STANDARD = 9.80665      # m/s^2, standard gravity (exact by definition)
P_ATM = 101325.0          # Pa, standard atmosphere (exact by definition)

def quantity(symbol: str, value: float, unit: str) -> Quantity:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise TypeError(f"{symbol}: expected a real number, got {type(value).__name__}")
    return Quantity(symbol=symbol, value=float(value), unit=unit)