"""
Routers for health check endpoints.
"""

from fastapi import APIRouter
from sqlalchemy import text
from sqlalchemy.orm.session import Session

from database import get_db

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    """
    Simple health check endpoint.

    Returns the application status and database connectivity.
    """
    try:
        # Test database connection
        db: Session = next(get_db())
        db.execute(text("SELECT 1"))
        db_status = "connected"
        db.close()
    except Exception as e:
        db_status: str = f"disconnected: {str(e)}"

    return {
        "status": "healthy",
        "database": db_status,
        "message": "ELI5 Server is running successfully!",
    }
