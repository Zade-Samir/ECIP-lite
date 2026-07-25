"""
Tests for AI Test Generation (Prompt 094).
"""
import pytest
from services.test_generation.test_generation_engine import TestGenerationEngine


def test_ai_test_generation_junit5():
    engine = TestGenerationEngine()
    suite = engine.generate_tests("UserService", ["getUserById", "saveUser"])

    assert suite.target_class == "UserService"
    assert "void test_getUserById()" in suite.code_content
    assert "void test_saveUser()" in suite.code_content
    assert suite.estimated_coverage_increase == 25.0
