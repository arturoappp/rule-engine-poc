"""
Health check endpoints.
"""

from fastapi import APIRouter, status
from pydantic import BaseModel
from app.utilities.logging import logger
from app.core.config import settings


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""
    status: str
    version: str


router = APIRouter()


@router.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
async def health_check():
    """Check the health of the service."""
    logger.info("Health check endpoint called")
    version = getattr(settings, "VERSION", "1.0.0")
    logger.debug(f"Returning health status: ok, version: {version}")

    return {
        "status": "ok",
        "version": version
    }
