from pydantic import BaseModel


class HybridResult(BaseModel):
    """
    Represents a merged result from both metadata lookups and semantic vector queries.
    """
    source: str  # "metadata" or "semantic"
    score: float
    chunk_id: str
    file_path: str
    class_name: str
    method_name: str
    chunk_type: str
    content: str
    start_line: int
    end_line: int
