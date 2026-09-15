"""Numerical backend seam for BAGUS: FINE-FM.

FINE-FM owns physical formulation ONLY. Every numerical evaluation is
routed through a backend implementing ``NumericBackend``.

Backends
--------
BloonBackend      routes evaluation through the BLOON stack
                  (State -> Operators -> Observables).
ReferenceBackend  minimal deterministic scalar evaluator used for
                  verification and for environments where the BLOON
                  package is not importable.

DOCUMENTED LIMITATION
---------------------
The BLOON public repository does not expose internal numerical API
signatures to external tooling (README: "The distinction between public
computational artifacts and private implementation machinery is
intentional."). ``BloonBackend._connect_bloon`` is therefore a single,
clearly marked integration point that must be wired to the real API
names in ``bloon/`` before it activates. Until wired, ``make_backend``
falls back to ``ReferenceBackend`` and EVERY printed report states which
backend produced the numbers. Nothing is hidden behind the fallback.

The ReferenceBackend is intentionally ~40 lines of scalar arithmetic.
It is a verification reference, not a parallel numerical framework.
"""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from typing import Callable

class BackendUnavailable(RuntimeError):
    """Raised when the BLOON backend cannot be activated."""

class NumericBackend(ABC):
    """Contract between FINE-FM formulations and numerical execution."""

    name: str = "abstract"

    @abstractmethod
    def add(self, *terms: float) -> float: ...

    @abstractmethod
    def mul(self, *factors: float) -> float: ...

    @abstractmethod
    def div(self, a: float, b: float) -> float: ...

    @abstractmethod
    def integrate_midpoint(
        self, f: Callable[[float], float], a: float, b: float, n: int
    ) -> float:
        """Composite midpoint rule for int_a^b f(y) dy with n cells."""

class ReferenceBackend(NumericBackend):
    """Deterministic scalar reference evaluator (float64)."""

    name = "reference"

    def add(self, *terms: float) -> float:
        return math.fsum(terms)

    def mul(self, *factors: float) -> float:
        r = 1.0
        for x in factors:
            r *= x
        return r

    def div(self, a: float, b: float) -> float:
        if b == 0.0:
            raise ZeroDivisionError("division by zero in backend")
        return a / b

    def integrate_midpoint(self, f, a, b, n):
        if n <= 0:
            raise ValueError("n must be positive")
        if b < a:
            raise ValueError("expected b >= a")
        dy = (b - a) / n
        return math.fsum(f(a + (i + 0.5) * dy) for i in range(n)) * dy

class BloonBackend(NumericBackend):
    """Routes numerical work through the actual BLOON stack.

    Activation requires that ``bloon`` is importable AND that
    ``_connect_bloon`` has been wired to the real public API.
    Otherwise raises BackendUnavailable (fail-closed, no silent
    fallback inside this class).
    """

    name = "bloon"

    def __init__(self) -> None:
        try:
            import bloon  # noqa: F401
        except ImportError as exc:
            raise BackendUnavailable(
                f"bloon package not importable: {exc}"
            ) from exc
        self._api = self._connect_bloon()

    def _connect_bloon(self):
        # TODO(VERIFY): wire to the real BLOON public API, e.g. map
        #   add/mul/div   -> scalar Operator evaluation on a State
        #   midpoint      -> 1D Discretization + quadrature Operator
        # using the same entry points consumed by examples/run_heat.py
        # and examples/run_structural.py. The BLOON public repo does not
        # expose these signatures externally; see module docstring.
        raise BackendUnavailable(
            "BloonBackend wiring pending: connect _connect_bloon to the "
            "real bloon State/Operator API (see docstring)."
        )

    # The four abstract methods delegate to self._api once wired.
    def add(self, *t): return self._api.add(*t)
    def mul(self, *f): return self._api.mul(*f)
    def div(self, a, b): return self._api.div(a, b)
    def integrate_midpoint(self, f, a, b, n):
        return self._api.integrate_midpoint(f, a, b, n)

def make_backend(prefer: str = "bloon") -> NumericBackend:
    """Select backend. Never lies about which one is active."""
    if prefer == "reference":
        return ReferenceBackend()
    try:
        return BloonBackend()
    except BackendUnavailable:
        return ReferenceBackend()