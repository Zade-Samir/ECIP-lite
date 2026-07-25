from pydantic import BaseModel, Field
from typing import List, Set


class Permission(BaseModel):
    name: str  # e.g., "workspace:read"
    description: str


class Role(BaseModel):
    name: str  # e.g., "Developer"
    permissions: Set[str] = Field(default_factory=set)
    inherits: List[str] = Field(default_factory=list) # Inherit permissions from other roles
