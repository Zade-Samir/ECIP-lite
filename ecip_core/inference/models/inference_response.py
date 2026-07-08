from pydantic import BaseModel
from ecip_core.retrieval.models.hybrid_result import HybridResult


class InferenceResponse(BaseModel):
    """
    Standardized response model for all inference backends and orchestration.
    """
    answer: str
    citations: list[HybridResult] = []
    model_name: str
    provider_name: str
    inference_time_ms: int
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    warnings: list[str] = []
    errors: list[str] = []

    @property
    def model(self) -> str:
        return self.model_name
