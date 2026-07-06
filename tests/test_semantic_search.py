import unittest
from unittest.mock import MagicMock, patch
from ecip_core.retrieval.semantic_search import SemanticSearch
from ecip_core.retrieval.models.search_result import SearchResult
from ecip_core.embedding.embedding_service import EmbeddingService
from ecip_core.vectorstore.faiss_store import FAISSStore
from ecip_core.embedding.models.embedding import Embedding


class TestSemanticSearch(unittest.TestCase):

    def setUp(self):
        self.mock_embedding_service = MagicMock(spec=EmbeddingService)
        self.mock_faiss_store = MagicMock(spec=FAISSStore)
        self.mock_faiss_store.dimension = 768

        self.search_service = SemanticSearch(
            embedding_service=self.mock_embedding_service,
            faiss_store=self.mock_faiss_store
        )

    def test_search_empty_query(self):
        self.assertEqual(self.search_service.search(""), [])
        self.assertEqual(self.search_service.search("   "), [])
        self.mock_embedding_service.embed_question.assert_not_called()

    def test_search_happy_path(self):
        query = "How is user validated?"
        query_vector = [0.1] * 768
        self.mock_embedding_service.embed_question.return_value = query_vector

        mock_embedding = Embedding(
            file_name="UserValidator.java",
            class_name="UserValidator",
            method_name="validate",
            source_code="public boolean validate(User u) { return true; }",
            vector=[0.2] * 768,
            chunk_id="chunk_123",
            file_path="/src/UserValidator.java",
            chunk_type="METHOD",
            start_line=10,
            end_line=15
        )
        self.mock_faiss_store.search_with_scores.return_value = [(mock_embedding, 0.5)]

        results = self.search_service.search(query, k=1)
        self.assertEqual(len(results), 1)
        res = results[0]

        self.assertEqual(res.chunk_id, "chunk_123")
        self.assertEqual(res.file_path, "/src/UserValidator.java")
        self.assertEqual(res.class_name, "UserValidator")
        self.assertEqual(res.method_name, "validate")
        self.assertEqual(res.chunk_type, "METHOD")
        self.assertEqual(res.start_line, 10)
        self.assertEqual(res.end_line, 15)
        self.assertEqual(res.content, "public boolean validate(User u) { return true; }")

        # Score calculation: 1.0 - (0.5 / 2.0) = 0.75
        self.assertAlmostEqual(res.score, 0.75)

        self.mock_embedding_service.embed_question.assert_called_once_with(query)
        self.mock_faiss_store.search_with_scores.assert_called_once_with(query_vector, 1)

    def test_search_dimension_validation(self):
        self.mock_embedding_service.embed_question.return_value = [0.1] * 384

        with self.assertRaises(ValueError):
            self.search_service.search("hello")

    def test_search_low_confidence_and_empty_warnings(self):
        # 1. No matches found
        self.mock_embedding_service.embed_question.return_value = [0.1] * 768
        self.mock_faiss_store.search_with_scores.return_value = []

        with self.assertLogs("ecip_core.retrieval.semantic_search", level="WARNING") as log_capture:
            results = self.search_service.search("hello")
            self.assertEqual(results, [])
            self.assertTrue(any("No semantic matches" in log for log in log_capture.output))

        # 2. Low confidence result (distance 1.8 => score 1.0 - 0.9 = 0.1 < 0.3)
        mock_embedding = Embedding(
            file_name="UserValidator.java",
            class_name="UserValidator",
            method_name="validate",
            source_code="some code",
            vector=[0.2] * 768
        )
        self.mock_faiss_store.search_with_scores.return_value = [(mock_embedding, 1.8)]

        with self.assertLogs("ecip_core.retrieval.semantic_search", level="WARNING") as log_capture:
            results = self.search_service.search("hello")
            self.assertEqual(len(results), 1)
            self.assertTrue(any("Low confidence results" in log for log in log_capture.output))

    def test_deterministic_score_and_id_ordering(self):
        self.mock_embedding_service.embed_question.return_value = [0.1] * 768

        emb1 = Embedding(file_name="A.java", class_name="A", method_name="m1", source_code="c1", vector=[], chunk_id="chunk_a")
        emb2 = Embedding(file_name="B.java", class_name="B", method_name="m2", source_code="c2", vector=[], chunk_id="chunk_b")
        emb3 = Embedding(file_name="C.java", class_name="C", method_name="m3", source_code="c3", vector=[], chunk_id="chunk_c")

        self.mock_faiss_store.search_with_scores.return_value = [
            (emb2, 0.4),
            (emb1, 0.4),
            (emb3, 0.2)
        ]

        results = self.search_service.search("query")

        # Expected Rank:
        # 1. chunk_c (score 0.9)
        # 2. chunk_a (score 0.8, tie-breaker chunk_id alphabetically first)
        # 3. chunk_b (score 0.8, tie-breaker chunk_id alphabetically second)
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0].chunk_id, "chunk_c")
        self.assertEqual(results[1].chunk_id, "chunk_a")
        self.assertEqual(results[2].chunk_id, "chunk_b")

    def test_search_result_serialization(self):
        res = SearchResult(
            score=0.9,
            chunk_id="chunk_xyz",
            file_path="/src/User.java",
            class_name="User",
            method_name="getName",
            chunk_type="METHOD",
            start_line=20,
            end_line=25,
            content="public String getName() { return name; }"
        )

        serialized = res.model_dump()
        self.assertEqual(serialized["score"], 0.9)
        self.assertEqual(serialized["chunk_id"], "chunk_xyz")
        self.assertEqual(serialized["file_path"], "/src/User.java")
        self.assertEqual(serialized["class_name"], "User")


if __name__ == "__main__":
    unittest.main()
