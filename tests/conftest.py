"""Pytest fixtures for AI Product Enricher tests."""

import os
from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Set test environment variables before importing app modules
os.environ["ZHIPUAI_API_KEY"] = "test-api-key"
os.environ["CLOUDRU_API_KEY"] = "test-cloudru-api-key"
os.environ["APP_ENV"] = "development"
os.environ["APP_DEBUG"] = "true"


@pytest.fixture
def mock_openai_response() -> MagicMock:
    """Create a mock OpenAI chat completion response with manufacturer/trademark."""
    mock_message = MagicMock()
    mock_message.content = """{
        "manufacturer": "Foxconn Technology Group",
        "trademark": "Apple",
        "category": "Смартфоны",
        "model_name": "iPhone 15 Pro Max 256GB",
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
def mock_cloudru_openai_response() -> MagicMock:
    """Create a mock OpenAI chat completion response for Cloud.ru (Russian product)."""
    mock_message = MagicMock()
    mock_message.content = """{
        "manufacturer": "Яндекс",
        "trademark": "Яндекс",
        "category": "Умные колонки",
        "model_name": "Станция Макс",
        "description": "Флагманская умная колонка с голосовым помощником Алиса.",
        "features": ["Голосовой помощник Алиса", "Качественный звук", "Умный дом"],
        "specifications": {"тип": "умная колонка", "голосовой помощник": "Алиса"},
        "seo_keywords": ["яндекс станция макс купить", "умная колонка алиса"]
    }"""

    mock_choice = MagicMock()
    mock_choice.message = mock_message

    mock_usage = MagicMock()
    mock_usage.total_tokens = 400

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
def mock_cloudru_client(mock_cloudru_openai_response: MagicMock) -> Generator[AsyncMock, None, None]:
    """Create a mock Cloud.ru client."""
    with patch(
        "ai_product_enricher.services.cloudru_client.AsyncOpenAI"
    ) as mock_class:
        mock_instance = AsyncMock()
        mock_instance.chat.completions.create = AsyncMock(return_value=mock_cloudru_openai_response)
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def sample_product_input() -> dict:
    """Create sample product input data - simplified to name + description only."""
    return {
        "name": "Смартфон Apple iPhone 15 Pro Max 256GB Black Titanium",
        "description": "Флагманский смартфон с чипом A17 Pro и титановым корпусом",
        "country_origin": "CN",
    }


@pytest.fixture
def sample_russian_product_input() -> dict:
    """Create sample Russian product input data."""
    return {
        "name": "Яндекс Станция Макс",
        "description": "Умная колонка с Алисой",
        "country_origin": "RU",
    }


@pytest.fixture
def sample_enrichment_request(sample_product_input: dict) -> dict:
    """Create sample enrichment request with new identification fields."""
    return {
        "product": sample_product_input,
        "enrichment_options": {
            "include_web_search": True,
            "language": "ru",
            "fields": [
                "manufacturer",
                "trademark",
                "category",
                "description",
                "features",
                "specifications",
                "seo_keywords",
            ],
        },
    }


@pytest.fixture
def sample_batch_request() -> dict:
    """Create sample batch enrichment request with simplified products."""
    return {
        "products": [
            {
                "name": "Смартфон Apple iPhone 15 Pro Max 256GB",
                "description": "Флагман Apple с A17 Pro",
            },
            {
                "name": "Смартфон Samsung Galaxy S24 Ultra 512GB",
            },
        ],
        "enrichment_options": {
            "include_web_search": False,
            "language": "ru",
        },
        "batch_options": {
            "max_concurrent": 2,
            "fail_strategy": "continue",
        },
    }


@pytest.fixture
def test_client(mock_zhipu_client: AsyncMock, mock_cloudru_client: AsyncMock) -> Generator[TestClient, None, None]:
    """Create a test client for the FastAPI app with both LLM clients mocked."""
    from ai_product_enricher.main import app

    with TestClient(app) as client:
        yield client
