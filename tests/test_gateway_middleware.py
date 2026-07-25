"""
Tests for API Gateway middleware components (Prompt 070).
"""
import time
import pytest
from services.api_gateway.middleware.rate_limiter import RateLimiter, TokenBucket
from services.api_gateway.middleware.circuit_breaker import (
    CircuitBreaker, CircuitBreakerRegistry, CircuitState
)
from services.api_gateway.middleware.auth_middleware import AuthMiddleware
from services.api_gateway.middleware.request_logger import RequestLogger


class TestTokenBucket:
    def test_full_bucket_allows_request(self):
        bucket = TokenBucket(capacity=10, refill_rate=1.0)
        assert bucket.consume() is True

    def test_empty_bucket_denies_request(self):
        bucket = TokenBucket(capacity=1, refill_rate=0.01)
        bucket.consume()  # Drain
        assert bucket.consume() is False

    def test_refill_over_time(self):
        bucket = TokenBucket(capacity=10, refill_rate=100.0)
        bucket.consume(10)  # Drain completely
        time.sleep(0.1)     # 100 tokens/s * 0.1s = 10 tokens
        assert bucket.consume() is True


class TestRateLimiter:
    def test_new_client_allowed(self):
        rl = RateLimiter(capacity=10, refill_rate=1.0)
        assert rl.is_allowed("client1") is True

    def test_exhausted_client_denied(self):
        rl = RateLimiter(capacity=2, refill_rate=0.01)
        rl.is_allowed("client1")
        rl.is_allowed("client1")
        assert rl.is_allowed("client1") is False

    def test_different_clients_independent(self):
        rl = RateLimiter(capacity=1, refill_rate=0.01)
        rl.is_allowed("c1")
        assert rl.is_allowed("c2") is True  # c2 has full bucket

    def test_reset_restores_client(self):
        rl = RateLimiter(capacity=1, refill_rate=0.01)
        rl.is_allowed("c1")
        rl.reset("c1")
        assert rl.is_allowed("c1") is True


class TestCircuitBreaker:
    def test_initial_state_closed(self):
        cb = CircuitBreaker()
        assert cb.state == CircuitState.CLOSED

    def test_allow_request_when_closed(self):
        cb = CircuitBreaker()
        assert cb.allow_request() is True

    def test_opens_after_threshold_failures(self):
        cb = CircuitBreaker(failure_threshold=3)
        for _ in range(3):
            cb.record_failure()
        assert cb.state == CircuitState.OPEN

    def test_rejects_when_open(self):
        cb = CircuitBreaker(failure_threshold=1)
        cb.record_failure()
        assert cb.allow_request() is False

    def test_half_open_after_cooldown(self):
        cb = CircuitBreaker(failure_threshold=1, cooldown_seconds=0.1)
        cb.record_failure()
        time.sleep(0.15)
        assert cb.allow_request() is True  # HALF_OPEN allows probe
        assert cb.state == CircuitState.HALF_OPEN

    def test_closes_after_success_in_half_open(self):
        cb = CircuitBreaker(failure_threshold=1, cooldown_seconds=0.1)
        cb.record_failure()
        time.sleep(0.15)
        cb.allow_request()  # Transition to HALF_OPEN
        cb.record_success()
        assert cb.state == CircuitState.CLOSED

    def test_reset_closes_breaker(self):
        cb = CircuitBreaker(failure_threshold=1)
        cb.record_failure()
        cb.reset()
        assert cb.state == CircuitState.CLOSED
        assert cb.allow_request() is True


class TestCircuitBreakerRegistry:
    def test_get_creates_breaker(self):
        reg = CircuitBreakerRegistry()
        cb = reg.get("service_a")
        assert cb is not None
        assert cb.name == "service_a"

    def test_get_same_instance(self):
        reg = CircuitBreakerRegistry()
        cb1 = reg.get("svc")
        cb2 = reg.get("svc")
        assert cb1 is cb2

    def test_status_includes_all(self):
        reg = CircuitBreakerRegistry()
        reg.get("svc1")
        reg.get("svc2")
        status = reg.status()
        names = [s["name"] for s in status]
        assert "svc1" in names
        assert "svc2" in names


class TestAuthMiddleware:
    def test_bypass_path_skipped(self):
        mw = AuthMiddleware(bypass_paths=["/health"])
        assert mw.should_bypass("/health") is True

    def test_non_bypass_path_not_skipped(self):
        mw = AuthMiddleware(bypass_paths=["/health"])
        assert mw.should_bypass("/api/v1/query") is False

    def test_valid_token_returns_payload(self):
        from services.api_gateway.middleware.auth_middleware import create_access_token
        token = create_access_token({"sub": "testuser"})
        mw = AuthMiddleware()
        result = mw.validate(f"Bearer {token}")
        assert result is not None
        assert result["sub"] == "testuser"

    def test_invalid_token_returns_none(self):
        mw = AuthMiddleware()
        assert mw.validate("Bearer garbage.token.here") is None

    def test_missing_header_returns_none(self):
        mw = AuthMiddleware()
        assert mw.validate(None) is None

    def test_malformed_header_returns_none(self):
        mw = AuthMiddleware()
        assert mw.validate("NotBearer xyz") is None


class TestRequestLogger:
    def test_start_request_returns_context(self):
        rl = RequestLogger()
        ctx = rl.start_request("GET", "/api/test", "127.0.0.1")
        assert "correlation_id" in ctx
        assert ctx["method"] == "GET"
        assert ctx["path"] == "/api/test"

    def test_end_request_does_not_raise(self):
        rl = RequestLogger()
        ctx = rl.start_request("POST", "/api/query", "10.0.0.1")
        rl.end_request(ctx, 200)  # Should not raise
