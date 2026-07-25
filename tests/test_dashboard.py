"""
Tests for Dashboard Service (Prompt 074).
"""
import pytest
from services.dashboard.dashboard_service import DashboardService


@pytest.fixture
def dashboard_service():
    return DashboardService()


def test_get_overview(dashboard_service):
    overview = dashboard_service.get_overview()
    assert "total_projects" in overview
    assert "system_status" in overview


def test_get_workspace_explorer(dashboard_service):
    ws = dashboard_service.get_workspace_explorer()
    assert "workspaces" in ws
    assert len(ws["workspaces"]) >= 1


def test_get_dependency_graph(dashboard_service):
    graph = dashboard_service.get_dependency_graph("sampleProject")
    assert "nodes" in graph
    assert "edges" in graph
    assert len(graph["nodes"]) > 0


def test_get_call_graph(dashboard_service):
    graph = dashboard_service.get_call_graph("UserController")
    assert "nodes" in graph
    assert len(graph["nodes"]) > 0


def test_get_system_health(dashboard_service):
    health = dashboard_service.get_system_health()
    assert health["api_gateway"] == "healthy"
