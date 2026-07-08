import io
import os
import sys
import logging
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from ecip_core.logging.correlation import CorrelationIdContext, get_correlation_id
from ecip_core.logging.factory import get_logger, configure_logging, StructuredLogger
from ecip_core.logging.formatter import StructuredFormatter
from ecip_core.logging.timing import measure_time, log_duration


class TestLogging(unittest.TestCase):

    def setUp(self):
        # Reset logging configuration for clean state
        logging.getLogger().handlers = []

    def test_logger_creation(self):
        """get_logger returns a StructuredLogger instance."""
        logger = get_logger("test_module")
        self.assertIsInstance(logger, StructuredLogger)

    def test_correlation_id_context_propagation(self):
        """CorrelationIdContext binds and cleans up context-specific IDs."""
        self.assertEqual(get_correlation_id(), "-")

        with CorrelationIdContext("custom-uuid-1234") as cid:
            self.assertEqual(cid, "custom-uuid-1234")
            self.assertEqual(get_correlation_id(), "custom-uuid-1234")

        self.assertEqual(get_correlation_id(), "-")

    def test_structured_formatter_places_correlation_id(self):
        """StructuredFormatter formats logs with correct correlation ID and extra details."""
        log_pattern = "[%(asctime)s] %(levelname)s | %(name)s | CID:%(correlation_id)s | %(message)s%(duration_str)s"
        formatter = StructuredFormatter(log_pattern)

        logger = logging.getLogger("test_formatter_logger")
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        # Log without context
        logger.info("Hello World")
        output = stream.getvalue()
        self.assertIn("CID:-", output)
        self.assertIn("Hello World", output)

        # Log inside correlation context
        stream.truncate(0)
        stream.seek(0)
        with CorrelationIdContext("uuid-999"):
            logger.info("Inside Request")
        output = stream.getvalue()
        self.assertIn("CID:uuid-999", output)
        self.assertIn("Inside Request", output)

    def test_performance_timing_helpers(self):
        """measure_time context manager and log_duration decorator inject correct duration string."""
        log_pattern = "%(message)s%(duration_str)s"
        formatter = StructuredFormatter(log_pattern)

        logger = logging.getLogger("test_timing_logger")
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        # Test measure_time
        with measure_time("block execution completed", logger):
            pass

        output = stream.getvalue()
        self.assertIn("block execution completed", output)
        self.assertIn("dur:", output)

        # Test log_duration decorator
        stream.truncate(0)
        stream.seek(0)

        @log_duration("function run completed", logger)
        def my_function():
            return "ok"

        res = my_function()
        self.assertEqual(res, "ok")
        output_dec = stream.getvalue()
        self.assertIn("function run completed", output_dec)
        self.assertIn("dur:", output_dec)

    def test_safe_exception_logging(self):
        """exception_safe logs errors without raising exceptions even if execution goes wrong."""
        logger = get_logger("test_exception_logger")
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        logger.addHandler(handler)

        try:
            raise ValueError("Something broke")
        except ValueError as e:
            logger.exception_safe("Safety wrapper activated", e)

        output = stream.getvalue()
        self.assertIn("Safety wrapper activated", output)
        self.assertIn("ValueError: Something broke", output)

    def tearDown(self):
        # Close and remove all handlers to avoid resource warning and file lock issues
        root_logger = logging.getLogger()
        for handler in list(root_logger.handlers):
            handler.close()
            root_logger.removeHandler(handler)

    def test_file_logging_configuration(self):
        """Rotating file logs are created and written properly."""
        with TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "sub" / "app.log"
            # Ensure custom configuration is applied with force=True
            configure_logging(log_file_path=str(log_file), force=True)

            logger = get_logger("file_logger")
            logger.info("Log line written to file")

            # Check that file handler successfully created directory and wrote to file
            self.assertTrue(log_file.exists())
            content = log_file.read_text(encoding="utf-8")
            self.assertIn("Log line written to file", content)


if __name__ == "__main__":
    unittest.main()
