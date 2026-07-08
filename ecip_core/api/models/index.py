from pydantic import BaseModel, Field


class IndexRequest(BaseModel):
    """
    FastAPI Index Request model.
    """
    project_path: str = Field(..., description="Absolute filesystem path to the Java project.")
    project_alias: str = Field(..., description="Unique alias name for the project.")


class IndexResponse(BaseModel):
    """
    FastAPI Index Response model.
    """
    status: str
    project_id: str
    files_scanned: int
    files_indexed: int
    files_skipped: int
    duration_ms: int
