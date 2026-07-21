import unittest
from unittest.mock import patch, MagicMock

from ecip_core.providers.graph.neo4j_provider import Neo4jGraphProvider


class TestNeo4jProvider(unittest.TestCase):

    @patch("neo4j.GraphDatabase.driver")
    def test_neo4j_connection(self, mock_driver_fn):
        mock_driver = MagicMock()
        mock_driver_fn.return_value = mock_driver

        provider = Neo4jGraphProvider(
            uri="bolt://localhost:7687",
            username="neo4j",
            password="password"
        )
        provider.connect()
        
        mock_driver_fn.assert_called_once_with(
            "bolt://localhost:7687",
            auth=("neo4j", "password")
        )
        mock_driver.verify_connectivity.assert_called_once()

    @patch("neo4j.GraphDatabase.driver")
    def test_neo4j_create_node(self, mock_driver_fn):
        mock_driver = MagicMock()
        mock_driver_fn.return_value = mock_driver
        mock_session = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session

        provider = Neo4jGraphProvider()
        provider.driver = mock_driver
        
        # Test class label validation and Merging properties
        provider.create_node(
            label="Class",
            properties={"id": "UserService", "project_id": "test_proj", "package": "com.example"}
        )
        
        # Verify run query
        mock_session.run.assert_called_once()
        args, kwargs = mock_session.run.call_args
        self.assertIn("MERGE (n:Class {id: $node_id, project_id: $project_id})", args[0])
        self.assertEqual(kwargs["node_id"], "UserService")
        self.assertEqual(kwargs["project_id"], "test_proj")

        # Test node type validation error
        with self.assertRaises(ValueError):
            provider.create_node("InvalidLabel", {"id": "123"})

    @patch("neo4j.GraphDatabase.driver")
    def test_neo4j_batch_insert_nodes(self, mock_driver_fn):
        mock_driver = MagicMock()
        mock_driver_fn.return_value = mock_driver
        mock_session = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session

        provider = Neo4jGraphProvider()
        provider.driver = mock_driver

        nodes = [
            {"type": "Class", "properties": {"id": "A", "project_id": "test"}},
            {"type": "Class", "properties": {"id": "B", "project_id": "test"}},
            {"type": "Method", "properties": {"id": "C", "project_id": "test"}}
        ]
        provider.batch_insert_nodes(nodes)
        
        # Verify run called twice (once for Class, once for Method)
        self.assertEqual(mock_session.run.call_count, 2)

    @patch("neo4j.GraphDatabase.driver")
    def test_neo4j_batch_insert_relationships(self, mock_driver_fn):
        mock_driver = MagicMock()
        mock_driver_fn.return_value = mock_driver
        mock_session = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session

        provider = Neo4jGraphProvider()
        provider.driver = mock_driver

        relationships = [
            {"source_id": "A", "target_id": "B", "type": "EXTENDS", "properties": {"project_id": "test"}},
            {"source_id": "A", "target_id": "C", "type": "DEPENDS_ON", "properties": {"project_id": "test"}}
        ]
        provider.batch_insert_relationships(relationships)
        
        # Verify run called twice (once for EXTENDS, once for DEPENDS_ON)
        self.assertEqual(mock_session.run.call_count, 2)
