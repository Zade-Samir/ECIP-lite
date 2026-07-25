"""
Model Gateway — Routes LLM requests to multiple providers with policies,
health checks, automatic failover, and metrics collection.
Local-only: works with Ollama as primary; OpenAI-compatible APIs as alternates.
"""
import time
import threading
from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional, Iterator, Any

from ecip_core.common.logger import get_logger

logger = get_logger(__name__)


# ------------------------------------------------------------------
# Routing policies
# ------------------------------------------------------------------

class RoutingPolicy(str, Enum):
    PREFERRED = "preferred"          # Use specific provider by name
    ROUND_ROBIN = "round_robin"      # Rotate through healthy providers
    LOWEST_LATENCY = "lowest_latency"  # Pick provider with lowest avg latency
    WEIGHTED = "weighted"            # Weight-based random selection
    HIGHEST_QUALITY = "highest_quality"  # Alias for preferred top-tier model


# ------------------------------------------------------------------
# Provider health status
# ------------------------------------------------------------------

class ProviderStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


class ProviderHealth:
    """Tracks rolling latency and failure rate for a provider."""

    def __init__(self, failure_threshold: int = 3, window: int = 10):
        self.failure_threshold = failure_threshold
        self.window = window
        self._latencies: list[float] = []
        self._failures: int = 0
        self._lock = threading.Lock()
        self.status = ProviderStatus.HEALTHY

    def record_success(self, latency_ms: float) -> None:
        with self._lock:
            self._latencies.append(latency_ms)
            if len(self._latencies) > self.window:
                self._latencies.pop(0)
            self._failures = max(0, self._failures - 1)
            self.status = ProviderStatus.HEALTHY

    def record_failure(self) -> None:
        with self._lock:
            self._failures += 1
            if self._failures >= self.failure_threshold:
                self.status = ProviderStatus.UNAVAILABLE
                logger.error("Provider unavailable")
            else:
                self.status = ProviderStatus.DEGRADED
                logger.warning("Provider degraded")

    def avg_latency(self) -> float:
        with self._lock:
            return sum(self._latencies) / len(self._latencies) if self._latencies else 9999.0

    def is_available(self) -> bool:
        return self.status != ProviderStatus.UNAVAILABLE


# ------------------------------------------------------------------
# LLM Provider abstract base
# ------------------------------------------------------------------

class LLMProvider(ABC):
    """Abstract base class for all LLM providers in the gateway."""

    def __init__(self, name: str, weight: int = 1):
        self.name = name
        self.weight = weight
        self.health = ProviderHealth()

    @abstractmethod
    def is_healthy(self) -> bool:
        """Quick liveness check (no heavy network call)."""
        ...

    @abstractmethod
    def chat(self, messages: list[dict], model: str, **kwargs) -> str:
        """Blocking chat completion. Returns response string."""
        ...

    @abstractmethod
    def stream_chat(self, messages: list[dict], model: str, **kwargs) -> Iterator[str]:
        """Streaming chat completion. Yields response tokens."""
        ...


# ------------------------------------------------------------------
# Model Gateway
# ------------------------------------------------------------------

