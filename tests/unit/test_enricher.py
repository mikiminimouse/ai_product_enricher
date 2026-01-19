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
from ai_product_enricher.services.cloudru_client import CloudruClient
from ai_product_enricher.services.enricher import ProductEnricherService
from ai_product_enricher.services.zhipu_client import ZhipuAIClient


class TestProductEnricherService:
    """Tests for ProductEnricherService."""

    @pytest.fixture
    def mock_zhipu_client(self) -> AsyncMock:
        """Create a mock Zhipu client with manufacturer/trademark extraction."""
        mock = AsyncMock()
        mock.provider_name = "zhipuai"
        mock.model_name = "GLM-4.7"
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
    def mock_cloudru_client(self) -> AsyncMock:
        """Create a mock Cloud.ru client for Russian products."""
        mock = AsyncMock()
        mock.provider_name = "cloudru"
        mock.model_name = "ai-sage/GigaChat3-10B-A1.8B"
        mock.is_configured = True
        mock.enrich_product = AsyncMock(
            return_value=(
                EnrichedProduct(
                    manufacturer="Яндекс",
                    trademark="Яндекс",
                    category="Умные колонки",
                    model_name="Станция Макс",
                    description="Флагманская умная колонка Яндекс",
                    features=["Голосовой помощник Алиса", "Качественный звук"],
                    specifications={"тип": "умная колонка"},
                    seo_keywords=["яндекс станция купить"],
                ),
                [],  # Cloud.ru doesn't return sources
                400,  # tokens
                800,  # processing time ms
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
        self, mock_zhipu_client: AsyncMock, mock_cloudru_client: AsyncMock, cache_service: CacheService
    ) -> ProductEnricherService:
        """Create enricher service with both LLM clients mocked."""
        return ProductEnricherService(
            zhipu_client=mock_zhipu_client,
            cloudru_client=mock_cloudru_client,
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


class TestLLMRouting:
    """Tests for LLM provider routing based on country_origin."""

    @pytest.fixture
    def mock_zhipu_client(self) -> AsyncMock:
        """Create a mock Zhipu client."""
        mock = AsyncMock()
        mock.provider_name = "zhipuai"
        mock.model_name = "GLM-4.7"
        mock.enrich_product = AsyncMock(
            return_value=(
                EnrichedProduct(
                    manufacturer="Foxconn",
                    trademark="Apple",
                    category="Смартфоны",
                    description="iPhone",
                ),
                [Source(title="Apple", url="https://apple.com")],
                500,
                1000,
            )
        )
        mock.health_check = AsyncMock(return_value=True)
        return mock

    @pytest.fixture
    def mock_cloudru_client(self) -> AsyncMock:
        """Create a mock Cloud.ru client."""
        mock = AsyncMock()
        mock.provider_name = "cloudru"
        mock.model_name = "ai-sage/GigaChat3-10B-A1.8B"
        mock.is_configured = True
        mock.enrich_product = AsyncMock(
            return_value=(
                EnrichedProduct(
                    manufacturer="Яндекс",
                    trademark="Яндекс",
                    category="Умные колонки",
                    description="Яндекс Станция",
                ),
                [],
                400,
                800,
            )
        )
        mock.health_check = AsyncMock(return_value=True)
        return mock

    @pytest.fixture
    def enricher_service(
        self, mock_zhipu_client: AsyncMock, mock_cloudru_client: AsyncMock
    ) -> ProductEnricherService:
        """Create enricher service with both clients."""
        return ProductEnricherService(
            zhipu_client=mock_zhipu_client,
            cloudru_client=mock_cloudru_client,
            cache_service=CacheService(),
        )

    @pytest.mark.asyncio
    async def test_routes_russian_product_to_cloudru(
        self,
        enricher_service: ProductEnricherService,
        mock_zhipu_client: AsyncMock,
        mock_cloudru_client: AsyncMock,
    ) -> None:
        """Test that Russian products (RU) are routed to Cloud.ru."""
        product = ProductInput(
            name="Яндекс Станция Макс",
            country_origin="RU",
        )

        result = await enricher_service.enrich_product(product, use_cache=False)

        # Should use Cloud.ru
        mock_cloudru_client.enrich_product.assert_called_once()
        mock_zhipu_client.enrich_product.assert_not_called()
        assert result.metadata.llm_provider == "cloudru"
        assert result.enriched.manufacturer == "Яндекс"

    @pytest.mark.asyncio
    async def test_routes_russian_product_rus_code(
        self,
        enricher_service: ProductEnricherService,
        mock_cloudru_client: AsyncMock,
    ) -> None:
        """Test that Russian products with RUS code are routed to Cloud.ru."""
        product = ProductInput(
            name="Касперский Антивирус",
            country_origin="RUS",
        )

        result = await enricher_service.enrich_product(product, use_cache=False)

        mock_cloudru_client.enrich_product.assert_called_once()
        assert result.metadata.llm_provider == "cloudru"

    @pytest.mark.asyncio
    async def test_routes_foreign_product_to_zhipu(
        self,
        enricher_service: ProductEnricherService,
        mock_zhipu_client: AsyncMock,
        mock_cloudru_client: AsyncMock,
    ) -> None:
        """Test that foreign products are routed to Zhipu AI."""
        product = ProductInput(
            name="iPhone 15 Pro",
            country_origin="CN",
        )

        result = await enricher_service.enrich_product(product, use_cache=False)

        # Should use Zhipu
        mock_zhipu_client.enrich_product.assert_called_once()
        mock_cloudru_client.enrich_product.assert_not_called()
        assert result.metadata.llm_provider == "zhipuai"

    @pytest.mark.asyncio
    async def test_routes_no_country_to_zhipu(
        self,
        enricher_service: ProductEnricherService,
        mock_zhipu_client: AsyncMock,
        mock_cloudru_client: AsyncMock,
    ) -> None:
        """Test that products without country_origin use Zhipu AI."""
        product = ProductInput(
            name="Generic Product",
            country_origin=None,
        )

        result = await enricher_service.enrich_product(product, use_cache=False)

        mock_zhipu_client.enrich_product.assert_called_once()
        mock_cloudru_client.enrich_product.assert_not_called()
        assert result.metadata.llm_provider == "zhipuai"

    @pytest.mark.asyncio
    async def test_fallback_to_zhipu_when_cloudru_not_configured(
        self,
        mock_zhipu_client: AsyncMock,
    ) -> None:
        """Test that Russian products fall back to Zhipu when Cloud.ru is not configured."""
        # Create unconfigured Cloud.ru client
        mock_cloudru = AsyncMock()
        mock_cloudru.is_configured = False

        service = ProductEnricherService(
            zhipu_client=mock_zhipu_client,
            cloudru_client=mock_cloudru,
        )

        product = ProductInput(
            name="Яндекс Станция",
            country_origin="RU",
        )

        result = await service.enrich_product(product, use_cache=False)

        # Should fall back to Zhipu
        mock_zhipu_client.enrich_product.assert_called_once()
        mock_cloudru.enrich_product.assert_not_called()
        assert result.metadata.llm_provider == "zhipuai"

    @pytest.mark.asyncio
    async def test_health_check_both_providers(
        self,
        enricher_service: ProductEnricherService,
        mock_zhipu_client: AsyncMock,
        mock_cloudru_client: AsyncMock,
    ) -> None:
        """Test health check returns status of both providers."""
        result = await enricher_service.health_check()

        assert result["zhipu_api"] == "connected"
        assert result["cloudru_api"] == "connected"
        mock_zhipu_client.health_check.assert_called_once()
        mock_cloudru_client.health_check.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_check_cloudru_not_configured(
        self,
        mock_zhipu_client: AsyncMock,
    ) -> None:
        """Test health check when Cloud.ru is not configured."""
        mock_cloudru = AsyncMock()
        mock_cloudru.is_configured = False

        service = ProductEnricherService(
            zhipu_client=mock_zhipu_client,
            cloudru_client=mock_cloudru,
        )

        result = await service.health_check()

        assert result["zhipu_api"] == "connected"
        assert result["cloudru_api"] == "not_configured"
