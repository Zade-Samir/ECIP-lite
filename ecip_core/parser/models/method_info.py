from pydantic import BaseModel, Field


class MethodInfo(BaseModel):
    """
    Represents a Java method inside a source file.
    """

    name: str
    signature: str | None = None
    return_type: str | None = None
    modifiers: list[str] = Field(default_factory=list)
    annotations: list[str] = Field(default_factory=list)
    parameters: list[str] = Field(default_factory=list)
    throws: list[str] = Field(default_factory=list)
    start_line: int
    end_line: int