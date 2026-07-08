from pydantic import BaseModel, Field
from typing import List
from ecip_core.dependency.models.relationship import Relationship


class ImpactReport(BaseModel):
    """
    Structured report produced by the Impact Analysis Engine.
    """
    project_id: str
    target_class: str
    affected_classes: List[str]
    dependency_tree: List[Relationship]
    traversal_depth: int
    total_affected: int
    warnings: List[str] = Field(default_factory=list)
