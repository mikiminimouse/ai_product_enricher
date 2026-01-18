"""Unit tests for cache service."""

from datetime import datetime

import pytest

from ai_product_enricher.models import (
    EnrichedProduct,
    EnrichmentMetadata,
    EnrichmentResult,
    ProductInput,
)
from ai_product_enricher.services.cache import CacheService


class TestCacheService:
    """Tests for CacheService."""

    @pytest.fixture
    def cache_service(self) -> CacheService:
        """Create a cache service for testing."""
        return CacheService(ttl_seconds=60, max_size=100)

    @pytest.fixture
    def sample_result(self) -> EnrichmentResult:
        """Create a sample enrichment result."""
        return EnrichmentResult(
            product=ProductInput(
                name="Test Product",
                brand="Test Brand",
                category="Test Category",
            ),
            enriched=EnrichedProduct(
                description="Test description",
                features=["Feature 1", "Feature 2"],
                specifications={"weight": "100g"},
                seo_keywords=["keyword1"],
            ),
            sources=[],
            metadata=EnrichmentMetadata(
                model_used="test-model",
                tokens_used=100,
                processing_time_ms=500,
                web_search_used=True,
                cached=False,
                timestamp=datetime.utcnow(),
            ),
        )

    def test_cache_set_and_get(
        self, cache_service: CacheService, sample_result: EnrichmentResult
    ) -> None:
        """Test setting and getting from cache."""
        # Set cache
        cache_service.set(
            result=sample_result,
            language="ru",
            fields=["description", "features"],
            web_search=True,
        )

        # Get from cache
        cached = cache_service.get(
            product_name="Test Product",
            product_brand="Test Brand",
            product_category="Test Category",
            language="ru",
            fields=["description", "features"],
            web_search=True,
        )

        assert cached is not None
        assert cached.product.name == "Test Product"
        assert cached.metadata.cached is True

    def test_cache_miss(self, cache_service: CacheService) -> None:
        """Test cache miss."""
        cached = cache_service.get(
            product_name="Nonexistent Product",
            language="ru",
        )
        assert cached is None

    def test_cache_key_sensitivity(
        self, cache_service: CacheService, sample_result: EnrichmentResult
    ) -> None:
        """Test that cache keys are sensitive to parameters."""
        # Set cache with one language
        cache_service.set(
            result=sample_result,
            language="ru",
            fields=["description"],
            web_search=True,
        )

        # Try to get with different language - should miss
        cached = cache_service.get(
            product_name="Test Product",
            product_brand="Test Brand",
            product_category="Test Category",
            language="en",  # Different language
            fields=["description"],
            web_search=True,
        )
        assert cached is None

    def test_cache_invalidate(
        self, cache_service: CacheService, sample_result: EnrichmentResult
    ) -> None:
        """Test cache invalidation."""
        # Set cache
        cache_service.set(
            result=sample_result,
            language="ru",
            fields=["description"],
            web_search=True,
        )

        # Verify it's in cache
        cached = cache_service.get(
            product_name="Test Product",
            product_brand="Test Brand",
            product_category="Test Category",
            language="ru",
            fields=["description"],
            web_search=True,
        )
        assert cached is not None

        # Invalidate
        result = cache_service.invalidate(
            product_name="Test Product",
            product_brand="Test Brand",
            product_category="Test Category",
            language="ru",
            fields=["description"],
            web_search=True,
        )
        assert result is True

        # Verify it's gone
        cached = cache_service.get(
            product_name="Test Product",
            product_brand="Test Brand",
            product_category="Test Category",
            language="ru",
            fields=["description"],
            web_search=True,
        )
        assert cached is None

    def test_cache_clear(
        self, cache_service: CacheService, sample_result: EnrichmentResult
    ) -> None:
        """Test clearing all cache."""
        # Set multiple entries
        cache_service.set(result=sample_result, language="ru")
        sample_result.product = ProductInput(name="Product 2")
        cache_service.set(result=sample_result, language="en")

        # Clear all
        count = cache_service.clear()
        assert count == 2

        # Verify stats
        stats = cache_service.get_stats()
        assert stats["size"] == 0

    def test_cache_stats(
        self, cache_service: CacheService, sample_result: EnrichmentResult
    ) -> None:
        """Test cache statistics."""
        # Initial stats
        stats = cache_service.get_stats()
        assert stats["size"] == 0
        assert stats["hits"] == 0
        assert stats["misses"] == 0

        # Add item
        cache_service.set(result=sample_result, language="ru")

        # Hit
        cache_service.get(
            product_name="Test Product",
            product_brand="Test Brand",
            product_category="Test Category",
            language="ru",
        )

        # Miss
        cache_service.get(product_name="Nonexistent", language="ru")

        # Check stats
        stats = cache_service.get_stats()
        assert stats["size"] == 1
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate_percent"] == 50.0

    def test_cache_case_insensitive(
        self, cache_service: CacheService, sample_result: EnrichmentResult
    ) -> None:
        """Test that cache is case-insensitive for product name."""
        # Set with lowercase
        cache_service.set(result=sample_result, language="ru")

        # Get with different case - should hit
        cached = cache_service.get(
            product_name="TEST PRODUCT",
            product_brand="TEST BRAND",
            product_category="TEST CATEGORY",
            language="ru",
        )
        assert cached is not None
