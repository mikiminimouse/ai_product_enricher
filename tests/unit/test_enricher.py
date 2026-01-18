"""Unit tests for enricher service."""

from unittest.mock import AsyncMock

import pytest

from ai_product_enricher.models import (
    BatchEnrichmentRequest,
    BatchOptions,
    EnrichedProduct,
    EnrichmentOptions,
    ProductInput,
    Source,
)
from ai_product_enricher.services.cache import CacheService
from ai_product_enricher.services.enricher import ProductEnricherService


class TestProductEnricherService:
    """Tests for ProductEnricherService."""

    @pytest.fixture
    def mock_zhipu_client(self) -> AsyncMock:
        """Create a mock Zhipu client with manufacturer/trademark extraction."""
        mock = AsyncMock()
        mock.enrich_product = AsyncMock(
            return_value=(
                EnrichedProduct(
                    manufacturer="Foxconn Technology Group",
                    trademark="Apple",
                    category="Смартфоны",
                    model_name="iPhone 15 Pro Max 256GB",
                    description="Флагманский смартфон Apple",
                    features=["Чип A17 Pro", "Титановый корпус"],
                    specifications={"storage": "256GB"},
                    seo_keywords=["iphone 15 pro max купить"],
                ),
                [Source(title="Apple Official", url="https://apple.com")],
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
        """Test successful product enrichment with manufacturer/trademark extraction."""
        # Simplified input - only name and description
        product = ProductInput(
            name="Смартфон Apple iPhone 15 Pro Max 256GB Black Titanium",
            description="Флагманский смартфон с чипом A17 Pro",
        )
        options = EnrichmentOptions(
            language="ru",
            fields=["manufacturer", "trademark", "category", "description", "features"],
        )

        result = await enricher_service.enrich_product(product, options)

        assert "iPhone 15 Pro" in result.product.name
        assert result.enriched.manufacturer == "Foxconn Technology Group"
        assert result.enriched.trademark == "Apple"
        assert result.enriched.category == "Смартфоны"
        assert result.enriched.description == "Флагманский смартфон Apple"
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
        product = ProductInput(name="Смартфон Apple iPhone 15 Pro Max 256GB")
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
        product = ProductInput(name="Картридж HP 123XL черный оригинальный")
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
        """Test successful batch enrichment with simplified inputs."""
        request = BatchEnrichmentRequest(
            products=[
                ProductInput(name="Смартфон Samsung Galaxy S24 Ultra 512GB"),
                ProductInput(name="Планшет Apple iPad Pro 12.9 M2 256GB"),
            ],
            enrichment_options=EnrichmentOptions(
                language="ru",
                fields=["manufacturer", "trademark", "description"],
            ),
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
                EnrichedProduct(
                    manufacturer="Samsung Electronics",
                    trademark="Samsung",
                    description="Флагманский смартфон Samsung",
                ),
                [],
                100,
                500,
            ),
            Exception("API Error"),
        ]

        request = BatchEnrichmentRequest(
            products=[
                ProductInput(name="Смартфон Samsung Galaxy S24 Ultra"),
                ProductInput(name="Ноутбук ASUS ROG Strix G16"),
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
                ProductInput(name="Товар 1 из прайс-листа"),
                ProductInput(name="Товар 2 из прайс-листа"),
                ProductInput(name="Товар 3 из прайс-листа"),
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
