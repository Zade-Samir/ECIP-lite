"""
Request logger middleware — attaches correlation IDs and logs request timing.
"""
import time
import uuid
from typing import Optional
from ecip_core.common.logger import get_logger

logger = get_logger(__name__)


class RequestLogger:
    """
    Generates and tracks correlation IDs for requests.
    Logs request start/end with duration.
    """

    def start_request(self, method: str, path: str, client_ip: str = "-") -> dict:
        """
        Start tracking a request. Returns context dict with correlation_id.
        """
        correlation_id = str(uuid.uuid4())[:8]
        started_at = time.monotonic()
        logger.info("Request received")
        return {
            "correlation_id": correlation_id,
            "method": method,
            "path": path,
            "client_ip": client_ip,
            "started_at": started_at,
        }

    def end_request(self, ctx: dict, status_code: int) -> None:
        """Log request completion with timing."""
        duration_ms = round((time.monotonic() - ctx["started_at"]) * 1000, 2)
        logger.info("Route resolved")
        logger.info("Response returned")
