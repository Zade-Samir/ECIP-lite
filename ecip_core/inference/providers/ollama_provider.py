## only work to take input as questions and give output as raw answers or LLM answers
## don't know about prompt builder, CLI, sqLite
## only know about the Ollama 

## Usko Prompt Builder ka pata nahi. Usko CLI ka pata nahi. Usko SQLite ka pata nahi. Usko Parser ka pata nahi. Ye Single Responsibility Principle ka perfect example hai.

from ecip_core.common.logger import get_logger
from ollama import chat

from ecip_core.inference.config.settings import settings


logger = get_logger(__name__)

class OllamaProvider:
    """
    Handles all communication with the local Ollama server.
    """

    def generate(self, prompt: str) -> str:

        logger.info("Sending request to Ollama.")

        response = chat(
            model=settings.MODEL_NAME,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        logger.info("Received response from Ollama.")

        return response.message.content