"""
Tests for Architecture Rules (Prompt 084).
"""
import pytest
from services.architecture_advisor.architecture_rules import check_layer_violations, check_oversized_classes


def test_oversized_class_rule():
    nodes = [
        {"id": "GodClass", "lines_count": 600, "methods_count": 25},
        {"id": "SmallClass", "lines_count": 50, "methods_count": 3},
    ]
    violations = check_oversized_classes(nodes, [])
    assert len(violations) == 1
    assert violations[0]["target"] == "GodClass"


def test_layer_violation_rule():
    edges = [
        {"source": "UserController", "target": "UserRepository"},
        {"source": "UserController", "target": "UserService"},
    ]
    violations = check_layer_violations([], edges)
    assert len(violations) == 1
    assert "UserController -> UserRepository" in violations[0]["target"]
