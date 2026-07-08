import contextvars
import uuid
from typing import Optional

_correlation_id_var = contextvars.ContextVar("correlation_id", default="-")


def get_correlation_id() -> str:
    """Retrieve the current request correlation ID."""
    return _correlation_id_var.get()


def set_correlation_id(cid: str) -> None:
    """Set the current request correlation ID."""
    _correlation_id_var.set(cid)


def clear_correlation_id() -> None:
    """Reset the correlation ID to the default placeholder."""
    _correlation_id_var.set("-")


class CorrelationIdContext:
    """
    Context manager to bind a Correlation ID to the current context.
    Works safely with parallel and async execution.
    """

    def __init__(self, cid: Optional[str] = None):
        self.cid = cid or str(uuid.uuid4())
        self.token = None

    def __enter__(self) -> str:
        self.token = _correlation_id_var.set(self.cid)
        return self.cid

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.token:
            _correlation_id_var.reset(self.token)
