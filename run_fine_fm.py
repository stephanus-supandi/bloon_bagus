#!/usr/bin/env python3
"""BAGUS: FINE-FM demonstration.

Usage:
    python examples/run_fine_fm.py            # interactive menu
    python examples/run_fine_fm.py --all      # non-interactive (CI)
    python examples/run_fine_fm.py --all --backend reference
    python examples/run_fine_fm.py --bucket   # the important one
"""

from __future__ import annotations

import argparse
import sys

from bloon_bagus import (
    G_STANDARD, P_ATM, RHO_WATER,
    VerificationResult, buoyancy, bucket_bottom_pressure,
    evaluate_gate, hydrostatic_pressure, hydrostatic_surface_force,
    make_backend, pascal_force, pressure_difference,
)
from verify import RTOL_ALGEBRAIC, RTOL_QUADRATURE

BANNER = """
====================================================
 BAGUS: FINE-FM
 Basically A Generally Useless Solver
 Fluid Idiot's Numerical Engine for Fluid Mechanics
====================================================

BLOON STACK DEMONSTRATION
Fundamental Fluid Mechanics / Fluid Statics
""".rstrip()

MENU = """
[1] Hydrostatic Pressure
[2] Pressure Difference
[3] Pascal Hydraulic System
[4] Buoyancy
[5] Hydrostatic Force
[6] Run All
[7] Water in a Bucket
[0] Exit
"""

STACK_FLOW = """\
flow: FINE-FM (physical problem + formulation)
        -> BLOON backend [{backend}] (numerical representation/execution)
        -> BLOON_MACHINE gate [{gate}] (policy + decision)
        -> numerical result
        -> verification vs analytical reference"""

def _print_flow(backend_name: str, gate) -> None:
    print(STACK_FLOW.format(backend=backend_name, gate=gate.decision))
    if gate.decision not in ("ACCEPT",):
        print(f"  gate detail: {gate.detail}")
    print()

def _facts(task: str, **inputs) -> dict:
    return {"task": task, "domain": "fluid-statics", "inputs": inputs}

def demo1(backend) -> VerificationResult:
    print("=" * 52)
    print("[1] Hydrostatic Pressure    P = P0 + rho*g*h")
    print("=" * 52)
    gate = evaluate_gate(_facts("hydrostatic_pressure",
                                rho=RHO_WATER, h=10.0, g=G_STANDARD, p0=P_ATM))
    if gate.blocked:
        print(f"BLOCKED by BLOON_MACHINE: {gate.detail}")
        return VerificationResult("Hydrostatic pressure", 0.0, 0.0, RTOL_ALGEBRAIC)
    _print_flow(backend.name, gate)

    r = hydrostatic_pressure(backend)
    print("Hydrostatic Pressure")
    print("--------------------")
    print(f"Fluid:              water")
    print(f"Density:            {RHO_WATER:.1f} kg/m^3")
    print(f"Depth:              10.0 m")
    print(f"Gravity:            {G_STANDARD} m/s^2")
    print(f"Reference Pressure: {P_ATM:.1f} Pa")
    print()
    print(f"Hydrostatic pressure contribution: {r.contribution:.4f} Pa")
    print(f"Absolute pressure:                 {r.absolute:.4f} Pa")
    print(f"Gauge pressure:                    {r.gauge:.4f} Pa")
    print()
    analytical = P_ATM + RHO_WATER * G_STANDARD * 10.0   # 199391.5
    v = VerificationResult("Hydrostatic pressure", analytical,
                           r.absolute, RTOL_ALGEBRAIC)
    print(v.block())
    return v

