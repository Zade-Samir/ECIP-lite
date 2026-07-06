import unittest
import sqlite3
from unittest.mock import MagicMock
from ecip_core.retrieval.metadata.metadata_service import MetadataSearchService
from ecip_core.retrieval.models.metadata_result import MetadataResult
from ecip_core.storage.sqlite.repository import JavaRepository
from ecip_core.vectorstore.faiss_store import FAISSStore
from ecip_core.embedding.models.embedding import Embedding


class TestMetadataSearchService(unittest.TestCase):

    def setUp(self):
        self.mock_repo = MagicMock(spec=JavaRepository)
        self.mock_faiss_store = MagicMock(spec=FAISSStore)
        self.mock_faiss_store.metadata = []

        self.service = MetadataSearchService(
            repository=self.mock_repo,
            faiss_store=self.mock_faiss_store
        )

    def test_class_lookup_exact(self):
        self.mock_repo.search_classes.return_value = [
            {
                "id": 1,
                "file_name": "UserService.java",
                "file_path": "/src/UserService.java",
                "package_name": "com.example.service",
                "class_name": "UserService"
            }
        ]

        emb = Embedding(
            file_name="UserService.java",
            class_name="UserService",
            method_name="",
            source_code="public class UserService {\n}",
            vector=[],
            chunk_id="chunk_01",
            file_path="/src/UserService.java",
            chunk_type="CLASS_OVERVIEW",
            start_line=1,
            end_line=20
        )
        self.mock_faiss_store.metadata = [emb]

        results = self.service.search_classes("UserService", exact=True)
        self.assertEqual(len(results), 1)
        res = results[0]

        self.assertEqual(res.class_name, "UserService")
        self.assertEqual(res.package_name, "com.example.service")
        self.assertEqual(res.file_path, "/src/UserService.java")
        self.assertEqual(res.method_name, "")
        self.assertEqual(res.signature, "public class UserService {")
        self.assertEqual(res.start_line, 1)
        self.assertEqual(res.end_line, 20)
        self.assertEqual(res.source_reference, "public class UserService {\n}")
        self.mock_repo.search_classes.assert_called_once_with("UserService", exact=True)

    def test_class_lookup_prefix(self):
        self.mock_repo.search_classes.return_value = [
            {
                "id": 1,
                "file_name": "UserService.java",
                "file_path": "/src/UserService.java",
                "package_name": "com.example.service",
                "class_name": "UserService"
            }
        ]
        emb = Embedding(
            file_name="UserService.java",
            class_name="UserService",
            method_name="",
            source_code="public class UserService { }",
            vector=[],
            chunk_id="chunk_01",
            file_path="/src/UserService.java",
            chunk_type="CLASS_OVERVIEW",
            start_line=1,
            end_line=20
        )
        self.mock_faiss_store.metadata = [emb]

        results = self.service.search_classes("User", exact=False)
        self.assertEqual(len(results), 1)
        self.mock_repo.search_classes.assert_called_once_with("User", exact=False)

    def test_method_lookup(self):
        self.mock_repo.search_methods.return_value = [
            {
                "file_id": 1,
                "file_name": "UserService.java",
                "file_path": "/src/UserService.java",
                "package_name": "com.example.service",
                "class_name": "UserService",
                "method_name": "getUser"
            }
        ]
        emb = Embedding(
            file_name="UserService.java",
            class_name="UserService",
            method_name="getUser",
            source_code="public User getUser() { return null; }",
            vector=[],
            chunk_id="chunk_02",
            file_path="/src/UserService.java",
            chunk_type="METHOD",
            start_line=10,
            end_line=12
        )
        self.mock_faiss_store.metadata = [emb]

        results = self.service.search_methods("getUser", exact=True)
        self.assertEqual(len(results), 1)
        res = results[0]
        self.assertEqual(res.method_name, "getUser")
        self.assertEqual(res.signature, "public User getUser() { return null; }")
        self.mock_repo.search_methods.assert_called_once_with("getUser", exact=True)

    def test_package_lookup(self):
        self.mock_repo.search_packages.return_value = [
            {
                "id": 1,
                "file_name": "UserService.java",
                "file_path": "/src/UserService.java",
                "package_name": "com.example.service",
                "class_name": "UserService"
            }
        ]
        emb = Embedding(
            file_name="UserService.java",
            class_name="UserService",
            method_name="",
            source_code="public class UserService {}",
            vector=[],
            chunk_id="chunk_01",
            file_path="/src/UserService.java",
            chunk_type="CLASS_OVERVIEW"
        )
        self.mock_faiss_store.metadata = [emb]

        results = self.service.search_packages("com.example.service", exact=True)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].package_name, "com.example.service")

    def test_file_path_lookup(self):
        self.mock_repo.search_file_paths.return_value = [
            {
                "id": 1,
                "file_name": "UserService.java",
                "file_path": "/src/UserService.java",
                "package_name": "com.example.service",
                "class_name": "UserService"
            }
        ]
        emb = Embedding(
            file_name="UserService.java",
            class_name="UserService",
            method_name="",
            source_code="public class UserService {}",
            vector=[],
            chunk_id="chunk_01",
            file_path="/src/UserService.java",
            chunk_type="CLASS_OVERVIEW"
        )
        self.mock_faiss_store.metadata = [emb]

        results = self.service.search_file_paths("/src/UserService.java", exact=True)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].file_path, "/src/UserService.java")

    def test_no_exact_match_warning_logs(self):
        self.mock_repo.search_classes.return_value = []

        with self.assertLogs("ecip_core.retrieval.metadata.metadata_service", level="WARNING") as log_capture:
            results = self.service.search_classes("UnknownService")
            self.assertEqual(results, [])
            self.assertTrue(any("No exact match" in log for log in log_capture.output))

    def test_database_error_handling(self):
        self.mock_repo.search_classes.side_effect = sqlite3.OperationalError("no such table")

        with self.assertLogs("ecip_core.retrieval.metadata.metadata_service", level="ERROR") as log_capture:
            with self.assertRaises(sqlite3.OperationalError):
                self.service.search_classes("UserService")
            self.assertTrue(any("Database unavailable" in log for log in log_capture.output))

    def test_metadata_result_serialization(self):
        res = MetadataResult(
            project_id="my-project",
            file_path="/src/A.java",
            package_name="com.a",
            class_name="A",
            method_name="m",
            signature="void m()",
            start_line=1,
            end_line=5,
            source_reference="void m() {}"
        )
        serialized = res.model_dump()
        self.assertEqual(serialized["project_id"], "my-project")
        self.assertEqual(serialized["class_name"], "A")


if __name__ == "__main__":
    unittest.main()
