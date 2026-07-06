from pydantic import BaseModel, Field


class FieldInfo(BaseModel):
    """
    Represents a Java class field with name, type, modifiers, and annotations.
    """

    name: str
    type: str
    modifiers: list[str] = Field(default_factory=list)
    annotations: list[str] = Field(default_factory=list)
