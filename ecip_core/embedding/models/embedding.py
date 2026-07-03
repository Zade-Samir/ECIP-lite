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