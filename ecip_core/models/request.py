from pydantic import BaseModel
from typing import Optional, List


class InferenceRequest(BaseModel):
    """
    Request sent to the inference pipeline.
    """

    question: str
    project_id: Optional[str] = "default"
    history: Optional[List[dict]] = None