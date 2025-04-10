"""
Health check endpoints.
"""

from fastapi import APIRouter, status
from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""
    status: str
    version: str


router = APIRouter()


@router.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
async def health_check():
    """Check the health of the service."""
    return {
        "status": "ok",
        "version": "1.0.0"
    }