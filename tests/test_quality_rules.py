"""
Tests for Quality Rule Engine (Prompt 087).
"""
import pytest
from services.code_quality.quality_analyzer import QualityMetrics
from services.quality_rules.quality_rule_engine import QualityRuleEngine


def test_quality_rule_evaluation():
    engine = QualityRuleEngine(min_maintainability=70.0, max_complexity=10.0)

    good = QualityMetrics(5.0, 85.0, 2.0, 0, 0)
    res_good = engine.evaluate(good)
    assert res_good["passed"] is True

    bad = QualityMetrics(12.0, 50.0, 10.0, 3, 1)
    res_bad = engine.evaluate(bad)
    assert res_bad["passed"] is False
    assert len(res_bad["violations"]) >= 2


def test_quality_regression_detection():
    engine = QualityRuleEngine()
    baseline = QualityMetrics(5.0, 85.0, 2.0, 0, 0)
    regressed = QualityMetrics(5.0, 75.0, 2.0, 0, 0)  # Dropped 10 points

    res = engine.evaluate(regressed, baseline=baseline)
    assert any("regressed" in v for v in res["violations"])
