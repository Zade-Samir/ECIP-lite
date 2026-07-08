import time
import logging
from functools import wraps
from contextlib import contextmanager
from typing import Any, Callable, Optional


@contextmanager
def measure_time(message: str, logger: logging.Logger, level: int = logging.INFO):
    """
    Context manager to measure the execution duration of a block of code
    and log the timing using structured formatting.
    """
    t0 = time.perf_counter()
    try:
        yield
    finally:
        duration = (time.perf_counter() - t0) * 1000  # ms
        logger.log(level, message, extra={"duration": f"{duration:.2f}ms"})


def log_duration(message: Optional[str] = None, logger: Optional[logging.Logger] = None, level: int = logging.INFO):
    """
    Decorator to log execution duration of a function.
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            log_target = logger or logging.getLogger(func.__module__)
            log_msg = message or f"Executed {func.__name__}"
            t0 = time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                duration = (time.perf_counter() - t0) * 1000  # ms
                log_target.log(level, log_msg, extra={"duration": f"{duration:.2f}ms"})
        return wrapper
    return decorator
