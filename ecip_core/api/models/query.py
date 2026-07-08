from pydantic import BaseModel, Field
from typing import List


class QueryRequest(BaseModel):
    """
    FastAPI Query Request model.
    """
    project_id: str = Field(..., description="The unique identifier of the project.")
    question: str = Field(..., description="The natural language question to ask.")


class CitationModel(BaseModel):
    """
    Structured citation model.
    """
    file_path: str
    class_name: str
    method_name: str = ""
    start_line: int = 0
    end_line: int = 0


class QueryResponse(BaseModel):
    """
    FastAPI Query Response model.
    """
    answer: str
    citations: List[CitationModel]
    model_name: str
    duration_ms: int
