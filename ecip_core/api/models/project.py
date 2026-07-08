from pydantic import BaseModel
from typing import List


class ProjectModel(BaseModel):
    """
    Project Metadata Response Model.
    """
    project_id: str
    alias: str
    root_path: str
    indexed_at: str
    indexed_files: int
    total_chunks: int
    total_vectors: int
    status: str


class ProjectListResponse(BaseModel):
    """
    Response model containing list of projects.
    """
    projects: List[ProjectModel]
