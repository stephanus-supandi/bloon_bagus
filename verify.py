"""Deterministic validation: analytical reference vs numerical result.

Tolerance policy (documented, not fabricated):
* Algebraic demos (1-4): both paths evaluate the same closed-form
  expression in float64; agreement is expected at round-off level.
  rtol = 1e-12.
* Demo 5 quadrature: integrand p(y) is linear, composite midpoint is
  exact in real arithmetic; observed error is float round-off only.
  rtol = 1e-12.
Where an analytical solution exists it is ALWAYS the reference.
"""

from __future__ import annotations

from dataclasses import dataclass

RTOL_ALGEBRAIC = 1e-12
RTOL_QUADRATURE = 1e-12

@dataclass(frozen=True)
class VerificationResult:
    label: str
    analytical: float
    numerical: float
    rtol: float

    @property
    def abs_error(self) -> float:
        return abs(self.numerical - self.analytical)

    @property
    def rel_error(self) -> float:
        if self.analytical == 0.0:
            return self.abs_error
        return self.abs_error / abs(self.analytical)

    @property
    def passed(self) -> bool:
        return self.rel_error <= self.rtol

    def line(self) -> str:
        tag = "[PASS]" if self.passed else "[FAIL]"
        return f"{tag} {self.label}"

    def block(self) -> str:
        return (
            f"  analytical : {self.analytical:.10e}\n"
            f"  numerical  : {self.numerical:.10e}\n"
            f"  abs error  : {self.abs_error:.3e}\n"
            f"  rel error  : {self.rel_error:.3e}  (rtol={self.rtol:.0e})\n"
            f"  {self.line()}"
        )