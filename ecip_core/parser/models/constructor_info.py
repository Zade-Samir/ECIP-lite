from pydantic import BaseModel, Field


class ConstructorInfo(BaseModel):
    """
    Represents a Java class constructor with parameters, annotations, modifiers, line numbers, and dependencies.
    """

    parameters: list[str] = Field(default_factory=list)
    annotations: list[str] = Field(default_factory=list)
    modifiers: list[str] = Field(default_factory=list)
    start_line: int | None = None
    end_line: int | None = None
    injected_dependency_types: list[str] = Field(default_factory=list)
