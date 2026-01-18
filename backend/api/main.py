"""
PesapalDB REST API

FastAPI-based REST API for the database.
"""

from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from typing import Any, Dict, List, Optional
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rdbms.engine import Database
from .models import (
    QueryRequest,
    QueryResponse,
    InsertRequest,
    UpdateRequest,
    TableInfo,
    DatabaseStats,
    HealthResponse,
)


# Initialize FastAPI app
app = FastAPI(
    title="PesapalDB API",
    description="REST API for PesapalDB - A Simple RDBMS Implementation",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database
db = Database(data_dir="./data")


# Health check
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check API and database health."""
    tables = db.get_tables()
    return HealthResponse(status="ok", database="connected", tables=len(tables))


# Database statistics
@app.get("/stats", response_model=DatabaseStats)
async def get_stats():
    """Get database statistics."""
    stats = db.get_stats()
    return DatabaseStats(**stats)


# Query execution
@app.post("/query", response_model=QueryResponse)
async def execute_query(sql: str = Body(..., embed=True)):
    """Execute a SQL query."""
    result = db.execute(sql)
    return QueryResponse(**result.to_dict())


# Table operations
@app.get("/tables")
async def list_tables():
    """List all tables."""
    tables = db.get_tables()
    result = []
    for name in tables:
        info = db.get_table_info(name)
        if info:
            result.append(
                {
                    "name": name,
                    "columns": len(info["columns"]),
                    "rows": info["row_count"],
                }
            )
    return {"tables": result}


@app.get("/tables/{table_name}", response_model=TableInfo)
async def get_table_info(table_name: str):
    """Get information about a specific table."""
    info = db.get_table_info(table_name)
    if not info:
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")
    return TableInfo(**info)


@app.get("/tables/{table_name}/rows")
async def get_table_rows(
    table_name: str,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    order_by: Optional[str] = Query(None),
    order_dir: str = Query("ASC", pattern="^(ASC|DESC)$"),
):
    """Get rows from a table with pagination."""
    if not db.schema.has_table(table_name):
        raise HTTPException(
            status_code=400, detail=f"Table '{table_name}' does not exist"
        )

    # Build query
    sql = f"SELECT * FROM {table_name}"
    if order_by:
        sql += f" ORDER BY {order_by} {order_dir}"
    sql += f" LIMIT {limit}"
    if offset:
        sql += f" OFFSET {offset}"

    result = db.execute(sql)

    return {
        "success": result.success,
        "rows": result.rows,
        "columns": result.columns,
        "row_count": result.row_count,
    }


@app.post("/tables/{table_name}/rows")
async def insert_row(table_name: str, request: InsertRequest):
    """Insert a row into a table."""
    if not db.schema.has_table(table_name):
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")

    # Get table columns for validation
    table_info = db.get_table_info(table_name)
    columns = [col["name"] for col in table_info["columns"]]

    # Build INSERT statement
    insert_columns = [k for k in request.data.keys() if k in columns and k != 'id']
    values = []
    for col in insert_columns:
        val = request.data[col]
        if isinstance(val, str):
            values.append(f"'{val}'")
        elif val is None:
            values.append("NULL")
        else:
            values.append(str(val))

    sql = f"INSERT INTO {table_name} ({', '.join(insert_columns)}) VALUES ({', '.join(values)})"
    result = db.execute(sql)

    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)

    return {"success": True, "message": result.message}


@app.put("/tables/{table_name}/rows/{row_id}")
async def update_row(table_name: str, row_id: int, request: UpdateRequest):
    """Update a row in a table."""
    if not db.schema.has_table(table_name):
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")

    # Get primary key column
    table_info = db.get_table_info(table_name)
    pk_col = None
    for col in table_info["columns"]:
        if col["primary_key"]:
            pk_col = col["name"]
            break

    if not pk_col:
        pk_col = "id"  # Fallback

    # Build UPDATE statement
    sets = []
    for col, val in request.data.items():
        if isinstance(val, str):
            sets.append(f"{col} = '{val}'")
        elif val is None:
            sets.append(f"{col} = NULL")
        else:
            sets.append(f"{col} = {val}")

    sql = f"UPDATE {table_name} SET {', '.join(sets)} WHERE {pk_col} = {row_id}"
    result = db.execute(sql)

    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)

    return {"success": True, "message": result.message}


@app.delete("/tables/{table_name}/rows/{row_id}")
async def delete_row(table_name: str, row_id: int):
    """Delete a row from a table."""
    if not db.schema.has_table(table_name):
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")

    # Get primary key column
    table_info = db.get_table_info(table_name)
    pk_col = None
    for col in table_info["columns"]:
        if col["primary_key"]:
            pk_col = col["name"]
            break

    if not pk_col:
        pk_col = "id"

    sql = f"DELETE FROM {table_name} WHERE {pk_col} = {row_id}"
    result = db.execute(sql)

    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)

    return {"success": True, "message": result.message}


@app.delete("/tables/{table_name}")
async def drop_table(table_name: str):
    """Drop a table."""
    if not db.schema.has_table(table_name):
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")

    sql = f"DROP TABLE {table_name}"
    result = db.execute(sql)

    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)

    return {"success": True, "message": result.message}
    
    
@app.post("/reset")
async def reset_database():
    """Reset the database."""
    db.reset()
    return {"success": True, "message": "Database has been reset"}

# Entry point
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
