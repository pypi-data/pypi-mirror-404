from __future__ import annotations

from pydantic import BaseModel, Field
from typing import List, Optional

# Existing models from your example
class TableDetail(BaseModel):
    table_name: str
    table_type: str

class ColumnDetail(BaseModel):
    column_name: str
    data_type: str
    column_default: Optional[str] = None
    is_nullable: str | bool

class ConstraintDetail(BaseModel):
    constraint_name: str
    constraint_type: str
    source_column: str | None = None
    referenced_table: str | None = None
    referenced_column: str | None = None

class IndexDetail(BaseModel):
    index_name: str
    index_definition: str

class ViewDetail(BaseModel):
    view_name: str
    view_definition: str

class TriggerDetail(BaseModel):
    trigger_name: str
    trigger_event: str
    trigger_condition: str
    trigger_operation: str

class TableMetadata(BaseModel):
    table_name: str
    table_type: str
    columns: List[ColumnDetail] = []
    constraints: List[ConstraintDetail] = []
    indexes: List[IndexDetail] = []
    triggers: List[TriggerDetail] = []

# DataSourceMetadata model to encapsulate all metadata for a data source
class DataSourceMetadata(BaseModel):
    data_source_id: str = Field(..., description="Unique identifier for the data source")
    tables: List[TableMetadata] = []
    views: List[ViewDetail] = []
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class MetadataModels:
    TableDetail = TableDetail
    ColumnDetail = ColumnDetail
    ConstraintDetail = ConstraintDetail
    IndexDetail = IndexDetail
    ViewDetail = ViewDetail
    TriggerDetail = TriggerDetail
    DataSourceMetadata = DataSourceMetadata