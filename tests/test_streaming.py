import unittest
from unittest.mock import MagicMock, patch
from ecip_core.inference.inference_service import InferenceService
from ecip_core.prompt.models.prompt import Prompt
from ecip_core.inference.models.inference_response import InferenceResponse
from ecip_core.models.request import InferenceRequest


class TestStreaming(unittest.TestCase):

    def setUp(self):
        self.service = InferenceService()
        self.mock_provider = MagicMock()
        self.service.providers["ollama"] = self.mock_provider

    def test_streaming_callback_invoked_and_order_preserved(self):
        self.mock_provider.validate_availability.return_value = True

        def mock_generate(prompt_text, model_name, callback=None):
            tokens = ["Hello", " ", "world", "!"]
            if callback:
                for token in tokens:
                    callback(token)
            return InferenceResponse(
                answer="Hello world!",
                model_name=model_name,
                provider_name="ollama",
                inference_time_ms=100,
                prompt_tokens=10,
                completion_tokens=5,
                total_tokens=15
            )

        self.mock_provider.generate.side_effect = mock_generate

        received_tokens = []
        def test_callback(token: str):
            received_tokens.append(token)

        prompt = Prompt(prompt_text="test", citations=[], token_estimate=10)
        res = self.service.ask(prompt, callback=test_callback)

        self.assertEqual(res.answer, "Hello world!")
        self.assertEqual(received_tokens, ["Hello", " ", "world", "!"])

    def test_sync_fallback_works_normally(self):
        self.mock_provider.validate_availability.return_value = True
        self.mock_provider.generate.return_value = InferenceResponse(
            answer="Sync reply",
            model_name="qwen",
            provider_name="ollama",
            inference_time_ms=50,
            prompt_tokens=5,
            completion_tokens=2,
            total_tokens=7
        )

        prompt = Prompt(prompt_text="test", citations=[], token_estimate=5)
        res = self.service.ask(prompt)

        self.assertEqual(res.answer, "Sync reply")
        self.mock_provider.generate.assert_called_once_with("test", "qwen3.5:9b", callback=None)

    def test_streaming_provider_disconnect_propagation(self):
        self.mock_provider.validate_availability.return_value = True
        self.mock_provider.generate.side_effect = ConnectionError("Connection lost during stream")

        received_tokens = []
        def test_callback(token: str):
            received_tokens.append(token)

        prompt = Prompt(prompt_text="test", citations=[], token_estimate=5)
        with self.assertRaises(ConnectionError):
            self.service.ask(prompt, callback=test_callback)

    def test_streaming_timeout_propagation(self):
        self.mock_provider.validate_availability.return_value = True
        self.mock_provider.generate.side_effect = TimeoutError("Stream timed out")

        prompt = Prompt(prompt_text="test", citations=[], token_estimate=5)
        with self.assertRaises(TimeoutError):
            self.service.ask(prompt, callback=lambda t: None)


if __name__ == "__main__":
    unittest.main()
