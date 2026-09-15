"""FINE-FM domain layer: fluid statics formulations.

This module owns PHYSICS ONLY: quantities, equations, validation of
physical inputs. It performs no numerical arithmetic itself -- every
operation is delegated to a NumericBackend (see backend.py).

Problems implemented (fluid statics, nothing more):
    P       = P0 + rho*g*h                 hydrostatic pressure
    dP      = rho*g*dh                     pressure difference
    F2      = F1 * A2/A1                   Pascal / hydraulic
    F_B     = rho_f * g * V_displaced      Archimedes buoyancy
    F       = int_A p dA,  p(y)=P0+rho*g*y hydrostatic surface force
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .backend import NumericBackend

G_STANDARD = 9.80665        # m/s^2
RHO_WATER = 1000.0          # kg/m^3
P_ATM = 101325.0            # Pa

def _require(cond: bool, msg: str) -> None:
    if not cond:
        raise ValueError(msg)

@dataclass(frozen=True)
class PressureResult:
    contribution: float     # rho*g*h          [Pa]
    absolute: float         # P0 + rho*g*h     [Pa]
    gauge: float            # absolute - P0    [Pa]

def hydrostatic_pressure(
    backend: NumericBackend,
    rho: float = RHO_WATER,
    g: float = G_STANDARD,
    h: float = 10.0,
    p0: float = P_ATM,
) -> PressureResult:
    _require(rho > 0.0, "density must be positive")
    _require(g > 0.0, "gravity must be positive")
    _require(h >= 0.0, "depth must be non-negative")
    contribution = backend.mul(rho, g, h)
    absolute = backend.add(p0, contribution)
    gauge = backend.add(absolute, -p0)
    return PressureResult(contribution, absolute, gauge)

@dataclass(frozen=True)
class PressureDifferenceResult:
    dh: float               # h2 - h1  [m]
    dp: float               # rho*g*dh [Pa]

def pressure_difference(
    backend: NumericBackend,
    h1: float,
    h2: float,
    rho: float = RHO_WATER,
    g: float = G_STANDARD,
) -> PressureDifferenceResult:
    _require(rho > 0.0, "density must be positive")
    _require(h1 >= 0.0 and h2 >= 0.0, "depths must be non-negative")
    dh = backend.add(h2, -h1)
    dp = backend.mul(rho, g, dh)
    return PressureDifferenceResult(dh, dp)

@dataclass(frozen=True)
class PascalResult:
    f2: float               # F1 * A2/A1  [N]
    ratio: float            # A2/A1       [-]

def pascal_force(
    backend: NumericBackend,
    f1: float,
    a1: float,
    a2: float,
) -> PascalResult:
    _require(a1 > 0.0, "area A1 must be positive")
    _require(a2 > 0.0, "area A2 must be positive")
    _require(f1 >= 0.0, "input force must be non-negative")
    ratio = backend.div(a2, a1)
    return PascalResult(backend.mul(f1, ratio), ratio)

FLOATS, SINKS, NEUTRAL = "FLOATS", "SINKS", "NEUTRAL"

@dataclass(frozen=True)
class BuoyancyResult:
    buoyant_force: float    # rho_f*g*V  [N]
    verdict: Optional[str]  # vs object weight, if given

def buoyancy(
    backend: NumericBackend,
    rho_f: float = RHO_WATER,
    v_displaced: float = 0.05,
    g: float = G_STANDARD,
    object_weight: Optional[float] = None,
) -> BuoyancyResult:
    _require(rho_f > 0.0, "fluid density must be positive")
    _require(v_displaced >= 0.0, "displaced volume must be non-negative")
    fb = backend.mul(rho_f, g, v_displaced)
    verdict = None
    if object_weight is not None:
        _require(object_weight >= 0.0, "weight must be non-negative")
        if fb > object_weight:
            verdict = FLOATS
        elif fb < object_weight:
            verdict = SINKS
        else:
            verdict = NEUTRAL
    return BuoyancyResult(fb, verdict)

@dataclass(frozen=True)
class SurfaceForceResult:
    analytical: float       # w * [P0*H + rho*g*((h2^2 - h1^2)/2)]
    numerical: float        # w * midpoint-quadrature of int p(y) dy
    n_cells: int
    abs_error: float
    rel_error: float

def hydrostatic_surface_force(
    backend: NumericBackend,
    width: float = 2.0,
    height: float = 3.0,
    top_depth: float = 1.0,
    rho: float = RHO_WATER,
    g: float = G_STANDARD,
    p0: float = P_ATM,
    n_cells: int = 400,
) -> SurfaceForceResult:
    """Vertical rectangular plate, width x height, top edge at depth
    top_depth. p(y) = p0 + rho*g*y is LINEAR in y, so the composite
    midpoint rule is exact in real arithmetic; the only error is float
    round-off. This is why the validation tolerance is 1e-12 relative,
    not a fabricated quadrature tolerance."""
    _require(width > 0.0, "width must be positive")
    _require(height > 0.0, "height must be positive")
    _require(top_depth >= 0.0, "top depth must be non-negative")
    _require(n_cells > 0, "n_cells must be positive")

    y_bot = top_depth + height
    # analytical: F = w * int_{h1}^{h2} (p0 + rho g y) dy
    integral_exact = p0 * height + rho * g * (y_bot**2 - top_depth**2) / 2.0
    analytical = width * integral_exact

    def p(y: float) -> float:
        return p0 + rho * g * y

    numerical = width * backend.integrate_midpoint(p, top_depth, y_bot, n_cells)

    abs_err = abs(numerical - analytical)
    rel_err = abs_err / abs(analytical) if analytical != 0.0 else abs_err
    return SurfaceForceResult(analytical, numerical, n_cells, abs_err, rel_err)

def bucket_bottom_pressure(
    backend: NumericBackend,
    depth: float = 0.30,
    rho: float = RHO_WATER,
    g: float = G_STANDARD,
    p0: float = P_ATM,
) -> PressureResult:
    """The water-in-a-bucket problem. The joke is intentional.
    The engineering is not."""
    return hydrostatic_pressure(backend, rho, g, depth, p0)