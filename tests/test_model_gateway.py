"""
Tests for ModelGateway (Prompt 069).
"""
import pytest
from unittest.mock import MagicMock, patch
from services.model_gateway.gateway import (
    ModelGateway, LLMProvider, RoutingPolicy, ProviderStatus
)


class MockProvider(LLMProvider):
    """Test provider that returns configurable responses."""

    def __init__(self, name: str, response: str = "OK", fail: bool = False, weight: int = 1):
        super().__init__(name=name, weight=weight)
        self.response = response
        self.fail = fail
        self.call_count = 0

    def is_healthy(self) -> bool:
        return not self.fail

    def chat(self, messages, model, **kwargs) -> str:
        self.call_count += 1
        if self.fail:
            raise RuntimeError(f"{self.name} is unavailable")
        return self.response

    def stream_chat(self, messages, model, **kwargs):
        if self.fail:
            raise RuntimeError(f"{self.name} is unavailable")
        for token in self.response.split():
            yield token


@pytest.fixture
def gateway():
    return ModelGateway(policy=RoutingPolicy.PREFERRED)


class TestModelGatewayRegistration:
    def test_register_provider(self, gateway):
        p = MockProvider("ollama")
        gateway.register(p)
        assert "ollama" in gateway.list_providers()

    def test_unregister_provider(self, gateway):
        p = MockProvider("ollama")
        gateway.register(p)
        result = gateway.unregister("ollama")
        assert result is True
        assert "ollama" not in gateway.list_providers()

    def test_unregister_nonexistent_returns_false(self, gateway):
        assert gateway.unregister("ghost") is False


class TestModelGatewayChat:
    def test_chat_returns_response(self, gateway):
        p = MockProvider("ollama", response="Hello World")
        gateway.register(p)
        result = gateway.chat([{"role": "user", "content": "hi"}], model="test")
        assert result == "Hello World"

    def test_chat_all_providers_unavailable_raises(self, gateway):
        p = MockProvider("bad", fail=True)
        gateway.register(p)
        p.health.status = ProviderStatus.UNAVAILABLE
        with pytest.raises(RuntimeError, match="unavailable"):
            gateway.chat([{"role": "user", "content": "hi"}], model="test")

    def test_chat_prefers_specific_provider(self):
        gw = ModelGateway(policy=RoutingPolicy.PREFERRED)
        p1 = MockProvider("primary", response="from_primary")
        p2 = MockProvider("secondary", response="from_secondary")
        gw.register(p1)
        gw.register(p2)
        result = gw.chat([], model="m", preferred_provider="secondary")
        assert result == "from_secondary"


class TestModelGatewayFallback:
    def test_fallback_to_second_on_primary_failure(self):
        gw = ModelGateway(policy=RoutingPolicy.PREFERRED)
        bad = MockProvider("primary", fail=True)
        good = MockProvider("secondary", response="from_secondary")
        gw.register(bad)
        gw.register(good)
        result = gw.chat([], model="m")
        assert result == "from_secondary"
        assert bad.health.status != ProviderStatus.HEALTHY

    def test_provider_health_updated_on_failure(self, gateway):
        p = MockProvider("failing", fail=True)
        gateway.register(p)
        try:
            gateway.chat([], model="m")
        except RuntimeError:
            pass
        assert p.health.status != ProviderStatus.HEALTHY


class TestModelGatewayRoutingPolicies:
    def test_round_robin_rotates_providers(self):
        gw = ModelGateway(policy=RoutingPolicy.ROUND_ROBIN)
        p1 = MockProvider("p1", response="r1")
        p2 = MockProvider("p2", response="r2")
        gw.register(p1)
        gw.register(p2)

        responses = [gw.chat([], model="m") for _ in range(4)]
        assert "r1" in responses
        assert "r2" in responses

    def test_lowest_latency_selects_fastest(self):
        gw = ModelGateway(policy=RoutingPolicy.LOWEST_LATENCY)
        p_slow = MockProvider("slow")
        p_fast = MockProvider("fast")
        p_slow.health._latencies = [500.0]
        p_fast.health._latencies = [10.0]
        gw.register(p_slow)
        gw.register(p_fast)
        gw.chat([], model="m")
        assert p_fast.call_count >= 1


class TestModelGatewayHealthReport:
    def test_health_report_contains_all_providers(self, gateway):
        gateway.register(MockProvider("p1"))
        gateway.register(MockProvider("p2"))
        report = gateway.health_report()
        names = [r["name"] for r in report]
        assert "p1" in names
        assert "p2" in names

    def test_health_report_shows_status(self, gateway):
        p = MockProvider("p1")
        gateway.register(p)
        report = gateway.health_report()
        entry = next(r for r in report if r["name"] == "p1")
        assert entry["status"] == ProviderStatus.HEALTHY


class TestModelGatewayStreaming:
    def test_stream_chat_yields_tokens(self, gateway):
        p = MockProvider("ollama", response="hello world test")
        gateway.register(p)
        tokens = list(gateway.stream_chat([], model="m"))
        assert tokens == ["hello", "world", "test"]
