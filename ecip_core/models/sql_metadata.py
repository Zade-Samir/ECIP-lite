from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class ColumnMetadata(BaseModel):
    name: str
    data_type: str
    is_primary: bool = False
    is_nullable: bool = True


class ForeignKeyMetadata(BaseModel):
    column: str
    referenced_table: str
    referenced_column: str


class TableMetadata(BaseModel):
    name: str
    columns: List[ColumnMetadata] = Field(default_factory=list)
    primary_keys: List[str] = Field(default_factory=list)
    foreign_keys: List[ForeignKeyMetadata] = Field(default_factory=list)


class ViewMetadata(BaseModel):
    name: str
    definition: str


class IndexMetadata(BaseModel):
    name: str
    table_name: str
    columns: List[str] = Field(default_factory=list)


class ProcedureMetadata(BaseModel):
    name: str


class SqlMetadata(BaseModel):
    file_path: str
    tables: List[TableMetadata] = Field(default_factory=list)
    views: List[ViewMetadata] = Field(default_factory=list)
    indexes: List[IndexMetadata] = Field(default_factory=list)
    procedures: List[ProcedureMetadata] = Field(default_factory=list)
