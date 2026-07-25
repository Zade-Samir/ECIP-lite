import unittest
import tempfile
import shutil
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from ecip_core.indexing.repository_indexer.indexer import RepositoryIndexer
from ecip_core.workspace.manager import workspace_manager
from ecip_core.storage.sqlite.database import Database


class TestRepositoryIndexer(unittest.TestCase):

    def setUp(self):
        self.indexer = RepositoryIndexer()
        self.test_dir = tempfile.mkdtemp()
        
        # Reset active workspace context variable to prevent test pollution
        try:
            workspace_manager.set_active_workspace("default")
        except ValueError:
            pass

        # Ensure registry DB starts clean for test cases
        self.indexer.workspace_manager._ensure_repositories_table()
        conn = Database.get_registry_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM repositories")
        cursor.execute("DELETE FROM projects WHERE project_id NOT IN ('default')")
        conn.commit()

    def tearDown(self):
        shutil.rmtree(self.test_dir)
        # Clean registry DB after tests
        conn = Database.get_registry_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM repositories")
        cursor.execute("DELETE FROM projects WHERE project_id NOT IN ('default')")
        conn.commit()

    def test_repository_registration(self):
        repo_id = "test-repo"
        repo_path = os.path.join(self.test_dir, "repo1")
        os.makedirs(repo_path, exist_ok=True)

        res = self.indexer.register_repository(
            repository_id=repo_id,
            name="Test Repo",
            root_path=repo_path,
            branch="main",
            language="Java",
            project_type="Maven"
        )

        self.assertEqual(res["repository_id"], repo_id)
        self.assertEqual(res["root_path"], repo_path)
        self.assertEqual(res["branch"], "main")

        # Test duplicate registration warning/exception
        with self.assertRaises(ValueError):
            self.indexer.register_repository(
                repository_id=repo_id,
                name="Test Repo",
                root_path=repo_path
            )

    def test_repository_discovery(self):
        repo1_path = Path(self.test_dir) / "repo1"
        repo1_path.mkdir()
        (repo1_path / ".git").mkdir()
        
        repo2_path = Path(self.test_dir) / "repo2"
        repo2_path.mkdir()
        (repo2_path / "pom.xml").touch()

        discovered = self.indexer.discover_repositories(self.test_dir)
        self.assertEqual(len(discovered), 2)
        repo_ids = [d["repository_id"] for d in discovered]
        self.assertIn("repo1", repo_ids)
        self.assertIn("repo2", repo_ids)

    @patch("ecip_core.indexing.repository_indexer.indexer.IndexBuilder")
    def test_independent_indexing_and_incremental(self, mock_index_builder):
        repo_path = os.path.join(self.test_dir, "repo1")
        os.makedirs(repo_path, exist_ok=True)
        
        self.indexer.register_repository("repo1", "Repo 1", repo_path)

        with patch.object(self.indexer, "get_git_commit_hash", return_value="hash123"):
            # First index run: should call IndexBuilder.build
            res = self.indexer.index_repository("repo1")
            self.assertEqual(res["status"], "success")
            self.assertEqual(res["commit_hash"], "hash123")
            mock_index_builder.return_value.build.assert_called_once()
            
            repo_details = workspace_manager.get_repository("repo1")
            self.assertEqual(repo_details["commit_hash"], "hash123")

            # Second index run: should skip
            mock_index_builder.return_value.build.reset_mock()
            res2 = self.indexer.index_repository("repo1")
            self.assertEqual(res2["status"], "skipped")
            mock_index_builder.return_value.build.assert_not_called()

    @patch("ecip_core.indexing.repository_indexer.indexer.get_graph_provider")
    def test_cross_repository_relationship_creation(self, mock_get_graph_provider):
        mock_provider = MagicMock()
        mock_get_graph_provider.return_value = mock_provider
        
        repo1_path = os.path.join(self.test_dir, "repo1")
        repo2_path = os.path.join(self.test_dir, "repo2")
        os.makedirs(repo1_path, exist_ok=True)
        os.makedirs(repo2_path, exist_ok=True)

        self.indexer.register_repository("repo1", "Repo 1", repo1_path)
        self.indexer.register_repository("repo2", "Repo 2", repo2_path)

        # Populate repo1 classes & edges (A depends on B)
        workspace_manager.set_active_workspace("repo1")
        db1 = Database()
        cursor1 = db1.get_connection().cursor()
        cursor1.execute("INSERT OR REPLACE INTO java_files (file_name, file_path, class_name) VALUES ('ClassA.java', '/src/ClassA.java', 'ClassA')")
        cursor1.execute("INSERT OR REPLACE INTO dependency_edges (project_id, source_class, target_class, relationship_type) VALUES ('repo1', 'ClassA', 'ClassB', 'DEPENDS_ON')")
        db1.get_connection().commit()

        # Populate repo2 classes (contains B)
        workspace_manager.set_active_workspace("repo2")
        db2 = Database()
        cursor2 = db2.get_connection().cursor()
        cursor2.execute("INSERT OR REPLACE INTO java_files (file_name, file_path, class_name) VALUES ('ClassB.java', '/src/ClassB.java', 'ClassB')")
        db2.get_connection().commit()

        # Trigger linking
        links_count = self.indexer.create_cross_repository_links()
        
        self.assertEqual(links_count, 1)
        mock_provider.create_cross_repo_relationship.assert_called_once_with(
            source_id="ClassA",
            source_project="repo1",
            target_id="ClassB",
            target_project="repo2",
            rel_type="DEPENDS_ON",
            properties={"cross_repository": "true"}
        )

    def test_indexing_failed_invalid_path(self):
        self.indexer.register_repository("repo1", "Repo 1", "/invalid/path/does/not/exist")
        with self.assertRaises(FileNotFoundError):
            self.indexer.index_repository("repo1")


if __name__ == "__main__":
    unittest.main()
