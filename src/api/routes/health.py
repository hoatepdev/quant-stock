"""Health check endpoints."""
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.database.connection import get_sync_session
from src.utils.config import get_settings

settings = get_settings()
router = APIRouter()


@router.get("/health")
async def health_check(db: Session = Depends(get_sync_session)) -> dict:
    """Health check endpoint.

    Args:
        db: Database session

    Returns:
        Health status
    """
    # Check database connectivity
    try:
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return {
        "status": "healthy" if db_status == "healthy" else "unhealthy",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": settings.ENVIRONMENT,
        "database": db_status,
    }


@router.get("/ready")
async def readiness_check() -> dict:
    """Readiness check endpoint.

    Returns:
        Readiness status
    """
    return {
        "status": "ready",
        "timestamp": datetime.utcnow().isoformat(),
    }
