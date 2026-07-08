import time
import urllib.request
from typing import Callable
from ollama import chat
from ecip_core.common.logger import get_logger
from ecip_core.inference.config.settings import settings
from ecip_core.inference.providers.base_provider import BaseProvider
from ecip_core.inference.models.inference_response import InferenceResponse

logger = get_logger(__name__)


class OllamaProvider(BaseProvider):
    """
    Handles all communication with the local Ollama server, including streaming.
    """

    def generate(
        self,
        prompt_text: str,
        model_name: str,
        callback: Callable[[str], None] = None
    ) -> InferenceResponse:
        start_time = time.perf_counter()

        # 1. Streaming Mode
        if callback is not None:
            logger.info("Stream started")
            answer_parts = []
            first_token_received = False

            try:
                response_stream = chat(
                    model=model_name,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt_text
                        }
                    ],
                    stream=True
                )

                for chunk in response_stream:
                    token = chunk.message.content if chunk.message else ""
                    if token:
                        if not first_token_received:
                            first_token_received = True
                            logger.info("First token received")
                        answer_parts.append(token)
                        callback(token)

                logger.info("Stream completed")
                answer = "".join(answer_parts)
                duration = time.perf_counter() - start_time
                logger.info(f"Total duration: {duration:.4f}s")
                inference_time_ms = int(duration * 1000)

            except (ConnectionResetError, ConnectionError) as e:
                logger.error(f"Provider disconnected: {e}")
                logger.warning("Stream interrupted")
                raise
            except TimeoutError as e:
                logger.error(f"Stream timeout: {e}")
                logger.warning("Stream interrupted")
                raise
            except Exception as e:
                logger.error(f"Invalid token sequence: {e}")
                logger.warning("Stream interrupted")
                raise

        # 2. Synchronous Mode (Fallback)
        else:
            logger.info("Sending request to Ollama.")
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
            except Exception as e:
                logger.error(f"Ollama generation failure: {e}")
                raise

        # Common metrics assembly
        if duration > 5.0:
            logger.warning("Slow inference")

        if not answer.strip():
            logger.warning("Empty completion")

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

    def validate_availability(self) -> bool:
        logger.info("Validating Ollama availability.")
        try:
            urllib.request.urlopen(settings.OLLAMA_BASE_URL, timeout=2.0)
            logger.info("Ollama is online.")
            return True
        except Exception as e:
            logger.error(f"Provider unavailable: {e}")
            return False