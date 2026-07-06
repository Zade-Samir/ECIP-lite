from pydantic import BaseModel, Field


class ConstructorInfo(BaseModel):
    """
    Represents a Java class constructor with parameters, annotations, and modifiers.
    """

    parameters: list[str] = Field(default_factory=list)
    annotations: list[str] = Field(default_factory=list)
    modifiers: list[str] = Field(default_factory=list)
