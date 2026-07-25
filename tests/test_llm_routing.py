"""
Tests for LLM routing policies and ProviderHealth (Prompt 069).
"""
import pytest
from services.model_gateway.gateway import (
    ModelGateway, RoutingPolicy, ProviderStatus, ProviderHealth
)
from tests.test_model_gateway import MockProvider


class TestProviderHealth:
    def test_initial_status_healthy(self):
        h = ProviderHealth()
        assert h.status == ProviderStatus.HEALTHY

    def test_record_success_updates_latency(self):
        h = ProviderHealth()
        h.record_success(100.0)
        assert h.avg_latency() == 100.0

    def test_record_success_resets_failure_count(self):
        h = ProviderHealth(failure_threshold=3)
        h.record_failure()
        h.record_success(50.0)
        assert h.status == ProviderStatus.HEALTHY

    def test_failure_marks_degraded(self):
        h = ProviderHealth(failure_threshold=3)
        h.record_failure()
        assert h.status == ProviderStatus.DEGRADED

    def test_failures_above_threshold_marks_unavailable(self):
        h = ProviderHealth(failure_threshold=2)
        h.record_failure()
        h.record_failure()
        assert h.status == ProviderStatus.UNAVAILABLE
        assert not h.is_available()

    def test_avg_latency_no_records(self):
        h = ProviderHealth()
        assert h.avg_latency() == 9999.0

    def test_avg_latency_rolling_window(self):
        h = ProviderHealth(window=3)
        for latency in [100, 200, 300, 400]:
            h.record_success(float(latency))
        # Window = 3, so only last 3: [200, 300, 400]
        assert h.avg_latency() == pytest.approx(300.0, rel=0.01)


class TestRoutingPolicies:
    def test_preferred_policy_picks_first(self):
        gw = ModelGateway(policy=RoutingPolicy.PREFERRED)
        p1 = MockProvider("first", response="r1")
        p2 = MockProvider("second", response="r2")
        gw.register(p1)
        gw.register(p2)
        result = gw.chat([], model="m")
        assert result == "r1"

    def test_round_robin_all_providers_used(self):
        gw = ModelGateway(policy=RoutingPolicy.ROUND_ROBIN)
        providers = [MockProvider(f"p{i}", response=f"r{i}") for i in range(3)]
        for p in providers:
            gw.register(p)
        responses = [gw.chat([], model="m") for _ in range(6)]
        assert len(set(responses)) == 3  # All 3 providers used

    def test_weighted_routing_respects_weights(self):
        """Higher weight provider should be called more often."""
        gw = ModelGateway(policy=RoutingPolicy.WEIGHTED)
        heavy = MockProvider("heavy", response="heavy", weight=10)
        light = MockProvider("light", response="light", weight=1)
        gw.register(heavy)
        gw.register(light)

        responses = [gw.chat([], model="m") for _ in range(50)]
        heavy_count = responses.count("heavy")
        # Heavy should be called significantly more than light
        assert heavy_count > 30

    def test_lowest_latency_picks_fastest(self):
        gw = ModelGateway(policy=RoutingPolicy.LOWEST_LATENCY)
        p_slow = MockProvider("slow", response="slow")
        p_fast = MockProvider("fast", response="fast")
        p_slow.health._latencies = [1000.0]
        p_fast.health._latencies = [10.0]
        gw.register(p_slow)
        gw.register(p_fast)

        result = gw.chat([], model="m")
        assert result == "fast"

    def test_fallback_chain_on_failures(self):
        gw = ModelGateway(policy=RoutingPolicy.PREFERRED)
        p1 = MockProvider("bad1", fail=True)
        p2 = MockProvider("bad2", fail=True)
        p3 = MockProvider("good", response="success")
        gw.register(p1)
        gw.register(p2)
        gw.register(p3)

        result = gw.chat([], model="m")
        assert result == "success"


class TestHealthChecks:
    def test_run_health_checks_marks_unavailable_recovered(self):
        gw = ModelGateway()
        p = MockProvider("p1", fail=False)
        p.health.status = ProviderStatus.UNAVAILABLE
        gw.register(p)
        gw.run_health_checks()
        assert p.health.status == ProviderStatus.HEALTHY

    def test_run_health_checks_marks_unavailable_when_down(self):
        gw = ModelGateway()
        p = MockProvider("p1", fail=True)
        gw.register(p)
        gw.run_health_checks()
        # After health check failure, failures counter should increase
        assert p.health._failures > 0 or p.health.status != ProviderStatus.HEALTHY
