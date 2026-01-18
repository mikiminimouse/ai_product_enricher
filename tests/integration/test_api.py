"""Integration tests for API endpoints."""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Set test environment variables
os.environ["ZHIPUAI_API_KEY"] = "test-api-key"
os.environ["APP_ENV"] = "development"
os.environ["APP_DEBUG"] = "true"


@pytest.fixture
def mock_openai_response() -> MagicMock:
    """Create a mock OpenAI chat completion response."""
    mock_message = MagicMock()
    mock_message.content = """{
        "description": "Флагманский смартфон Apple с титановым корпусом.",
        "features": ["Титановый корпус", "Камера 48MP", "A17 Pro чип"],
        "specifications": {"display": "6.7 Super Retina XDR", "processor": "A17 Pro"},
        "seo_keywords": ["iphone 15 pro max купить", "apple смартфон"]
    }"""

    mock_choice = MagicMock()
    mock_choice.message = mock_message

    mock_usage = MagicMock()
    mock_usage.total_tokens = 500

    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_response.usage = mock_usage

    return mock_response


@pytest.fixture
def client(mock_openai_response: MagicMock) -> TestClient:
    """Create test client with mocked Zhipu API."""
    with patch("ai_product_enricher.services.zhipu_client.AsyncOpenAI") as mock_class:
        mock_instance = MagicMock()
        mock_instance.chat = MagicMock()
        mock_instance.chat.completions = MagicMock()
        mock_instance.chat.completions.create = AsyncMock(return_value=mock_openai_response)
        mock_class.return_value = mock_instance

        # Clear cached services to use mocked client
        from ai_product_enricher.api.dependencies import (
            get_cache_service,
            get_enricher_service,
            get_zhipu_client,
        )

        get_zhipu_client.cache_clear()
        get_cache_service.cache_clear()
        get_enricher_service.cache_clear()

        from ai_product_enricher.main import app

        with TestClient(app) as test_client:
            yield test_client


