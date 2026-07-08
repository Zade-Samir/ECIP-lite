from pydantic import BaseModel


class IntentResult(BaseModel):
    """
    Represents the output of the intent analysis step.
    """
    intent: str
    confidence: float
    matched_patterns: list[str]
    normalized_query: str
