"""Unit tests for Zhipu AI client."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai_product_enricher.core import ZhipuAPIError
from ai_product_enricher.models import EnrichmentOptions, ProductInput
from ai_product_enricher.services.zhipu_client import ZhipuAIClient


class TestZhipuAIClient:
    """Tests for ZhipuAIClient."""

    @pytest.fixture
    def mock_openai_response(self) -> MagicMock:
        """Create a mock OpenAI response with manufacturer/trademark."""
        mock_message = MagicMock()
        mock_message.content = """{
            "manufacturer": "Foxconn Technology Group",
            "trademark": "Apple",
            "category": "Смартфоны",
            "model_name": "iPhone 15 Pro 256GB",
            "description": "Флагманский смартфон Apple",
            "features": ["Чип A17 Pro", "Титановый корпус"],
            "specifications": {"storage": "256GB"},
            "seo_keywords": ["iphone 15 pro купить"]
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
    def mock_client(self, mock_openai_response: MagicMock) -> MagicMock:
        """Create a mock AsyncOpenAI client."""
        mock = MagicMock()
        mock.chat = MagicMock()
        mock.chat.completions = MagicMock()
        mock.chat.completions.create = AsyncMock(return_value=mock_openai_response)
        return mock

    @pytest.mark.asyncio
    async def test_enrich_product_success(
        self, mock_client: MagicMock, mock_openai_response: MagicMock
    ) -> None:
        """Test successful product enrichment with manufacturer/trademark extraction."""
        with patch(
            "ai_product_enricher.services.zhipu_client.AsyncOpenAI",
            return_value=mock_client,
        ):
            client = ZhipuAIClient(api_key="test-key")

            # Simplified input - only name from price list
            product = ProductInput(
                name="Смартфон Apple iPhone 15 Pro 256GB Black Titanium"
            )
            options = EnrichmentOptions(
                language="ru",
                fields=[
                    "manufacturer",
                    "trademark",
                    "category",
                    "description",
                    "features",
                    "specifications",
                ],
            )

            enriched, sources, tokens, time_ms = await client.enrich_product(
                product, options
            )

            # Verify identification fields
            assert enriched.manufacturer == "Foxconn Technology Group"
            assert enriched.trademark == "Apple"
            assert enriched.category == "Смартфоны"
            # Verify content fields
            assert enriched.description == "Флагманский смартфон Apple"
            assert len(enriched.features) == 2
            assert enriched.specifications == {"storage": "256GB"}
            assert tokens == 500
            assert time_ms >= 0

    @pytest.mark.asyncio
    async def test_enrich_product_with_web_search(
        self, mock_client: MagicMock
    ) -> None:
        """Test enrichment with web search enabled for manufacturer detection."""
        with patch(
            "ai_product_enricher.services.zhipu_client.AsyncOpenAI",
            return_value=mock_client,
        ):
            client = ZhipuAIClient(api_key="test-key")

            product = ProductInput(name="Картридж HP 123XL черный оригинальный")
            options = EnrichmentOptions(include_web_search=True)

            await client.enrich_product(product, options)

            # Verify tools were passed for web search
            call_kwargs = mock_client.chat.completions.create.call_args.kwargs
            assert "tools" in call_kwargs

    @pytest.mark.asyncio
    async def test_enrich_product_without_web_search(
        self, mock_client: MagicMock
    ) -> None:
        """Test enrichment without web search."""
        with patch(
            "ai_product_enricher.services.zhipu_client.AsyncOpenAI",
            return_value=mock_client,
        ):
            client = ZhipuAIClient(api_key="test-key")

            product = ProductInput(name="Ноутбук ASUS ROG Strix G16")
            options = EnrichmentOptions(include_web_search=False)

            await client.enrich_product(product, options)

            # Verify no tools were passed
            call_kwargs = mock_client.chat.completions.create.call_args.kwargs
            assert "tools" not in call_kwargs

    @pytest.mark.asyncio
    async def test_enrich_product_api_error(self, mock_client: MagicMock) -> None:
        """Test API error handling."""
        mock_client.chat.completions.create = AsyncMock(
            side_effect=Exception("API Error")
        )

        with patch(
            "ai_product_enricher.services.zhipu_client.AsyncOpenAI",
            return_value=mock_client,
        ):
            client = ZhipuAIClient(api_key="test-key")

            product = ProductInput(name="Тестовый товар из прайс-листа")
            options = EnrichmentOptions()

            with pytest.raises(ZhipuAPIError) as exc_info:
                await client.enrich_product(product, options)

            assert "API Error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_parse_response_with_markdown(
        self, mock_client: MagicMock
    ) -> None:
        """Test parsing response with markdown code blocks."""
        mock_message = MagicMock()
        mock_message.content = """```json
{
    "manufacturer": "Samsung Electronics",
    "trademark": "Samsung",
    "description": "Test description",
    "features": ["Feature 1"]
}
```"""

        mock_choice = MagicMock()
        mock_choice.message = mock_message

        mock_usage = MagicMock()
        mock_usage.total_tokens = 100

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = mock_usage

        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch(
            "ai_product_enricher.services.zhipu_client.AsyncOpenAI",
            return_value=mock_client,
        ):
            client = ZhipuAIClient(api_key="test-key")

            product = ProductInput(name="Телевизор Samsung QN65S95D")
            options = EnrichmentOptions(
                fields=["manufacturer", "trademark", "description", "features"]
            )

            enriched, _, _, _ = await client.enrich_product(product, options)

            assert enriched.manufacturer == "Samsung Electronics"
            assert enriched.trademark == "Samsung"
            assert enriched.description == "Test description"
            assert enriched.features == ["Feature 1"]

    @pytest.mark.asyncio
    async def test_health_check_success(self, mock_client: MagicMock) -> None:
        """Test successful health check."""
        with patch(
            "ai_product_enricher.services.zhipu_client.AsyncOpenAI",
            return_value=mock_client,
        ):
            client = ZhipuAIClient(api_key="test-key")

            result = await client.health_check()

            assert result is True

    @pytest.mark.asyncio
    async def test_health_check_failure(self, mock_client: MagicMock) -> None:
        """Test failed health check."""
        mock_client.chat.completions.create = AsyncMock(
            side_effect=Exception("Connection error")
        )

        with patch(
            "ai_product_enricher.services.zhipu_client.AsyncOpenAI",
            return_value=mock_client,
        ):
            client = ZhipuAIClient(api_key="test-key")

            result = await client.health_check()

            assert result is False

    def test_build_system_prompt(self) -> None:
        """Test system prompt includes manufacturer/trademark extraction instructions."""
        with patch(
            "ai_product_enricher.services.zhipu_client.AsyncOpenAI",
        ):
            client = ZhipuAIClient(api_key="test-key")

            options = EnrichmentOptions(
                language="ru",
                fields=["manufacturer", "trademark", "description"],
                max_features=5,
            )

            prompt = client._build_system_prompt(options)

            assert "Russian" in prompt
            assert "MANUFACTURER" in prompt
            assert "TRADEMARK" in prompt
            assert "manufacturer" in prompt
            assert "trademark" in prompt

    def test_build_user_prompt(self) -> None:
        """Test user prompt building with simplified input."""
        with patch(
            "ai_product_enricher.services.zhipu_client.AsyncOpenAI",
        ):
            client = ZhipuAIClient(api_key="test-key")

            # Only name and description - typical price list input
            product = ProductInput(
                name="Смартфон Apple iPhone 15 Pro Max 256GB",
                description="Новейший флагман с чипом A17 Pro",
            )
            options = EnrichmentOptions(
                fields=["manufacturer", "trademark", "description"]
            )

            prompt = client._build_user_prompt(product, options)

            assert "iPhone 15 Pro" in prompt
            assert "A17 Pro" in prompt
            assert "manufacturer" in prompt.lower()
            assert "trademark" in prompt.lower()
