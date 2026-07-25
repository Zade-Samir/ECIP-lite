from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class ConfigMetadata(BaseModel):
    file_path: str
    properties: Dict[str, str] = Field(default_factory=dict)
    profiles: List[str] = Field(default_factory=list)
    datasource_url: Optional[str] = None
    server_port: Optional[str] = None
