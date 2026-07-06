from pydantic import BaseModel


class SearchResult(BaseModel):
    """
    Represents a structured semantic search hit.
    """
    score: float
    chunk_id: str
    file_path: str
    class_name: str
    method_name: str
    chunk_type: str
    start_line: int
    end_line: int
    content: str
