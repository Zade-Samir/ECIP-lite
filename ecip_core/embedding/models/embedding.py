from pydantic import BaseModel


class Embedding(BaseModel):
    """
    Represents an embedding generated from a code chunk.
    """

    file_name: str

    class_name: str

    method_name: str

    source_code: str

    vector: list[float]

    # Optional metadata fields
    chunk_id: str | None = None
    file_path: str | None = None
    chunk_type: str | None = None
    start_line: int | None = None
    end_line: int | None = None