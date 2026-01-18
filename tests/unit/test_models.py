"""Unit tests for Pydantic models."""

import pytest
from pydantic import ValidationError

from ai_product_enricher.models import (
    APIResponse,
    BatchEnrichmentRequest,
    BatchOptions,
    EnrichedProduct,
    EnrichmentOptions,
    EnrichmentRequest,
    ProductInput,
)


class TestProductInput:
    """Tests for ProductInput model."""

    def test_valid_product_input(self) -> None:
        """Test creating a valid product input with name from price list."""
        product = ProductInput(
            name="Смартфон Apple iPhone 15 Pro Max 256GB Black Titanium",
            description="Флагманский смартфон с чипом A17 Pro",
        )
        assert "iPhone 15 Pro" in product.name
        assert product.description is not None

    def test_minimal_product_input(self) -> None:
        """Test creating a product with only name (typical price list entry)."""
        product = ProductInput(name="Картридж HP 123XL черный оригинальный")
        assert product.name == "Картридж HP 123XL черный оригинальный"
        assert product.description is None

    def test_product_input_with_description(self) -> None:
        """Test creating a product with description containing specs."""
        product = ProductInput(
            name="Ноутбук ASUS ROG Strix G16 G614JI-N3132",
            description="Intel Core i9, RTX 4070, 32GB RAM, 1TB SSD",
        )
        assert "ROG Strix" in product.name
        assert "RTX 4070" in product.description

    def test_empty_name_raises_error(self) -> None:
        """Test that empty name raises validation error."""
        with pytest.raises(ValidationError):
            ProductInput(name="")

    def test_get_search_query(self) -> None:
        """Test search query generation uses full product name."""
        product = ProductInput(
            name="Смартфон Samsung Galaxy S24 Ultra 512GB Titanium Gray",
        )
        query = product.get_search_query()
        assert "Samsung Galaxy S24 Ultra" in query

    def test_to_prompt_context(self) -> None:
        """Test prompt context generation."""
        product = ProductInput(
            name="Пылесос Dyson V15 Detect Absolute",
            description="Беспроводной с лазерной подсветкой пыли",
        )
        context = product.to_prompt_context()
        assert "Dyson V15 Detect" in context
        assert "лазерной подсветкой" in context


class TestEnrichmentOptions:
    """Tests for EnrichmentOptions model."""

    def test_default_options(self) -> None:
        """Test default enrichment options include new identification fields."""
        options = EnrichmentOptions()
        assert options.include_web_search is True
        assert options.language == "ru"
        assert "manufacturer" in options.fields
        assert "trademark" in options.fields
        assert "category" in options.fields
        assert "description" in options.fields
        assert options.search_recency == "month"

    def test_custom_options(self) -> None:
        """Test custom enrichment options."""
        options = EnrichmentOptions(
            include_web_search=False,
            language="en",
            fields=["manufacturer", "trademark", "description"],
            max_features=5,
        )
        assert options.include_web_search is False
        assert options.language == "en"
        assert len(options.fields) == 3
        assert options.max_features == 5


class TestEnrichmentRequest:
    """Tests for EnrichmentRequest model."""

    def test_valid_request(self) -> None:
        """Test creating a valid enrichment request."""
        request = EnrichmentRequest(
            product=ProductInput(name="Принтер HP LaserJet Pro M404dn"),
            enrichment_options=EnrichmentOptions(language="en"),
        )
        assert request.product.name == "Принтер HP LaserJet Pro M404dn"
        assert request.enrichment_options is not None
        assert request.enrichment_options.language == "en"

    def test_request_without_options(self) -> None:
        """Test request with default options."""
        request = EnrichmentRequest(
            product=ProductInput(name="Кофемашина DeLonghi Magnifica S")
        )
        assert request.enrichment_options is None


class TestEnrichedProduct:
    """Tests for EnrichedProduct model."""

    def test_enriched_product_defaults(self) -> None:
        """Test default values for enriched product."""
        enriched = EnrichedProduct()
        # New identification fields
        assert enriched.manufacturer is None
        assert enriched.trademark is None
        assert enriched.category is None
        assert enriched.model_name is None
        # Content fields
        assert enriched.description is None
        assert enriched.features == []
        assert enriched.specifications == {}
        assert enriched.seo_keywords == []

    def test_enriched_product_with_identification(self) -> None:
        """Test enriched product with manufacturer and trademark."""
        enriched = EnrichedProduct(
            manufacturer="Foxconn Technology Group",
            trademark="Apple",
            category="Смартфоны",
            model_name="iPhone 15 Pro Max 256GB",
            description="Флагманский смартфон Apple",
            features=["Чип A17 Pro", "Титановый корпус"],
            specifications={"storage": "256GB", "color": "Black Titanium"},
        )
        assert enriched.manufacturer == "Foxconn Technology Group"
        assert enriched.trademark == "Apple"
        assert enriched.category == "Смартфоны"
        assert enriched.model_name == "iPhone 15 Pro Max 256GB"
        assert enriched.description == "Флагманский смартфон Apple"
        assert len(enriched.features) == 2

    def test_enriched_product_same_manufacturer_trademark(self) -> None:
        """Test when manufacturer equals trademark (common case)."""
        enriched = EnrichedProduct(
            manufacturer="Samsung Electronics",
            trademark="Samsung",
            category="Телевизоры",
            model_name="QN65S95D",
        )
        assert enriched.manufacturer == "Samsung Electronics"
        assert enriched.trademark == "Samsung"


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
                ProductInput(name="Товар 1 из прайс-листа"),
                ProductInput(name="Товар 2 из прайс-листа"),
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
