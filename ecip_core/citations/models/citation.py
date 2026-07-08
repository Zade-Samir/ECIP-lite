from pydantic import BaseModel, Field


class Citation(BaseModel):
    """
    Typed citation that maps a generated answer back to its source code location.
    """
    project_id: str = ""
    file_path: str
    class_name: str
    method_name: str
    start_line: int
    end_line: int
    chunk_id: str
    confidence: float = Field(ge=0.0, le=1.0)
