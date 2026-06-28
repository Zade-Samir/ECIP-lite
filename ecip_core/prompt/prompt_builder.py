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