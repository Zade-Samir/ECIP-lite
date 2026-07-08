import time
import urllib.request
from ollama import chat
from ecip_core.common.logger import get_logger
from ecip_core.inference.config.settings import settings
from ecip_core.inference.providers.base_provider import BaseProvider
from ecip_core.inference.models.inference_response import InferenceResponse

logger = get_logger(__name__)


class OllamaProvider(BaseProvider):
    """
    Handles all communication with the local Ollama server.
    """

    def generate(self, prompt_text: str, model_name: str) -> InferenceResponse:
        logger.info("Sending request to Ollama.")
        start_time = time.perf_counter()

        try:
            response = chat(
                model=model_name,
                messages=[
                    {
                        "role": "user",
                        "content": prompt_text
                    }
                ]
            )
            duration = time.perf_counter() - start_time
            logger.info("Received response from Ollama.")

            answer = response.message.content if response.message else ""
            inference_time_ms = int(duration * 1000)

            # Warn on slow inference (> 5 seconds)
            if duration > 5.0:
                logger.warning("Slow inference")

            # Warn on empty completion
            if not answer.strip():
                logger.warning("Empty completion")

            # Heuristic token calculations
            prompt_tokens = int(len(prompt_text) / 4) + 1
            completion_tokens = int(len(answer) / 4) + 1
            total_tokens = prompt_tokens + completion_tokens

            return InferenceResponse(
                answer=answer,
                citations=[],
                model_name=model_name,
                provider_name="ollama",
                inference_time_ms=inference_time_ms,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                warnings=[],
                errors=[]
            )

        except Exception as e:
            logger.error(f"Ollama generation failure: {e}")
            raise

    def validate_availability(self) -> bool:
        logger.info("Validating Ollama availability.")
        try:
            urllib.request.urlopen(settings.OLLAMA_BASE_URL, timeout=2.0)
            logger.info("Ollama is online.")
            return True
        except Exception as e:
            logger.error(f"Provider unavailable: {e}")
            return False