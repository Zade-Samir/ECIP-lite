from pydantic import BaseModel
from ecip_core.retrieval.models.hybrid_result import HybridResult


class Prompt(BaseModel):
    """
    Strongly typed prompt object returned by the PromptBuilder.
    """
    prompt_text: str
    citations: list[HybridResult]
    token_estimate: int
