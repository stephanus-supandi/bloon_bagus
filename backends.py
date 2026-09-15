"""Numerical backends.

The domain layer NEVER performs raw arithmetic itself. It formulates each
problem in terms of the BLOON computational lifecycle and delegates
evaluation to a Backend. The Backend protocol mirrors that lifecycle:

    grid()                  -> Discretization      (1D uniform grid in y)
    pressure_operator()     -> Operator            (pointwise p = p0 + slope*y)
    pressure_profile()      -> State               (discrete pressure values)
    hydrostatic_force()     -> Observable          (trapezoid integral of p*w dy)
    add/sub/mul/div         -> primitive scalar algebra

PureBackend implements the protocol directly in Python (stdlib only) and is
the reference implementation used by the test suite.

BloonBackend is the alignment point with the real BLOON package. Because the
public repository does not expose the internal API signatures (documented,
intentional per BLOON README), BloonBackend raises BackendUnavailable with
ADAPTER NOTES instead of inventing calls. Wiring it is a mechanical, single-
file change once the real class/function names are known — no other module
in FINE-FM changes.
"""

import math
from dataclasses import dataclass
from typing import List, Protocol, Sequence

class BackendUnavailable(RuntimeError):
    """Raised when a backend cannot be constructed in this environment."""

class Backend(Protocol):
    name: str

    # --- primitive scalar algebra -------------------------------------
    def add(self, a: float, b: float) -> float: ...
    def sub(self, a: float, b: float) -> float: ...
    def mul(self, a: float, b: float) -> float: ...
    def div(self, a: float, b: float) -> float: ...

    # --- lifecycle primitives (BLOON-shaped) ---------------------------
    def grid(self, y_top: float, y_bottom: float, n: int) -> List[float]: ...
    def pressure_operator(self, p0: float, slope: float, y: float) -> float: ...
    def pressure_profile(self, p0: float, slope: float,
                         y_top: float, y_bottom: float, n: int) -> List[float]: ...
    def hydrostatic_force(self, profile: Sequence[float], grid: Sequence[float],
                          width: float) -> float: ...

class PureBackend:
    """Reference backend: the same lifecycle, plain Python arithmetic."""

    name = "PureBackend (stdlib reference)"

    def add(self, a: float, b: float) -> float:
        return a + b

    def sub(self, a: float, b: float) -> float:
        return a - b

    def mul(self, a: float, b: float) -> float:
        if a == 0.0 or b == 0.0:
            return 0.0
        return a * b

    def div(self, a: float, b: float) -> float:
        if b == 0.0:
            raise ZeroDivisionError("division by zero in backend arithmetic")
        return a / b

    def grid(self, y_top: float, y_bottom: float, n: int) -> List[float]:
        if n < 1:
            raise ValueError("grid requires n >= 1 intervals")
        if y_bottom < y_top:
            raise ValueError("y_bottom must be >= y_top (depth increases downward)")
        dy = (y_bottom - y_top) / n
        return [y_top + i * dy for i in range(n + 1)]

    def pressure_operator(self, p0: float, slope: float, y: float) -> float:
        # Pointwise hydrostatic pressure operator: p(y) = p0 + slope * y
        return p0 + slope * y

    def pressure_profile(self, p0: float, slope: float,
                         y_top: float, y_bottom: float, n: int) -> List[float]:
        return [self.pressure_operator(p0, slope, y) for y in self.grid(y_top, y_bottom, n)]

    def hydrostatic_force(self, profile: Sequence[float], grid: Sequence[float],
                          width: float) -> float:
        # Composite trapezoid rule for F = width * integral(p dy).
        # NOTE: for a LINEAR integrand p(y) the composite trapezoid rule is
        # exact (error term ~ f''(y) = 0); residual error is float rounding.
        if len(profile) != len(grid) or len(profile) < 2:
            raise ValueError("profile and grid must have matching length >= 2")
        total = 0.0
        for i in range(len(grid) - 1):
            dy = grid[i + 1] - grid[i]
            total += 0.5 * (profile[i] + profile[i + 1]) * dy
        return width * total

class BloonBackend:
    """Backend that evaluates through the real BLOON package.

    ADAPTER NOTES (alignment required — see fine_fm/README.md):
      1. Replace `import bloon` targets with the actual public API used by
         examples/run_heat.py and examples/run_structural.py (State,
         discretization/grid construction, operator classes, observable
         extraction, verification helpers).
      2. Map PureBackend.grid            -> BLOON 1D discretization
         PureBackend.pressure_operator   -> BLOON pointwise operator on State
         PureBackend.pressure_profile    -> BLOON State evaluation
         PureBackend.hydrostatic_force   -> BLOON observable (quadrature over State)
      3. Do NOT change any other FINE-FM module: the Backend protocol is the
         only contract the domain layer consumes.
    """

    name = "BloonBackend (BLOON package)"

    def __init__(self) -> None:
        try:
            import bloon  # noqa: F401
        except ImportError as exc:
            raise BackendUnavailable(
                "bloon package not importable from this working directory: "
                f"{exc}. Run from the BLOON project root."
            ) from exc
        raise BackendUnavailable(
            "BloonBackend adapter alignment pending: the public BLOON surface "
            "does not document State/Operator/Observable constructor "
            "signatures. Wire this class against examples/run_heat.py and "
            "examples/run_structural.py conventions (see ADAPTER NOTES). "
            "Use --backend pure until then."
        )

def get_backend(name: str) -> Backend:
    if name == "pure":
        return PureBackend()
    if name == "bloon":
        return BloonBackend()  # raises BackendUnavailable until aligned
    raise ValueError(f"unknown backend: {name!r} (expected 'pure' or 'bloon')")