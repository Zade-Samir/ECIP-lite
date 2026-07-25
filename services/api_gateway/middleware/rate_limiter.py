"""
Token bucket rate limiter middleware for the API Gateway.
Per-IP rate limiting using in-memory token bucket algorithm.
"""
import time
import threading
from collections import defaultdict
from ecip_core.common.logger import get_logger

logger = get_logger(__name__)


class TokenBucket:
    """Thread-safe token bucket for a single client."""

    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate  # tokens per second
        self.tokens = float(capacity)
        self.last_refill = time.monotonic()
        self._lock = threading.Lock()

    def consume(self, tokens: int = 1) -> bool:
        with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_refill
            self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
            self.last_refill = now

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False


class RateLimiter:
    """
    Per-client in-memory rate limiter using token bucket algorithm.

    Configuration:
        capacity: Max tokens (burst size)
        refill_rate: Tokens added per second
    """

    def __init__(self, capacity: int = 60, refill_rate: float = 1.0):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self._buckets: dict[str, TokenBucket] = {}
        self._lock = threading.Lock()

    def is_allowed(self, client_id: str, tokens: int = 1) -> bool:
        bucket = self._get_bucket(client_id)
        allowed = bucket.consume(tokens)
        if not allowed:
            logger.warning("Rate limit exceeded")
        return allowed

    def reset(self, client_id: str) -> None:
        with self._lock:
            self._buckets.pop(client_id, None)

    def _get_bucket(self, client_id: str) -> TokenBucket:
        with self._lock:
            if client_id not in self._buckets:
                self._buckets[client_id] = TokenBucket(
                    capacity=self.capacity,
                    refill_rate=self.refill_rate,
                )
            return self._buckets[client_id]
