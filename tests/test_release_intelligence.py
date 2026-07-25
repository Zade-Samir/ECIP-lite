"""
Tests for Readiness Engine (Prompt 090).
"""
import pytest
from services.release_gates.release_gate_evaluator import ReleaseGate
from services.release_intelligence.readiness_engine import ReadinessEngine


def test_readiness_engine_go_decision():
    engine = ReadinessEngine()
    gates = [
        ReleaseGate("security", "Security", is_blocking=True, passed=True, score=100.0),
        ReleaseGate("quality", "Quality", is_blocking=True, passed=True, score=100.0),
        ReleaseGate("backup", "Ops", is_blocking=False, passed=True, score=100.0),
    ]

    report = engine.evaluate_release(gates)
    assert report["decision"] == "GO"
    assert report["readiness_score"] == 100.0


def test_readiness_engine_no_go_decision():
    engine = ReadinessEngine()
    gates = [
        ReleaseGate("security", "Security", is_blocking=True, passed=False, score=0.0),
    ]

    report = engine.evaluate_release(gates)
    assert report["decision"] == "NO-GO"
    assert report["readiness_score"] == 0.0
