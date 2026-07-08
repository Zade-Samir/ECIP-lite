from pydantic import BaseModel, Field
from typing import List


class FormattedResponse(BaseModel):
    """
    Structured output produced by the ResponseFormatter.
    Contains all sections that will be rendered to the CLI.
    """
    question: str = ""
    answer: str
    intent: str = ""
    citations_text: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    model: str = ""
    duration_ms: float = 0.0
    retrieved_chunks: int = 0
    rendered: str = ""
