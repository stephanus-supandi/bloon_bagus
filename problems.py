"""The five fluid-statics problems, formulated by FINE-FM, evaluated by the
backend, validated against closed-form analytical solutions.

Each demo follows the visible stack pipeline:

    FINE-FM (physical problem)
      -> mathematical formulation (equation + operator graph)
      -> backend (BLOON-shaped lifecycle: grid/operator/state/observable)
      -> numerical result
      -> validation (analytical vs numerical, PASS/FAIL)

The BLOON_MACHINE gate is applied by the runner BEFORE calling into these
functions (see examples/run_fine_fm.py), matching the
run_heat_with_machine.py pattern: gate first, compute second.
"""

from dataclasses import dataclass, field
from typing import Dict, List

from .backends import Backend
from .quantities import G_STANDARD, P_ATM, RHO_WATER, Quantity
from .validation import (
    ABS_TOL_ALGEBRA, ABS_TOL_TRAPEZOID_LINEAR,
    REL_TOL_ALGEBRA, REL_TOL_TRAPEZOID_LINEAR, ValidationRecord,
)

@dataclass
class DemoRecord:
    key: str
    title: str
    formulation: List[str]                 # mathematical formulation lines
    inputs: List[Quantity]                 # physical inputs (FINE-FM owns)
    computed: Dict[str, Quantity] = field(default_factory=dict)
    validation: List[ValidationRecord] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(v.passed for v in self.validation)

# --------------------------------------------------------------------------
# Demo 1 — Hydrostatic Pressure:  P = P0 + rho * g * h
# --------------------------------------------------------------------------

def hydrostatic_pressure(backend: Backend, *,
                         rho: float = RHO_WATER, g: float = G_STANDARD,
                         h: float = 10.0, p0: float = P_ATM) -> DemoRecord:
    if h < 0.0:
        raise ValueError(f"depth must be >= 0 (got {h} m)")
    if rho <= 0.0 or g <= 0.0:
        raise ValueError("density and gravity must be positive")

    contribution = backend.mul(backend.mul(rho, g), h)          # rho*g*h
    absolute = backend.add(p0, contribution)                    # P0 + rho*g*h
    gauge = backend.sub(absolute, p0)                           # == contribution

    rec = DemoRecord(
        key="hydrostatic_pressure",
        title="Hydrostatic Pressure",
        formulation=["P = P0 + rho * g * h"],
        inputs=[Quantity("rho", rho, "kg/m^3"), Quantity("h", h, "m"),
                Quantity("g", g, "m/s^2"), Quantity("P0", p0, "Pa")],
        computed={
            "contribution": Quantity("rho*g*h", contribution, "Pa"),
            "absolute": Quantity("P", absolute, "Pa"),
            "gauge": Quantity("P - P0", gauge, "Pa"),
        },
    )
    analytical = p0 + rho * g * h
    rec.validation.append(ValidationRecord(
        "Hydrostatic pressure", analytical, absolute, "Pa",
        REL_TOL_ALGEBRA, ABS_TOL_ALGEBRA))
    return rec

# --------------------------------------------------------------------------
# Demo 2 — Pressure Difference:  dP = rho * g * dh   (P0 cancels)
# --------------------------------------------------------------------------

def pressure_difference(backend: Backend, *,
                        rho: float = RHO_WATER, g: float = G_STANDARD,
                        h1: float = 2.0, h2: float = 7.0,
                        p0: float = P_ATM) -> DemoRecord:
    if h1 < 0.0 or h2 < 0.0:
        raise ValueError("depths must be >= 0")

    p1 = backend.add(p0, backend.mul(backend.mul(rho, g), h1))
    p2 = backend.add(p0, backend.mul(backend.mul(rho, g), h2))
    dp_numeric = backend.sub(p2, p1)                            # P0 cancels here
    dh = backend.sub(h2, h1)
    dp_direct = backend.mul(backend.mul(rho, g), dh)            # rho*g*dh

    rec = DemoRecord(
        key="pressure_difference",
        title="Pressure Difference",
        formulation=[
            "P(h) = P0 + rho * g * h",
            "dP = P(h2) - P(h1) = rho * g * (h2 - h1)",
            "-> dP is independent of the reference pressure P0",
        ],
        inputs=[Quantity("h1", h1, "m"), Quantity("h2", h2, "m"),
                Quantity("rho", rho, "kg/m^3"), Quantity("g", g, "m/s^2"),
                Quantity("P0", p0, "Pa")],
        computed={
            "P(h1)": Quantity("P1", p1, "Pa"),
            "P(h2)": Quantity("P2", p2, "Pa"),
            "dP": Quantity("dP", dp_numeric, "Pa"),
            "dP (direct rho*g*dh)": Quantity("dP", dp_direct, "Pa"),
        },
        notes=["Same dP results for P0 = 0 and P0 = 101325 Pa "
               "(covered by the test suite)."],
    )
    analytical = rho * g * (h2 - h1)
    rec.validation.append(ValidationRecord(
        "Pressure difference", analytical, dp_numeric, "Pa",
        REL_TOL_ALGEBRA, ABS_TOL_ALGEBRA))
    return rec

