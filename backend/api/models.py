"""
PesapalDB REST API Models

Pydantic models for request/response validation.
"""

from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional


class QueryRequest(BaseModel):
    """Request model for SQL query execution."""

    sql: str = Field(..., description="SQL query to execute")


class QueryResponse(BaseModel):
    """Response model for query results."""

    success: bool
    message: str
    rows: List[Dict[str, Any]] = []
    columns: List[str] = []
    row_count: int = 0


class InsertRequest(BaseModel):
    """Request model for inserting a row."""

    data: Dict[str, Any] = Field(..., description="Row data to insert")


class UpdateRequest(BaseModel):
    """Request model for updating a row."""

    data: Dict[str, Any] = Field(..., description="Fields to update")


class TableInfo(BaseModel):
    """Response model for table information."""

    name: str
    columns: List[Dict[str, Any]]
    row_count: int
    indexes: List[str]


class DatabaseStats(BaseModel):
    """Response model for database statistics."""

    table_count: int
    total_size_bytes: int
    data_directory: str
    tables: Dict[str, int] = {}
    created_at: Optional[str] = None
    last_modified: Optional[str] = None


class HealthResponse(BaseModel):
    """Response model for health check."""

    status: str = "ok"
    database: str = "connected"
    tables: int = 0
