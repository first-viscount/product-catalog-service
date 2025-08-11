"""Health check endpoints."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from src.core.config import settings
from src.core.database import get_db
from src.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get(
    "/health",
    summary="Health Check",
    description="""
Check the health status of the Product Catalog Service.

Returns the service status and optionally database connectivity.
This endpoint is used by load balancers and monitoring systems to determine service health.

**Response includes:**
- Service name and version
- Current status (healthy/unhealthy)
- Database connectivity status
- Timestamp of the check
    """,
    response_description="Service health status",
    responses={
        200: {
            "description": "Service is healthy",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "service": "product-catalog-service",
                        "version": "0.1.0",
                        "database": "connected",
                        "timestamp": "2025-01-29T12:00:00Z",
                    }
                }
            },
        },
        503: {
            "description": "Service is unhealthy",
            "content": {
                "application/json": {
                    "example": {
                        "status": "unhealthy",
                        "service": "product-catalog-service",
                        "version": "0.1.0",
                        "database": "disconnected",
                        "timestamp": "2025-01-29T12:00:00Z",
                        "error": "Database connection failed",
                    }
                }
            },
        },
    },
    tags=["health"],
)
async def health_check(db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    """Health check endpoint."""
    from datetime import UTC, datetime

    health_data = {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "timestamp": datetime.now(UTC).isoformat(),
    }

    try:
        # Test database connectivity
        if settings.database_url:
            await db.execute(text("SELECT 1"))
            health_data["database"] = "connected"
        else:
            health_data["database"] = "not configured"

        logger.debug("Health check passed", **health_data)
        return health_data

    except Exception as e:
        error_msg = f"Database health check failed: {str(e)}"
        logger.error("Health check failed", error=error_msg)
        
        health_data.update({
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
        })
        
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=health_data,
        )


@router.get(
    "/health/ready",
    summary="Readiness Check",
    description="""
Check if the Product Catalog Service is ready to serve traffic.

This is more comprehensive than the basic health check and verifies:
- Service is initialized
- Database is accessible
- All required dependencies are available

Used by Kubernetes readiness probes.
    """,
    response_description="Service readiness status",
    responses={
        200: {
            "description": "Service is ready",
            "content": {
                "application/json": {
                    "example": {
                        "ready": True,
                        "service": "product-catalog-service",
                        "version": "0.1.0",
                        "checks": {
                            "database": "connected",
                        },
                    }
                }
            },
        },
        503: {
            "description": "Service is not ready",
            "content": {
                "application/json": {
                    "example": {
                        "ready": False,
                        "service": "product-catalog-service",
                        "version": "0.1.0",
                        "checks": {
                            "database": "failed",
                        },
                        "error": "Database connection failed",
                    }
                }
            },
        },
    },
    tags=["health"],
)
async def readiness_check(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """Readiness check endpoint."""
    checks = {}
    ready = True
    error = None

    try:
        # Check database
        if settings.database_url:
            await db.execute(text("SELECT 1"))
            checks["database"] = "connected"
        else:
            checks["database"] = "not configured"

    except Exception as e:
        checks["database"] = "failed"
        ready = False
        error = f"Database check failed: {str(e)}"
        logger.error("Readiness check failed", error=error)

    response_data = {
        "ready": ready,
        "service": settings.app_name,
        "version": settings.app_version,
        "checks": checks,
    }

    if error:
        response_data["error"] = error

    if not ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=response_data,
        )

    return response_data