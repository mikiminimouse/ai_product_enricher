"""Unit tests for enricher service."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai_product_enricher.models import (
    BatchEnrichmentRequest,
    BatchOptions,
    EnrichedProduct,
    EnrichmentMetadata,
    EnrichmentOptions,
    EnrichmentResult,
    ProductInput,
    Source,
)
from ai_product_enricher.services.cache import CacheService
from ai_product_enricher.services.enricher import ProductEnricherService


class TestProductEnricherService:
    """Tests for ProductEnricherService."""

    @pytest.fixture
    def mock_zhipu_client(self) -> AsyncMock:
        """Create a mock Zhipu client."""
        mock = AsyncMock()
        mock.enrich_product = AsyncMock(
            return_value=(
                EnrichedProduct(
                    description="Test description",
                    features=["Feature 1", "Feature 2"],
                    specifications={"weight": "100g"},
                    seo_keywords=["keyword1"],
                ),
                [Source(title="Test Source", url="https://example.com")],
                500,  # tokens
                1000,  # processing time ms
            )
        )
        mock.health_check = AsyncMock(return_value=True)
        return mock

    @pytest.fixture
    def cache_service(self) -> CacheService:
        """Create a cache service for testing."""
        return CacheService(ttl_seconds=60, max_size=100)

    @pytest.fixture
    def enricher_service(
        self, mock_zhipu_client: AsyncMock, cache_service: CacheService
    ) -> ProductEnricherService:
        """Create enricher service with mocks."""
        return ProductEnricherService(
            zhipu_client=mock_zhipu_client,
            cache_service=cache_service,
        )

    @pytest.mark.asyncio
    async def test_enrich_product_success(
        self,
        enricher_service: ProductEnricherService,
        mock_zhipu_client: AsyncMock,
    ) -> None:
        """Test successful product enrichment."""
        product = ProductInput(name="Test Product", brand="Test Brand")
        options = EnrichmentOptions(language="ru")

        result = await enricher_service.enrich_product(product, options)

        assert result.product.name == "Test Product"
        assert result.enriched.description == "Test description"
        assert len(result.enriched.features) == 2
        assert result.metadata.tokens_used == 500
        assert result.metadata.web_search_used is True
        mock_zhipu_client.enrich_product.assert_called_once()

    @pytest.mark.asyncio
    async def test_enrich_product_uses_cache(
        self,
        enricher_service: ProductEnricherService,
        mock_zhipu_client: AsyncMock,
    ) -> None:
        """Test that enrichment uses cache."""
        product = ProductInput(name="Test Product", brand="Test Brand")
        options = EnrichmentOptions(language="ru")

        # First call - should call API
        result1 = await enricher_service.enrich_product(product, options)
        assert result1.metadata.cached is False
        assert mock_zhipu_client.enrich_product.call_count == 1

        # Second call - should use cache
        result2 = await enricher_service.enrich_product(product, options)
        assert result2.metadata.cached is True
        assert mock_zhipu_client.enrich_product.call_count == 1  # No additional calls

    @pytest.mark.asyncio
    async def test_enrich_product_skip_cache(
        self,
        enricher_service: ProductEnricherService,
        mock_zhipu_client: AsyncMock,
    ) -> None:
        """Test enrichment without cache."""
        product = ProductInput(name="Test Product")
        options = EnrichmentOptions()

        # First call
        await enricher_service.enrich_product(product, options, use_cache=False)
        assert mock_zhipu_client.enrich_product.call_count == 1

        # Second call - should still call API
        await enricher_service.enrich_product(product, options, use_cache=False)
        assert mock_zhipu_client.enrich_product.call_count == 2

    @pytest.mark.asyncio
    async def test_enrich_batch_success(
        self,
        enricher_service: ProductEnricherService,
        mock_zhipu_client: AsyncMock,
    ) -> None:
        """Test successful batch enrichment."""
        request = BatchEnrichmentRequest(
            products=[
                ProductInput(name="Product 1"),
                ProductInput(name="Product 2"),
            ],
            enrichment_options=EnrichmentOptions(language="en"),
            batch_options=BatchOptions(max_concurrent=2),
        )

        result = await enricher_service.enrich_batch(request)

        assert result["summary"]["total"] == 2
        assert result["summary"]["succeeded"] == 2
        assert result["summary"]["failed"] == 0
        assert len(result["results"]) == 2

    @pytest.mark.asyncio
    async def test_enrich_batch_with_failure(
        self,
        enricher_service: ProductEnricherService,
        mock_zhipu_client: AsyncMock,
    ) -> None:
        """Test batch enrichment with partial failure."""
        # Make second call fail
        mock_zhipu_client.enrich_product.side_effect = [
            (
                EnrichedProduct(description="Success"),
                [],
                100,
                500,
            ),
            Exception("API Error"),
        ]

        request = BatchEnrichmentRequest(
            products=[
                ProductInput(name="Product 1"),
                ProductInput(name="Product 2"),
            ],
            batch_options=BatchOptions(fail_strategy="continue"),
        )

        result = await enricher_service.enrich_batch(request, use_cache=False)

        assert result["summary"]["total"] == 2
        assert result["summary"]["succeeded"] == 1
        assert result["summary"]["failed"] == 1

    @pytest.mark.asyncio
    async def test_enrich_batch_stop_on_failure(
        self,
        enricher_service: ProductEnricherService,
        mock_zhipu_client: AsyncMock,
    ) -> None:
        """Test batch enrichment that stops on first failure."""
        # Make first call fail
        mock_zhipu_client.enrich_product.side_effect = Exception("API Error")

        request = BatchEnrichmentRequest(
            products=[
                ProductInput(name="Product 1"),
                ProductInput(name="Product 2"),
                ProductInput(name="Product 3"),
            ],
            batch_options=BatchOptions(fail_strategy="stop"),
        )

        result = await enricher_service.enrich_batch(request, use_cache=False)

        # Should stop after first failure
        assert result["summary"]["total"] == 1
        assert result["summary"]["failed"] == 1

    @pytest.mark.asyncio
    async def test_health_check(
        self,
        enricher_service: ProductEnricherService,
        mock_zhipu_client: AsyncMock,
    ) -> None:
        """Test health check."""
        result = await enricher_service.health_check()

        assert result["zhipu_api"] == "connected"
        assert "cache" in result
        mock_zhipu_client.health_check.assert_called_once()

    def test_get_cache_stats(
        self,
        enricher_service: ProductEnricherService,
    ) -> None:
        """Test getting cache statistics."""
        stats = enricher_service.get_cache_stats()

        assert "size" in stats
        assert "hits" in stats
        assert "misses" in stats
        assert "hit_rate_percent" in stats
