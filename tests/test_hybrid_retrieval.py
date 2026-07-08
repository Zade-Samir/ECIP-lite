import unittest
from unittest.mock import MagicMock
from ecip_core.retrieval.hybrid_retrieval import HybridRetrieval
from ecip_core.retrieval.models.hybrid_result import HybridResult
from ecip_core.retrieval.models.search_result import SearchResult
from ecip_core.retrieval.models.metadata_result import MetadataResult
from ecip_core.retrieval.metadata.metadata_service import MetadataSearchService
from ecip_core.retrieval.semantic_search import SemanticSearch


class TestHybridRetrieval(unittest.TestCase):

    def setUp(self):
        self.mock_metadata_service = MagicMock(spec=MetadataSearchService)
        self.mock_semantic_search = MagicMock(spec=SemanticSearch)

        self.retriever = HybridRetrieval(
            metadata_service=self.mock_metadata_service,
            semantic_search=self.mock_semantic_search
        )

    def test_retrieve_empty_query(self):
        self.assertEqual(self.retriever.retrieve(""), [])
        self.assertEqual(self.retriever.retrieve("   "), [])
        self.mock_metadata_service.search_classes.assert_not_called()
        self.mock_semantic_search.search.assert_not_called()

    def test_metadata_first_ranking_priority(self):
        # 1. Mock Metadata Search hits (method, class, package)
        # Tier 1 (Method match)
        self.mock_metadata_service.search_methods.return_value = [
            MetadataResult(
                project_id="test",
                chunk_id="chunk_method",
                file_path="/src/UserService.java",
                package_name="com.example.service",
                class_name="UserService",
                method_name="getUser",
                signature="public User getUser()",
                start_line=10,
                end_line=15,
                source_reference="public User getUser() { }"
            )
        ]
        # Tier 2 (Class match)
        self.mock_metadata_service.search_classes.return_value = [
            MetadataResult(
                project_id="test",
                chunk_id="chunk_class",
                file_path="/src/UserService.java",
                package_name="com.example.service",
                class_name="UserService",
                method_name="",
                signature="public class UserService",
                start_line=1,
                end_line=50,
                source_reference="public class UserService { }"
            )
        ]
        self.mock_metadata_service.search_packages.return_value = []
        self.mock_metadata_service.search_file_paths.return_value = []

        # 2. Mock Semantic Search hits (which have higher semantic score, e.g. 0.95, but should rank below metadata)
        self.mock_semantic_search.search.return_value = [
            SearchResult(
                score=0.95,
                chunk_id="chunk_semantic",
                file_path="/src/OtherService.java",
                class_name="OtherService",
                method_name="doSomething",
                chunk_type="METHOD",
                start_line=20,
                end_line=25,
                content="public void doSomething() { }"
            )
        ]

        results = self.retriever.retrieve("Explain UserService getUser", k=5)

        # Expected output ranking:
        # 1. Exact method match (tier=1, score=1.0)
        # 2. Exact class match (tier=2, score=0.9)
        # 3. Semantic match (tier=4, score=0.95)
        self.assertEqual(len(results), 3)

        self.assertEqual(results[0].chunk_id, "chunk_method")
        self.assertEqual(results[0].source, "metadata")
        self.assertEqual(results[0].score, 1.0)

        self.assertEqual(results[1].chunk_id, "chunk_class")
        self.assertEqual(results[1].source, "metadata")
        self.assertEqual(results[1].score, 0.9)

        self.assertEqual(results[2].chunk_id, "chunk_semantic")
        self.assertEqual(results[2].source, "semantic")
        self.assertEqual(results[2].score, 0.95)

    def test_semantic_fallback_only(self):
        # When no metadata matches exist, semantic hits should be returned directly
        self.mock_metadata_service.search_methods.return_value = []
        self.mock_metadata_service.search_classes.return_value = []
        self.mock_metadata_service.search_packages.return_value = []
        self.mock_metadata_service.search_file_paths.return_value = []

        self.mock_semantic_search.search.return_value = [
            SearchResult(
                score=0.85,
                chunk_id="chunk_sem1",
                file_path="/src/A.java",
                class_name="A",
                method_name="m1",
                chunk_type="METHOD",
                start_line=1,
                end_line=5,
                content="void m1() {}"
            )
        ]

        results = self.retriever.retrieve("some query")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].chunk_id, "chunk_sem1")
        self.assertEqual(results[0].source, "semantic")

    def test_duplicate_removal_prefer_metadata(self):
        # Setup duplicate results in both searches
        # Metadata exact class match
        self.mock_metadata_service.search_classes.return_value = [
            MetadataResult(
                project_id="test",
                chunk_id="chunk_dup",
                file_path="/src/A.java",
                package_name="com.a",
                class_name="A",
                method_name="",
                signature="class A",
                start_line=1,
                end_line=10,
                source_reference="class A {}"
            )
        ]
        self.mock_metadata_service.search_methods.return_value = []
        self.mock_metadata_service.search_packages.return_value = []
        self.mock_metadata_service.search_file_paths.return_value = []

        # Semantic returns the same class chunk
        self.mock_semantic_search.search.return_value = [
            SearchResult(
                score=0.75,
                chunk_id="chunk_dup",
                file_path="/src/A.java",
                class_name="A",
                method_name="",
                chunk_type="CLASS_OVERVIEW",
                start_line=1,
                end_line=10,
                content="class A {}"
            )
        ]

        results = self.retriever.retrieve("class A")
        
        # Deduplication must yield exactly 1 result with source="metadata"
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].source, "metadata")
        self.assertEqual(results[0].score, 0.9)  # Class match tier score

    def test_stable_tie_breaker_ordering(self):
        self.mock_metadata_service.search_methods.return_value = []
        self.mock_metadata_service.search_classes.return_value = []
        self.mock_metadata_service.search_packages.return_value = []
        self.mock_metadata_service.search_file_paths.return_value = []

        # Return semantic hits with identical scores
        self.mock_semantic_search.search.return_value = [
            SearchResult(
                score=0.8,
                chunk_id="chunk_c",
                file_path="/src/C.java",
                class_name="C",
                method_name="m",
                chunk_type="METHOD",
                start_line=1,
                end_line=2,
                content="void m() {}"
            ),
            SearchResult(
                score=0.8,
                chunk_id="chunk_a",
                file_path="/src/A.java",
                class_name="A",
                method_name="m",
                chunk_type="METHOD",
                start_line=1,
                end_line=2,
                content="void m() {}"
            )
        ]

        results = self.retriever.retrieve("query")
        self.assertEqual(len(results), 2)
        # Should be sorted alphabetically by chunk_id on score tie: chunk_a then chunk_c
        self.assertEqual(results[0].chunk_id, "chunk_a")
        self.assertEqual(results[1].chunk_id, "chunk_c")

    def test_error_handling_fails_gracefully(self):
        # Exception in metadata search should log error but not crash the entire flow if semantic search succeeds
        self.mock_metadata_service.search_classes.side_effect = Exception("db crash")
        self.mock_metadata_service.search_methods.return_value = []
        self.mock_metadata_service.search_packages.return_value = []
        self.mock_metadata_service.search_file_paths.return_value = []

        self.mock_semantic_search.search.return_value = [
            SearchResult(
                score=0.8,
                chunk_id="chunk_s",
                file_path="/src/S.java",
                class_name="S",
                method_name="m",
                chunk_type="METHOD",
                start_line=1,
                end_line=2,
                content="void m() {}"
            )
        ]

        results = self.retriever.retrieve("S")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].chunk_id, "chunk_s")

    def test_hybrid_result_serialization(self):
        res = HybridResult(
            source="metadata",
            score=1.0,
            chunk_id="chunk_1",
            file_path="/src/A.java",
            class_name="A",
            method_name="m",
            chunk_type="METHOD",
            content="void m() {}",
            start_line=10,
            end_line=12
        )
        serialized = res.model_dump()
        self.assertEqual(serialized["source"], "metadata")
        self.assertEqual(serialized["score"], 1.0)
        self.assertEqual(serialized["chunk_id"], "chunk_1")


if __name__ == "__main__":
    unittest.main()
