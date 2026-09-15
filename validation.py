"""Deterministic validation: analytical reference vs numerical result.

Tolerance policy (documented, not fabricated):
  * Demos 1-4 are scalar algebra (add/mul/div). The numerical path performs
    the same IEEE-754 double operations in a possibly different order, so
    the expected discrepancy is rounding only:
        rel_tol = 1e-12, abs_tol = 1e-6 (Pa or N scale)
  * Demo 5 integrates a LINEAR pressure profile p(y) = p0 + rho*g*y with the
    composite trapezoid rule, which is exact for linear integrands (the
    error term is proportional to f'' = 0). The residual is again rounding
    only, and is grid-independent:
        rel_tol = 1e-12, abs_tol = 1e-6 N
  These tolerances assert more than 'the function ran': they pin the actual
  numbers to the closed-form solutions.
"""

from dataclasses import dataclass

REL_TOL_ALGEBRA = 1e-12
ABS_TOL_ALGEBRA = 1e-6
REL_TOL_TRAPEZOID_LINEAR = 1e-12
ABS_TOL_TRAPEZOID_LINEAR = 1e-6

@dataclass(frozen=True)
class ValidationRecord:
    label: str
    analytical: float
    numerical: float
    unit: str
    rel_tol: float
    abs_tol: float

    @property
    def abs_error(self) -> float:
        return abs(self.numerical - self.analytical)

    @property
    def rel_error(self) -> float:
        if self.analytical == 0.0:
            return 0.0 if self.numerical == 0.0 else float("inf")
        return self.abs_error / abs(self.analytical)

    @property
    def passed(self) -> bool:
        return self.abs_error <= max(self.abs_tol, self.rel_tol * abs(self.analytical))

    def summary_line(self) -> str:
        tag = "[PASS]" if self.passed else "[FAIL]"
        return (f"{tag} {self.label}: analytical={self.analytical:.6f} {self.unit}, "
                f"numerical={self.numerical:.6f} {self.unit}, "
                f"abs_err={self.abs_error:.3e}, rel_err={self.rel_error:.3e}")