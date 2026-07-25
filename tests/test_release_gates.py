"""
Tests for Release Gate Evaluator (Prompt 090).
"""
import pytest
from services.release_gates.release_gate_evaluator import ReleaseGate, ReleaseGateEvaluator


def test_release_gate_evaluator_all_pass():
    evaluator = ReleaseGateEvaluator()
    gates = [
        ReleaseGate("security_scan", "Security", is_blocking=True, passed=True, score=100.0),
        ReleaseGate("quality_metrics", "Quality", is_blocking=True, passed=True, score=100.0),
    ]

    res = evaluator.evaluate_gates(gates)
    assert res["all_blocking_passed"] is True
    assert len(res["passed_gates"]) == 2


def test_release_gate_evaluator_blocking_failure():
    evaluator = ReleaseGateEvaluator()
    gates = [
        ReleaseGate("security_scan", "Security", is_blocking=True, passed=False, score=0.0),
    ]

    res = evaluator.evaluate_gates(gates)
    assert res["all_blocking_passed"] is False
    assert "security_scan" in res["failed_blocking"]
