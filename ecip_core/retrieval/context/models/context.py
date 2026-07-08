from pydantic import BaseModel
from ecip_core.retrieval.models.hybrid_result import HybridResult


class Context(BaseModel):
    """
    Strongly typed context object generated for Prompt Builder consumption.
    """
    project_id: str
    project_name: str
    question: str
    class_context: str
    method_context: str
    dependency_context: str
    supporting_chunks: list[HybridResult]
    citations: list[HybridResult]
    token_estimate: int
