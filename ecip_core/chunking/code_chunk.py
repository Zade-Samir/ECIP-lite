from pydantic import BaseModel


class CodeChunk(BaseModel):
    """
    Represents a chunk of Java source code.
    """

    file_name: str

    class_name: str

    method_name: str

    source_code: str