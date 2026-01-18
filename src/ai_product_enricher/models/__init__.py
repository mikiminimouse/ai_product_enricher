"""Data models for AI Product Enricher."""

from .common import APIResponse, ErrorDetail, PaginatedResponse
from .enrichment import (
    BatchEnrichmentRequest,
    BatchEnrichmentResponse,
    BatchOptions,
    BatchResultItem,
    BatchSummary,
    EnrichedProduct,
    EnrichmentMetadata,
    EnrichmentOptions,
    EnrichmentRequest,
    EnrichmentResponse,
    EnrichmentResult,
    Source,
)
from .product import ProductInput

__all__ = [
    # Common
    "APIResponse",
    "ErrorDetail",
    "PaginatedResponse",
    # Product
    "ProductInput",
    # Enrichment
    "EnrichmentOptions",
    "EnrichmentRequest",
    "EnrichedProduct",
    "EnrichmentMetadata",
    "Source",
    "EnrichmentResult",
    "EnrichmentResponse",
    "BatchOptions",
    "BatchEnrichmentRequest",
    "BatchResultItem",
    "BatchSummary",
    "BatchEnrichmentResponse",
]
