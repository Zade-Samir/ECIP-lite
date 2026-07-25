"""
Tests for Architecture Copilot (Prompt 096).
"""
import pytest
from services.architecture_copilot.copilot_engine import ArchitectureCopilotEngine


def test_architecture_copilot_analysis():
    copilot = ArchitectureCopilotEngine()
    res = copilot.analyze_architecture([{"name": "OrderModule"}, {"name": "PaymentModule"}])

    assert len(res["recommendations"]) == 2
    assert res["modules_analyzed"] == 2
