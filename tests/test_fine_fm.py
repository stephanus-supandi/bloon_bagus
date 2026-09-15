"""Automated tests for BAGUS: FINE-FM.
Convention: matches tests/ baseline (pytest, deterministic, analytical
references). These tests assert ACTUAL NUMBERS against closed-form
solutions — not merely that functions execute.
"""
import math
import sys
import pytest
from pathlib import Path

# Add the grandparent directory (E:\) to sys.path so 'bloon_bagus' is found
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from bloon_bagus import problems
from bloon_bagus.backends import PureBackend, get_backend
from bloon_bagus.machine_gate import evaluate_request
from bloon_bagus.quantities import G_STANDARD, P_ATM, RHO_WATER

RHO_G = RHO_WATER * G_STANDARD          # 9806.65 Pa/m

@pytest.fixture
def backend():
    return PureBackend()

# --- Demo 1: hydrostatic pressure ------------------------------------------

def test_hydrostatic_pressure_exact_values(backend):
    rec = problems.hydrostatic_pressure(backend)
    assert rec.passed
    assert rec.computed["contribution"].value == pytest.approx(RHO_G * 10.0, rel=1e-12)
    assert rec.computed["absolute"].value == pytest.approx(P_ATM + RHO_G * 10.0, rel=1e-12)
    assert rec.computed["gauge"].value == pytest.approx(RHO_G * 10.0, rel=1e-12)

def test_hydrostatic_pressure_zero_depth_is_reference(backend):
    rec = problems.hydrostatic_pressure(backend, h=0.0)
    assert rec.computed["absolute"].value == pytest.approx(P_ATM, rel=1e-12)
    assert rec.computed["gauge"].value == pytest.approx(0.0, abs=1e-9)

def test_hydrostatic_pressure_negative_depth_raises(backend):
    with pytest.raises(ValueError):
        problems.hydrostatic_pressure(backend, h=-1.0)

# --- Demo 2: pressure difference -------------------------------------------

def test_pressure_difference_exact_value(backend):
    rec = problems.pressure_difference(backend, h1=2.0, h2=7.0)
    assert rec.passed
    assert rec.computed["dP"].value == pytest.approx(RHO_G * 5.0, rel=1e-12)

def test_pressure_difference_independent_of_reference(backend):
    rec_atm = problems.pressure_difference(backend, p0=P_ATM)
    rec_vac = problems.pressure_difference(backend, p0=0.0)
    assert rec_atm.computed["dP"].value == pytest.approx(
        rec_vac.computed["dP"].value, rel=1e-12)
    assert rec_vac.computed["dP"].value == pytest.approx(RHO_G * 5.0, rel=1e-12)

# --- Demo 3: Pascal ---------------------------------------------------------

def test_pascal_output_force(backend):
    rec = problems.pascal_hydraulic(backend, a1=0.01, a2=0.10, f1=100.0)
    assert rec.passed
    assert rec.computed["output force"].value == pytest.approx(1000.0, rel=1e-12)
    assert rec.computed["system pressure"].value == pytest.approx(10000.0, rel=1e-12)

def test_pascal_pressure_equality_invariant(backend):
    rec = problems.pascal_hydraulic(backend, a1=0.03, a2=0.27, f1=250.0)
    p1 = rec.computed["system pressure"].value
    p2 = rec.computed["output force"].value / 0.27
    assert p1 == pytest.approx(p2, rel=1e-12)

def test_pascal_zero_area_raises(backend):
    with pytest.raises(ValueError):
        problems.pascal_hydraulic(backend, a1=0.0)

# --- Demo 4: buoyancy ---------------------------------------------------------

def test_buoyancy_exact_value(backend):
    rec = problems.buoyancy(backend, rho_f=1000.0, v_disp=0.05)
    assert rec.passed
    assert rec.computed["buoyant force"].value == pytest.approx(RHO_G * 0.05, rel=1e-12)
    assert rec.computed["buoyant force"].value == pytest.approx(490.3325, rel=1e-12)

def test_buoyancy_sink_float_verdict(backend):
    floats = problems.buoyancy(backend, v_disp=0.05, object_mass=40.0)   # W=392.27 < F_B
    sinks = problems.buoyancy(backend, v_disp=0.05, object_mass=60.0)     # W=588.40 > F_B
    assert "floats" in floats.notes[0]
    assert "sinks" in sinks.notes[0]

def test_buoyancy_negative_volume_raises(backend):
    with pytest.raises(ValueError):
        problems.buoyancy(backend, v_disp=-0.01)

# --- Demo 5: hydrostatic force -----------------------------------------------

def test_hydrostatic_force_matches_analytical(backend):
    # w=2, H=3, h_top=1 -> A=6, h_c=2.5
    rec = problems.hydrostatic_force(backend, width=2.0, height=3.0, h_top=1.0)
    analytical = (P_ATM + RHO_G * 2.5) * 6.0
    assert rec.passed
    assert analytical == pytest.approx(755049.75, rel=1e-12)   # pinned closed form
    assert rec.computed["numerical force"].value == pytest.approx(analytical, rel=1e-12)

def test_hydrostatic_force_grid_independence(backend):
    # Trapezoid is exact for linear p(y): result must not depend on n.
    coarse = problems.hydrostatic_force(backend, n=4)
    fine = problems.hydrostatic_force(backend, n=1024)
    assert coarse.computed["numerical force"].value == pytest.approx(
        fine.computed["numerical force"].value, rel=1e-12)

def test_hydrostatic_force_gauge_only(backend):
    # p0 = 0 -> pure hydrostatic contribution: F = rho*g*h_c*A
    rec = problems.hydrostatic_force(backend, p0=0.0, width=1.0, height=2.0, h_top=0.0)
    assert rec.computed["numerical force"].value == pytest.approx(RHO_G * 1.0 * 2.0, rel=1e-12)

def test_hydrostatic_force_zero_height(backend):
    rec = problems.hydrostatic_force(backend, height=0.0)
    assert rec.computed["numerical force"].value == pytest.approx(0.0, abs=1e-9)

def test_hydrostatic_force_bad_geometry_raises(backend):
    with pytest.raises(ValueError):
        problems.hydrostatic_force(backend, width=-1.0)
    with pytest.raises(ValueError):
        problems.hydrostatic_force(backend, n=0)

# --- bucket + stack plumbing ---------------------------------------------------

def test_bucket_is_just_hydrostatics(backend):
    rec = problems.bucket(backend, h=0.30)
    assert rec.passed
    assert rec.computed["gauge"].value == pytest.approx(RHO_G * 0.30, rel=1e-12)

def test_backend_selection():
    assert isinstance(get_backend("pure"), PureBackend)
    with pytest.raises(ValueError):
        get_backend("imaginary")

def test_machine_gate_reports_unavailable_or_real_decision():
    # Without BLOON_MACHINE installed the gate must report honestly
    # (UNAVAILABLE in dev mode, REJECT when strict) — never fabricate ACCEPT.
    dev = evaluate_request("test.task", {"x": 1}, strict=False)
    strict = evaluate_request("test.task", {"x": 1}, strict=True)
    if dev.status == "UNAVAILABLE":
        assert strict.status == "REJECT"
        assert not strict.allows_computation
    else:
        assert dev.status in ("ACCEPT", "WARN", "REJECT")