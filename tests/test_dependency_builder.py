import sqlite3
# Monkey-patch sqlite3 to allow multi-threaded access without thread-ownership errors
original_connect = sqlite3.connect
def custom_connect(*args, **kwargs):
    kwargs["check_same_thread"] = False
    return original_connect(*args, **kwargs)
sqlite3.connect = custom_connect

import unittest
from unittest.mock import patch, MagicMock
from ecip_core.dependency.graph_builder import DependencyGraphBuilder
from ecip_core.parser.models.parsed_java_file import ParsedJavaFile
from ecip_core.parser.models.constructor_info import ConstructorInfo
from ecip_core.parser.models.dependency_metadata import DependencyMetadata
from ecip_core.storage.sqlite.repository import JavaRepository


class TestDependencyBuilder(unittest.TestCase):

    def setUp(self):
        self.builder = DependencyGraphBuilder()
        self.builder.repository.delete_class_edges("test-proj", "UserService")
        self.builder.repository.delete_class_edges("test-proj", "UserController")

    def test_implements_relationship_extraction(self):
        parsed = ParsedJavaFile(
            file_name="UserService.java",
            file_path="/src/UserService.java",
            package_name="com.example",
            class_name="UserService",
            implemented_interfaces=["BaseService"],
            interfaces=[]
        )

        project_classes = {"UserService", "BaseService"}

        with self.assertLogs("ecip_core.dependency.graph_builder", level="INFO") as log_capture:
            self.builder.build_class_edges("test-proj", parsed, project_classes)
            self.assertTrue(any("Edge created: UserService -> IMPLEMENTS -> BaseService" in log for log in log_capture.output))

        edges = self.builder.repository.get_edges("test-proj")
        implements_edges = [e for e in edges if e["relationship_type"] == "IMPLEMENTS"]
        self.assertEqual(len(implements_edges), 1)
        self.assertEqual(implements_edges[0]["source_class"], "UserService")
        self.assertEqual(implements_edges[0]["target_class"], "BaseService")

    def test_extends_relationship_extraction(self):
        parsed = ParsedJavaFile(
            file_name="UserController.java",
            file_path="/src/UserController.java",
            package_name="com.example",
            class_name="UserController",
            superclass="BaseController"
        )

        project_classes = {"UserController", "BaseController"}

        with self.assertLogs("ecip_core.dependency.graph_builder", level="INFO") as log_capture:
            self.builder.build_class_edges("test-proj", parsed, project_classes)
            self.assertTrue(any("Edge created: UserController -> EXTENDS -> BaseController" in log for log in log_capture.output))

        edges = self.builder.repository.get_edges("test-proj")
        extends_edges = [e for e in edges if e["relationship_type"] == "EXTENDS"]
        self.assertEqual(len(extends_edges), 1)
        self.assertEqual(extends_edges[0]["source_class"], "UserController")
        self.assertEqual(extends_edges[0]["target_class"], "BaseController")

    def test_constructor_injection_depends_on_extraction(self):
        parsed = ParsedJavaFile(
            file_name="UserService.java",
            file_path="/src/UserService.java",
            package_name="com.example",
            class_name="UserService",
            constructors=[
                ConstructorInfo(
                    injected_dependency_types=["UserRepository"]
                )
            ]
        )

        project_classes = {"UserService", "UserRepository"}

        self.builder.build_class_edges("test-proj", parsed, project_classes)

        edges = self.builder.repository.get_edges("test-proj")
        depends_edges = [e for e in edges if e["relationship_type"] == "DEPENDS_ON"]
        self.assertEqual(len(depends_edges), 1)
        self.assertEqual(depends_edges[0]["source_class"], "UserService")
        self.assertEqual(depends_edges[0]["target_class"], "UserRepository")

    def test_dependency_metadata_injection_depends_on_extraction(self):
        parsed = ParsedJavaFile(
            file_name="UserService.java",
            file_path="/src/UserService.java",
            package_name="com.example",
            class_name="UserService",
            dependencies=[
                DependencyMetadata(
                    source_class="UserService",
                    target_class="UserRepository",
                    injection_type="CONSTRUCTOR"
                )
            ]
        )

        project_classes = {"UserService", "UserRepository"}

        self.builder.build_class_edges("test-proj", parsed, project_classes)

        edges = self.builder.repository.get_edges("test-proj")
        depends_edges = [e for e in edges if e["relationship_type"] == "DEPENDS_ON"]
        self.assertEqual(len(depends_edges), 1)
        self.assertEqual(depends_edges[0]["target_class"], "UserRepository")

    def test_external_library_unresolved_ignored(self):
        parsed = ParsedJavaFile(
            file_name="UserService.java",
            file_path="/src/UserService.java",
            class_name="UserService",
            superclass="SpringService",
            implemented_interfaces=["Serializable"]
        )

        project_classes = {"UserService"}

        with self.assertLogs("ecip_core.dependency.graph_builder", level="WARNING") as log_capture:
            self.builder.build_class_edges("test-proj", parsed, project_classes)
            self.assertTrue(any("Unresolved dependency: SpringService" in log for log in log_capture.output))
            self.assertTrue(any("Unresolved dependency: Serializable" in log for log in log_capture.output))

        edges = self.builder.repository.get_edges("test-proj")
        self.assertEqual(len(edges), 0)

    def test_self_dependency_ignored(self):
        parsed = ParsedJavaFile(
            file_name="UserService.java",
            file_path="/src/UserService.java",
            class_name="UserService",
            superclass="UserService"
        )

        project_classes = {"UserService"}

        self.builder.build_class_edges("test-proj", parsed, project_classes)
        edges = self.builder.repository.get_edges("test-proj")
        self.assertEqual(len(edges), 0)

    def test_duplicate_prevention_logging(self):
        self.builder.repository.save_edge("test-proj", "UserService", "UserRepository", "DEPENDS_ON")

        parsed = ParsedJavaFile(
            file_name="UserService.java",
            file_path="/src/UserService.java",
            class_name="UserService",
            constructors=[
                ConstructorInfo(
                    injected_dependency_types=["UserRepository"]
                )
            ]
        )
        project_classes = {"UserService", "UserRepository"}

        self.builder.build_class_edges("test-proj", parsed, project_classes)

        with patch.object(self.builder.repository, "save_edge", return_value=False):
            with self.assertLogs("ecip_core.dependency.graph_builder", level="WARNING") as log_capture:
                self.builder.build_class_edges("test-proj", parsed, project_classes)
                self.assertTrue(any("Duplicate edge skipped" in log for log in log_capture.output))

    def test_get_stats(self):
        self.builder.repository.delete_class_edges("test-proj", "UserService")
        self.builder.repository.save_edge("test-proj", "UserService", "UserRepository", "DEPENDS_ON")
        stats = self.builder.get_stats("test-proj")
        self.assertGreaterEqual(stats["total_edges"], 1)


if __name__ == "__main__":
    unittest.main()
