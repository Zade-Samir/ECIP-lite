"""
Tests for Recommendation Engine (Prompt 084).
"""
import pytest
from services.architecture_advisor.recommendation_engine import RecommendationEngine


def test_recommendation_engine_analysis():
    engine = RecommendationEngine()
    nodes = [{"id": "MegaService", "lines_count": 800, "methods_count": 30}]
    edges = [{"source": "UserController", "target": "UserRepository"}]

    recs = engine.analyze(nodes, edges)
    assert len(recs) == 2

    report = engine.export_report(recs)
    assert report["total_recommendations"] == 2
    assert report["high_severity_count"] == 2
