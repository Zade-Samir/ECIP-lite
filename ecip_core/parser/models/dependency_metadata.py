from pydantic import BaseModel


class DependencyMetadata(BaseModel):
    """
    Represents a code dependency relationship suitable for graph generation.
    """

    source_class: str
    target_class: str
    injection_type: str  # "CONSTRUCTOR" or "FIELD"
    parameter_name: str | None = None
