import unittest
from ecip_core.query.intent_analyzer import IntentAnalyzer
from ecip_core.query.models.intent_result import IntentResult
from ecip_core.query.intent import QueryIntent


class TestIntentAnalyzer(unittest.TestCase):

    def setUp(self):
        self.analyzer = IntentAnalyzer()

    def test_explain_code_intent(self):
        result = self.analyzer.analyze("Explain class UserService")
        self.assertEqual(result.intent, "explain_code")
        self.assertGreaterEqual(result.confidence, 0.8)
        self.assertIn("explain", result.matched_patterns)

        result_what_is = self.analyzer.analyze("What is class BookingController?")
        self.assertEqual(result_what_is.intent, "explain_code")

    def test_explain_method_intent(self):
        result = self.analyzer.analyze("Explain method getUserById")
        self.assertEqual(result.intent, "explain_method")
        self.assertGreaterEqual(result.confidence, 0.8)
        self.assertIn("method", result.matched_patterns)

    def test_dependency_intent(self):
        result = self.analyzer.analyze("What depends on BookingService?")
        self.assertEqual(result.intent, "dependency_analysis")
        self.assertIn("depends on", result.matched_patterns)

    def test_impact_intent(self):
        result = self.analyzer.analyze("What breaks if I change PaymentService?")
        self.assertEqual(result.intent, "impact_analysis")
        self.assertIn("what breaks", result.matched_patterns)

    def test_endpoint_intent(self):
        result = self.analyzer.analyze("Show all endpoints in BookingController")
        self.assertEqual(result.intent, "endpoint_lookup")
        self.assertIn("endpoints", result.matched_patterns)

    def test_navigation_intent(self):
        result = self.analyzer.analyze("Open file UserService.java")
        self.assertEqual(result.intent, "navigation")
        self.assertIn("open", result.matched_patterns)

    def test_semantic_question_intent(self):
        result = self.analyzer.analyze("How is authentication handled in this project?")
        self.assertEqual(result.intent, "semantic_question")
        self.assertIn("how is", result.matched_patterns)

    def test_general_concept_fallback(self):
        result = self.analyzer.analyze("what is java?")
        self.assertEqual(result.intent, "semantic_question")
        self.assertIn("what is", result.matched_patterns)

    def test_unknown_intent_for_garbage(self):
        result = self.analyzer.analyze("xyzabc blahblah")
        self.assertEqual(result.intent, "unknown")
        self.assertEqual(result.confidence, 0.0)

    def test_empty_query_handling(self):
        result_empty = self.analyzer.analyze("")
        self.assertEqual(result_empty.intent, "unknown")
        self.assertEqual(result_empty.confidence, 0.0)
        self.assertEqual(result_empty.normalized_query, "")

        result_whitespace = self.analyzer.analyze("   ")
        self.assertEqual(result_whitespace.intent, "unknown")

    def test_confidence_increment(self):
        result_single = self.analyzer.analyze("explain UserService")
        result_multiple = self.analyzer.analyze("explain class UserService")
        self.assertGreater(result_multiple.confidence, result_single.confidence)

    def test_backward_compatibility_detect(self):
        self.assertEqual(self.analyzer.detect("list files"), QueryIntent.LIST_FILES)
        self.assertEqual(self.analyzer.detect("methods of class A"), QueryIntent.FIND_METHODS)
        self.assertEqual(self.analyzer.detect("where is method name"), QueryIntent.FIND_FILE_BY_METHOD)
        self.assertEqual(self.analyzer.detect("some generic LLM question"), QueryIntent.LLM)

    def test_serialization(self):
        res = IntentResult(
            intent="explain_code",
            confidence=0.9,
            matched_patterns=["explain", "class"],
            normalized_query="explain class user"
        )
        serialized = res.model_dump()
        self.assertEqual(serialized["intent"], "explain_code")
        self.assertEqual(serialized["confidence"], 0.9)


if __name__ == "__main__":
    unittest.main()
