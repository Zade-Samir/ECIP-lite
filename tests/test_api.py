import sqlite3
# Monkey-patch sqlite3 to allow multi-threaded access without thread-ownership errors
original_connect = sqlite3.connect
def custom_connect(*args, **kwargs):
    kwargs["check_same_thread"] = False
    return original_connect(*args, **kwargs)
sqlite3.connect = custom_connect

import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from ecip_core.api.main import app
from ecip_core.api.routes.query import get_coordinator
from ecip_core.query.models.coordinator_response import CoordinatorResponse
from ecip_core.query.models.intent_result import IntentResult
from ecip_core.retrieval.models.hybrid_result import HybridResult


class TestAPI(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)
        self.mock_coord = MagicMock()
        app.dependency_overrides[get_coordinator] = lambda: self.mock_coord

    def tearDown(self):
        app.dependency_overrides.clear()

    # --- Query Endpoint Tests ---

    @patch("ecip_core.api.routes.query.workspace_manager")
    @patch("ecip_core.api.routes.query.JavaRepository")
    def test_query_success_flow(self, mock_repo_class, mock_ws):
        mock_ws.get_workspace.return_value = {"project_id": "sample-project", "root_path": "/projects/sample"}
        mock_repo = mock_repo_class.return_value
        mock_repo.get_all_file_paths.return_value = ["/src/UserService.java"]

        self.mock_coord.process.return_value = CoordinatorResponse(
            answer="Here is the class UserService.",
            model="qwen2.5-coder:3b",
            intent=IntentResult(
                intent="explain_code", confidence=1.0, matched_patterns=["explain"], normalized_query="explain userservice"
            ),
            entities=[],
            citations=[
                HybridResult(
                    source="metadata",
                    score=1.0,
                    chunk_id="chunk_1",
                    file_path="/src/UserService.java",
                    class_name="UserService",
                    method_name="",
                    chunk_type="class",
                    content="code content",
                    start_line=1,
                    end_line=20
                )
            ]
        )

        payload = {
            "project_id": "sample-project",
            "question": "Explain UserService"
        }

        response = self.client.post("/api/v1/query", json=payload)
        self.assertEqual(response.status_code, 200)

        res_json = response.json()
        self.assertEqual(res_json["answer"], "Here is the class UserService.")
        self.assertEqual(res_json["model_name"], "qwen2.5-coder:3b")
        self.assertEqual(len(res_json["citations"]), 1)
        self.assertEqual(res_json["citations"][0]["file_path"], "/src/UserService.java")
        self.assertIn("duration_ms", res_json)

    def test_invalid_payload_validation_error(self):
        response = self.client.post("/api/v1/query", json={"question": "hello"})
        self.assertEqual(response.status_code, 422)

        response = self.client.post("/api/v1/query", json={"project_id": "default"})
        self.assertEqual(response.status_code, 422)

    @patch("ecip_core.api.routes.query.JavaRepository")
    def test_missing_project_not_found_404(self, mock_repo_class):
        response = self.client.post("/api/v1/query", json={"project_id": "wrong-proj", "question": "hello"})
        self.assertEqual(response.status_code, 404)

        # When project_id is 'sample-project', it hits workspace lookup — returns 404 (workspace not registered)
        # When project is registered but index is empty, also returns 404
        mock_repo = mock_repo_class.return_value
        mock_repo.get_all_file_paths.return_value = []

        with patch("ecip_core.api.routes.query.workspace_manager") as mock_ws:
            mock_ws.get_workspace.return_value = {"project_id": "sample-project"}
            response = self.client.post("/api/v1/query", json={"project_id": "sample-project", "question": "hello"})
            self.assertEqual(response.status_code, 404)
            self.assertIn("indexed project", response.json()["detail"].lower())

    @patch("ecip_core.api.routes.query.workspace_manager")
    @patch("ecip_core.api.routes.query.JavaRepository")
    def test_provider_unavailable_503_error(self, mock_repo_class, mock_ws):
        mock_ws.get_workspace.return_value = {"project_id": "sample-project", "root_path": "/projects/sample"}
        mock_repo = mock_repo_class.return_value
        mock_repo.get_all_file_paths.return_value = ["/src/UserService.java"]

        self.mock_coord.process.side_effect = ConnectionError("Ollama is offline")

        payload = {"project_id": "sample-project", "question": "hello"}
        response = self.client.post("/api/v1/query", json=payload)
        self.assertEqual(response.status_code, 503)
        self.assertIn("Inference Provider Unavailable", response.json()["detail"])

    @patch("ecip_core.api.routes.query.workspace_manager")
    @patch("ecip_core.api.routes.query.JavaRepository")
    def test_unexpected_error_500_mapping(self, mock_repo_class, mock_ws):
        mock_ws.get_workspace.return_value = {"project_id": "sample-project", "root_path": "/projects/sample"}
        mock_repo = mock_repo_class.return_value
        mock_repo.get_all_file_paths.return_value = ["/src/UserService.java"]

        self.mock_coord.process.side_effect = RuntimeError("Something crashed inside the pipeline")

        payload = {"project_id": "sample-project", "question": "hello"}
        response = self.client.post("/api/v1/query", json=payload)
        self.assertEqual(response.status_code, 500)
        self.assertIn("Internal Server Error", response.json()["detail"])

    def test_openapi_schema_generation(self):
        response = self.client.get("/openapi.json")
        self.assertEqual(response.status_code, 200)
        schema = response.json()
        self.assertIn("info", schema)
        self.assertIn("paths", schema)
        self.assertIn("/api/v1/query", schema["paths"])
        self.assertIn("/health", schema["paths"])

    # --- Indexing Endpoint Tests ---

    @patch("ecip_core.api.routes.indexing.Path")
    @patch("ecip_core.api.routes.indexing.IndexBuilder")
    @patch("ecip_core.api.routes.indexing.JavaRepository")
    @patch("ecip_core.api.routes.indexing.ProjectScanner")
    def test_indexing_success_flow(self, mock_scanner_class, mock_repo_class, mock_builder_class, mock_path_class):
        mock_path = mock_path_class.return_value
        mock_path.exists.return_value = True
        mock_path.is_dir.return_value = True
        mock_path.resolve.return_value = mock_path

        mock_scanner = mock_scanner_class.return_value
        mock_file = MagicMock()
        mock_file.resolve.return_value = "/projects/sample/UserService.java"
        mock_file.name = "UserService.java"
        mock_scanner.scan.return_value = [mock_file]

        mock_repo = mock_repo_class.return_value
        mock_repo.get_file_hash.return_value = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

        with patch("builtins.open", unittest.mock.mock_open(read_data=b"")):
            response = self.client.post("/api/v1/index", json={"project_path": "/projects/sample", "project_alias": "sample-project"})

        self.assertEqual(response.status_code, 200)
        res_json = response.json()
        self.assertEqual(res_json["status"], "success")
        self.assertEqual(res_json["project_id"], "sample-project")
        self.assertEqual(res_json["files_scanned"], 1)
        self.assertEqual(res_json["files_skipped"], 1)
        self.assertEqual(res_json["files_indexed"], 0)

    def test_indexing_invalid_payload_error(self):
        response = self.client.post("/api/v1/index", json={"project_path": "/projects/sample"})
        self.assertEqual(response.status_code, 422)

        response = self.client.post("/api/v1/index", json={"project_alias": "sample"})
        self.assertEqual(response.status_code, 422)

    def test_indexing_invalid_path_error(self):
        response = self.client.post("/api/v1/index", json={"project_path": "/projects/non-existent-path-abc", "project_alias": "sample"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("does not exist", response.json()["detail"])

    @patch("ecip_core.api.routes.indexing.Path")
    @patch("ecip_core.api.routes.indexing.ProjectScanner")
    def test_indexing_permission_error_mapping_403(self, mock_scanner_class, mock_path_class):
        mock_path = mock_path_class.return_value
        mock_path.exists.return_value = True
        mock_path.is_dir.return_value = True
        mock_path.resolve.return_value = mock_path

        mock_scanner = mock_scanner_class.return_value
        mock_scanner.scan.side_effect = PermissionError("Access denied")

        response = self.client.post("/api/v1/index", json={"project_path": "/projects/sample", "project_alias": "sample"})
        self.assertEqual(response.status_code, 403)
        self.assertIn("Permission Denied", response.json()["detail"])

    @patch("ecip_core.api.routes.indexing.Path")
    @patch("ecip_core.api.routes.indexing.ProjectScanner")
    def test_indexing_pipeline_failure_500(self, mock_scanner_class, mock_path_class):
        mock_path = mock_path_class.return_value
        mock_path.exists.return_value = True
        mock_path.is_dir.return_value = True
        mock_path.resolve.return_value = mock_path

        mock_scanner = mock_scanner_class.return_value
        mock_scanner.scan.side_effect = RuntimeError("Scanner crashed")

        response = self.client.post("/api/v1/index", json={"project_path": "/projects/sample", "project_alias": "sample"})
        self.assertEqual(response.status_code, 500)
        self.assertIn("Failed to scan directory", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()
