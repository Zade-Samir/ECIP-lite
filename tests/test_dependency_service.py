import sqlite3
# Monkey-patch sqlite3 to allow multi-threaded access without thread-ownership errors
original_connect = sqlite3.connect
def custom_connect(*args, **kwargs):
    kwargs["check_same_thread"] = False
    return original_connect(*args, **kwargs)
sqlite3.connect = custom_connect

import unittest
from unittest.mock import patch, MagicMock
from ecip_core.dependency.dependency_service import DependencyQueryService
from ecip_core.dependency.models.relationship import Relationship


class TestDependencyService(unittest.TestCase):

    @patch("ecip_core.dependency.dependency_service.JavaRepository")
    def test_check_class_exists_database(self, mock_repo_class):
        mock_repo = mock_repo_class.return_value
        mock_repo.search_classes.return_value = [{"class_name": "UserService"}]

        service = DependencyQueryService("test-proj")
        exists = service._check_class_exists("test-proj", "UserService")
        self.assertTrue(exists)

    @patch("ecip_core.dependency.dependency_service.JavaRepository")
    def test_get_dependencies_success(self, mock_repo_class):
        mock_repo = mock_repo_class.return_value
        mock_repo.search_classes.return_value = [{"class_name": "UserService"}]
        mock_repo.get_outgoing_edges.return_value = [
            {
                "source_class": "UserService",
                "target_class": "UserRepository",
                "relationship_type": "DEPENDS_ON",
                "discovered_at": "2026-07-08T18:00:00Z"
            }
        ]

        service = DependencyQueryService("test-proj")
        res = service.get_dependencies("UserService")
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0].source_class, "UserService")
        self.assertEqual(res[0].target_class, "UserRepository")
        self.assertEqual(res[0].relationship_type, "DEPENDS_ON")

    @patch("ecip_core.dependency.dependency_service.JavaRepository")
    def test_get_dependents_success(self, mock_repo_class):
        mock_repo = mock_repo_class.return_value
        mock_repo.search_classes.return_value = [{"class_name": "UserService"}]
        mock_repo.get_incoming_edges.return_value = [
            {
                "source_class": "UserController",
                "target_class": "UserService",
                "relationship_type": "DEPENDS_ON",
                "discovered_at": "2026-07-08T18:00:00Z"
            }
        ]

        service = DependencyQueryService("test-proj")
        res = service.get_dependents("UserService")
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0].source_class, "UserController")
        self.assertEqual(res[0].target_class, "UserService")

    @patch("ecip_core.dependency.dependency_service.JavaRepository")
    def test_get_relationships_combined(self, mock_repo_class):
        mock_repo = mock_repo_class.return_value
        mock_repo.search_classes.return_value = [{"class_name": "UserService"}]
        mock_repo.get_all_class_edges.return_value = [
            {
                "source_class": "UserService",
                "target_class": "UserRepository",
                "relationship_type": "DEPENDS_ON",
                "discovered_at": "2026-07-08T18:00:00Z"
            },
            {
                "source_class": "UserController",
                "target_class": "UserService",
                "relationship_type": "DEPENDS_ON",
                "discovered_at": "2026-07-08T18:00:00Z"
            }
        ]

        service = DependencyQueryService("test-proj")
        res = service.get_relationships("UserService")
        self.assertEqual(len(res), 2)
        self.assertEqual(res[0].source_class, "UserController")
        self.assertEqual(res[1].source_class, "UserService")

    @patch("ecip_core.dependency.dependency_service.JavaRepository")
    def test_get_dependency_tree_bfs(self, mock_repo_class):
        mock_repo = mock_repo_class.return_value
        mock_repo.search_classes.return_value = [{"class_name": "UserController"}]
        
        def mock_outgoing(project_id, class_name):
            if class_name == "UserController":
                return [
                    {
                        "source_class": "UserController",
                        "target_class": "UserService",
                        "relationship_type": "DEPENDS_ON",
                        "discovered_at": "2026-07-08T18:00:00Z"
                    }
                ]
            elif class_name == "UserService":
                return [
                    {
                        "source_class": "UserService",
                        "target_class": "UserRepository",
                        "relationship_type": "DEPENDS_ON",
                        "discovered_at": "2026-07-08T18:00:00Z"
                    }
                ]
            return []

        mock_repo.get_outgoing_edges.side_effect = mock_outgoing

        service = DependencyQueryService("test-proj")
        res = service.get_dependency_tree("UserController", depth=2)
        self.assertEqual(len(res), 2)
        self.assertEqual(res[0].source_class, "UserController")
        self.assertEqual(res[0].depth, 1)
        self.assertEqual(res[1].source_class, "UserService")
        self.assertEqual(res[1].depth, 2)

    @patch("ecip_core.dependency.dependency_service.JavaRepository")
    def test_unknown_class_logs_warning(self, mock_repo_class):
        mock_repo = mock_repo_class.return_value
        mock_repo.search_classes.return_value = []
        
        mock_cursor = MagicMock()
        mock_repo.connection.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None

        service = DependencyQueryService("test-proj")
        with self.assertLogs("ecip_core.dependency.dependency_service", level="WARNING") as log_capture:
            res = service.get_dependencies("UnknownClass")
            self.assertEqual(res, [])
            self.assertTrue(any("Unknown class: UnknownClass" in log for log in log_capture.output))

    def test_invalid_depth_raises_value_error(self):
        service = DependencyQueryService("test-proj")
        with self.assertRaises(ValueError):
            service.get_dependency_tree("UserService", depth=0)


if __name__ == "__main__":
    unittest.main()
