import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from ecip_core.workspace.manager import workspace_manager, WorkspaceManager
from ecip_core.storage.sqlite.database import Database
from ecip_core.storage.sqlite.repository import JavaRepository
from ecip_core.settings import settings
from ecip_core.parser.models.parsed_java_file import ParsedJavaFile


class TestWorkspace(unittest.TestCase):

    def setUp(self):
        # Save previous active project to restore in tearDown
        self.prev_active = workspace_manager.get_active_workspace()
        
        # We clean the registry projects table
        conn = Database.get_registry_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM projects")
        conn.commit()

        # Re-register default
        workspace_manager.register_workspace("default", "Default Workspace", "projects/default")
        workspace_manager.set_active_workspace("default")

    def tearDown(self):
        # Restore previous active project
        workspace_manager.set_active_workspace(self.prev_active)
        
        # Clean up temporary test databases
        for p in ["proj_a", "proj_b"]:
            workspace_manager.delete_workspace(p)

    def test_workspace_registration_and_selection(self):
        """Registering a project creates workspace entries and updates active paths on selection."""
        res = workspace_manager.register_workspace(
            project_id="proj_a",
            alias="Project A Workspace",
            root_path="projects/proj_a"
        )
        self.assertEqual(res["project_id"], "proj_a")
        self.assertEqual(res["alias"], "Project A Workspace")

        # Verify default paths first
        self.assertEqual(settings.DB_PATH, "data/ecip.db")
        self.assertEqual(settings.FAISS_INDEX_PATH, ".ecip/faiss.index")

        # Switch to Project A
        workspace_manager.set_active_workspace("proj_a")
        self.assertEqual(workspace_manager.get_active_workspace(), "proj_a")

        # Verify paths updated dynamically
        self.assertEqual(settings.DB_PATH, "data/ecip_proj_a.db")
        self.assertEqual(settings.FAISS_INDEX_PATH, ".ecip/faiss_proj_a.index")
        self.assertEqual(settings.FAISS_METADATA_PATH, ".ecip/faiss_metadata_proj_a.json")

    def test_workspace_metadata_and_vector_isolation(self):
        """Verifies metadata saved in Project A does not appear in Project B."""
        # 1. Register projects
        workspace_manager.register_workspace("proj_a", "Project A", "projects/proj_a")
        workspace_manager.register_workspace("proj_b", "Project B", "projects/proj_b")

        # 2. Save metadata to Project A
        workspace_manager.set_active_workspace("proj_a")
        repo_a = JavaRepository()
        file_a = ParsedJavaFile(
            file_name="ClassA.java",
            file_path="projects/proj_a/ClassA.java",
            package_name="com.test",
            class_name="ClassA",
            methods=[]
        )
        repo_a.save(file_a, file_hash="hash_a")

        # Verify A contains ClassA
        self.assertEqual(len(repo_a.get_all_files()), 1)
        self.assertEqual(repo_a.get_all_files()[0]["class_name"], "ClassA")

        # 3. Switch to Project B and verify empty/isolated
        workspace_manager.set_active_workspace("proj_b")
        repo_b = JavaRepository()
        self.assertEqual(len(repo_b.get_all_files()), 0)

        # Save metadata to Project B
        file_b = ParsedJavaFile(
            file_name="ClassB.java",
            file_path="projects/proj_b/ClassB.java",
            package_name="com.test",
            class_name="ClassB",
            methods=[]
        )
        repo_b.save(file_b, file_hash="hash_b")

        # Verify B has ClassB, but A still only has ClassA
        self.assertEqual(len(repo_b.get_all_files()), 1)
        self.assertEqual(repo_b.get_all_files()[0]["class_name"], "ClassB")

        workspace_manager.set_active_workspace("proj_a")
        self.assertEqual(len(repo_a.get_all_files()), 1)
        self.assertEqual(repo_a.get_all_files()[0]["class_name"], "ClassA")

    def test_cache_isolation(self):
        """Verifies that caching records under Project A doesn't hit under Project B."""
        from ecip_core.cache.manager import cache_manager
        cache_manager.clear()

        # Dummy function to decorate
        call_count = 0

        @cache_manager.cached()
        def get_data(param):
            nonlocal call_count
            call_count += 1
            return f"result_{param}"

        workspace_manager.register_workspace("proj_a", "Project A", "projects/proj_a")
        workspace_manager.register_workspace("proj_b", "Project B", "projects/proj_b")

        # Run under Project A (Cache Miss -> Cache Hit)
        workspace_manager.set_active_workspace("proj_a")
        self.assertEqual(get_data("test"), "result_test")
        self.assertEqual(call_count, 1)

        self.assertEqual(get_data("test"), "result_test")
        self.assertEqual(call_count, 1)  # Cache hit (call count does not change)

        # Switch to Project B (Cache Miss)
        workspace_manager.set_active_workspace("proj_b")
        self.assertEqual(get_data("test"), "result_test")
        self.assertEqual(call_count, 2)  # Cache miss under different workspace!

    def test_workspace_deletion(self):
        """Deleting a workspace unlinks database files and clears registry details."""
        workspace_manager.register_workspace("proj_a", "Project A", "projects/proj_a")
        self.assertIsNotNone(workspace_manager.get_workspace("proj_a"))
        
        # Verify db file created
        db_file = Path("data/ecip_proj_a.db")
        workspace_manager.set_active_workspace("proj_a")
        self.assertTrue(db_file.exists())

        # Switch away to allow clean deletion/unlink without file locks
        workspace_manager.set_active_workspace("default")
        workspace_manager.delete_workspace("proj_a")

        self.assertIsNone(workspace_manager.get_workspace("proj_a"))
        self.assertFalse(db_file.exists())


if __name__ == "__main__":
    unittest.main()
