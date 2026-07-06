from pydantic import BaseModel, Field


class CodeChunk(BaseModel):
    """
    Represents a chunk of Java source code (class overview or method chunk).
    """

    chunk_id: str
    project_id: str
    file_path: str
    class_name: str
    method_name: str | None = None
    chunk_type: str  # "CLASS_OVERVIEW" or "METHOD"
    content: str
    source_code: str  # Kept for backward compatibility with embedding services
    start_line: int
    end_line: int
    content_hash: str
    created_at: str | None = None
