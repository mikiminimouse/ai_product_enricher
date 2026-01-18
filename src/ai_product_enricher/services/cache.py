"""In-memory cache service for AI Product Enricher."""

import hashlib
import json
from typing import Any

from cachetools import TTLCache

from ..core import get_logger, settings
from ..models import EnrichmentResult

logger = get_logger(__name__)


class CacheService:
    """In-memory cache service for enrichment results.

    Cache key is based on:
    - Product name (case-insensitive)
    - Language
    - Fields to enrich
    - Web search flag
    """

    def __init__(
        self,
        ttl_seconds: int | None = None,
        max_size: int | None = None,
    ) -> None:
        """Initialize cache service.

        Args:
            ttl_seconds: Cache TTL in seconds (default from settings)
            max_size: Maximum cache size (default from settings)
        """
        self._ttl = ttl_seconds or settings.cache_ttl_seconds
        self._max_size = max_size or settings.cache_max_size
        self._cache: TTLCache[str, dict[str, Any]] = TTLCache(
            maxsize=self._max_size,
            ttl=self._ttl,
        )
        self._hits = 0
        self._misses = 0
        logger.info(
            "cache_initialized",
            ttl_seconds=self._ttl,
            max_size=self._max_size,
        )

    def _generate_key(
        self,
        product_name: str,
        language: str,
        fields: list[str],
        web_search: bool,
    ) -> str:
        """Generate cache key from enrichment parameters.

        Args:
            product_name: Product name from price list
            language: Enrichment language
            fields: Fields to enrich
            web_search: Whether web search is enabled

        Returns:
            MD5 hash as cache key
        """
        key_data = {
            "name": product_name.lower().strip(),
            "language": language,
            "fields": sorted(fields),
            "web_search": web_search,
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()

    def get(
        self,
        product_name: str,
        language: str = "ru",
        fields: list[str] | None = None,
        web_search: bool = True,
    ) -> EnrichmentResult | None:
        """Get cached enrichment result.

        Args:
            product_name: Product name from price list
            language: Enrichment language
            fields: Fields that were enriched
            web_search: Whether web search was enabled

        Returns:
            Cached EnrichmentResult or None if not found
        """
        if fields is None:
            fields = [
                "manufacturer",
                "trademark",
                "category",
                "model_name",
                "description",
                "features",
                "specifications",
                "seo_keywords",
            ]

        key = self._generate_key(product_name, language, fields, web_search)

        cached_data = self._cache.get(key)
        if cached_data is not None:
            self._hits += 1
            logger.debug("cache_hit", key=key[:8], product_name=product_name)
            result = EnrichmentResult.model_validate(cached_data)
            result.metadata.cached = True
            return result

        self._misses += 1
        logger.debug("cache_miss", key=key[:8], product_name=product_name)
        return None

    def set(
        self,
        result: EnrichmentResult,
        language: str = "ru",
        fields: list[str] | None = None,
        web_search: bool = True,
    ) -> None:
        """Store enrichment result in cache.

        Args:
            result: EnrichmentResult to cache
            language: Enrichment language
            fields: Fields that were enriched
            web_search: Whether web search was enabled
        """
        if fields is None:
            fields = [
                "manufacturer",
                "trademark",
                "category",
                "model_name",
                "description",
                "features",
                "specifications",
                "seo_keywords",
            ]

        key = self._generate_key(
            result.product.name,
            language,
            fields,
            web_search,
        )

        self._cache[key] = result.model_dump()
        logger.debug(
            "cache_set",
            key=key[:8],
            product_name=result.product.name,
        )

    def invalidate(
        self,
        product_name: str,
        language: str = "ru",
        fields: list[str] | None = None,
        web_search: bool = True,
    ) -> bool:
        """Invalidate cached enrichment result.

        Args:
            product_name: Product name
            language: Enrichment language
            fields: Fields that were enriched
            web_search: Whether web search was enabled

        Returns:
            True if entry was found and removed, False otherwise
        """
        if fields is None:
            fields = [
                "manufacturer",
                "trademark",
                "category",
                "model_name",
                "description",
                "features",
                "specifications",
                "seo_keywords",
            ]

        key = self._generate_key(product_name, language, fields, web_search)

        if key in self._cache:
            del self._cache[key]
            logger.debug("cache_invalidated", key=key[:8], product_name=product_name)
            return True
        return False

    def clear(self) -> int:
        """Clear all cached entries.

        Returns:
            Number of entries cleared
        """
        count = len(self._cache)
        self._cache.clear()
        logger.info("cache_cleared", entries_removed=count)
        return count

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        total_requests = self._hits + self._misses
        hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0.0

        return {
            "size": len(self._cache),
            "max_size": self._max_size,
            "ttl_seconds": self._ttl,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate_percent": round(hit_rate, 2),
        }
