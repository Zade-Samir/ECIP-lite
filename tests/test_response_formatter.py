import sqlite3
original_connect = sqlite3.connect
def custom_connect(*args, **kwargs):
    kwargs["check_same_thread"] = False
    return original_connect(*args, **kwargs)
sqlite3.connect = custom_connect

import unittest
from ecip_core.output.response_formatter import ResponseFormatter
from ecip_core.output.models.formatted_response import FormattedResponse
from ecip_core.query.models.coordinator_response import CoordinatorResponse
from ecip_core.query.models.intent_result import IntentResult
from ecip_core.query.models.entity_result import EntityResult
from ecip_core.citations.models.citation import Citation


def make_intent(intent="explain_code", confidence=0.9):
    return IntentResult(
        intent=intent,
        confidence=confidence,
        matched_patterns=[],
        normalized_query="test query"
    )


def make_citation(
    chunk_id="c1",
    file_path="/src/UserService.java",
    class_name="UserService",
    method_name="getUser",
    start_line=10,
    end_line=30,
    confidence=0.95
) -> Citation:
    return Citation(
        project_id="test-proj",
        file_path=file_path,
        class_name=class_name,
        method_name=method_name,
        start_line=start_line,
        end_line=end_line,
        chunk_id=chunk_id,
        confidence=confidence
    )


def make_response(
    answer="UserService handles user operations.",
    model="test-model",
    intent="explain_code",
    citations=None
) -> CoordinatorResponse:
    return CoordinatorResponse(
        answer=answer,
        model=model,
        intent=make_intent(intent),
        entities=[],
        citations=citations or []
    )


class TestResponseFormatter(unittest.TestCase):

    def setUp(self):
        # Disable ANSI for stable string comparison
        self.formatter = ResponseFormatter(ansi=False)

    # ─── Standard rendering ───────────────────────────────────────────────

    def test_returns_formatted_response_type(self):
        response = make_response()
        result = self.formatter.format(response, question="Explain UserService")
        self.assertIsInstance(result, FormattedResponse)

    def test_rendered_contains_answer(self):
        response = make_response(answer="UserService handles user ops.")
        result = self.formatter.format(response, question="Explain UserService")
        self.assertIn("UserService handles user ops.", result.rendered)

    def test_rendered_contains_question(self):
        response = make_response()
        result = self.formatter.format(response, question="Explain UserService")
        self.assertIn("Explain UserService", result.rendered)

    def test_rendered_contains_model_name(self):
        response = make_response(model="llama3")
        result = self.formatter.format(response, question="Q")
        self.assertIn("llama3", result.rendered)

    def test_rendered_contains_intent(self):
        response = make_response(intent="dependency_analysis")
        result = self.formatter.format(response, question="Q")
        self.assertIn("dependency_analysis", result.rendered)

    def test_rendered_contains_duration(self):
        response = make_response()
        result = self.formatter.format(response, question="Q", duration_ms=342.5)
        self.assertIn("342 ms", result.rendered)

    def test_duration_shown_as_seconds_when_large(self):
        response = make_response()
        result = self.formatter.format(response, question="Q", duration_ms=2500.0)
        self.assertIn("2.50 s", result.rendered)

    # ─── Citation formatting ──────────────────────────────────────────────

    def test_citation_file_and_lines_in_rendered(self):
        cit = make_citation(file_path="/src/UserService.java", start_line=45, end_line=63)
        response = make_response(citations=[cit])
        result = self.formatter.format(response, question="Q")
        self.assertIn("UserService.java", result.rendered)
        self.assertIn("L45", result.rendered)
        self.assertIn("63", result.rendered)

    def test_citation_method_name_in_rendered(self):
        cit = make_citation(method_name="processOrder")
        response = make_response(citations=[cit])
        result = self.formatter.format(response, question="Q")
        self.assertIn("processOrder", result.rendered)

    def test_citation_ordering_preserved(self):
        c1 = make_citation(chunk_id="c1", file_path="/src/A.java", start_line=1,  end_line=5)
        c2 = make_citation(chunk_id="c2", file_path="/src/B.java", start_line=10, end_line=20)
        response = make_response(citations=[c1, c2])
        result = self.formatter.format(response, question="Q")
        a_pos = result.rendered.index("A.java")
        b_pos = result.rendered.index("B.java")
        self.assertLess(a_pos, b_pos)

    def test_no_citations_shows_placeholder(self):
        response = make_response(citations=[])
        with self.assertLogs("ecip_core.output.response_formatter", level="WARNING") as log:
            result = self.formatter.format(response, question="Q")
            self.assertTrue(any("Empty citations" in m for m in log.output))
        self.assertIn("no source citations", result.rendered)

    # ─── Empty / edge responses ───────────────────────────────────────────

    def test_empty_answer_logs_warning(self):
        response = make_response(answer="")
        with self.assertLogs("ecip_core.output.response_formatter", level="WARNING") as log:
            result = self.formatter.format(response, question="Q")
            self.assertTrue(any("Empty answer" in m for m in log.output))

    def test_empty_answer_shows_placeholder(self):
        response = make_response(answer="")
        result = self.formatter.format(response, question="Q")
        self.assertIn("no answer", result.rendered)

    def test_no_question_still_renders(self):
        response = make_response()
        result = self.formatter.format(response, question="")
        self.assertIsInstance(result, FormattedResponse)
        self.assertIsNotNone(result.rendered)

    # ─── Warnings ─────────────────────────────────────────────────────────

    def test_warnings_appear_in_rendered(self):
        response = make_response()
        result = self.formatter.format(
            response, question="Q",
            warnings=["Low confidence retrieval", "Graph data may be stale"]
        )
        self.assertIn("Low confidence retrieval", result.rendered)
        self.assertIn("Graph data may be stale", result.rendered)

    def test_no_warnings_section_skipped(self):
        response = make_response()
        result = self.formatter.format(response, question="Q", warnings=[])
        self.assertNotIn("⚠", result.rendered)

    # ─── ANSI toggle ──────────────────────────────────────────────────────

    def test_ansi_disabled_no_escape_codes(self):
        formatter_plain = ResponseFormatter(ansi=False)
        response = make_response()
        result = formatter_plain.format(response, question="Q")
        self.assertNotIn("\033[", result.rendered)

    def test_ansi_enabled_contains_escape_codes(self):
        formatter_color = ResponseFormatter(ansi=True)
        response = make_response()
        result = formatter_color.format(response, question="Q")
        self.assertIn("\033[", result.rendered)

    # ─── FormattedResponse fields ─────────────────────────────────────────

    def test_formatted_response_fields_populated(self):
        cit = make_citation()
        response = make_response(citations=[cit])
        result = self.formatter.format(response, question="Test Q", duration_ms=100.0)

        self.assertEqual(result.question, "Test Q")
        self.assertEqual(result.answer, "UserService handles user operations.")
        self.assertEqual(result.model, "test-model")
        self.assertAlmostEqual(result.duration_ms, 100.0)
        self.assertEqual(result.retrieved_chunks, 1)
        self.assertEqual(len(result.citations_text), 1)

    def test_serialization(self):
        response = make_response()
        result = self.formatter.format(response, question="Q")
        dumped = result.model_dump()
        self.assertIn("answer", dumped)
        self.assertIn("rendered", dumped)
        self.assertIn("citations_text", dumped)


if __name__ == "__main__":
    unittest.main()
