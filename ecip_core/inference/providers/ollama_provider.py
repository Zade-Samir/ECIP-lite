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