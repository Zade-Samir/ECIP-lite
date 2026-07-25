"""
Tests for Refactoring Rules (Prompt 085).
"""
import pytest
from services.modernization.modernization_analyzer import ModernizationAnalyzer


def test_breaking_changes_identified():
    analyzer = ModernizationAnalyzer()
    findings = analyzer.analyze({"java_version": "8", "spring_boot_version": "2.2.0"})

    spring_finding = next(f for f in findings if f.category == "Framework")
    assert "javax.* packages renamed to jakarta.*" in spring_finding.breaking_changes
