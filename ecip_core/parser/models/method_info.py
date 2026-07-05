from pydantic import BaseModel


class MethodInfo(BaseModel):
    """
    Represents a Java method inside a source file.
    """

    name: str

    start_line: int

    end_line: int