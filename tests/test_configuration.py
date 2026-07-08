import os
import unittest
from unittest.mock import patch
from pydantic import ValidationError

from ecip_core.config.loader import load_settings, Settings


class TestConfiguration(unittest.TestCase):

    def test_default_profile_loads_development(self):
        """Without any env variables, it defaults to the development profile."""
        with patch.dict(os.environ, {}, clear=True):
            s = load_settings()
            self.assertEqual(s.ECIP_PROFILE, "development")
            self.assertEqual(s.database.db_path, "data/ecip.db")
            self.assertEqual(s.faiss.index_path, ".ecip/faiss.index")
            self.assertEqual(s.logging.level, "INFO")
            self.assertEqual(s.api.port, 8000)
            self.assertTrue(s.cli.ansi_colors)

    def test_testing_profile_configuration(self):
        """Testing profile should override database, faiss, logging, and cache correctly."""
        with patch.dict(os.environ, {"ECIP_PROFILE": "testing"}, clear=True):
            s = load_settings()
            self.assertEqual(s.ECIP_PROFILE, "testing")
            self.assertEqual(s.database.db_path, "data/ecip_test.db")
            self.assertEqual(s.faiss.index_path, ".ecip/faiss_test.index")
            self.assertEqual(s.logging.level, "WARNING")
            self.assertEqual(s.api.port, 8001)
            self.assertFalse(s.cli.ansi_colors)
            self.assertFalse(s.cache.enabled)

    def test_production_profile_configuration(self):
        """Production profile overrides database, faiss, logging, and api host."""
        with patch.dict(os.environ, {"ECIP_PROFILE": "production"}, clear=True):
            s = load_settings()
            self.assertEqual(s.ECIP_PROFILE, "production")
            self.assertEqual(s.database.db_path, "data/ecip_prod.db")
            self.assertEqual(s.faiss.index_path, ".ecip/faiss_prod.index")
            self.assertEqual(s.logging.level, "ERROR")
            self.assertEqual(s.api.host, "0.0.0.0")
            self.assertEqual(s.api.port, 80)

    def test_environment_variable_override(self):
        """Environment variables take priority over profile settings."""
        with patch.dict(os.environ, {
            "ECIP_PROFILE": "development",
            "DB_PATH": "custom/db_path.db",
            "MODEL_NAME": "custom-llm-model",
            "API_PORT": "9090",
        }, clear=True):
            s = load_settings()
            self.assertEqual(s.ECIP_PROFILE, "development")
            self.assertEqual(s.database.db_path, "custom/db_path.db")
            self.assertEqual(s.inference.model, "custom-llm-model")
            self.assertEqual(s.api.port, 9090)

    def test_invalid_profile_fails_gracefully(self):
        """An invalid profile name defaults back to development profile."""
        with patch.dict(os.environ, {"ECIP_PROFILE": "invalid-profile"}, clear=True):
            with self.assertLogs("ecip_core.config.loader", level="ERROR") as log:
                s = load_settings()
                self.assertEqual(s.ECIP_PROFILE, "development")
                self.assertTrue(any("Invalid profile" in m for m in log.output))

    def test_validation_missing_db_path(self):
        """Empty or blank DB path should fail validation."""
        with self.assertRaises(ValueError):
            Settings(DB_PATH="")

    def test_validation_invalid_ollama_url(self):
        """Ollama URL must start with http:// or https://."""
        with self.assertRaises(ValueError):
            Settings(OLLAMA_BASE_URL="localhost:11434")

    def test_validation_negative_port(self):
        """Numeric configurations must be positive."""
        with self.assertRaises(ValueError):
            Settings(API_PORT=-80)

    def test_validation_negative_max_tokens(self):
        """Max tokens must be positive."""
        with self.assertRaises(ValueError):
            Settings(MAX_TOKENS=0)


if __name__ == "__main__":
    unittest.main()
