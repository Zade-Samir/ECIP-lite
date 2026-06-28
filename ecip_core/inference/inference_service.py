## first orchestrator of this ECIP
## Question -> Prompt Builder -> Prompt -> Ollama Provider -> Answer -> Return
## Inference Service khud prompt nahi banata. Inference Service khud Ollama call nahi karta. Inference Service sirf coordinate karta hai. Isi liye iska naam Inference Service hai.

from ecip_core.prompt.prompt_builder import PromptBuilder
from ecip_core.inference.providers.ollama_provider import OllamaProvider

## This is the main orchestrator. Isko sab kuch pata hai. Iska kaam hai sabko jod ke rakhna.
class InferenceService:
    """
    Coordinates the inference pipeline.
    """

    def __init__(self):
        self.prompt_builder = PromptBuilder()
        self.provider = OllamaProvider()

    def ask(self, question: str) -> str:
        prompt = self.prompt_builder.build_prompt(question)

        answer = self.provider.generate(prompt)

        return answer