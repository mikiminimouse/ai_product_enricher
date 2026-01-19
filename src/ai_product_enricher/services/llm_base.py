"""Abstract base interface for LLM clients."""

from abc import ABC, abstractmethod
from typing import Protocol, runtime_checkable

from ..models import EnrichedProduct, EnrichmentOptions, ProductInput, Source


@runtime_checkable
class LLMClient(Protocol):
    """Protocol for LLM clients that can enrich product data.

    All LLM clients (ZhipuAI, Cloud.ru, etc.) must implement this interface
    to be used interchangeably by the ProductEnricherService.
    """

    @property
    def provider_name(self) -> str:
        """Return the provider name for metadata (e.g., 'zhipuai', 'cloudru')."""
        ...

    @property
    def model_name(self) -> str:
        """Return the model name being used."""
        ...

    async def enrich_product(
        self,
        product: ProductInput,
        options: EnrichmentOptions,
    ) -> tuple[EnrichedProduct, list[Source], int, int]:
        """Enrich a product using the LLM.

        Args:
            product: Product to enrich
            options: Enrichment options

        Returns:
            Tuple of (EnrichedProduct, Sources, tokens_used, processing_time_ms)

        Raises:
            Exception: If API call fails (specific exception depends on provider)
        """
        ...

    async def health_check(self) -> bool:
        """Check if the LLM API is accessible.

        Returns:
            True if API is accessible, False otherwise
        """
        ...


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients.

    Provides common functionality and enforces the interface.
    Concrete implementations should inherit from this class.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name for metadata."""
        ...

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the model name being used."""
        ...

    @abstractmethod
    async def enrich_product(
        self,
        product: ProductInput,
        options: EnrichmentOptions,
    ) -> tuple[EnrichedProduct, list[Source], int, int]:
        """Enrich a product using the LLM."""
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the LLM API is accessible."""
        ...