# --------------------------------------------------------------------------
# Demo 3 — Pascal / Hydraulic System:  F1/A1 = F2/A2
# --------------------------------------------------------------------------

def pascal_hydraulic(backend: Backend, *,
                     a1: float = 0.01, a2: float = 0.10,
                     f1: float = 100.0) -> DemoRecord:
    if a1 <= 0.0 or a2 <= 0.0:
        raise ValueError("piston areas must be positive")
    if f1 < 0.0:
        raise ValueError("input force must be >= 0")

    pressure = backend.div(f1, a1)                              # F1/A1
    f2 = backend.mul(pressure, a2)                              # (F1/A1) * A2
    ratio = backend.div(a2, a1)
    mechanical_advantage_check = backend.div(f2, f1) if f1 > 0 else 0.0

    rec = DemoRecord(
        key="pascal_hydraulic",
        title="Pascal Hydraulic System",
        formulation=[
            "F1 / A1 = F2 / A2        (Pascal's principle)",
            "F2 = F1 * (A2 / A1)",
        ],
        inputs=[Quantity("A1", a1, "m^2"), Quantity("A2", a2, "m^2"),
                Quantity("F1", f1, "N")],
        computed={
            "system pressure": Quantity("F1/A1", pressure, "Pa"),
            "area ratio": Quantity("A2/A1", ratio, "-"),
            "output force": Quantity("F2", f2, "N"),
            "F2/F1": Quantity("F2/F1", mechanical_advantage_check, "-"),
        },
        notes=["F2/A2 must equal F1/A1 — asserted by validation below."],
    )
    analytical = f1 * (a2 / a1)
    rec.validation.append(ValidationRecord(
        "Pascal hydraulic force", analytical, f2, "N",
        REL_TOL_ALGEBRA, ABS_TOL_ALGEBRA))
    # Physical invariant: pressure equal on both sides.
    rec.validation.append(ValidationRecord(
        "Pascal pressure equality F2/A2 == F1/A1", pressure, backend.div(f2, a2), "Pa",
        REL_TOL_ALGEBRA, ABS_TOL_ALGEBRA))
    return rec

# --------------------------------------------------------------------------
# Demo 4 — Buoyancy:  F_B = rho_f * g * V_displaced
# --------------------------------------------------------------------------

def buoyancy(backend: Backend, *,
             rho_f: float = RHO_WATER, g: float = G_STANDARD,
             v_disp: float = 0.05,
             object_mass: float = 40.0) -> DemoRecord:
    if v_disp < 0.0:
        raise ValueError("displaced volume must be >= 0")
    if rho_f <= 0.0 or g <= 0.0:
        raise ValueError("fluid density and gravity must be positive")
    if object_mass < 0.0:
        raise ValueError("object mass must be >= 0")

    f_b = backend.mul(backend.mul(rho_f, g), v_disp)            # rho_f*g*V
    weight = backend.mul(object_mass, g)                        # m*g
    if backend.sub(f_b, weight) > 0.0:
        verdict = "floats / rises (F_B > W)"
    elif backend.sub(f_b, weight) < 0.0:
        verdict = "sinks (F_B < W)"
    else:
        verdict = "neutrally buoyant (F_B = W)"

    rec = DemoRecord(
        key="buoyancy",
        title="Buoyancy (Archimedes)",
        formulation=[
            "F_B = rho_f * g * V_displaced",
            "sink/float: compare F_B with W = m * g",
        ],
        inputs=[Quantity("rho_f", rho_f, "kg/m^3"),
                Quantity("V_displaced", v_disp, "m^3"),
                Quantity("g", g, "m/s^2"),
                Quantity("m_object", object_mass, "kg")],
        computed={
            "buoyant force": Quantity("F_B", f_b, "N"),
            "object weight": Quantity("W", weight, "N"),
        },
        notes=[f"Verdict for fully submerged object: {verdict}"],
    )
    analytical = rho_f * g * v_disp
    rec.validation.append(ValidationRecord(
        "Buoyancy", analytical, f_b, "N",
        REL_TOL_ALGEBRA, ABS_TOL_ALGEBRA))
    return rec

