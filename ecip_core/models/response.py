from pydantic import BaseModel


class InferenceResponse(BaseModel):
    """
    Response returned by the inference pipeline.
    """

    answer: str

    model: str