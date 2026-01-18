"""Product enrichment service."""

import asyncio
import time
from datetime import datetime
from typing import Any

from ..core import EnrichmentError, get_logger, settings
from ..models import (
    BatchEnrichmentRequest,
    BatchOptions,
    BatchResultItem,
    BatchSummary,
    EnrichmentMetadata,
    EnrichmentOptions,
    EnrichmentResult,
    ProductInput,
)
from .cache import CacheService
from .zhipu_client import ZhipuAIClient

logger = get_logger(__name__)


class ProductEnricherService:
    """Service for enriching product data."""

    def __init__(
        self,
        zhipu_client: ZhipuAIClient | None = None,
        cache_service: CacheService | None = None,
    ) -> None:
        """Initialize enricher service.

        Args:
            zhipu_client: Zhipu AI client (creates default if not provided)
            cache_service: Cache service (creates default if not provided)
        """
        self._zhipu_client = zhipu_client or ZhipuAIClient()
        self._cache = cache_service or CacheService()

        logger.info("enricher_service_initialized")

    async def enrich_product(
        self,
        product: ProductInput,
        options: EnrichmentOptions | None = None,
        use_cache: bool = True,
    ) -> EnrichmentResult:
        """Enrich a single product.

        Args:
            product: Product to enrich
            options: Enrichment options (uses defaults if not provided)
            use_cache: Whether to use cache

        Returns:
            EnrichmentResult with enriched data

        Raises:
            EnrichmentError: If enrichment fails
        """
        options = options or EnrichmentOptions()

        logger.info(
            "enriching_product",
            product_name=product.name,
            language=options.language,
            web_search=options.include_web_search,
        )

        # Check cache first
        if use_cache:
            cached = self._cache.get(
                product_name=product.name,
                product_brand=product.brand,
                product_category=product.category,
                language=options.language,
                fields=options.fields,
                web_search=options.include_web_search,
            )
            if cached:
                logger.info("returning_cached_result", product_name=product.name)
                return cached

        try:
            # Call Zhipu AI for enrichment
            (
                enriched,
                sources,
                tokens_used,
                processing_time_ms,
            ) = await self._zhipu_client.enrich_product(product, options)

            # Build result
            metadata = EnrichmentMetadata(
                model_used=settings.zhipuai_model,
                tokens_used=tokens_used,
                processing_time_ms=processing_time_ms,
                web_search_used=options.include_web_search,
                cached=False,
                timestamp=datetime.utcnow(),
            )

            result = EnrichmentResult(
                product=product,
                enriched=enriched,
                sources=sources,
                metadata=metadata,
            )

            # Cache the result
            if use_cache:
                self._cache.set(
                    result=result,
                    language=options.language,
                    fields=options.fields,
                    web_search=options.include_web_search,
                )

            logger.info(
                "product_enriched",
                product_name=product.name,
                tokens=tokens_used,
                time_ms=processing_time_ms,
            )

            return result

        except Exception as e:
            logger.error(
                "enrichment_failed",
                product_name=product.name,
                error=str(e),
            )
            raise EnrichmentError(
                message=f"Failed to enrich product: {e!s}",
                product_name=product.name,
                stage="api_call",
            ) from e

    async def enrich_batch(
        self,
        request: BatchEnrichmentRequest,
        use_cache: bool = True,
    ) -> dict[str, Any]:
        """Enrich multiple products in batch.

        Args:
            request: Batch enrichment request
            use_cache: Whether to use cache

        Returns:
            Dictionary with results and summary
        """
        start_time = time.time()

        options = request.enrichment_options or EnrichmentOptions()
        batch_options = request.batch_options or BatchOptions()

        logger.info(
            "batch_enrichment_started",
            total_products=len(request.products),
            max_concurrent=batch_options.max_concurrent,
        )

        results: list[BatchResultItem] = []
        total_tokens = 0
        succeeded = 0
        failed = 0

        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(batch_options.max_concurrent)

        async def process_product(index: int, product: ProductInput) -> BatchResultItem:
            """Process single product with semaphore."""
            async with semaphore:
                try:
                    result = await asyncio.wait_for(
                        self.enrich_product(product, options, use_cache),
                        timeout=batch_options.timeout_per_product,
                    )
                    return BatchResultItem(
                        index=index,
                        success=True,
                        result=result,
                        error=None,
                    )
                except TimeoutError:
                    return BatchResultItem(
                        index=index,
                        success=False,
                        result=None,
                        error=f"Timeout after {batch_options.timeout_per_product}s",
                    )
                except Exception as e:
                    return BatchResultItem(
                        index=index,
                        success=False,
                        result=None,
                        error=str(e),
                    )

        # Process products based on fail strategy
        if batch_options.fail_strategy == "continue":
            # Process all products concurrently
            tasks = [process_product(i, product) for i, product in enumerate(request.products)]
            results = await asyncio.gather(*tasks)
        else:
            # Stop on first failure
            for i, product in enumerate(request.products):
                result = await process_product(i, product)
                results.append(result)
                if not result.success:
                    logger.warning(
                        "batch_stopped_on_failure",
                        index=i,
                        product_name=product.name,
                    )
                    break

        # Calculate summary
        for result in results:
            if result.success and result.result:
                succeeded += 1
                total_tokens += result.result.metadata.tokens_used
            else:
                failed += 1

        total_time_ms = int((time.time() - start_time) * 1000)

        summary = BatchSummary(
            total=len(results),
            succeeded=succeeded,
            failed=failed,
            total_tokens=total_tokens,
            total_time_ms=total_time_ms,
        )

        logger.info(
            "batch_enrichment_completed",
            total=summary.total,
            succeeded=summary.succeeded,
            failed=summary.failed,
            total_time_ms=total_time_ms,
        )

        return {
            "results": [r.model_dump() for r in results],
            "summary": summary.model_dump(),
        }

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Cache statistics dictionary
        """
        return self._cache.get_stats()

    async def health_check(self) -> dict[str, Any]:
        """Perform health check.

        Returns:
            Health check result
        """
        zhipu_healthy = await self._zhipu_client.health_check()
        cache_stats = self._cache.get_stats()

        return {
            "zhipu_api": "connected" if zhipu_healthy else "disconnected",
            "cache": cache_stats,
        }
