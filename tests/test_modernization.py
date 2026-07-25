"""
Tests for Modernization Analyzer (Prompt 085).
"""
import pytest
from services.modernization.modernization_analyzer import ModernizationAnalyzer
from services.modernization.refactoring_planner import RefactoringPlanner


def test_modernization_analyzer():
    analyzer = ModernizationAnalyzer()
    findings = analyzer.analyze({
        "java_version": "8",
        "spring_boot_version": "2.4.0",
        "frameworks": ["spring", "unknown_lib"]
    })

    assert len(findings) == 2
    cats = [f.category for f in findings]
    assert "JavaVersion" in cats
    assert "Framework" in cats


def test_refactoring_planner():
    analyzer = ModernizationAnalyzer()
    planner = RefactoringPlanner()

    findings = analyzer.analyze({"java_version": "11", "spring_boot_version": "2.7.0"})
    report = planner.generate_migration_plan(findings)

    assert report["total_findings"] == 2
    assert report["estimated_total_hours"] == 100.0
    assert len(report["phases"]) == 2
