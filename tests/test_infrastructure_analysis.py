"""
Tests for Infrastructure Analysis (Prompt 097).
"""
import pytest
from services.devops_copilot.devops_engine import DevOpsCopilotEngine


def test_empty_manifests_warning():
    engine = DevOpsCopilotEngine()
    report = engine.analyze_infrastructure([])
    assert report["total_manifests_analyzed"] == 0
