"""Health check endpoint."""

import time
from datetime import datetime
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from ..config import get_config

router = APIRouter(prefix="/health", tags=["health"])

# Server start time for uptime calculation
_start_time: float = time.time()


class DatabaseStatus(BaseModel):
    """Database connection status."""

    connected: bool
    node_count: Optional[int] = None
    relationship_count: Optional[int] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response."""

    status: str  # "healthy", "starting", "unhealthy"
    version: str
    uptime_seconds: float
    repo_root: Optional[str]
    database: DatabaseStatus
    timestamp: datetime


def _check_database() -> DatabaseStatus:
    """Check database connection status."""
    config = get_config()

    try:
        # Try to import and connect to database
        # This will be replaced with actual database check once services are moved
        db_path = config.database_full_path
        if db_path.exists():
            return DatabaseStatus(
                connected=True,
                node_count=0,  # TODO: Get actual counts
                relationship_count=0,
            )
        else:
            return DatabaseStatus(
                connected=False,
                error="Database not initialized"
            )
    except Exception as e:
        return DatabaseStatus(
            connected=False,
            error=str(e)
        )


@router.get("", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Check server health status."""
    from .. import __version__

    config = get_config()
    db_status = _check_database()

    status = "healthy" if db_status.connected else "starting"

    return HealthResponse(
        status=status,
        version=__version__,
        uptime_seconds=time.time() - _start_time,
        repo_root=config.repo_root,
        database=db_status,
        timestamp=datetime.now(),
    )


@router.get("/ready")
async def readiness_check() -> dict:
    """Simple readiness probe for container orchestration."""
    return {"ready": True}


@router.get("/live")
async def liveness_check() -> dict:
    """Simple liveness probe for container orchestration."""
    return {"alive": True}
