## only work to get the input prompt as questions and give the formatted output as answer

from ecip_core.inference.config.settings import settings


class PromptBuilder:
    """
    Builds prompts for the LLM.
    """

    def build_prompt(
        self,
        question: str,
        context: str = ""
    ) -> str:

        return f"""
You are a Senior Java Architect.

Use the provided project context if available.
If no project context is available, answer using your own knowledge.

{context}

Question:
{question}

Answer:
"""