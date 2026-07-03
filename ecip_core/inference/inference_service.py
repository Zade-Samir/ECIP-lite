## first orchestrator of this ECIP
## Question -> Prompt Builder -> Prompt -> Ollama Provider -> Answer -> Return
## Inference Service khud prompt nahi banata. Inference Service khud Ollama call nahi karta. Inference Service sirf coordinate karta hai. Isi liye iska naam Inference Service hai.

from ecip_core.models.request import InferenceRequest
from ecip_core.models.response import InferenceResponse

from ecip_core.prompt.prompt_builder import PromptBuilder
from ecip_core.inference.providers.ollama_provider import OllamaProvider
from ecip_core.inference.config.settings import settings

from ecip_core.common.logger import get_logger

logger = get_logger(__name__)


class InferenceService:
    """
    Coordinates the inference pipeline.
    """

    def __init__(self):

        self.prompt_builder = PromptBuilder()
        self.inference_provider = OllamaProvider()

    def ask(
        self,
        request: InferenceRequest,
        context: str = ""
    ) -> InferenceResponse:

        logger.info("Building prompt...")

        prompt = self.prompt_builder.build_prompt(
            question=request.question,
            context=context
        )

        logger.info("Prompt generated successfully.")

        logger.info("Generating answer from provider...")

        answer = self.inference_provider.generate(prompt)

        logger.info("Answer generated successfully.")

        logger.info("Creating response...")

        response = InferenceResponse(
            answer=answer,
            model=settings.MODEL_NAME
        )

        logger.info("Response created successfully.")

        return response