import logging
import sys


def get_logger(name: str) -> logging.Logger:
    """
    Returns a configured logger instance.
    Every ECIP module should use this logger.
    """

    logger = logging.getLogger(name)

    if logger.hasHandlers():
        return logger

    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)

    return logger


from ecip_core.inference.inference_service import InferenceService
from ecip_core.models.request import InferenceRequest
from ecip_core.models.response import InferenceResponse


class QueryCoordinator:
    """
    Main workflow coordinator of ECIP.

    Responsibilities:
    - Receive user requests.
    - Coordinate the complete processing pipeline.
    - Delegate inference to InferenceService.

    Future Responsibilities:
    - Project validation
    - Parser execution
    - Chunk retrieval
    - Project Memory
    - Graph Traversal
    - Context Assembly
    """

    def __init__(self):
        self.inference_service = InferenceService()

    def process(
        self,
        request: InferenceRequest
    ) -> InferenceResponse:

        return self.inference_service.ask(request)


## data which can be used further like environment variables, model paths, etc.

## Socho tumhare ghar me electricity hai. TV ko current chahiye. Fridge ko current chahiye. AC ko current chahiye. Har device ka apna wire nahi hota. Sab main switch board se current lete hain. settings.py wahi Main Switch Board hai. Project ka koi bhi module agar configuration chahta hai to usko yahi file milegi.

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central configuration for the entire ECIP application.
    Every module should read configuration from here.
    """

    OLLAMA_BASE_URL: str = "http://localhost:11434"

    MODEL_NAME: str = "qwen3.5:9b"

    TEMPERATURE: float = 0.2

    TOP_P: float = 0.9

    MAX_TOKENS: int = 4096

    STREAM: bool = False

    SYSTEM_PROMPT: str = (
        "You are ECIP, an expert Java and Spring Boot Architect."
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True
    )


settings = Settings()

## only work to take input as questions and give output as raw answers or LLM answers
## don't know about prompt builder, CLI, sqLite
## only know about the Ollama 

## Usko Prompt Builder ka pata nahi. Usko CLI ka pata nahi. Usko SQLite ka pata nahi. Usko Parser ka pata nahi. Ye Single Responsibility Principle ka perfect example hai.

from ollama import chat

from ecip_core.inference.config.settings import settings


class OllamaProvider:
    """
    Handles all communication with the local Ollama server.
    """

    def generate(self, prompt: str) -> str:

        response = chat(
            model=settings.MODEL_NAME,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        return response.message.content


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

## This is the main orchestrator. Isko sab kuch pata hai. Iska kaam hai sabko jod ke rakhna.
class InferenceService:
    """
    Coordinates the complete inference workflow.
    Responsibilities:
    - Accept inference requests
    - Build prompts
    - Delegate prompt execution to the configured provider
    - Return structured responses
    """

    def __init__(self):
        self.prompt_builder = PromptBuilder()
        self.inference_provider = OllamaProvider()

    def ask(self, request: InferenceRequest) -> InferenceResponse:

        logger.info("Building prompt...")

        prompt = self.prompt_builder.build_prompt(request.question)

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


from pydantic import BaseModel


class InferenceRequest(BaseModel):
    """
    Request sent to the inference pipeline.
    """

    question: str


from pydantic import BaseModel


class InferenceResponse(BaseModel):
    """
    Response returned by the inference pipeline.
    """

    answer: str

    model: str


## only work to get the input prompt as questions and give the formatted output as answer

from ecip_core.inference.config.settings import settings


class PromptBuilder:
    """
    Responsible for building prompts for the LLM.
    """

    def build_prompt(self, question: str, context: str | None = None) -> str:
        return f"""
{settings.SYSTEM_PROMPT}

Instructions:
- Answer professionally.
- Explain clearly.
- Use simple language where possible.

User Question:
{question}
""".strip()


from ecip_core.coordinator.query_coordinator import QueryCoordinator
from ecip_core.models.request import InferenceRequest


def main():

    coordinator = QueryCoordinator()

    print("=" * 60)
    print("🚀 Welcome to ECIP Lite")
    print("Type 'exit' to quit.")
    print("=" * 60)

    while True:

        question = input("\nAsk ECIP > ")

        if question.lower() in {"exit", "quit"}:
            print("Goodbye 👋")
            break

        request = InferenceRequest(
            question=question
        )

        response = coordinator.process(request)

        print("\nECIP:\n")
        print(response.answer)


if __name__ == "__main__":
    main()



annotated-types==0.7.0
anyio==4.14.1
certifi==2026.6.17
h11==0.16.0
httpcore==1.0.9
httpx==0.28.1
idna==3.18
ollama==0.6.2
pydantic==2.13.4
pydantic-settings==2.14.2
pydantic_core==2.46.4
python-dotenv==1.2.2
typing-inspection==0.4.2
typing_extensions==4.15.0
