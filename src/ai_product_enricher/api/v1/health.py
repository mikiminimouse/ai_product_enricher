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
        - Cloud.ru API connectivity
        - Uptime in seconds
        - Cache statistics
    """
    health_data = await enricher.health_check()

    uptime_seconds = int(time.time() - _start_time)

    # Determine overall status
    # healthy: primary provider (zhipu) is connected
    # degraded: primary provider down or secondary provider down when configured
    zhipu_ok = health_data["zhipu_api"] == "connected"
    cloudru_ok = health_data["cloudru_api"] in ("connected", "not_configured")

    if zhipu_ok and cloudru_ok:
        status = "healthy"
    elif zhipu_ok:
        status = "degraded"  # Cloud.ru configured but not working
    else:
        status = "unhealthy"  # Primary provider down

    return {
        "status": status,
        "version": __version__,
        "zhipu_api": health_data["zhipu_api"],
        "cloudru_api": health_data["cloudru_api"],
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
