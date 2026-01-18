"""Pytest fixtures for AI Product Enricher tests."""

import os
from collections.abc import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Set test environment variables before importing app modules
os.environ["ZHIPUAI_API_KEY"] = "test-api-key"
os.environ["APP_ENV"] = "development"
os.environ["APP_DEBUG"] = "true"


@pytest.fixture
def mock_openai_response() -> MagicMock:
    """Create a mock OpenAI chat completion response."""
    mock_message = MagicMock()
    mock_message.content = """{
        "description": "Флагманский смартфон Apple с титановым корпусом и чипом A17 Pro.",
        "features": ["Титановый корпус", "Камера 48MP", "A17 Pro чип"],
        "specifications": {"display": "6.7\\" Super Retina XDR", "processor": "A17 Pro"},
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
def mock_zhipu_client(mock_openai_response: MagicMock) -> Generator[AsyncMock, None, None]:
    """Create a mock Zhipu AI client."""
    with patch(
        "ai_product_enricher.services.zhipu_client.AsyncOpenAI"
    ) as mock_class:
        mock_instance = AsyncMock()
        mock_instance.chat.completions.create = AsyncMock(return_value=mock_openai_response)
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def sample_product_input() -> dict:
    """Create sample product input data."""
    return {
        "name": "iPhone 15 Pro Max",
        "category": "smartphones",
        "brand": "Apple",
        "description": "Flagship smartphone",
        "sku": "IPHN15PM-256-BLK",
    }


@pytest.fixture
def sample_enrichment_request(sample_product_input: dict) -> dict:
    """Create sample enrichment request."""
    return {
        "product": sample_product_input,
        "enrichment_options": {
            "include_web_search": True,
            "language": "ru",
            "fields": ["description", "features", "specifications", "seo_keywords"],
        },
    }


@pytest.fixture
def sample_batch_request(sample_product_input: dict) -> dict:
    """Create sample batch enrichment request."""
    return {
        "products": [
            sample_product_input,
            {
                "name": "Samsung Galaxy S24 Ultra",
                "category": "smartphones",
                "brand": "Samsung",
            },
        ],
        "enrichment_options": {
            "include_web_search": False,
            "language": "en",
        },
        "batch_options": {
            "max_concurrent": 2,
            "fail_strategy": "continue",
        },
    }


@pytest.fixture
def test_client(mock_zhipu_client: AsyncMock) -> Generator[TestClient, None, None]:
    """Create a test client for the FastAPI app."""
    from ai_product_enricher.main import app

    with TestClient(app) as client:
        yield client
