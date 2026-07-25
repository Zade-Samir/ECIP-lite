import unittest
from unittest.mock import MagicMock, patch
from ecip_core.graph.synchronization.synchronizer import GraphSynchronizer
from ecip_core.parser.models.parsed_java_file import ParsedJavaFile
from ecip_core.parser.models.method_info import MethodInfo


class TestGraphSync(unittest.TestCase):

    def setUp(self):
        self.mock_provider = MagicMock()
        # Mock class name so it is detected as Neo4jGraphProvider to build Cypher
        self.mock_provider.__class__.__name__ = "Neo4jGraphProvider"
        self.synchronizer = GraphSynchronizer(provider=self.mock_provider)

    def test_sync_class_basic(self):
        parsed = ParsedJavaFile(
            file_name="UserService.java",
            file_path="/src/UserService.java",
            package_name="com.example",
            class_name="UserService",
            methods=[
                MethodInfo(name="getUser", return_type="User", parameters=["String id"], start_line=10, end_line=20)
            ]
        )

        self.synchronizer.sync_class("test_project", parsed)

        # Verify execute_transaction was called
        self.mock_provider.execute_transaction.assert_called_once()
        queries = self.mock_provider.execute_transaction.call_args[0][0]

        # Verify queries contents
        self.assertTrue(any("MERGE (p:Project" in q[0] for q in queries))
        self.assertTrue(any("MERGE (pkg:Package" in q[0] for q in queries))
        self.assertTrue(any("MERGE (c:Class" in q[0] for q in queries))
        self.assertTrue(any("DETACH DELETE m" in q[0] for q in queries))
        self.assertTrue(any("MERGE (m:Method" in q[0] for q in queries))
        self.assertTrue(any("MERGE (c)-[:HAS_METHOD]->(m)" in q[0] for q in queries))

    def test_delete_class(self):
        self.synchronizer.delete_class("test_project", "UserService")

        # Verify execute_transaction was called
        self.mock_provider.execute_transaction.assert_called_once()
        queries = self.mock_provider.execute_transaction.call_args[0][0]

        # Verify method cleaning queries
        self.assertTrue(any("DETACH DELETE m" in q[0] for q in queries))
        self.assertTrue(any("DETACH DELETE c" in q[0] for q in queries))

    def test_retry_behavior_success_after_failure(self):
        calls = []
        def side_effect(*args, **kwargs):
            calls.append(1)
            if len(calls) == 1:
                raise RuntimeError("Network Timeout")
            return None

        self.mock_provider.execute_transaction.side_effect = side_effect

        queries = [("CREATE (n)", {})]
        with patch("time.sleep") as mock_sleep:
            self.synchronizer.execute_with_retry(queries, max_retries=3, initial_delay=0.1)
            self.assertEqual(len(calls), 2)
            mock_sleep.assert_called_once_with(0.1)

    def test_retry_behavior_failure_all_attempts(self):
        self.mock_provider.execute_transaction.side_effect = RuntimeError("Database Locked")

        queries = [("CREATE (n)", {})]
        with patch("time.sleep") as mock_sleep:
            with self.assertRaises(RuntimeError):
                self.synchronizer.execute_with_retry(queries, max_retries=3, initial_delay=0.1)
            self.assertEqual(self.mock_provider.execute_transaction.call_count, 3)
            self.assertEqual(mock_sleep.call_count, 3)

    def test_transaction_rollback_handled(self):
        self.mock_provider.execute_transaction.side_effect = RuntimeError("Fatal DB Error")
        with patch("time.sleep"):
            with self.assertRaises(RuntimeError) as context:
                self.synchronizer.execute_with_retry([("Q", {})])
            self.assertEqual(str(context.exception), "Fatal DB Error")


if __name__ == "__main__":
    unittest.main()
