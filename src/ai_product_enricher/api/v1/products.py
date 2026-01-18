"""Product enrichment endpoints."""

from typing import Any

from fastapi import APIRouter, HTTPException, status

from ...core import EnrichmentError, ValidationError, ZhipuAPIError, get_logger
from ...models import (
    BatchEnrichmentRequest,
    BatchEnrichmentResponse,
    EnrichmentRequest,
    EnrichmentResponse,
)
from ..dependencies import EnricherServiceDep

router = APIRouter(prefix="/products", tags=["Products"])
logger = get_logger(__name__)


@router.post(
    "/enrich",
    response_model=EnrichmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Enrich Product",
    description="Enrich a single product with AI-generated content using Zhipu AI.",
    responses={
        200: {"description": "Product enriched successfully"},
        400: {"description": "Validation error"},
        500: {"description": "Internal server error"},
        502: {"description": "Zhipu AI API error"},
    },
)
async def enrich_product(
    request: EnrichmentRequest,
    enricher: EnricherServiceDep,
) -> EnrichmentResponse:
    """Enrich a single product.

    Args:
        request: Enrichment request with product and options
        enricher: Injected enricher service

    Returns:
        EnrichmentResponse with enriched product data

    Raises:
        HTTPException: On validation or API errors
    """
    logger.info(
        "enrich_product_request",
        product_name=request.product.name,
        options=request.enrichment_options.model_dump() if request.enrichment_options else None,
    )

    try:
        result = await enricher.enrich_product(
            product=request.product,
            options=request.enrichment_options,
            use_cache=True,
        )

        return EnrichmentResponse(
            success=True,
            data=result,
            error=None,
        )

    except ValidationError as e:
        logger.warning("validation_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.to_dict(),
        ) from e

    except ZhipuAPIError as e:
        logger.error("zhipu_api_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=e.to_dict(),
        ) from e

    except EnrichmentError as e:
        logger.error("enrichment_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.to_dict(),
        ) from e

    except Exception as e:
        logger.exception("unexpected_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "INTERNAL_ERROR", "message": str(e)},
        ) from e


@router.post(
    "/enrich/batch",
    response_model=BatchEnrichmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Batch Enrich Products",
    description="Enrich multiple products in batch with concurrency control.",
    responses={
        200: {"description": "Batch processing completed"},
        400: {"description": "Validation error"},
        500: {"description": "Internal server error"},
    },
)
async def enrich_batch(
    request: BatchEnrichmentRequest,
    enricher: EnricherServiceDep,
) -> BatchEnrichmentResponse:
    """Enrich multiple products in batch.

    Args:
        request: Batch enrichment request with products and options
        enricher: Injected enricher service

    Returns:
        BatchEnrichmentResponse with results and summary

    Raises:
        HTTPException: On validation or processing errors
    """
    logger.info(
        "batch_enrich_request",
        total_products=len(request.products),
        batch_options=request.batch_options.model_dump() if request.batch_options else None,
    )

    try:
        result = await enricher.enrich_batch(
            request=request,
            use_cache=True,
        )

        return BatchEnrichmentResponse(
            success=True,
            data=result,
            error=None,
        )

    except ValidationError as e:
        logger.warning("validation_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.to_dict(),
        ) from e

    except Exception as e:
        logger.exception("batch_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "BATCH_ERROR", "message": str(e)},
        ) from e


@router.get(
    "/cache/stats",
    response_model=dict[str, Any],
    summary="Cache Statistics",
    description="Get cache statistics for product enrichment.",
)
async def get_cache_stats(enricher: EnricherServiceDep) -> dict[str, Any]:
    """Get cache statistics.

    Args:
        enricher: Injected enricher service

    Returns:
        Cache statistics
    """
    return enricher.get_cache_stats()


@router.post(
    "/cache/clear",
    response_model=dict[str, Any],
    summary="Clear Cache",
    description="Clear all cached enrichment results.",
)
async def clear_cache(enricher: EnricherServiceDep) -> dict[str, Any]:
    """Clear all cached entries.

    Args:
        enricher: Injected enricher service

    Returns:
        Number of entries cleared
    """
    count = enricher._cache.clear()
    logger.info("cache_cleared_via_api", entries_removed=count)
    return {"cleared": count}
