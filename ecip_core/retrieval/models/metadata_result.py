from pydantic import BaseModel


class MetadataResult(BaseModel):
    """
    Represents a structured metadata search result.
    """
    project_id: str
    file_path: str
    package_name: str
    class_name: str
    method_name: str
    signature: str
    start_line: int
    end_line: int
    source_reference: str
