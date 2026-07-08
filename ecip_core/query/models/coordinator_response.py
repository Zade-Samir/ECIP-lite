from typing import Union
from pydantic import BaseModel
from ecip_core.query.models.intent_result import IntentResult
from ecip_core.query.models.entity_result import EntityResult
from ecip_core.retrieval.models.hybrid_result import HybridResult
from ecip_core.citations.models.citation import Citation


class CoordinatorResponse(BaseModel):
    """
    Typed response returned by the Query Coordinator orchestrating the QA pipeline.
    Citations may be HybridResult (raw retrieval) or Citation (engine-validated).
    """
    answer: str
    model: str
    intent: IntentResult
    entities: list[EntityResult]
    citations: list[Union[Citation, HybridResult]]
