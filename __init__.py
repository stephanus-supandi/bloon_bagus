"""BAGUS: FINE-FM — Fluid Idiot's Numerical Engine for Fluid Mechanics.

A domain layer for fundamental fluid mechanics / fluid statics on top of
the BLOON -> BLOON_MACHINE stack.

FINE-FM owns:   physical quantities, problem formulation, equations.
BLOON owns:     numerical representation and evaluation.
BLOON_MACHINE:  policy + decision gating (ACCEPT / WARN / REJECT).

Basically A Generally Useless Solver. The numbers, however, are expected
to be correct.
"""

__version__ = "0.1.0"