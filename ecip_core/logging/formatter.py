import logging
from ecip_core.logging.correlation import get_correlation_id


class StructuredFormatter(logging.Formatter):
    """
    Structured log formatter.
    Ensures every log contains a timestamp, log level, module/logger name,
    correlation ID, message, and execution duration (when applicable).
    """

    def format(self, record: logging.LogRecord) -> str:
        # Fetch correlation ID
        record.correlation_id = get_correlation_id()

        # Format execution duration if provided as extra={"duration": ...}
        duration = getattr(record, "duration", None)
        record.duration_str = f" | dur:{duration}" if duration is not None else ""

        return super().format(record)
