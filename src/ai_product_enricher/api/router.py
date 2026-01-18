"""Main API router configuration."""

from fastapi import APIRouter

from .v1 import health, products

# Create main API router with version prefix
api_router = APIRouter(prefix="/api/v1")

# Include sub-routers
api_router.include_router(products.router)
api_router.include_router(health.router)
