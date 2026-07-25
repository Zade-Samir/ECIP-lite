"""
Tests for Impact Analyzer (Prompt 082).
"""
import pytest
from services.reasoning.graph_reasoning_engine import GraphEdge, GraphNode, GraphReasoningEngine
from services.reasoning.impact_analyzer import ImpactAnalyzer


def test_impact_analysis():
    gre = GraphReasoningEngine()
    gre.add_node(GraphNode("Repo", "Repository"))
    gre.add_node(GraphNode("Service", "Class"))
    gre.add_node(GraphNode("Controller", "Class"))

    gre.add_edge(GraphEdge("Repo", "Service", "USED_BY"))
    gre.add_edge(GraphEdge("Service", "Controller", "USED_BY"))

    analyzer = ImpactAnalyzer(gre)
    report = analyzer.analyze_impact("Repo")

    assert report["target"] == "Repo"
    assert report["affected_nodes_count"] == 2
    assert "Service" in report["affected_nodes"]
    assert "Controller" in report["affected_nodes"]
    assert report["risk_score"] > 0
