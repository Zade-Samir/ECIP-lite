import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from ecip_core.retrieval.hybrid.hybrid_retrieval_engine import HybridRetrievalEngine
from ecip_core.retrieval.models.hybrid_result import HybridResult
from ecip_core.workspace.manager import workspace_manager
from ecip_core.storage.sqlite.database import Database


class TestHybridSearch(unittest.TestCase):

    def setUp(self):
        conn = Database.get_registry_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM projects WHERE project_id = 'test_hybrid'")
        conn.commit()

        self.temp_dir = tempfile.mkdtemp()
        workspace_manager.register_workspace("test_hybrid", "Test Hybrid", self.temp_dir)
        workspace_manager.set_active_workspace("test_hybrid")
        
        self.mock_semantic_search = MagicMock()

    def tearDown(self):
        workspace_manager.delete_workspace("test_hybrid")
        shutil.rmtree(self.temp_dir)

    def test_hybrid_search_scoring_and_weights(self):
        from ecip_core.search.bm25.bm25 import BM25Index
        bm25_index = BM25Index()
        chunks = [
            {
                "chunk_id": "chunk_1",
                "content": "public class UserService { public void getUser() {} }",
                "file_path": "UserService.java"
            },
            {
                "chunk_id": "chunk_2",
                "content": "public class OrderService { public void getOrder() {} }",
                "file_path": "OrderService.java"
            }
        ]
        bm25_index.fit(chunks)
        ecip_dir = Path(self.temp_dir) / ".ecip"
        ecip_dir.mkdir(exist_ok=True)
        bm25_index.save(str(ecip_dir / "bm25_index.json"))

        self.mock_semantic_search.search.return_value = [
            HybridResult(
                source="semantic",
                score=0.1,  # Small L2 distance (similar)
                chunk_id="chunk_2",
                file_path="OrderService.java",
                class_name="OrderService",
                method_name="getOrder",
                chunk_type="METHOD",
                content="public class OrderService { public void getOrder() {} }",
                start_line=1,
                end_line=5
            ),
            HybridResult(
                source="semantic",
                score=0.9,  # Larger L2 distance
                chunk_id="chunk_1",
                file_path="UserService.java",
                class_name="UserService",
                method_name="getUser",
                chunk_type="METHOD",
                content="public class UserService { public void getUser() {} }",
                start_line=1,
                end_line=5
            )
        ]

        engine = HybridRetrievalEngine(
            self.mock_semantic_search,
            bm25_weight=0.30,
            vector_weight=0.70
        )

        results = engine.retrieve("getOrder", k=2)

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].chunk_id, "chunk_2")
        self.assertGreater(results[0].score, results[1].score)

    def test_missing_bm25_index_graceful_fallback(self):
        self.mock_semantic_search.search.return_value = [
            HybridResult(
                source="semantic",
                score=0.5,
                chunk_id="chunk_1",
                file_path="UserService.java",
                class_name="UserService",
                method_name="getUser",
                chunk_type="METHOD",
                content="class UserService {}",
                start_line=1,
                end_line=5
            )
        ]

        engine = HybridRetrievalEngine(self.mock_semantic_search)
        results = engine.retrieve("UserService", k=1)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].chunk_id, "chunk_1")


if __name__ == "__main__":
    unittest.main()