# --------------------------------------------------------------------------
# Demo 5 — Hydrostatic Force on a vertical rectangular surface
#          F = integral_A p dA,  p(y) = p0 + rho*g*y
# --------------------------------------------------------------------------

def hydrostatic_force(backend: Backend, *,
                      width: float = 2.0, height: float = 3.0,
                      h_top: float = 1.0,
                      rho: float = RHO_WATER, g: float = G_STANDARD,
                      p0: float = P_ATM, n: int = 64) -> DemoRecord:
    if width <= 0.0 or height < 0.0:
        raise ValueError("width must be positive and height >= 0")
    if h_top < 0.0:
        raise ValueError("top depth must be >= 0")
    if n < 1:
        raise ValueError("quadrature requires n >= 1 intervals")

    slope = backend.mul(rho, g)                                 # rho*g
    y_bottom = backend.add(h_top, height)

    # BLOON-shaped lifecycle, all through the backend:
    grid = backend.grid(h_top, y_bottom, n)                     # Discretization
    profile = backend.pressure_profile(p0, slope, h_top, y_bottom, n)  # Operator -> State
    f_numeric = backend.hydrostatic_force(profile, grid, width)        # Observable

    # Analytical closed form: F = (p0 + rho*g*h_c) * A, h_c = h_top + height/2
    area = width * height
    h_c = h_top + 0.5 * height
    f_analytical = (p0 + rho * g * h_c) * area

    rec = DemoRecord(
        key="hydrostatic_force",
        title="Hydrostatic Force on a Vertical Rectangular Surface",
        formulation=[
            "p(y) = p0 + rho * g * y           (pressure distribution)",
            "F = integral_A p dA = w * integral_{h_top}^{h_bot} p(y) dy",
            "analytical: F = (p0 + rho*g*h_c) * A,  h_c = h_top + H/2",
            "numerical: composite trapezoid rule over the discrete state",
        ],
        inputs=[Quantity("geometry", 0.0, "vertical rectangle"),
                Quantity("w", width, "m"), Quantity("H", height, "m"),
                Quantity("h_top", h_top, "m"), Quantity("rho", rho, "kg/m^3"),
                Quantity("g", g, "m/s^2"), Quantity("p0", p0, "Pa"),
                Quantity("n", float(n), "intervals")],
        computed={
            "area": Quantity("A", area, "m^2"),
            "centroid depth": Quantity("h_c", h_c, "m"),
            "numerical force": Quantity("F_num", f_numeric, "N"),
        },
        notes=[
            "Trapezoid rule is EXACT for a linear integrand (error ~ f'' = 0);",
            "observed residual is float rounding only and is grid-independent.",
        ],
    )
    rec.validation.append(ValidationRecord(
        "Hydrostatic surface force", f_analytical, f_numeric, "N",
        REL_TOL_TRAPEZOID_LINEAR, ABS_TOL_TRAPEZOID_LINEAR))
    return rec

# --------------------------------------------------------------------------
# The bucket — deliberately trivial, deliberately the point.
# --------------------------------------------------------------------------

def bucket(backend: Backend, *, h: float = 0.30) -> DemoRecord:
    """A bucket contains water. How much pressure is at the bottom?"""
    rec = hydrostatic_pressure(backend, h=h)
    rec.key = "bucket"
    rec.title = "Water in a Bucket"
    rec.formulation = ["Question: how much pressure at the bottom of a bucket?"] + rec.formulation
    rec.notes = [
        f"A bucket, {h:g} m of water. That's the whole problem.",
        "If the BLOON stack cannot cleanly solve a bucket of water,",
        "it has no business pretending to solve anything more complicated.",
    ]
    return rec

ALL_DEMO_FACTORIES = {
    "1": hydrostatic_pressure,
    "2": pressure_difference,
    "3": pascal_hydraulic,
    "4": buoyancy,
    "5": hydrostatic_force,
}