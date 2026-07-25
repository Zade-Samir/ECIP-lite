"""
Tests for Cross-Repository Reasoning Engine (Prompt 083).
"""
import pytest
from services.cross_repo_reasoning.cross_repo_engine import CrossRepoEdge, CrossRepoEngine, RepoNode


def test_cross_repo_traversal():
    engine = CrossRepoEngine()

    engine.register_repo("user-service", [RepoNode("user-service", "UserController", "Class")])
    engine.register_repo("auth-service", [RepoNode("auth-service", "AuthTokenProvider", "Class")])
    engine.register_repo("common-lib", [RepoNode("common-lib", "JwtUtils", "Class")])

    engine.add_cross_repo_edge(CrossRepoEdge("user-service", "UserController", "auth-service", "AuthTokenProvider", "CALLS_API"))
    engine.add_cross_repo_edge(CrossRepoEdge("auth-service", "AuthTokenProvider", "common-lib", "JwtUtils", "IMPORTS_LIB"))

    report = engine.generate_report("user-service", "UserController")

    assert report["chain_length"] == 3
    assert "auth-service" in report["repos_spanned"]
    assert "common-lib" in report["repos_spanned"]
