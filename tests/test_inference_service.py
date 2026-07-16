import unittest
from unittest.mock import MagicMock, patch
from ecip_core.inference.inference_service import InferenceService
from ecip_core.prompt.models.prompt import Prompt
from ecip_core.retrieval.models.hybrid_result import HybridResult
from ecip_core.inference.models.inference_response import InferenceResponse
from ecip_core.models.request import InferenceRequest


class TestInferenceService(unittest.TestCase):

    def setUp(self):
        self.service = InferenceService()
        self.mock_provider = MagicMock()
        self.service.providers["ollama"] = self.mock_provider

    def test_provider_offline_handling(self):
        self.mock_provider.validate_availability.return_value = False

        prompt = Prompt(prompt_text="hello", citations=[], token_estimate=10)
        with self.assertRaises(ConnectionError):
            self.service.ask(prompt)

    def test_successful_inference_and_normalization(self):
        self.mock_provider.validate_availability.return_value = True

        mock_response = InferenceResponse(
            answer="Here is the class UserService.",
            model_name="qwen2.5-coder:3b",
            provider_name="ollama",
            inference_time_ms=1200,
            prompt_tokens=20,
            completion_tokens=10,
            total_tokens=30,
            warnings=[],
            errors=[]
        )
        self.mock_provider.generate.return_value = mock_response

        citation = HybridResult(
            source="metadata", score=1.0, chunk_id="c1", file_path="U.java",
            class_name="U", method_name="", chunk_type="class", content="class U",
            start_line=1, end_line=2
        )
        prompt = Prompt(prompt_text="explain U", citations=[citation], token_estimate=15)

        with self.assertLogs("ecip_core.inference.inference_service", level="INFO") as log_capture:
            res = self.service.ask(prompt)
            self.assertTrue(any("Provider selected: ollama" in log for log in log_capture.output))
            self.assertTrue(any("Response received in" in log for log in log_capture.output))

        self.assertEqual(res.answer, "Here is the class UserService.")
        self.assertEqual(res.provider_name, "ollama")
        self.assertEqual(len(res.citations), 1)
        self.assertEqual(res.citations[0].chunk_id, "c1")
        self.assertEqual(res.prompt_tokens, 20)

    def test_timeout_handling(self):
        self.mock_provider.validate_availability.return_value = True
        self.mock_provider.generate.side_effect = TimeoutError("Ollama connection timed out")

        prompt = Prompt(prompt_text="hello", citations=[], token_estimate=10)
        with self.assertRaises(TimeoutError):
            self.service.ask(prompt)

    def test_legacy_request_mode(self):
        self.mock_provider.validate_availability.return_value = True
        mock_response = InferenceResponse(
            answer="Legacy response.",
            model_name="qwen2.5-coder:3b",
            provider_name="ollama",
            inference_time_ms=500,
            prompt_tokens=0,
            completion_tokens=5,
            total_tokens=5,
            warnings=[],
            errors=[]
        )
        self.mock_provider.generate.return_value = mock_response

        req = InferenceRequest(question="explain U")
        res = self.service.ask(req, context="Legacy Context")

        self.assertEqual(res.answer, "Legacy response.")
        self.mock_provider.generate.assert_called_once()
        self.assertGreater(res.prompt_tokens, 0)

    def test_serialization(self):
        mock_response = InferenceResponse(
            answer="Reply",
            model_name="qwen2.5-coder:3b",
            provider_name="ollama",
            inference_time_ms=500,
            prompt_tokens=10,
            completion_tokens=5,
            total_tokens=15,
            warnings=["slow"],
            errors=[]
        )
        dumped = mock_response.model_dump()
        self.assertEqual(dumped["answer"], "Reply")
        self.assertEqual(dumped["warnings"], ["slow"])


if __name__ == "__main__":
    unittest.main()
