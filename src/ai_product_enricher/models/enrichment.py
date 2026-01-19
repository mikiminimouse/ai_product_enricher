"""Enrichment models for AI Product Enricher."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from .product import ProductInput


class EnrichmentOptions(BaseModel):
    """Options for product enrichment."""

    include_web_search: bool = Field(
        default=True,
        description="Whether to use web search for enrichment",
    )
    language: str = Field(
        default="ru",
        min_length=2,
        max_length=5,
        description="Language for enriched content (ISO 639-1 code)",
    )
    fields: list[str] = Field(
        default_factory=lambda: [
            "manufacturer",
            "trademark",
            "category",
            "model_name",
            "description",
            "features",
            "specifications",
            "seo_keywords",
        ],
        description="Fields to enrich",
    )
    search_recency: Literal["day", "week", "month", "year"] = Field(
        default="month",
        description="Recency filter for web search results",
    )
    max_features: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum number of features to extract",
    )
    max_keywords: int = Field(
        default=15,
        ge=1,
        le=50,
        description="Maximum number of SEO keywords",
    )


class EnrichmentRequest(BaseModel):
    """Request model for single product enrichment."""

    product: ProductInput = Field(..., description="Product to enrich")
    enrichment_options: EnrichmentOptions | None = Field(
        default=None,
        description="Enrichment options (defaults applied if not provided)",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "product": {
                        "name": "Смартфон Apple iPhone 15 Pro Max 256GB Black Titanium",
                        "description": "Новейший флагман с чипом A17 Pro",
                    },
                    "enrichment_options": {
                        "include_web_search": True,
                        "language": "ru",
                        "fields": ["manufacturer", "trademark", "description", "features", "specifications"],
                    },
                },
                {
                    "product": {
                        "name": "Картридж HP 123XL черный оригинальный F6V19AE",
                        "description": None,
                    },
                    "enrichment_options": {
                        "include_web_search": False,
                        "language": "ru",
                    },
                },
            ]
        }
    }


class Source(BaseModel):
    """Web search source model."""

    title: str = Field(..., description="Source title")
    url: str = Field(..., description="Source URL")
    date: str | None = Field(default=None, description="Source date")


class EnrichedProduct(BaseModel):
    """Enriched product data.

    Includes extracted manufacturer and trademark which are determined
    from product name, description, and optionally web search.
    """

    # Extracted identification fields (from name/description/web search)
    manufacturer: str | None = Field(
        default=None,
        description="Extracted manufacturer - company that physically produces the product",
    )
    trademark: str | None = Field(
        default=None,
        description="Extracted trademark/brand - brand name under which product is sold",
    )
    category: str | None = Field(
        default=None,
        description="Determined product category",
    )
    model_name: str | None = Field(
        default=None,
        description="Extracted product model name/number",
    )

    # Enriched content fields
    description: str | None = Field(default=None, description="Enriched description")
    features: list[str] = Field(default_factory=list, description="Key product features")
    specifications: dict[str, Any] = Field(
        default_factory=dict, description="Technical specifications"
    )
    seo_keywords: list[str] = Field(default_factory=list, description="SEO keywords")
    marketing_copy: str | None = Field(default=None, description="Marketing text")
    pros: list[str] = Field(default_factory=list, description="Product advantages")
    cons: list[str] = Field(default_factory=list, description="Product disadvantages")


class EnrichmentMetadata(BaseModel):
    """Metadata about the enrichment process."""

    model_used: str = Field(..., description="AI model used for enrichment")
    llm_provider: str = Field(
        default="zhipuai",
        description="LLM provider used for enrichment (zhipuai, cloudru)",
    )
    tokens_used: int = Field(..., ge=0, description="Total tokens consumed")
    processing_time_ms: int = Field(..., ge=0, description="Processing time in milliseconds")
    web_search_used: bool = Field(..., description="Whether web search was used")
    cached: bool = Field(default=False, description="Whether result was from cache")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Enrichment timestamp")


class EnrichmentResult(BaseModel):
    """Result of product enrichment."""

    product: ProductInput = Field(..., description="Original product input")
    enriched: EnrichedProduct = Field(..., description="Enriched product data")
    sources: list[Source] = Field(default_factory=list, description="Web search sources")
    metadata: EnrichmentMetadata = Field(..., description="Enrichment metadata")


class EnrichmentResponse(BaseModel):
    """API response for single product enrichment."""

    success: bool = Field(default=True, description="Whether enrichment was successful")
    data: EnrichmentResult | None = Field(default=None, description="Enrichment result")
    error: dict[str, Any] | None = Field(default=None, description="Error details if failed")


# Batch enrichment models


class BatchOptions(BaseModel):
    """Options for batch processing."""

    max_concurrent: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum concurrent enrichment requests",
    )
    fail_strategy: Literal["continue", "stop"] = Field(
        default="continue",
        description="Strategy when enrichment fails: continue or stop",
    )
    timeout_per_product: int = Field(
        default=60,
        ge=10,
        le=300,
        description="Timeout per product in seconds",
    )


class BatchEnrichmentRequest(BaseModel):
    """Request model for batch product enrichment."""

    products: list[ProductInput] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="List of products to enrich",
    )
    enrichment_options: EnrichmentOptions | None = Field(
        default=None,
        description="Enrichment options applied to all products",
    )
    batch_options: BatchOptions | None = Field(
        default=None,
        description="Batch processing options",
    )


class BatchResultItem(BaseModel):
    """Single item result in batch processing."""

    index: int = Field(..., ge=0, description="Index of product in original request")
    success: bool = Field(..., description="Whether this product enrichment succeeded")
    result: EnrichmentResult | None = Field(default=None, description="Enrichment result")
    error: str | None = Field(default=None, description="Error message if failed")


class BatchSummary(BaseModel):
    """Summary of batch processing."""

    total: int = Field(..., ge=0, description="Total products processed")
    succeeded: int = Field(..., ge=0, description="Number of successful enrichments")
    failed: int = Field(..., ge=0, description="Number of failed enrichments")
    total_tokens: int = Field(..., ge=0, description="Total tokens used")
    total_time_ms: int = Field(..., ge=0, description="Total processing time in milliseconds")


class BatchEnrichmentResponse(BaseModel):
    """API response for batch product enrichment."""

    success: bool = Field(default=True, description="Whether batch processing completed")
    data: dict[str, Any] | None = Field(default=None, description="Batch results and summary")
    error: dict[str, Any] | None = Field(default=None, description="Error details if failed")
