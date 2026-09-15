#!/usr/bin/env python3
"""BAGUS: FINE-FM demonstration runner.

Usage:
    python examples/run_fine_fm.py            # interactive menu
    python examples/run_fine_fm.py --all      # CI mode: run everything
    python examples/run_fine_fm.py --demo 5   # single demo
    python examples/run_fine_fm.py --backend bloon --strict-gate

Follows the examples/ convention: standalone executable, no side effects on
the BLOON package.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from bloon_bagus import problems                                  # noqa: E402
from bloon_bagus.backends import BackendUnavailable, get_backend   # noqa: E402
from bloon_bagus.machine_gate import evaluate_request              # noqa: E402

BANNER = """
====================================================
BAGUS: FINE-FM
Basically A Generally Useless Solver
Fluid Idiot's Numerical Engine for Fluid Mechanics
====================================================

BLOON STACK DEMONSTRATION
Fundamental Fluid Mechanics / Fluid Statics
"""

MENU = """
[1] Hydrostatic Pressure
[2] Pressure Difference
[3] Pascal Hydraulic System
[4] Buoyancy
[5] Hydrostatic Force
[6] Run All
[0] Exit
"""

STACK_TEMPLATE = """
      FINE-FM            physical quantities + equations
         |
         v
      BLOON              numerical representation   [{backend}]
         |
         v
      BLOON_MACHINE      execution gate             [{gate}]
         |
         v
      numerical result -> validation
"""

def _print_stack(backend_name: str, gate_status: str) -> None:
    print(STACK_TEMPLATE.format(backend=backend_name, gate=gate_status))

def _run_one(key: str, backend, gate_status: str) -> bool:
    factory = problems.ALL_DEMO_FACTORIES[key]
    facts = {"problem": factory.__name__, "domain": "fluid-statics"}
    decision = evaluate_request(f"fine_fm.{factory.__name__}", facts)

    print("-" * 52)
    if decision.status == "REJECT":
        print(f"[BLOCKED] BLOON_MACHINE gate REJECTED '{factory.__name__}': "
              f"{decision.reason}")
        return False
    if decision.status == "UNAVAILABLE":
        print(f"[WARN] BLOON_MACHINE gate unavailable: {decision.reason}")
        print("       (dev mode: proceeding ungated; use --strict-gate to fail closed)")

    record = factory(backend)
    _print_stack(backend.name, decision.status)

    print(record.title)
    print("-" * len(record.title))
    print("Formulation:")
    for line in record.formulation:
        print(f"  {line}")
    print("Inputs:")
    for q in record.inputs:
        if q.symbol == "geometry":
            print(f"  Geometry:           {q.unit}")
        else:
            print(f"  {q.symbol:<18}{q}")
    print("Results:")
    for label, q in record.computed.items():
        print(f"  {label + ':':<24}{q.value:.6f} {q.unit}")
    for note in record.notes:
        print(f"  # {note}")
    print("Validation:")
    for v in record.validation:
        print(f"  {v.summary_line()}")
    return record.passed

def run_all(backend, verbose_stack: bool = True) -> int:
    results = {}
    for key in ("1", "2", "3", "4", "5"):
        results[key] = _run_one(key, backend, "n/a" if not verbose_stack else "")
    # The bucket: the philosophy check.
    print("-" * 52)
    bucket_rec = problems.bucket(backend)
    print(bucket_rec.title)
    for line in bucket_rec.formulation:
        print(f"  {line}")
    for label, q in bucket_rec.computed.items():
        print(f"  {label + ':':<24}{q.value:.6f} {q.unit}")
    for note in bucket_rec.notes:
        print(f"  # {note}")
    for v in bucket_rec.validation:
        print(f"  {v.summary_line()}")
    results["bucket"] = bucket_rec.passed

    print("=" * 52)
    print(" SUMMARY")
    print("=" * 52)
    labels = {"1": "Hydrostatic pressure", "2": "Pressure difference",
              "3": "Pascal hydraulic force", "4": "Buoyancy",
              "5": "Hydrostatic surface force", "bucket": "Water in a bucket"}
    all_pass = True
    for key, ok in results.items():
        print(f"  {'[PASS]' if ok else '[FAIL]'} {labels[key]}")
        all_pass = all_pass and ok
    print()
    print("  BAGUS may be generally useless.")
    print("  The numbers, however, are expected to be correct.")
    return 0 if all_pass else 1

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="run_fine_fm",
                                     description="BAGUS: FINE-FM demonstration")
    parser.add_argument("--all", action="store_true", help="run all demos (CI mode)")
    parser.add_argument("--demo", choices=list(problems.ALL_DEMO_FACTORIES),
                        help="run a single demo")
    parser.add_argument("--backend", choices=("pure", "bloon"), default="pure",
                        help="numerical backend (default: pure)")
    parser.add_argument("--strict-gate", action="store_true",
                        help="fail closed when BLOON_MACHINE adapter is unreachable")
    args = parser.parse_args(argv)

    print(BANNER)
    try:
        backend = get_backend(args.backend)
    except BackendUnavailable as exc:
        print(f"[ERROR] backend '{args.backend}' unavailable:\n  {exc}")
        return 2

    if args.all:
        return run_all(backend)
    if args.demo:
        ok = _run_one(args.demo, backend, "")
        return 0 if ok else 1

    while True:
        print(MENU)
        try:
            choice = input("Choose> ").strip()
        except (EOFError, KeyboardInterrupt):
            return 0
        if choice == "0":
            return 0
        if choice == "6":
            return run_all(backend)
        if choice in problems.ALL_DEMO_FACTORIES:
            _run_one(choice, backend, "")
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    sys.exit(main())