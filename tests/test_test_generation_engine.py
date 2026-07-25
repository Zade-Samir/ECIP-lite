"""
Tests for Test Generation Engine (Prompt 094).
"""
import pytest
from services.test_generation.test_generation_engine import TestGenerationEngine


def test_test_generation_engine_content():
    engine = TestGenerationEngine()
    suite = engine.generate_tests("OrderController", ["createOrder"], framework="junit5")

    assert "public class OrderControllerTest" in suite.code_content
    assert suite.test_type == "Unit"
