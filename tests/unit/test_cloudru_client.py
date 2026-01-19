"""Unit tests for Cloud.ru (GigaChat) client."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from ai_product_enricher.models import EnrichmentOptions, ProductInput
from ai_product_enricher.services import CloudruClient
from ai_product_enricher.core import CloudruAPIError


class TestCloudruClientProperties:
    """Test CloudruClient properties."""

    def test_provider_name(self, mock_cloudru_client: AsyncMock) -> None:
        """Test that provider_name returns 'cloudru'."""
        client = CloudruClient(api_key="test-key")
        assert client.provider_name == "cloudru"

    def test_model_name(self, mock_cloudru_client: AsyncMock) -> None:
        """Test that model_name returns the configured model."""
        client = CloudruClient(api_key="test-key", model="test-model")
        assert client.model_name == "test-model"

    def test_is_configured_with_api_key(self, mock_cloudru_client: AsyncMock) -> None:
        """Test that is_configured returns True when API key is set."""
        client = CloudruClient(api_key="test-key")
        assert client.is_configured is True

    def test_is_configured_without_api_key(self) -> None:
        """Test that is_configured returns False when API key is not set."""
        # Directly pass empty api_key to bypass environment
        client = CloudruClient.__new__(CloudruClient)
        client._api_key = None
        client._client = None
        assert client.is_configured is False


class TestCloudruClientEnrichProduct:
    """Test CloudruClient.enrich_product method."""

    @pytest.mark.asyncio
    async def test_enrich_product_success(
        self, mock_cloudru_client: AsyncMock, mock_cloudru_openai_response: MagicMock
    ) -> None:
        """Test successful product enrichment."""
        client = CloudruClient(api_key="test-key")

        product = ProductInput(
            name="Яндекс Станция Макс",
            description="Умная колонка с Алисой",
            country_origin="RU",
        )
        options = EnrichmentOptions(
            include_web_search=True,  # Should be ignored
            language="ru",
            fields=["manufacturer", "trademark", "category", "model_name", "description"],
        )

        enriched, sources, tokens, time_ms = await client.enrich_product(product, options)

        # Verify response parsing
        assert enriched.manufacturer == "Яндекс"
        assert enriched.trademark == "Яндекс"
        assert enriched.category == "Умные колонки"
        assert enriched.model_name == "Станция Макс"

        # Cloud.ru doesn't support web search
        assert sources == []
        assert tokens > 0
        assert time_ms >= 0

    @pytest.mark.asyncio
    async def test_enrich_product_disables_web_search(
        self, mock_cloudru_client: AsyncMock, mock_cloudru_openai_response: MagicMock
    ) -> None:
        """Test that web search is disabled for Cloud.ru."""
        client = CloudruClient(api_key="test-key")

        product = ProductInput(name="Тест продукт", country_origin="RU")
        options = EnrichmentOptions(include_web_search=True)

        await client.enrich_product(product, options)

        # Verify API was called without tools (no web search)
        call_kwargs = mock_cloudru_client.chat.completions.create.call_args.kwargs
        assert "tools" not in call_kwargs

    @pytest.mark.asyncio
    async def test_enrich_product_not_configured(self) -> None:
        """Test that enrich_product raises error when not configured."""
        client = CloudruClient(api_key=None)
        client._client = None  # Simulate no API key

        product = ProductInput(name="Тест продукт")
        options = EnrichmentOptions()

        with pytest.raises(CloudruAPIError) as exc_info:
            await client.enrich_product(product, options)

        assert "not configured" in str(exc_info.value.message)


class TestCloudruClientHealthCheck:
    """Test CloudruClient.health_check method."""

    @pytest.mark.asyncio
    async def test_health_check_success(
        self, mock_cloudru_client: AsyncMock, mock_cloudru_openai_response: MagicMock
    ) -> None:
        """Test successful health check."""
        client = CloudruClient(api_key="test-key")

        result = await client.health_check()

        assert result is True

    @pytest.mark.asyncio
    async def test_health_check_not_configured(self) -> None:
        """Test health check returns False when not configured."""
        client = CloudruClient(api_key=None)
        client._client = None

        result = await client.health_check()

        assert result is False

    @pytest.mark.asyncio
    async def test_health_check_api_error(self, mock_cloudru_client: AsyncMock) -> None:
        """Test health check returns False on API error."""
        mock_cloudru_client.chat.completions.create.side_effect = Exception("API Error")

        client = CloudruClient(api_key="test-key")

        result = await client.health_check()

        assert result is False


class TestCloudruClientPrompts:
    """Test CloudruClient prompt building."""

    def test_system_prompt_in_russian(self, mock_cloudru_client: AsyncMock) -> None:
        """Test that system prompt is in Russian."""
        client = CloudruClient(api_key="test-key")

        options = EnrichmentOptions(language="ru", fields=["manufacturer", "trademark"])
        prompt = client._build_system_prompt(options)

        # Should contain Russian text
        assert "Ты профессиональный аналитик" in prompt
        assert "ПРОИЗВОДИТЕЛЬ" in prompt
        assert "ТОРГОВАЯ МАРКА" in prompt

    def test_user_prompt_in_russian(self, mock_cloudru_client: AsyncMock) -> None:
        """Test that user prompt is in Russian."""
        client = CloudruClient(api_key="test-key")

        product = ProductInput(name="Тест продукт", description="Описание")
        options = EnrichmentOptions(fields=["manufacturer", "trademark"])

        prompt = client._build_user_prompt(product, options)

        assert "Проанализируй и обогати" in prompt
        assert "Тест продукт" in prompt