class TestRootEndpoint:
    """Tests for root endpoint."""

    def test_root_endpoint(self, client: TestClient) -> None:
        """Test root endpoint returns API info."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "AI Product Enricher"
        assert "version" in data
        assert "health" in data


class TestHealthEndpoints:
    """Tests for health endpoints."""

    def test_ping(self, client: TestClient) -> None:
        """Test ping endpoint."""
        response = client.get("/api/v1/ping")

        assert response.status_code == 200
        assert response.json() == {"status": "pong"}

    def test_health_check(self, client: TestClient) -> None:
        """Test health check endpoint."""
        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert "zhipu_api" in data
        assert "uptime_seconds" in data

    def test_metrics(self, client: TestClient) -> None:
        """Test metrics endpoint."""
        response = client.get("/api/v1/metrics")

        assert response.status_code == 200
        data = response.json()
        assert "uptime_seconds" in data
        assert "cache" in data


class TestProductEndpoints:
    """Tests for product enrichment endpoints."""

    def test_enrich_product_success(self, client: TestClient) -> None:
        """Test successful product enrichment."""
        request_data = {
            "product": {
                "name": "iPhone 15 Pro Max",
                "category": "smartphones",
                "brand": "Apple",
            },
            "enrichment_options": {
                "include_web_search": True,
                "language": "ru",
                "fields": ["description", "features", "specifications", "seo_keywords"],
            },
        }

        response = client.post("/api/v1/products/enrich", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"] is not None
        assert data["data"]["product"]["name"] == "iPhone 15 Pro Max"
        assert data["data"]["enriched"]["description"] is not None
        assert len(data["data"]["enriched"]["features"]) > 0
        assert data["data"]["metadata"]["tokens_used"] > 0

    def test_enrich_product_minimal_request(self, client: TestClient) -> None:
        """Test enrichment with minimal request."""
        request_data = {"product": {"name": "Test Product"}}

        response = client.post("/api/v1/products/enrich", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_enrich_product_invalid_request(self, client: TestClient) -> None:
        """Test enrichment with invalid request."""
        # Missing product name
        request_data = {"product": {"category": "test"}}

        response = client.post("/api/v1/products/enrich", json=request_data)

        assert response.status_code == 422

    def test_enrich_product_empty_name(self, client: TestClient) -> None:
        """Test enrichment with empty product name."""
        request_data = {"product": {"name": ""}}

        response = client.post("/api/v1/products/enrich", json=request_data)

        assert response.status_code == 422

    def test_enrich_batch_success(self, client: TestClient) -> None:
        """Test successful batch enrichment."""
        request_data = {
            "products": [
                {"name": "Product 1", "category": "cat1"},
                {"name": "Product 2", "category": "cat2"},
            ],
            "enrichment_options": {"include_web_search": False, "language": "en"},
            "batch_options": {"max_concurrent": 2, "fail_strategy": "continue"},
        }

        response = client.post("/api/v1/products/enrich/batch", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["summary"]["total"] == 2
        assert data["data"]["summary"]["succeeded"] >= 0
        assert len(data["data"]["results"]) == 2

    def test_enrich_batch_empty_products(self, client: TestClient) -> None:
        """Test batch enrichment with empty products list."""
        request_data = {"products": []}

        response = client.post("/api/v1/products/enrich/batch", json=request_data)

        assert response.status_code == 422

    def test_cache_stats(self, client: TestClient) -> None:
        """Test cache stats endpoint."""
        response = client.get("/api/v1/products/cache/stats")

        assert response.status_code == 200
        data = response.json()
        assert "size" in data
        assert "hits" in data
        assert "misses" in data

    def test_cache_clear(self, client: TestClient) -> None:
        """Test cache clear endpoint."""
        response = client.post("/api/v1/products/cache/clear")

        assert response.status_code == 200
        data = response.json()
        assert "cleared" in data


class TestEnrichmentFlow:
    """Integration tests for full enrichment flow."""

    def test_enrichment_caching(self, client: TestClient) -> None:
        """Test that repeated requests use cache."""
        request_data = {
            "product": {"name": "Cached Product", "brand": "Test Brand"},
            "enrichment_options": {"language": "ru"},
        }

        # First request
        response1 = client.post("/api/v1/products/enrich", json=request_data)
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1["data"]["metadata"]["cached"] is False

        # Second request - should be cached
        response2 = client.post("/api/v1/products/enrich", json=request_data)
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["data"]["metadata"]["cached"] is True

    def test_different_options_not_cached(self, client: TestClient) -> None:
        """Test that different options result in different cache entries."""
        request_ru = {
            "product": {"name": "Language Test Product"},
            "enrichment_options": {"language": "ru"},
        }
        request_en = {
            "product": {"name": "Language Test Product"},
            "enrichment_options": {"language": "en"},
        }

        # Russian request
        response_ru = client.post("/api/v1/products/enrich", json=request_ru)
        assert response_ru.status_code == 200
        assert response_ru.json()["data"]["metadata"]["cached"] is False

        # English request - different language, should not be cached
        response_en = client.post("/api/v1/products/enrich", json=request_en)
        assert response_en.status_code == 200
        assert response_en.json()["data"]["metadata"]["cached"] is False


class TestErrorHandling:
    """Tests for error handling."""

    def test_invalid_json(self, client: TestClient) -> None:
        """Test handling of invalid JSON."""
        response = client.post(
            "/api/v1/products/enrich",
            content="not valid json",
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 422

    def test_missing_required_field(self, client: TestClient) -> None:
        """Test handling of missing required field."""
        response = client.post("/api/v1/products/enrich", json={})

        assert response.status_code == 422

    def test_invalid_enrichment_options(self, client: TestClient) -> None:
        """Test handling of invalid enrichment options."""
        request_data = {
            "product": {"name": "Test Product"},
            "enrichment_options": {
                "max_features": 100,  # Over limit
            },
        }

        response = client.post("/api/v1/products/enrich", json=request_data)

        assert response.status_code == 422

    def test_invalid_batch_options(self, client: TestClient) -> None:
        """Test handling of invalid batch options."""
        request_data = {
            "products": [{"name": "Test Product"}],
            "batch_options": {
                "max_concurrent": 100,  # Over limit
            },
        }

        response = client.post("/api/v1/products/enrich/batch", json=request_data)

        assert response.status_code == 422
