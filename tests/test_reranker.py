import unittest
from unittest.mock import MagicMock, patch

from ecip_core.reranking.cross_encoder import CrossEncoderReRanker
from ecip_core.retrieval.models.hybrid_result import HybridResult
from ecip_core.config.loader import settings


class TestReRanker(unittest.TestCase):

    def setUp(self):
        self.candidates = [
            HybridResult(
                source="hybrid",
                score=0.4,
                chunk_id="chunk_a",
                file_path="A.java",
                class_name="A",
                method_name="",
                chunk_type="CLASS_OVERVIEW",
                content="Class A is the main class",
                start_line=1,
                end_line=5
            ),
            HybridResult(
                source="hybrid",
                score=0.6,
                chunk_id="chunk_b",
                file_path="B.java",
                class_name="B",
                method_name="",
                chunk_type="CLASS_OVERVIEW",
                content="Class B handles database persistence",
                start_line=1,
                end_line=5
            )
        ]

    def test_disabled_mode(self):
        with patch.object(settings, "ENABLE_RERANKING", False):
            reranker = CrossEncoderReRanker()
            res = reranker.rerank("database", self.candidates)
            # Should return candidates unchanged when disabled
            self.assertEqual(res, self.candidates)

    def test_low_candidate_count_threshold(self):
        reranker = CrossEncoderReRanker()
        single_candidate = [self.candidates[0]]
        
        # When less than 2 candidates, it should skip re-ranking and return them directly
        res = reranker.rerank("database", single_candidate)
        self.assertEqual(res, single_candidate)

    def test_batch_scoring_and_stable_ranking(self):
        with patch.object(settings, "RERANKING_TOP_K", 1):
            reranker = CrossEncoderReRanker()
            res = reranker.rerank("database", self.candidates)
            self.assertEqual(len(res), 1)
            self.assertEqual(res[0].chunk_id, "chunk_b")
            self.assertGreater(res[0].score, 0.0)

    def test_deterministic_tie_breaking(self):
        reranker = CrossEncoderReRanker()
        # Query that doesn't match either candidate word, making scores equal (0.0)
        res = reranker.rerank("unmatchedquery", self.candidates)
        
        # Under tie scores, it must sort alphabetically by chunk_id
        self.assertEqual(res[0].chunk_id, "chunk_a")
        self.assertEqual(res[1].chunk_id, "chunk_b")

    def test_empty_candidates(self):
        reranker = CrossEncoderReRanker()
        res = reranker.rerank("query", [])
        self.assertEqual(res, [])


if __name__ == "__main__":
    unittest.main()
