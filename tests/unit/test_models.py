"""Unit tests for Pydantic models."""

import pytest
from pydantic import ValidationError

from ai_product_enricher.models import (
    APIResponse,
    BatchEnrichmentRequest,
    BatchOptions,
    EnrichedProduct,
    EnrichmentMetadata,
    EnrichmentOptions,
    EnrichmentRequest,
    ProductInput,
)


class TestProductInput:
    """Tests for ProductInput model."""

    def test_valid_product_input(self) -> None:
        """Test creating a valid product input."""
        product = ProductInput(
            name="iPhone 15 Pro",
            category="smartphones",
            brand="Apple",
        )
        assert product.name == "iPhone 15 Pro"
        assert product.category == "smartphones"
        assert product.brand == "Apple"

    def test_minimal_product_input(self) -> None:
        """Test creating a product with only required fields."""
        product = ProductInput(name="Test Product")
        assert product.name == "Test Product"
        assert product.category is None
        assert product.brand is None

    def test_product_input_with_attributes(self) -> None:
        """Test creating a product with attributes."""
        product = ProductInput(
            name="Test Product",
            attributes={"color": "black", "size": "large"},
        )
        assert product.attributes == {"color": "black", "size": "large"}

    def test_empty_name_raises_error(self) -> None:
        """Test that empty name raises validation error."""
        with pytest.raises(ValidationError):
            ProductInput(name="")

    def test_get_search_query(self) -> None:
        """Test search query generation."""
        product = ProductInput(
            name="iPhone 15 Pro",
            brand="Apple",
            category="smartphones",
        )
        query = product.get_search_query()
        assert "Apple" in query
        assert "iPhone 15 Pro" in query
        assert "smartphones" in query

    def test_to_prompt_context(self) -> None:
        """Test prompt context generation."""
        product = ProductInput(
            name="iPhone 15 Pro",
            brand="Apple",
            category="smartphones",
            description="Flagship phone",
        )
        context = product.to_prompt_context()
        assert "iPhone 15 Pro" in context
        assert "Apple" in context
        assert "smartphones" in context
        assert "Flagship phone" in context


class TestEnrichmentOptions:
    """Tests for EnrichmentOptions model."""

    def test_default_options(self) -> None:
        """Test default enrichment options."""
        options = EnrichmentOptions()
        assert options.include_web_search is True
        assert options.language == "ru"
        assert "description" in options.fields
        assert options.search_recency == "month"

    def test_custom_options(self) -> None:
        """Test custom enrichment options."""
        options = EnrichmentOptions(
            include_web_search=False,
            language="en",
            fields=["description", "features"],
            max_features=5,
        )
        assert options.include_web_search is False
        assert options.language == "en"
        assert len(options.fields) == 2
        assert options.max_features == 5


class TestEnrichmentRequest:
    """Tests for EnrichmentRequest model."""

    def test_valid_request(self) -> None:
        """Test creating a valid enrichment request."""
        request = EnrichmentRequest(
            product=ProductInput(name="Test Product"),
            enrichment_options=EnrichmentOptions(language="en"),
        )
        assert request.product.name == "Test Product"
        assert request.enrichment_options is not None
        assert request.enrichment_options.language == "en"

    def test_request_without_options(self) -> None:
        """Test request with default options."""
        request = EnrichmentRequest(product=ProductInput(name="Test Product"))
        assert request.enrichment_options is None


class TestEnrichedProduct:
    """Tests for EnrichedProduct model."""

    def test_enriched_product_defaults(self) -> None:
        """Test default values for enriched product."""
        enriched = EnrichedProduct()
        assert enriched.description is None
        assert enriched.features == []
        assert enriched.specifications == {}
        assert enriched.seo_keywords == []

    def test_enriched_product_with_data(self) -> None:
        """Test enriched product with data."""
        enriched = EnrichedProduct(
            description="Great product",
            features=["Feature 1", "Feature 2"],
            specifications={"weight": "100g"},
            seo_keywords=["keyword1", "keyword2"],
        )
        assert enriched.description == "Great product"
        assert len(enriched.features) == 2
        assert enriched.specifications["weight"] == "100g"


class TestBatchOptions:
    """Tests for BatchOptions model."""

    def test_default_batch_options(self) -> None:
        """Test default batch options."""
        options = BatchOptions()
        assert options.max_concurrent == 5
        assert options.fail_strategy == "continue"
        assert options.timeout_per_product == 60

    def test_custom_batch_options(self) -> None:
        """Test custom batch options."""
        options = BatchOptions(
            max_concurrent=10,
            fail_strategy="stop",
            timeout_per_product=120,
        )
        assert options.max_concurrent == 10
        assert options.fail_strategy == "stop"
        assert options.timeout_per_product == 120

    def test_invalid_max_concurrent(self) -> None:
        """Test that invalid max_concurrent raises error."""
        with pytest.raises(ValidationError):
            BatchOptions(max_concurrent=0)
        with pytest.raises(ValidationError):
            BatchOptions(max_concurrent=100)


class TestBatchEnrichmentRequest:
    """Tests for BatchEnrichmentRequest model."""

    def test_valid_batch_request(self) -> None:
        """Test creating a valid batch request."""
        request = BatchEnrichmentRequest(
            products=[
                ProductInput(name="Product 1"),
                ProductInput(name="Product 2"),
            ]
        )
        assert len(request.products) == 2
        assert request.enrichment_options is None
        assert request.batch_options is None

    def test_empty_products_raises_error(self) -> None:
        """Test that empty products list raises error."""
        with pytest.raises(ValidationError):
            BatchEnrichmentRequest(products=[])


class TestAPIResponse:
    """Tests for APIResponse model."""

    def test_success_response(self) -> None:
        """Test creating a success response."""
        response = APIResponse.ok(data={"key": "value"})
        assert response.success is True
        assert response.data == {"key": "value"}
        assert response.error is None

    def test_fail_response(self) -> None:
        """Test creating a fail response."""
        from ai_product_enricher.models.common import ErrorDetail

        error = ErrorDetail(code="ERROR", message="Something went wrong")
        response = APIResponse.fail(error=error)
        assert response.success is False
        assert response.data is None
        assert response.error is not None
        assert response.error.code == "ERROR"
