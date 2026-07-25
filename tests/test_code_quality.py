"""
Tests for Quality Analyzer (Prompt 087).
"""
import pytest
from services.code_quality.quality_analyzer import QualityAnalyzer


def test_quality_analyzer_metrics():
    qa = QualityAnalyzer()
    files_meta = [
        {"lines": 100, "complexity": 5.0, "duplication_lines": 5, "dead_code_count": 1},
        {"lines": 200, "complexity": 10.0, "duplication_lines": 15, "dead_code_count": 0},
    ]

    metrics = qa.analyze(files_meta)
    assert metrics.cyclomatic_complexity == 7.5
    assert metrics.maintainability_index == 77.5
    assert metrics.dead_code_items == 1
