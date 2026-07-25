"""
Circuit breaker middleware for the API Gateway.
Opens after N consecutive failures, resets after a cooldown period.
"""
import time
import threading
from enum import Enum
from ecip_core.common.logger import get_logger

logger = get_logger(__name__)


class CircuitState(str, Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Blocking requests (too many failures)
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """
    Per-route circuit breaker.

    States:
        CLOSED  → Normal. Failures increment counter.
        OPEN    → After failure_threshold failures. Rejects all requests.
        HALF_OPEN → After cooldown. Allows one probe request.

    Usage:
        cb = CircuitBreaker(failure_threshold=5, cooldown_seconds=30)
        if cb.allow_request():
            try:
                result = do_something()
                cb.record_success()
            except Exception:
                cb.record_failure()
        else:
            raise ServiceUnavailable("Circuit open")
    """

    def __init__(
        self,
        name: str = "default",
        failure_threshold: int = 5,
        cooldown_seconds: float = 30.0,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self._failures = 0
        self._state = CircuitState.CLOSED
        self._opened_at: float = 0.0
        self._lock = threading.Lock()

    def allow_request(self) -> bool:
        with self._lock:
            if self._state == CircuitState.CLOSED:
                return True

            if self._state == CircuitState.OPEN:
                if time.monotonic() - self._opened_at >= self.cooldown_seconds:
                    self._state = CircuitState.HALF_OPEN
                    return True  # Allow probe
                logger.error("Circuit breaker opened")
                return False

            if self._state == CircuitState.HALF_OPEN:
                return True  # Allow one probe

        return False

    def record_success(self) -> None:
        with self._lock:
            self._failures = 0
            self._state = CircuitState.CLOSED

    def record_failure(self) -> None:
        with self._lock:
            self._failures += 1
            if self._failures >= self.failure_threshold:
                self._state = CircuitState.OPEN
                self._opened_at = time.monotonic()
                logger.error("Circuit breaker opened")
            elif self._state == CircuitState.HALF_OPEN:
                # Probe failed — stay open
                self._state = CircuitState.OPEN
                self._opened_at = time.monotonic()

    @property
    def state(self) -> CircuitState:
        with self._lock:
            return self._state

    def is_open(self) -> bool:
        return self.state == CircuitState.OPEN

    def reset(self) -> None:
        with self._lock:
            self._failures = 0
            self._state = CircuitState.CLOSED


class CircuitBreakerRegistry:
    """Manages circuit breakers per named route/service."""

    def __init__(self, failure_threshold: int = 5, cooldown_seconds: float = 30.0):
        self._breakers: dict[str, CircuitBreaker] = {}
        self._lock = threading.Lock()
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds

    def get(self, name: str) -> CircuitBreaker:
        with self._lock:
            if name not in self._breakers:
                self._breakers[name] = CircuitBreaker(
                    name=name,
                    failure_threshold=self.failure_threshold,
                    cooldown_seconds=self.cooldown_seconds,
                )
            return self._breakers[name]

    def status(self) -> list[dict]:
        with self._lock:
            return [
                {"name": name, "state": cb.state.value, "failures": cb._failures}
                for name, cb in self._breakers.items()
            ]
