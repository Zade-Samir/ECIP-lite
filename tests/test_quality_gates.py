"""
Tests for Quality Gate Evaluator (Prompt 088).
"""
import pytest
from services.quality_gates.gate_evaluator import GateEvaluator, QualityGate


def test_quality_gate_passed():
    evaluator = GateEvaluator()
    gates = [
        QualityGate("coverage", is_blocking=True, threshold_value=80.0, actual_value=85.0, comparator=">="),
        QualityGate("complexity", is_blocking=True, threshold_value=15.0, actual_value=8.0, comparator="<="),
    ]

    res = evaluator.evaluate_pipeline(gates)
    assert res["status"] == "PASSED"
    assert len(res["passed_gates"]) == 2


def test_quality_gate_failed_blocking():
    evaluator = GateEvaluator()
    gates = [
        QualityGate("critical_vulnerabilities", is_blocking=True, threshold_value=0.0, actual_value=2.0, comparator="<="),
    ]

    res = evaluator.evaluate_pipeline(gates)
    assert res["status"] == "FAILED"
    assert "critical_vulnerabilities" in res["failed_blocking"]
