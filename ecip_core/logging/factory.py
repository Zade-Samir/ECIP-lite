import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from typing import Optional

from ecip_core.logging.formatter import StructuredFormatter


def get_log_level() -> int:
    """Safely retrieves log level from configuration settings or environment."""
    try:
        from ecip_core.settings import settings
        level_str = settings.LOG_LEVEL.upper()
    except Exception:
        level_str = os.environ.get("LOG_LEVEL", "INFO").upper()

    levels = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    return levels.get(level_str, logging.INFO)


class StructuredLogger(logging.Logger):
    """
    Custom logger subclass supporting extra exception details
    or specialized structured log formats.
    """

    def exception_safe(self, message: str, exception: Exception, level: int = logging.ERROR):
        """Safely logs exceptions without crashing or throwing formatting errors."""
        try:
            self.log(level, f"{message}: {str(exception)}", exc_info=exception)
        except Exception as e:
            # Fallback to sys.stderr if logging infrastructure fails
            sys.stderr.write(f"Logging Failure: {e}\nOriginal Error: {message}: {exception}\n")


# Register custom Logger class
logging.setLoggerClass(StructuredLogger)


def configure_logging(
    log_file_path: Optional[str] = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5,
    force: bool = False,
) -> None:
    """
    Configures the root logging handlers.
    Sets up StructuredFormatter on Console and optional File handlers.
    """
    log_level = get_log_level()
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    if force:
        for handler in list(root_logger.handlers):
            handler.close()
            root_logger.removeHandler(handler)
    elif root_logger.handlers:
        return

    # Structured pattern
    log_pattern = "[%(asctime)s] %(levelname)s | %(name)s | CID:%(correlation_id)s | %(message)s%(duration_str)s"
    formatter = StructuredFormatter(log_pattern, datefmt="%Y-%m-%d %H:%M:%S")

    # Console handler (sys.stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Optional File Handler
    if log_file_path:
        try:
            log_path = Path(log_file_path) if hasattr(log_file_path, "parent") else None
            if not log_path:
                from pathlib import Path
                log_path = Path(log_file_path)

            log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = RotatingFileHandler(
                log_path, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
            )
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        except Exception as e:
            # Gracefully handle file system or permission issues
            sys.stderr.write(f"Warning: Failed to configure log file handler ({log_file_path}): {e}\n")


def get_logger(name: str) -> StructuredLogger:
    """
    LoggerFactory entry point. Retrieves a StructuredLogger instance
    configured under the hierarchy of root handlers.
    """
    # Ensure root logging handlers are configured on first logger retrieval
    # Defaults file path to .ecip/app.log
    if not logging.getLogger().handlers:
        default_log_file = os.environ.get("LOG_FILE_PATH", ".ecip/app.log")
        configure_logging(log_file_path=default_log_file)

    logger = logging.getLogger(name)
    # Ensure it uses the correct type
    assert isinstance(logger, StructuredLogger)
    return logger
