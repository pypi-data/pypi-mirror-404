"""Graph query endpoints for MCP server proxy."""

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/graph", tags=["graph"])


class QueryRequest(BaseModel):
    """Request to execute a Cypher query."""
    query: str = Field(..., description="Cypher query to execute")
    params: dict[str, Any] = Field(default_factory=dict, description="Query parameters")


class QueryResponse(BaseModel):
    """Response from a Cypher query."""
    rows: list[dict[str, Any]] = Field(default_factory=list)
    columns: list[str] = Field(default_factory=list)
    row_count: int = 0


@router.post("/query", response_model=QueryResponse)
async def execute_query(request: QueryRequest):
    """Execute a read-only Cypher query.

    This endpoint is used by the MCP server to proxy queries through
    the emdash server, avoiding KuzuDB lock conflicts.

    Only read queries are allowed (no CREATE, MERGE, SET, DELETE).
    """
    # Basic safety check - block write operations
    query_upper = request.query.upper()
    write_keywords = ["CREATE", "MERGE", "SET ", "DELETE", "DROP", "REMOVE"]
    for keyword in write_keywords:
        if keyword in query_upper:
            raise HTTPException(
                status_code=400,
                detail=f"Write operations not allowed via this endpoint: {keyword}"
            )

    try:
        from ..graph.connection import get_read_connection

        conn = get_read_connection()
        rows = conn.execute(request.query, request.params)

        columns = list(rows[0].keys()) if rows else []

        return QueryResponse(
            rows=rows,
            columns=columns,
            row_count=len(rows),
        )
    except Exception as e:
        error_msg = str(e)
        # Provide helpful error for common issues
        if "not found" in error_msg.lower() or "does not exist" in error_msg.lower():
            raise HTTPException(
                status_code=404,
                detail=f"Query failed - table or property may not exist: {error_msg}"
            )
        raise HTTPException(status_code=500, detail=error_msg)


@router.get("/health")
async def graph_health():
    """Check if graph database is accessible."""
    try:
        from ..graph.connection import get_read_connection

        conn = get_read_connection()
        conn.execute("RETURN 1 AS num", {})
        return {"status": "healthy", "database": "kuzu"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
