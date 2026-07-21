import unittest
from unittest.mock import patch, MagicMock

from ecip_core.config.loader import settings
from ecip_core.graph.factory import get_graph_provider, _sqlite_provider_var, _neo4j_provider_var
from ecip_core.providers.graph.sqlite_provider import SqliteGraphProvider
from ecip_core.providers.graph.neo4j_provider import Neo4jGraphProvider


class TestGraphProvider(unittest.TestCase):

    def setUp(self):
        # Reset ContextVar caches before each test case
        _sqlite_provider_var.set(None)
        _neo4j_provider_var.set(None)

    def test_sqlite_provider_default(self):
        with patch.object(settings, "GRAPH_PROVIDER", "sqlite"):
            provider = get_graph_provider()
            self.assertIsInstance(provider, SqliteGraphProvider)

    def test_neo4j_provider_loading(self):
        with patch.object(settings, "GRAPH_PROVIDER", "neo4j"):
            with patch("ecip_core.providers.graph.neo4j_provider.Neo4jGraphProvider.connect") as mock_connect:
                provider = get_graph_provider()
                self.assertIsInstance(provider, Neo4jGraphProvider)
                mock_connect.assert_called_once()
