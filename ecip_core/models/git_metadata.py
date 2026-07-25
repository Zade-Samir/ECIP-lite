from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class CommitMetadata(BaseModel):
    commit_hash: str
    author: str
    date: str
    message: str
    files_changed: List[str] = Field(default_factory=list)


class FileGitMetadata(BaseModel):
    file_path: str
    creation_commit: str
    last_modified_commit: str
    total_revisions: int
    contributors: List[str] = Field(default_factory=list)


class GitRepositoryMetadata(BaseModel):
    branch: str
    head_commit: str
    commits: List[CommitMetadata] = Field(default_factory=list)
    files: List[FileGitMetadata] = Field(default_factory=list)
