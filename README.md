# BAGUS: FINE-FM

**B**asically **A** **G**enerally **U**seless **S**olver —
**F**luid **I**diot's **N**umerical **E**ngine for **F**luid **M**echanics

Companion demo to the article *"BAGUS: FINE-FM – Testing the BLOON Stack
with Water in a Bucket."*

> BAGUS may be generally useless. The numbers, however, are expected to
> be correct.

The joke is the wrapper. Underneath it is a serious architectural claim:

**A real engineering domain — fluid statics — can be expressed as a thin
domain layer on top of the existing BLOON → BLOON_MACHINE stack, without
modifying BLOON and without building a second numerical framework.**

If the BLOON stack cannot cleanly solve a bucket of water, it has no
business pretending to solve anything more complicated.

## Ownership

| Layer           | Owns                                                    |
|-----------------|---------------------------------------------------------|
| **FINE-FM**     | Physical quantities, equations, input validation, analytical references, presentation |
| **BLOON**       | Numerical representation and evaluation (State → Operators → Observables lifecycle) |
| **BLOON_MACHINE** | Policy + decision gate (ACCEPT / WARN / REJECT, fail-closed) via `integration.machine` |

FINE-FM contains **zero** numerical arithmetic of its own: every
operation is routed through the `NumericBackend` seam (`backend.py`).

## Supported problems (fluid statics only)

1. Hydrostatic pressure — `P = P0 + ρgh`
2. Pressure difference — `ΔP = ρgΔh`
3. Pascal hydraulic — `F2 = F1·A2/A1`
4. Buoyancy — `F_B = ρ_f·g·V` (+ float/sink verdict)
5. Hydrostatic surface force — `F = ∫ p dA`, vertical rectangle,
   numerical quadrature vs analytical
6. Water in a bucket — deliberately trivial, deliberately included

## Build / Run / Test

No build step (pure Python, no new dependencies; `pytest` for tests).

```bash
python examples/run_fine_fm.py --all       # non-interactive, CI-safe
python examples/run_fine_fm.py             # interactive menu
python examples/run_fine_fm.py --bucket    # the important one
python -m pytest tests -v                  # FINE-FM + existing suite