"""Health check endpoints."""

import time
from typing import Any

from fastapi import APIRouter

from ... import __version__
from ..dependencies import EnricherServiceDep

router = APIRouter(tags=["Health"])

# Track application start time
_start_time = time.time()


@router.get(
    "/health",
    response_model=dict[str, Any],
    summary="Health Check",
    description="Check the health status of the application and its dependencies.",
)
async def health_check(enricher: EnricherServiceDep) -> dict[str, Any]:
    """Health check endpoint.

    Returns:
        Health status including:
        - Overall status
        - Application version
        - Zhipu API connectivity
        - Uptime in seconds
        - Cache statistics
    """
    health_data = await enricher.health_check()

    uptime_seconds = int(time.time() - _start_time)

    return {
        "status": "healthy" if health_data["zhipu_api"] == "connected" else "degraded",
        "version": __version__,
        "zhipu_api": health_data["zhipu_api"],
        "uptime_seconds": uptime_seconds,
        "cache": health_data["cache"],
    }


@router.get(
    "/metrics",
    response_model=dict[str, Any],
    summary="Application Metrics",
    description="Get application metrics including cache statistics.",
)
async def get_metrics(enricher: EnricherServiceDep) -> dict[str, Any]:
    """Get application metrics.

    Returns:
        Metrics including:
        - Cache statistics
        - Uptime
    """
    cache_stats = enricher.get_cache_stats()
    uptime_seconds = int(time.time() - _start_time)

    return {
        "uptime_seconds": uptime_seconds,
        "cache": cache_stats,
    }


@router.get(
    "/ping",
    response_model=dict[str, str],
    summary="Simple Ping",
    description="Simple ping endpoint for basic connectivity check.",
)
async def ping() -> dict[str, str]:
    """Simple ping endpoint.

    Returns:
        Pong response
    """
    return {"status": "pong"}
