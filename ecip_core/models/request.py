from pydantic import BaseModel


class InferenceRequest(BaseModel):
    """
    Request sent to the inference pipeline.
    """

    question: str