"""BLOON_MACHINE integration boundary.

Architectural invariant (from the BLOON README):
    BLOON         = facts + computation
    BLOON_MACHINE = policy + decision (ACCEPT / WARN / REJECT, fail-closed)

FINE-FM submits a computational request (task id + physical facts) to the
`integration.machine` adapter BEFORE evaluation. The adapter API signatures
are not exposed publicly, so this module attempts the documented import and
reports honestly when the boundary is unreachable — it never fabricates a
decision.

Semantics implemented here:
    ACCEPT      -> proceed
    WARN        -> proceed, warning retained in the output
    REJECT      -> computation blocked (fail-closed)
    UNAVAILABLE -> adapter not reachable; treated as WARN in dev mode,
                   as REJECT when strict=True (fail-closed by policy)
"""

from dataclasses import dataclass, field
from typing import Any, Dict

@dataclass(frozen=True)
class Decision:
    status: str                      # ACCEPT | WARN | REJECT | UNAVAILABLE
    reason: str = ""
    raw: Any = field(default=None, repr=False)

    @property
    def allows_computation(self) -> bool:
        return self.status in ("ACCEPT", "WARN")

def evaluate_request(task_id: str, facts: Dict[str, Any], strict: bool = False) -> Decision:
    """Submit a computational request through the integration boundary."""
    try:
        import integration.machine as machine  # noqa: F401
    except Exception as exc:  # ImportError or namespace issues — fail honest
        status = "REJECT" if strict else "UNAVAILABLE"
        return Decision(
            status=status,
            reason=f"integration.machine adapter unreachable ({exc!r}); "
                   f"strict={'on (fail-closed)' if strict else 'off (dev mode)'}",
        )

    # Adapter reachable: call the documented evaluation entry point.
    # Candidate names cover the plausible public surface; the FIRST that
    # exists wins. If none matches, fail closed rather than guess.
    request = {"task": task_id, "facts": facts}
    for attr in ("evaluate", "evaluate_request", "decide", "gate"):
        fn = getattr(machine, attr, None)
        if callable(fn):
            try:
                result = fn(request)
            except TypeError:
                result = fn(task_id, facts)
            status = str(getattr(result, "status", result)).upper()
            if status.startswith("ACCEPT"):
                return Decision("ACCEPT", "machine policy satisfied", result)
            if status.startswith("WARN"):
                return Decision("WARN", str(getattr(result, "reason", result)), result)
            return Decision("REJECT", str(getattr(result, "reason", result)), result)
    return Decision(
        "REJECT",
        "integration.machine exposes no known evaluation entry point "
        "(fail-closed: cannot safely evaluate the request)",
    )