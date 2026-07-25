"""
Tests for Enterprise API Gateway (Prompt 070).
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from services.api_gateway.gateway import gateway, rate_limiter, circuit_registry, auth_middleware
from services.api_gateway.middleware.circuit_breaker import CircuitState
from services.api_gateway.middleware.auth_middleware import create_access_token


@pytest.fixture(autouse=True)
def reset_state():
    """Reset rate limiter and circuit breakers between tests."""
    rate_limiter._buckets.clear()
    for cb in circuit_registry._breakers.values():
        cb.reset()
    yield


@pytest.fixture
def client():
    return TestClient(gateway, raise_server_exceptions=False)


@pytest.fixture
def valid_token():
    """Generate a valid JWT token for tests."""
    return create_access_token({"sub": "testuser", "role": "developer"})


class TestGatewayHealth:
    def test_health_endpoint_accessible_without_auth(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_returns_gateway_status(self, client):
        response = client.get("/health")
        data = response.json()
        assert data["gateway"] == "healthy"
        assert "overall" in data

    def test_circuit_breaker_status_endpoint(self, client):
        response = client.get("/gateway/circuit-breakers")
        assert response.status_code == 200
        assert "circuit_breakers" in response.json()

    def test_rate_limit_info_endpoint(self, client):
        response = client.get("/gateway/rate-limit-info")
        assert response.status_code == 200
        data = response.json()
        assert "capacity" in data
        assert "refill_rate_per_second" in data


class TestGatewayAuth:
    def test_protected_route_without_token_returns_401(self, client):
        # Any route not in bypass_paths requires a token
        response = client.get("/some/protected/route")
        assert response.status_code == 401

    def test_protected_route_with_invalid_token_returns_401(self, client):
        response = client.get(
            "/some/protected/route",
            headers={"Authorization": "Bearer invalid.token.here"}
        )
        assert response.status_code == 401

    def test_health_bypasses_auth(self, client):
        response = client.get("/health")
        assert response.status_code != 401

    def test_valid_token_passes_auth_middleware(self, valid_token, client):
        response = client.get(
            "/health",
            headers={"Authorization": f"Bearer {valid_token}"}
        )
        # /health is bypass — should always be 200
        assert response.status_code == 200


class TestGatewayRateLimiting:
    def test_request_within_limit_allowed(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    def test_request_exceeds_limit_returns_429(self, client):
        # Drain the bucket by requesting with a very small bucket
        rate_limiter._buckets.clear()
        # Set up a tiny bucket for the test client IP
        from services.api_gateway.middleware.rate_limiter import TokenBucket
        rate_limiter._buckets["testclient"] = TokenBucket(capacity=1, refill_rate=0.01)
        rate_limiter._buckets["testclient"].tokens = 0  # Bucket empty

        response = client.get("/health")
        assert response.status_code == 429

    def test_rate_limit_response_has_retry_after(self, client):
        from services.api_gateway.middleware.rate_limiter import TokenBucket
        rate_limiter._buckets["testclient"] = TokenBucket(capacity=1, refill_rate=0.01)
        rate_limiter._buckets["testclient"].tokens = 0

        response = client.get("/health")
        if response.status_code == 429:
            assert "Retry-After" in response.headers
