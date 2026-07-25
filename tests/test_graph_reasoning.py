"""
Tests for Graph Reasoning Engine (Prompt 082).
"""
import pytest
from services.reasoning.graph_reasoning_engine import GraphEdge, GraphNode, GraphReasoningEngine


def test_multi_hop_traversal():
    gre = GraphReasoningEngine()
    gre.add_node(GraphNode("c1", "Class"))
    gre.add_node(GraphNode("c2", "Class"))
    gre.add_node(GraphNode("c3", "Class"))

    gre.add_edge(GraphEdge("c1", "c2", "DEPENDS_ON"))
    gre.add_edge(GraphEdge("c2", "c3", "DEPENDS_ON"))

    paths = gre.multi_hop_traversal("c1", max_depth=3)
    assert len(paths) == 1
    assert paths[0] == ["c1", "c2", "c3"]


def test_cycle_detection():
    gre = GraphReasoningEngine()
    gre.add_node(GraphNode("n1", "Class"))
    gre.add_node(GraphNode("n2", "Class"))

    gre.add_edge(GraphEdge("n1", "n2", "CALLS"))
    gre.add_edge(GraphEdge("n2", "n1", "CALLS"))

    cycles = gre.detect_cycles()
    assert len(cycles) >= 1
    assert cycles[0][0] == cycles[0][-1]
