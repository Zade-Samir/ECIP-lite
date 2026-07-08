import sqlite3
original_connect = sqlite3.connect
def custom_connect(*args, **kwargs):
    kwargs["check_same_thread"] = False
    return original_connect(*args, **kwargs)
sqlite3.connect = custom_connect

import unittest
from ecip_core.citations.citation_engine import CitationEngine
from ecip_core.citations.models.citation import Citation
from ecip_core.retrieval.models.hybrid_result import HybridResult


def make_chunk(
    chunk_id="chunk_1",
    file_path="/src/UserService.java",
    class_name="UserService",
    method_name="getUser",
    start_line=10,
    end_line=30,
    score=0.95,
    source="semantic"
) -> HybridResult:
    return HybridResult(
        source=source,
        score=score,
        chunk_id=chunk_id,
        file_path=file_path,
        class_name=class_name,
        method_name=method_name,
        chunk_type="method",
        content="public User getUser() {}",
        start_line=start_line,
        end_line=end_line
    )


class TestCitationEngine(unittest.TestCase):

    def setUp(self):
        self.engine = CitationEngine()

    # ─── Citation generation ──────────────────────────────────────────────

    def test_generate_single_citation(self):
        chunks = [make_chunk()]
        citations = self.engine.generate(chunks, project_id="test-proj")

        self.assertEqual(len(citations), 1)
        self.assertIsInstance(citations[0], Citation)
        self.assertEqual(citations[0].file_path, "/src/UserService.java")
        self.assertEqual(citations[0].class_name, "UserService")
        self.assertEqual(citations[0].start_line, 10)
        self.assertEqual(citations[0].end_line, 30)
        self.assertEqual(citations[0].confidence, 0.95)
        self.assertEqual(citations[0].project_id, "test-proj")

    def test_generate_empty_chunks_returns_empty(self):
        citations = self.engine.generate([], project_id="test-proj")
        self.assertEqual(citations, [])

    def test_generate_multiple_citations(self):
        chunks = [
            make_chunk(chunk_id="chunk_1", file_path="/src/A.java", start_line=1, end_line=10),
            make_chunk(chunk_id="chunk_2", file_path="/src/B.java", start_line=5, end_line=20),
        ]
        citations = self.engine.generate(chunks, project_id="test-proj")
        self.assertEqual(len(citations), 2)

    # ─── Duplicate removal ────────────────────────────────────────────────

    def test_duplicate_chunk_ids_removed(self):
        chunks = [
            make_chunk(chunk_id="chunk_1"),
            make_chunk(chunk_id="chunk_1"),  # duplicate
            make_chunk(chunk_id="chunk_2"),
        ]
        with self.assertLogs("ecip_core.citations.citation_engine", level="WARNING") as log:
            citations = self.engine.generate(chunks, project_id="test-proj")
            self.assertTrue(any("Duplicate citation removed" in m for m in log.output))

        self.assertEqual(len(citations), 2)
        chunk_ids = [c.chunk_id for c in citations]
        self.assertEqual(chunk_ids.count("chunk_1"), 1)

    def test_first_occurrence_preserved_on_dedup(self):
        """First occurrence of a duplicate must be kept, not the second."""
        chunks = [
            make_chunk(chunk_id="chunk_1", score=0.9, start_line=1),
            make_chunk(chunk_id="chunk_1", score=0.5, start_line=1),
        ]
        citations = self.engine.generate(chunks, project_id="test-proj")
        self.assertEqual(len(citations), 1)
        self.assertAlmostEqual(citations[0].confidence, 0.9)

    # ─── Deterministic ordering ───────────────────────────────────────────

    def test_citations_sorted_by_file_then_line(self):
        chunks = [
            make_chunk(chunk_id="c3", file_path="/src/Z.java",  start_line=1,  end_line=5),
            make_chunk(chunk_id="c1", file_path="/src/A.java",  start_line=50, end_line=60),
            make_chunk(chunk_id="c2", file_path="/src/A.java",  start_line=10, end_line=20),
        ]
        citations = self.engine.generate(chunks, project_id="test-proj")
        self.assertEqual(citations[0].file_path, "/src/A.java")
        self.assertEqual(citations[0].start_line, 10)
        self.assertEqual(citations[1].file_path, "/src/A.java")
        self.assertEqual(citations[1].start_line, 50)
        self.assertEqual(citations[2].file_path, "/src/Z.java")

    # ─── Validation ───────────────────────────────────────────────────────

    def test_invalid_file_path_excluded(self):
        chunks = [
            make_chunk(chunk_id="c1", file_path=""),
            make_chunk(chunk_id="c2", file_path="/src/Valid.java"),
        ]
        with self.assertLogs("ecip_core.citations.citation_engine", level="ERROR") as log:
            citations = self.engine.generate(chunks, project_id="test-proj")
            self.assertTrue(any("Invalid file path" in m for m in log.output))

        self.assertEqual(len(citations), 1)
        self.assertEqual(citations[0].chunk_id, "c2")

    def test_invalid_line_range_excluded(self):
        """start_line > end_line should be rejected."""
        # Pydantic HybridResult will accept this, CitationEngine must reject it
        chunk = make_chunk(chunk_id="c1", start_line=50, end_line=10)
        with self.assertLogs("ecip_core.citations.citation_engine", level="ERROR") as log:
            citations = self.engine.generate([chunk], project_id="test-proj")
            self.assertTrue(any("Invalid line range" in m for m in log.output))

        self.assertEqual(len(citations), 0)

    def test_valid_citation_logged(self):
        chunks = [make_chunk()]
        with self.assertLogs("ecip_core.citations.citation_engine", level="INFO") as log:
            self.engine.generate(chunks, project_id="test-proj")
            self.assertTrue(any("Citation validated" in m for m in log.output))

    def test_confidence_clamped_to_1(self):
        """Score > 1.0 should be clamped to 1.0."""
        chunk = make_chunk(score=1.5)
        citations = self.engine.generate([chunk], project_id="test-proj")
        self.assertEqual(citations[0].confidence, 1.0)

    def test_confidence_clamped_to_0(self):
        """Negative score should be clamped to 0.0."""
        chunk = make_chunk(score=-0.3)
        citations = self.engine.generate([chunk], project_id="test-proj")
        self.assertEqual(citations[0].confidence, 0.0)

    # ─── Serialization ────────────────────────────────────────────────────

    def test_citation_serialization(self):
        chunks = [make_chunk()]
        citations = self.engine.generate(chunks, project_id="test-proj")
        dumped = citations[0].model_dump()

        self.assertIn("project_id", dumped)
        self.assertIn("file_path", dumped)
        self.assertIn("class_name", dumped)
        self.assertIn("method_name", dumped)
        self.assertIn("start_line", dumped)
        self.assertIn("end_line", dumped)
        self.assertIn("chunk_id", dumped)
        self.assertIn("confidence", dumped)


if __name__ == "__main__":
    unittest.main()
