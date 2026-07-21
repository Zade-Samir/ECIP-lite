import time
from typing import Callable
from ecip_core.common.logger import get_logger
from ecip_core.models.request import InferenceRequest
from ecip_core.prompt.prompt_builder import PromptBuilder
from ecip_core.prompt.models.prompt import Prompt
from ecip_core.inference.providers.ollama_provider import OllamaProvider
from ecip_core.inference.models.inference_response import InferenceResponse
from ecip_core.inference.config.settings import settings

logger = get_logger(__name__)


class InferenceService:
    """
    Coordinates the provider-agnostic inference pipeline.
    """

    def __init__(self):
        self.prompt_builder = PromptBuilder()
        self.providers = {
            "ollama": OllamaProvider()
        }

    def ask(
        self,
        prompt: Prompt | InferenceRequest,
        context: str = "",
        callback: Callable[[str], None] = None
    ) -> InferenceResponse:
        """
        Executes LLM inference via the configured provider.
        Supports both Prompt objects and legacy InferenceRequest inputs.
        Supports token streaming when callback is provided.
        """
        logger.info("Inference started")

        # 1. Select provider
        provider_name = "ollama"
        provider = self.providers.get(provider_name)
        if not provider:
            logger.error("Provider unavailable: configured provider not found")
            raise ValueError(f"Provider {provider_name} not registered")

        logger.info(f"Provider selected: {provider_name}")

        # Validate availability
        if not provider.validate_availability():
            logger.error("Provider unavailable: provider offline")
            raise ConnectionError(f"Provider {provider_name} is offline")

        # 2. Extract prompt text and citations
        if isinstance(prompt, InferenceRequest):
            logger.info("Legacy InferenceRequest input, building prompt...")
            prompt_text = self.prompt_builder.build_prompt(
                question=prompt.question,
                context=context,
                history=getattr(prompt, "history", None)
            )
            citations = []
            prompt_tokens_est = int(len(prompt_text) / 4) + 1
        else:
            prompt_text = prompt.prompt_text
            citations = prompt.citations
            prompt_tokens_est = prompt.token_estimate

        if not prompt_text.strip():
            logger.error("Invalid response: empty prompt text")
            raise ValueError("Prompt text cannot be empty")

        # 3. Execute generation
        model_name = getattr(prompt, "model", None) or settings.MODEL_NAME
        start_time = time.perf_counter()
        try:
            response = provider.generate(prompt_text, model_name, callback=callback)
        except TimeoutError as e:
            logger.error(f"Timeout: {e}")
            raise
        except Exception as e:
            logger.error(f"Inference failure: {e}")
            raise

        duration_ms = int((time.perf_counter() - start_time) * 1000)
        logger.info(f"Response received in {duration_ms}ms")

        # Standardize completion and token metadata
        response.citations = citations
        response.inference_time_ms = duration_ms

        if response.prompt_tokens == 0:
            response.prompt_tokens = prompt_tokens_est
            response.total_tokens = response.prompt_tokens + response.completion_tokens

        logger.info("Duration: %d ms" % duration_ms)
        return response