import os
import shutil
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from ecip_core.diagnostics.service import DiagnosticsService
from ecip_core.diagnostics.models import HealthReport
from ecip_core.workspace.manager import workspace_manager
from ecip_core.storage.sqlite.database import Database
from ecip_core.settings import settings


class TestDiagnostics(unittest.TestCase):

    def setUp(self):
        # Backup active workspace
        self.prev_active = workspace_manager.get_active_workspace()
        
        # Clean registry and set to default
        conn = Database.get_registry_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM projects")
        conn.commit()

        workspace_manager.register_workspace("default", "Default Workspace", "projects/default")
        workspace_manager.set_active_workspace("default")

        self.service = DiagnosticsService()

    def tearDown(self):
        workspace_manager.set_active_workspace(self.prev_active)
        workspace_manager.delete_workspace("test_proj")

    @patch("ecip_core.diagnostics.service.Path.exists")
    @patch("faiss.read_index")
    def test_healthy_project(self, mock_read_index, mock_exists):
        """Verifies report is 'healthy' when all workspace, database, and FAISS checks pass."""
        mock_exists.return_value = True
        
        # Mock FAISS Index with flat flat structure
        mock_index = MagicMock()
        mock_index.ntotal = 0
        mock_read_index.return_value = mock_index

        # Mock database returns zero records (empty is healthy)
        with patch.object(Database, "get_connection") as mock_conn:
            mock_cursor = MagicMock()
            mock_cursor.fetchone.side_effect = [
                ("ok",), # integrity check ok
                (0,),    # chunk count
                (0,),    # orphaned chunks count
            ]
            mock_cursor.fetchall.return_value = [] # no files, no chunks, no edges
            mock_conn.return_value.cursor.return_value = mock_cursor

            report = self.service.run_diagnostics()
            
            self.assertEqual(report.overall_status, "healthy")
            self.assertEqual(len(report.errors), 0)
            self.assertEqual(len(report.warnings), 0)
            self.assertIn("SQLite Integrity Check", report.checks_passed)
            self.assertIn("FAISS Index Availability", report.checks_passed)

    @patch("ecip_core.diagnostics.service.Path.exists")
    def test_missing_faiss_vectors(self, mock_exists):
        """Verifies report is 'unhealthy' with clear recommendations when FAISS index file is missing."""
        # SQLite passes, but FAISS files are missing
        mock_exists.side_effect = lambda: False  # all exists checks return False

        with patch.object(Database, "get_connection") as mock_conn:
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = ("ok",) # integrity check ok
            mock_cursor.fetchall.return_value = []
            mock_conn.return_value.cursor.return_value = mock_cursor

            report = self.service.run_diagnostics()
            
            self.assertEqual(report.overall_status, "unhealthy")
            self.assertTrue(any("FAISS index file not found" in err for err in report.errors))
            self.assertIn("Run indexer command to generate missing vector store index.", report.recommendations)

    def test_corrupt_workspace(self):
        """Verifies report detects invalid/missing workspace root directory."""
        workspace_manager.register_workspace("test_proj", "Test Project", "projects/non_existent_folder_abc")
        workspace_manager.set_active_workspace("test_proj")

        report = self.service.run_diagnostics()
        self.assertEqual(report.overall_status, "unhealthy")
        self.assertTrue(any("does not exist on filesystem" in err for err in report.errors))
        self.assertIn("Restore workspace directory or update root path in registry.", report.recommendations)

    @patch("ecip_core.diagnostics.service.Path.exists")
    @patch("faiss.read_index")
    def test_vector_chunk_count_mismatch(self, mock_read_index, mock_exists):
        """Verifies warning is triggered when chunk count does not match vector count."""
        mock_exists.return_value = True

        mock_index = MagicMock()
        mock_index.ntotal = 10  # 10 vectors in FAISS
        mock_read_index.return_value = mock_index

        with patch.object(Database, "get_connection") as mock_conn:
            mock_cursor = MagicMock()
            mock_cursor.fetchone.side_effect = [
                ("ok",), # integrity check
                (5,), # 5 chunks in SQLite database
                (0,), # orphaned
            ]
            mock_cursor.fetchall.return_value = []
            mock_conn.return_value.cursor.return_value = mock_cursor

            report = self.service.run_diagnostics()
            
            self.assertEqual(report.overall_status, "degraded")
            self.assertEqual(len(report.errors), 0)
            self.assertTrue(any("Vector mismatch" in w for w in report.warnings))
            self.assertIn("Perform full re-index to synchronize chunk metadata with FAISS vectors.", report.recommendations)

    def test_json_serialization(self):
        """Verifies report can be serialized to JSON successfully."""
        report = HealthReport(
            overall_status="healthy",
            warnings=["Warn A"],
            errors=["Err A"],
            checks_passed=["Check A"],
            checks_failed=[],
            recommendations=["Rec A"],
            execution_time_ms=1.5
        )
        json_str = report.model_dump_json()
        self.assertIn("healthy", json_str)
        self.assertIn("Warn A", json_str)
        self.assertIn("Err A", json_str)


if __name__ == "__main__":
    unittest.main()
