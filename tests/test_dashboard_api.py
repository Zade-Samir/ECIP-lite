"""
Tests for Dashboard API endpoints (Prompt 074).
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from dashboard.backend import router


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_overview_endpoint(client):
    response = client.get("/dashboard/overview")
    assert response.status_code == 200
    assert "total_projects" in response.json()


def test_workspaces_endpoint(client):
    response = client.get("/dashboard/workspaces")
    assert response.status_code == 200
    assert "workspaces" in response.json()


def test_dependency_graph_endpoint(client):
    response = client.get("/dashboard/graph/dependency")
    assert response.status_code == 200
    assert "nodes" in response.json()


def test_call_graph_endpoint(client):
    response = client.get("/dashboard/graph/call")
    assert response.status_code == 200
    assert "nodes" in response.json()


def test_health_endpoint(client):
    response = client.get("/dashboard/health")
    assert response.status_code == 200
    assert response.json()["api_gateway"] == "healthy"
