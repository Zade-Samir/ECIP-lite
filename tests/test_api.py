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
        # Override FastAPI dependency injection resolver
        app.dependency_overrides[get_coordinator] = lambda: self.mock_coord

    def tearDown(self):
        # Clear overrides to prevent cross-test contamination
        app.dependency_overrides.clear()

    @patch("ecip_core.api.routes.query.JavaRepository")
    def test_query_success_flow(self, mock_repo_class):
        mock_repo = mock_repo_class.return_value
        mock_repo.get_all_file_paths.return_value = ["/src/UserService.java"]

        self.mock_coord.process.return_value = CoordinatorResponse(
            answer="Here is the class UserService.",
            model="qwen3.5:9b",
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

        response = self.client.post("/query", json=payload)
        self.assertEqual(response.status_code, 200)

        res_json = response.json()
        self.assertEqual(res_json["answer"], "Here is the class UserService.")
        self.assertEqual(res_json["model_name"], "qwen3.5:9b")
        self.assertEqual(len(res_json["citations"]), 1)
        self.assertEqual(res_json["citations"][0]["file_path"], "/src/UserService.java")
        self.assertIn("duration_ms", res_json)

    def test_invalid_payload_validation_error(self):
        response = self.client.post("/query", json={"question": "hello"})
        self.assertEqual(response.status_code, 422)

        response = self.client.post("/query", json={"project_id": "default"})
        self.assertEqual(response.status_code, 422)

    @patch("ecip_core.api.routes.query.JavaRepository")
    def test_missing_project_not_found_404(self, mock_repo_class):
        response = self.client.post("/query", json={"project_id": "wrong-proj", "question": "hello"})
        self.assertEqual(response.status_code, 404)

        mock_repo = mock_repo_class.return_value
        mock_repo.get_all_file_paths.return_value = []

        response = self.client.post("/query", json={"project_id": "sample-project", "question": "hello"})
        self.assertEqual(response.status_code, 404)
        self.assertIn("No indexed project", response.json()["detail"])

    @patch("ecip_core.api.routes.query.JavaRepository")
    def test_provider_unavailable_503_error(self, mock_repo_class):
        mock_repo = mock_repo_class.return_value
        mock_repo.get_all_file_paths.return_value = ["/src/UserService.java"]

        self.mock_coord.process.side_effect = ConnectionError("Ollama is offline")

        payload = {"project_id": "sample-project", "question": "hello"}
        response = self.client.post("/query", json=payload)
        self.assertEqual(response.status_code, 503)
        self.assertIn("Inference Provider Unavailable", response.json()["detail"])

    @patch("ecip_core.api.routes.query.JavaRepository")
    def test_unexpected_error_500_mapping(self, mock_repo_class):
        mock_repo = mock_repo_class.return_value
        mock_repo.get_all_file_paths.return_value = ["/src/UserService.java"]

        self.mock_coord.process.side_effect = RuntimeError("Something crashed inside the pipeline")

        payload = {"project_id": "sample-project", "question": "hello"}
        response = self.client.post("/query", json=payload)
        self.assertEqual(response.status_code, 500)
        self.assertIn("Internal Server Error", response.json()["detail"])

    def test_openapi_schema_generation(self):
        response = self.client.get("/openapi.json")
        self.assertEqual(response.status_code, 200)
        schema = response.json()
        self.assertIn("info", schema)
        self.assertIn("paths", schema)
        self.assertIn("/query", schema["paths"])
        self.assertIn("/health", schema["paths"])


if __name__ == "__main__":
    unittest.main()
