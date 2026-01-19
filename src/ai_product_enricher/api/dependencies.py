"""Dependency injection for FastAPI."""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from ..services import CacheService, CloudruClient, ProductEnricherService, ZhipuAIClient


@lru_cache
def get_zhipu_client() -> ZhipuAIClient:
    """Get singleton Zhipu AI client."""
    return ZhipuAIClient()


@lru_cache
def get_cloudru_client() -> CloudruClient:
    """Get singleton Cloud.ru client."""
    return CloudruClient()


@lru_cache
def get_cache_service() -> CacheService:
    """Get singleton cache service."""
    return CacheService()


@lru_cache
def get_enricher_service() -> ProductEnricherService:
    """Get singleton enricher service with both LLM providers."""
    return ProductEnricherService(
        zhipu_client=get_zhipu_client(),
        cloudru_client=get_cloudru_client(),
        cache_service=get_cache_service(),
    )


# Type aliases for dependency injection
ZhipuClientDep = Annotated[ZhipuAIClient, Depends(get_zhipu_client)]
CloudruClientDep = Annotated[CloudruClient, Depends(get_cloudru_client)]
CacheServiceDep = Annotated[CacheService, Depends(get_cache_service)]
EnricherServiceDep = Annotated[ProductEnricherService, Depends(get_enricher_service)]