def demo2(backend) -> VerificationResult:
    print("=" * 52)
    print("[2] Pressure Difference    dP = rho*g*dh")
    print("=" * 52)
    gate = evaluate_gate(_facts("pressure_difference", h1=2.0, h2=7.0))
    _print_flow(backend.name, gate)

    h1, h2 = 2.0, 7.0
    r = pressure_difference(backend, h1, h2)
    print(f"depth_1 = {h1} m, depth_2 = {h2} m, dh = {r.dh} m")
    print("dP depends ONLY on the depth difference, not on P0:")
    print(f"  P(h1) = P0 + rho*g*h1,  P(h2) = P0 + rho*g*h2")
    print(f"  P(h2) - P(h1) = rho*g*(h2-h1)   [P0 cancels]")
    print(f"dP = {r.dp:.4f} Pa")
    print()
    analytical = RHO_WATER * G_STANDARD * (h2 - h1)      # 49033.25
    v = VerificationResult("Pressure difference", analytical,
                           r.dp, RTOL_ALGEBRAIC)
    print(v.block())
    return v

def demo3(backend) -> VerificationResult:
    print("=" * 52)
    print("[3] Pascal Hydraulic System    F1/A1 = F2/A2")
    print("=" * 52)
    f1, a1, a2 = 100.0, 0.01, 0.10
    gate = evaluate_gate(_facts("pascal_force", F1=f1, A1=a1, A2=a2))
    _print_flow(backend.name, gate)

    r = pascal_force(backend, f1, a1, a2)
    print("Inputs:")
    print(f"  A1 = {a1} m^2")
    print(f"  A2 = {a2} m^2")
    print(f"  F1 = {f1} N")
    print(f"Equation: F2 = F1 * A2/A1 = {f1} * {r.ratio:.1f}")
    print(f"Result:   F2 = {r.f2:.4f} N   (mechanical advantage x{r.ratio:.0f})")
    print()
    analytical = f1 * a2 / a1                            # 1000.0
    v = VerificationResult("Pascal hydraulic force", analytical,
                           r.f2, RTOL_ALGEBRAIC)
    print(v.block())
    return v

def demo4(backend) -> VerificationResult:
    print("=" * 52)
    print("[4] Buoyancy    F_B = rho_f * g * V_displaced")
    print("=" * 52)
    v_disp = 0.05
    gate = evaluate_gate(_facts("buoyancy", rho_f=RHO_WATER, V=v_disp))
    _print_flow(backend.name, gate)

    r = buoyancy(backend, v_displaced=v_disp, object_weight=400.0)
    print("Buoyancy")
    print("--------")
    print(f"Fluid density:    {RHO_WATER:.1f} kg/m^3")
    print(f"Displaced volume: {v_disp} m^3")
    print(f"Gravity:          {G_STANDARD} m/s^2")
    print()
    print(f"Buoyant force:    {r.buoyant_force:.4f} N")
    print(f"Object weight:    400.0 N  ->  verdict: {r.verdict}")
    print()
    analytical = RHO_WATER * G_STANDARD * v_disp          # 490.3325
    v = VerificationResult("Buoyancy", analytical,
                           r.buoyant_force, RTOL_ALGEBRAIC)
    print(v.block())
    return v

def demo5(backend) -> VerificationResult:
    print("=" * 52)
    print("[5] Hydrostatic Force on a Surface    F = int_A p dA")
    print("=" * 52)
    w, h, h_top = 2.0, 3.0, 1.0
    gate = evaluate_gate(_facts(
        "hydrostatic_surface_force", width=w, height=h, top_depth=h_top))
    _print_flow(backend.name, gate)

    r = hydrostatic_surface_force(backend, width=w, height=h,
                                  top_depth=h_top, n_cells=400)
    print("Hydrostatic Force")
    print("-----------------")
    print("Geometry:         vertical rectangular plate")
    print(f"Width:            {w} m")
    print(f"Height:           {h} m")
    print(f"Top depth:        {h_top} m")
    print(f"Fluid density:    {RHO_WATER:.1f} kg/m^3")
    print(f"Gravity:          {G_STANDARD} m/s^2")
    print(f"Reference pressure: {P_ATM:.1f} Pa")
    print(f"Quadrature:       composite midpoint, n = {r.n_cells}")
    print()
    print("p(y) = p0 + rho*g*y  is linear in y, so midpoint quadrature")
    print("is EXACT in real arithmetic; rtol=1e-12 covers float round-off.")
    print()
    print(f"Analytical force: {r.analytical:.6f} N")
    print(f"Numerical force:  {r.numerical:.6f} N")
    print(f"Absolute error:   {r.abs_error:.3e} N")
    print(f"Relative error:   {r.rel_error:.3e}")
    print()
    v = VerificationResult("Hydrostatic surface force", r.analytical,
                           r.numerical, RTOL_QUADRATURE)
    print(v.block())
    return v

