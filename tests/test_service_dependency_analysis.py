"""
Tests for Service Dependency Analyzer (Prompt 083).
"""
import pytest
from services.cross_repo_reasoning.cross_repo_engine import CrossRepoEdge, CrossRepoEngine, RepoNode
from services.cross_repo_reasoning.service_dependency_analyzer import ServiceDependencyAnalyzer


def test_service_dependency_analysis():
    engine = CrossRepoEngine()
    engine.register_repo("order-svc", [RepoNode("order-svc", "OrderAPI", "API")])
    engine.register_repo("payment-svc", [RepoNode("payment-svc", "PaymentAPI", "API")])

    engine.add_cross_repo_edge(CrossRepoEdge("order-svc", "OrderAPI", "payment-svc", "PaymentAPI", "CALLS_API"))

    analyzer = ServiceDependencyAnalyzer(engine)
    res = analyzer.analyze_service("order-svc")

    assert res["service_repo"] == "order-svc"
    assert len(res["outgoing_dependencies"]) == 1
    assert res["outgoing_dependencies"][0]["target_repo"] == "payment-svc"
