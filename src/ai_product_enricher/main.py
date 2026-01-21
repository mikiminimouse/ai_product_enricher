"""FastAPI application entry point."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from . import __version__
from .api.router import api_router
from .core import (
    AIProductEnricherError,
    ValidationError,
    get_logger,
    settings,
    setup_logging,
)

# Initialize logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan events handler."""
    # Startup
    logger.info(
        "application_starting",
        version=__version__,
        environment=settings.app_env,
        debug=settings.app_debug,
    )
    yield
    # Shutdown
    logger.info("application_shutting_down")


# Create FastAPI application
app = FastAPI(
    title="AI Product Enricher",
    description="Production-ready service for enriching product data using Zhipu AI (GLM-4.7) API with web search support",
    version=__version__,
    docs_url="/docs" if settings.docs_enabled else None,
    redoc_url="/redoc" if settings.docs_enabled else None,
    openapi_url="/openapi.json" if settings.docs_enabled else None,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.is_development else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handlers
@app.exception_handler(AIProductEnricherError)
async def handle_app_error(request: Request, exc: AIProductEnricherError) -> JSONResponse:
    """Handle application-specific errors."""
    logger.error(
        "application_error",
        error_code=exc.code,
        error_message=exc.message,
        path=request.url.path,
    )
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "success": False,
            "error": exc.to_dict(),
        },
    )


@app.exception_handler(ValidationError)
async def handle_validation_error(request: Request, exc: ValidationError) -> JSONResponse:
    """Handle validation errors."""
    logger.warning(
        "validation_error",
        error_message=exc.message,
        field=exc.field,
        path=request.url.path,
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": exc.to_dict(),
        },
    )


@app.exception_handler(Exception)
async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected errors."""
    logger.exception(
        "unexpected_error",
        error=str(exc),
        path=request.url.path,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred" if settings.is_production else str(exc),
            },
        },
    )


# Include API router
app.include_router(api_router)


# Root endpoint
@app.get("/", response_model=dict[str, Any])
async def root() -> dict[str, Any]:
    """Root endpoint with API information."""
    return {
        "name": "AI Product Enricher",
        "version": __version__,
        "docs": "/docs" if settings.app_debug or settings.is_development else None,
        "health": "/api/v1/health",
    }


def run() -> None:
    """Run the application using uvicorn."""
    import uvicorn

    uvicorn.run(
        "ai_product_enricher.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.is_development,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    run()
