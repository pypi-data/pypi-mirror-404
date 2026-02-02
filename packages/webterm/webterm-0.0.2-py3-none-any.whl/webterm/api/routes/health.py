"""Health check endpoint."""

from fastapi import APIRouter

from webterm.core.session import session_manager

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """Health check endpoint.

    Returns:
        Health status and session count
    """
    return {
        "status": "healthy",
        "sessions": session_manager.session_count,
    }