def demo_bucket(backend) -> VerificationResult:
    print("=" * 52)
    print("[7] Water in a Bucket    (the entire point)")
    print("=" * 52)
    gate = evaluate_gate(_facts("bucket", depth=0.30))
    _print_flow(backend.name, gate)

    print("A bucket contains water. Water depth: 0.30 m.")
    print()
    print("Question:")
    print("  How much pressure exists at the bottom?")
    print()
    print("Answer:")
    print("  P = P0 + rho*g*h")
    r = bucket_bottom_pressure(backend, depth=0.30)
    print(f"  P = {P_ATM:.1f} + 1000*{G_STANDARD}*0.30")
    print(f"  P = {r.absolute:.4f} Pa  (gauge: {r.gauge:.4f} Pa)")
    print()
    print('  "If the BLOON stack cannot cleanly solve a bucket of water,')
    print('   it has no business pretending to solve anything more')
    print('   complicated."')
    print()
    analytical = P_ATM + RHO_WATER * G_STANDARD * 0.30    # 104266.995
    v = VerificationResult("Water in a bucket", analytical,
                           r.absolute, RTOL_ALGEBRAIC)
    print(v.block())
    return v

DEMOS = {
    "1": demo1, "2": demo2, "3": demo3, "4": demo4,
    "5": demo5, "7": demo_bucket,
}

def run_all(backend):
    results = [demo1(backend), demo2(backend), demo3(backend),
               demo4(backend), demo5(backend), demo_bucket(backend)]
    print()
    print("=" * 52)
    print("VALIDATION SUMMARY")
    print("=" * 52)
    for v in results:
        print(v.line())
    print()
    print(f"backend: {backend.name}")
    print("BAGUS may be generally useless. The numbers, however,")
    print("are expected to be correct.")
    return all(v.passed for v in results)

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="BAGUS: FINE-FM demo")
    ap.add_argument("--all", action="store_true",
                    help="run every demo non-interactively (CI mode)")
    ap.add_argument("--bucket", action="store_true",
                    help="run only the water-in-a-bucket demo")
    ap.add_argument("--backend", choices=("bloon", "reference"),
                    default="bloon",
                    help="prefer BLOON backend; falls back to the "
                         "declared reference backend if unavailable")
    args = ap.parse_args(argv)

    print(BANNER)
    backend = make_backend(args.backend)
    print(f"\nactive numerical backend: {backend.name}")
    if backend.name != "bloon":
        print("NOTE: BLOON backend not wired in this environment;")
        print("      results below are produced by the declared")
        print("      reference backend (see backend.py docstring).")

    if args.all:
        return 0 if run_all(backend) else 1
    if args.bucket:
        return 0 if demo_bucket(backend).passed else 1

    while True:
        print(MENU)
        try:
            choice = input("select> ").strip()
        except (EOFError, KeyboardInterrupt):
            return 0
        if choice == "0":
            return 0
        if choice == "6":
            ok = run_all(backend)
            if not ok:
                return 1
            continue
        fn = DEMOS.get(choice)
        if fn:
            fn(backend)
        else:
            print("invalid choice")

if __name__ == "__main__":
    sys.exit(main())