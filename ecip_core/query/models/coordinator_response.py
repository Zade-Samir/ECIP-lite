from pydantic import BaseModel
from ecip_core.query.models.intent_result import IntentResult
from ecip_core.query.models.entity_result import EntityResult
from ecip_core.retrieval.models.hybrid_result import HybridResult


class CoordinatorResponse(BaseModel):
    """
    Typed response returned by the Query Coordinator orchestrating the QA pipeline.
    """
    answer: str
    model: str
    intent: IntentResult
    entities: list[EntityResult]
    citations: list[HybridResult]
