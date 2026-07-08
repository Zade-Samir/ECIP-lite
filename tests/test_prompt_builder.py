import unittest
from ecip_core.prompt.prompt_builder import PromptBuilder
from ecip_core.retrieval.context.models.context import Context
from ecip_core.retrieval.models.hybrid_result import HybridResult
from ecip_core.prompt.models.prompt import Prompt


class TestPromptBuilder(unittest.TestCase):

    def setUp(self):
        self.builder = PromptBuilder(max_tokens=3000)

    def test_legacy_fallback(self):
        prompt_str = self.builder.build_prompt(
            question="What is the class name?",
            context="Some text context"
        )
        self.assertIsInstance(prompt_str, str)
        self.assertIn("Some text context", prompt_str)
        self.assertIn("What is the class name?", prompt_str)

    def test_prompt_sections_and_grounding_rules(self):
        ctx = Context(
            project_id="test-proj",
            project_name="OrderApp",
            question="how to save order?",
            class_context="public class OrderService {}",
            method_context="public void saveOrder() {}",
            dependency_context="- Injected: OrderRepository",
            supporting_chunks=[],
            citations=[
                HybridResult(
                    source="metadata",
                    score=1.0,
                    chunk_id="chunk_1",
                    file_path="/src/OrderService.java",
                    class_name="OrderService",
                    method_name="saveOrder",
                    chunk_type="method",
                    content="code",
                    start_line=5,
                    end_line=10
                )
            ],
            token_estimate=100
        )

        res = self.builder.build_prompt(question=ctx.question, context=ctx)
        self.assertIsInstance(res, Prompt)
        self.assertEqual(len(res.citations), 1)
        self.assertEqual(res.citations[0].chunk_id, "chunk_1")

        text = res.prompt_text
        self.assertIn("OrderApp", text)
        self.assertIn("public class OrderService {}", text)
        self.assertIn("public void saveOrder() {}", text)
        self.assertIn("- Injected: OrderRepository", text)
        self.assertIn("how to save order?", text)
        self.assertIn("Response Rules:", text)
        self.assertIn("UserService.java:10-20", text)

    def test_missing_sections_logging(self):
        ctx_empty = Context(
            project_id="test",
            project_name="App",
            question="q",
            class_context="",
            method_context="",
            dependency_context="",
            supporting_chunks=[],
            citations=[],
            token_estimate=0
        )
        with self.assertLogs("ecip_core.prompt.prompt_builder", level="WARNING") as log_capture:
            res = self.builder.build_prompt(question="q", context=ctx_empty)
            self.assertTrue(any("Missing context section: class_context" in log for log in log_capture.output))
            self.assertTrue(any("Missing context section: method_context" in log for log in log_capture.output))
            self.assertTrue(any("Missing context section: dependency_context" in log for log in log_capture.output))

    def test_context_truncation(self):
        strict_builder = PromptBuilder(max_tokens=100)

        ctx = Context(
            project_id="test",
            project_name="App",
            question="extremely long question text to fill space",
            class_context="public class OrderService {" + " " * 300 + "}",
            method_context="public void saveOrder() {" + " " * 300 + "}",
            dependency_context="- Injected: Repo",
            supporting_chunks=[],
            citations=[],
            token_estimate=200
        )

        with self.assertLogs("ecip_core.prompt.prompt_builder", level="WARNING") as log_capture:
            res = strict_builder.build_prompt(question=ctx.question, context=ctx)
            self.assertTrue(any("Context truncated" in log for log in log_capture.output))

        self.assertNotIn("- Injected: Repo", res.prompt_text)

    def test_stable_output(self):
        ctx = Context(
            project_id="test",
            project_name="App",
            question="question",
            class_context="class",
            method_context="method",
            dependency_context="dep",
            supporting_chunks=[],
            citations=[],
            token_estimate=10
        )
        res1 = self.builder.build_prompt(question=ctx.question, context=ctx)
        res2 = self.builder.build_prompt(question=ctx.question, context=ctx)
        self.assertEqual(res1.prompt_text, res2.prompt_text)

    def test_serialization(self):
        ctx = Context(
            project_id="test",
            project_name="App",
            question="question",
            class_context="class",
            method_context="method",
            dependency_context="dep",
            supporting_chunks=[],
            citations=[],
            token_estimate=10
        )
        res = self.builder.build_prompt(question=ctx.question, context=ctx)
        dumped = res.model_dump()
        self.assertEqual(dumped["token_estimate"], res.token_estimate)
        self.assertIn("App", dumped["prompt_text"])


if __name__ == "__main__":
    unittest.main()
