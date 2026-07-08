from pydantic import BaseModel


class EntityResult(BaseModel):
    """
    Represents an extracted project-specific entity from a query.
    """
    entity_type: str  # e.g., class_name, method_name, package_name, rest_endpoint, repository_name, service_name, controller_name, entity_name
    entity_name: str
    confidence: float
    matched_text: str
    normalized_value: str
