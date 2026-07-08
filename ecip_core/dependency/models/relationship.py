from pydantic import BaseModel


class Relationship(BaseModel):
    """
    Standard model representing a class dependency relationship.
    """
    source_class: str
    target_class: str
    relationship_type: str
    depth: int
    project_id: str