class ModelGateway:
    """
    Central LLM request router.

    Registers multiple LLMProvider instances and selects one per request
    based on the configured routing policy. Handles automatic failover,
    health monitoring, and per-provider metrics.

    Usage:
        gateway = ModelGateway(policy=RoutingPolicy.LOWEST_LATENCY)
        gateway.register(OllamaGatewayProvider("ollama", base_url="..."))
        response = gateway.chat(messages, model="qwen2.5-coder:3b")
    """

    def __init__(self, policy: RoutingPolicy = RoutingPolicy.PREFERRED):
        self._providers: dict[str, LLMProvider] = {}
        self._provider_order: list[str] = []
        self._policy = policy
        self._rr_index = 0
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(self, provider: LLMProvider) -> None:
        with self._lock:
            self._providers[provider.name] = provider
            self._provider_order.append(provider.name)
        logger.info("Provider selected")

    def unregister(self, name: str) -> bool:
        with self._lock:
            if name in self._providers:
                del self._providers[name]
                self._provider_order.remove(name)
                return True
        return False

    # ------------------------------------------------------------------
    # Request routing
    # ------------------------------------------------------------------

    def chat(
        self,
        messages: list[dict],
        model: str,
        preferred_provider: Optional[str] = None,
        **kwargs,
    ) -> str:
        """
        Route a chat request to the best available provider.
        Tries providers in fallback order on failure.
        """
        candidates = self._get_candidates(preferred_provider)

        for provider in candidates:
            if not provider.health.is_available():
                continue
            try:
                start = time.monotonic()
                response = provider.chat(messages, model, **kwargs)
                latency = (time.monotonic() - start) * 1000
                provider.health.record_success(latency)
                logger.info("Provider selected")
                logger.info("Request completed")
                return response
            except Exception as e:
                logger.warning("Fallback executed")
                provider.health.record_failure()

        logger.error("Routing failure")
        raise RuntimeError("All LLM providers are unavailable")

    def stream_chat(
        self,
        messages: list[dict],
        model: str,
        preferred_provider: Optional[str] = None,
        **kwargs,
    ) -> Iterator[str]:
        """Stream chat response from best available provider."""
        candidates = self._get_candidates(preferred_provider)

        for provider in candidates:
            if not provider.health.is_available():
                continue
            try:
                start = time.monotonic()
                tokens = list(provider.stream_chat(messages, model, **kwargs))
                latency = (time.monotonic() - start) * 1000
                provider.health.record_success(latency)
                logger.info("Provider selected")
                yield from tokens
                return
            except Exception as e:
                logger.warning("Fallback executed")
                provider.health.record_failure()

        logger.error("Routing failure")
        raise RuntimeError("All LLM providers are unavailable")

    # ------------------------------------------------------------------
    # Health & metrics
    # ------------------------------------------------------------------

    def health_report(self) -> list[dict]:
        with self._lock:
            return [
                {
                    "name": p.name,
                    "status": p.health.status.value,
                    "avg_latency_ms": round(p.health.avg_latency(), 2),
                    "available": p.health.is_available(),
                }
                for p in self._providers.values()
            ]

    def run_health_checks(self) -> None:
        """Ping all providers and update health status."""
        with self._lock:
            providers = list(self._providers.values())
        for p in providers:
            try:
                alive = p.is_healthy()
                if alive:
                    if p.health.status == ProviderStatus.UNAVAILABLE:
                        p.health.status = ProviderStatus.HEALTHY
                else:
                    p.health.record_failure()
            except Exception:
                p.health.record_failure()

    def list_providers(self) -> list[str]:
        with self._lock:
            return list(self._provider_order)

    # ------------------------------------------------------------------
    # Private routing helpers
    # ------------------------------------------------------------------

    def _get_candidates(self, preferred: Optional[str]) -> list[LLMProvider]:
        with self._lock:
            order = list(self._provider_order)
            providers = dict(self._providers)

        if self._policy == RoutingPolicy.PREFERRED or preferred:
            name = preferred or (order[0] if order else None)
            ordered = [name] + [n for n in order if n != name]
        elif self._policy == RoutingPolicy.LOWEST_LATENCY:
            ordered = sorted(order, key=lambda n: providers[n].health.avg_latency())
        elif self._policy == RoutingPolicy.ROUND_ROBIN:
            with self._lock:
                start = self._rr_index % len(order) if order else 0
                self._rr_index += 1
            ordered = order[start:] + order[:start]
        elif self._policy == RoutingPolicy.WEIGHTED:
            import random
            weights = [providers[n].weight for n in order]
            ordered = random.choices(order, weights=weights, k=len(order))
        else:
            ordered = order

        return [providers[n] for n in ordered if n in providers]
