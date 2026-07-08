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


class TestProjectAPI(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    @patch("ecip_core.api.routes.projects.JavaRepository")
    def test_list_projects(self, mock_repo_class):
        mock_repo = mock_repo_class.return_value
        mock_repo.get_projects.return_value = [
            {
                "project_id": "sample-project",
                "alias": "sample-project",
                "root_path": "/projects/sample",
                "indexed_at": "2026-07-08T18:00:00Z",
                "indexed_files": 10,
                "total_chunks": 50,
                "total_vectors": 50,
                "status": "active"
            }
        ]

        response = self.client.get("/projects")
        self.assertEqual(response.status_code, 200)
        res_json = response.json()
        self.assertIn("projects", res_json)
        self.assertEqual(len(res_json["projects"]), 1)
        self.assertEqual(res_json["projects"][0]["project_id"], "sample-project")
        self.assertEqual(res_json["projects"][0]["alias"], "sample-project")

    @patch("ecip_core.api.routes.projects.JavaRepository")
    def test_list_projects_empty(self, mock_repo_class):
        mock_repo = mock_repo_class.return_value
        mock_repo.get_projects.return_value = []

        response = self.client.get("/projects")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"projects": []})

    @patch("ecip_core.api.routes.projects.JavaRepository")
    def test_get_project_details_success(self, mock_repo_class):
        mock_repo = mock_repo_class.return_value
        mock_repo.get_project.return_value = {
            "project_id": "sample-project",
            "alias": "sample-project",
            "root_path": "/projects/sample",
            "indexed_at": "2026-07-08T18:00:00Z",
            "indexed_files": 10,
            "total_chunks": 50,
            "total_vectors": 50,
            "status": "active"
        }

        response = self.client.get("/projects/sample-project")
        self.assertEqual(response.status_code, 200)
        res_json = response.json()
        self.assertEqual(res_json["project_id"], "sample-project")
        self.assertEqual(res_json["root_path"], "/projects/sample")

    @patch("ecip_core.api.routes.projects.JavaRepository")
    def test_get_project_details_not_found(self, mock_repo_class):
        mock_repo = mock_repo_class.return_value
        mock_repo.get_project.return_value = None

        response = self.client.get("/projects/wrong-id")
        self.assertEqual(response.status_code, 404)
        self.assertIn("not found", response.json()["detail"])

    @patch("ecip_core.api.routes.projects.shutil.rmtree")
    @patch("ecip_core.api.routes.projects.Path")
    @patch("ecip_core.api.routes.projects.JavaRepository")
    def test_delete_project_success(self, mock_repo_class, mock_path_class, mock_rmtree):
        mock_repo = mock_repo_class.return_value
        mock_repo.get_project.return_value = {
            "project_id": "sample-project",
            "alias": "sample-project",
            "root_path": "/projects/sample",
            "indexed_at": "2026-07-08T18:00:00Z",
            "indexed_files": 10,
            "total_chunks": 50,
            "total_vectors": 50,
            "status": "active"
        }

        mock_path = mock_path_class.return_value
        mock_path.exists.return_value = True
        mock_path.is_dir.return_value = True
        mock_path.__truediv__.return_value = mock_path

        response = self.client.delete("/projects/sample-project")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "success")

        mock_rmtree.assert_called_once_with(mock_path)
        mock_repo.delete_project.assert_called_once_with("sample-project")

    @patch("ecip_core.api.routes.projects.JavaRepository")
    def test_delete_project_not_found(self, mock_repo_class):
        mock_repo = mock_repo_class.return_value
        mock_repo.get_project.return_value = None

        response = self.client.delete("/projects/wrong-id")
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
