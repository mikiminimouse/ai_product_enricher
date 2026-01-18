"""Zhipu AI API client using OpenAI SDK."""

import json
import time
from typing import Any

from openai import AsyncOpenAI
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from ..core import ZhipuAPIError, get_logger, settings
from ..models import EnrichedProduct, EnrichmentOptions, ProductInput, Source

logger = get_logger(__name__)


class ZhipuAIClient:
    """Client for Zhipu AI API using OpenAI SDK compatibility."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        timeout: int | None = None,
    ) -> None:
        """Initialize Zhipu AI client.

        Args:
            api_key: API key (default from settings)
            base_url: API base URL (default from settings)
            model: Model name (default from settings)
            timeout: Request timeout in seconds (default from settings)
        """
        self._api_key = api_key or settings.zhipuai_api_key
        self._base_url = base_url or settings.zhipuai_base_url
        self._model = model or settings.zhipuai_model
        self._timeout = timeout or settings.zhipuai_timeout

        self._client = AsyncOpenAI(
            api_key=self._api_key,
            base_url=self._base_url,
            timeout=self._timeout,
        )

        logger.info(
            "zhipu_client_initialized",
            model=self._model,
            base_url=self._base_url,
        )

    def _build_system_prompt(self, options: EnrichmentOptions) -> str:
        """Build system prompt for product enrichment.

        Args:
            options: Enrichment options

        Returns:
            System prompt string
        """
        language_name = {
            "ru": "Russian",
            "en": "English",
            "zh": "Chinese",
            "es": "Spanish",
            "de": "German",
            "fr": "French",
        }.get(options.language, options.language)

        return f"""You are a professional product content specialist. Your task is to enrich product information based on available data and web search results.

IMPORTANT GUIDELINES:
1. Generate content in {language_name} language
2. Be factual and accurate - only include verified information
3. Use professional, marketing-friendly language
4. Structure information clearly and logically
5. Focus on the requested fields: {", ".join(options.fields)}

OUTPUT FORMAT:
You must respond with a valid JSON object containing ONLY the requested fields.
Do not include markdown code blocks or any other formatting.

Available fields and their expected formats:
- "description": A comprehensive product description (string, 2-4 sentences)
- "features": Key product features (array of strings, max {options.max_features} items)
- "specifications": Technical specifications (object with key-value pairs)
- "seo_keywords": SEO-friendly keywords (array of strings, max {options.max_keywords} items)
- "marketing_copy": Promotional marketing text (string, 1-2 sentences)
- "pros": Product advantages (array of strings)
- "cons": Product disadvantages (array of strings)

Example response:
{{"description": "Product description here", "features": ["Feature 1", "Feature 2"], "specifications": {{"weight": "150g", "dimensions": "10x5x2cm"}}}}"""

    def _build_user_prompt(self, product: ProductInput, options: EnrichmentOptions) -> str:
        """Build user prompt for product enrichment.

        Args:
            product: Product input
            options: Enrichment options

        Returns:
            User prompt string
        """
        prompt = f"""Please enrich the following product information:

{product.to_prompt_context()}

Generate the following fields: {", ".join(options.fields)}

Respond with a valid JSON object only. No markdown, no explanations."""

        return prompt

    def _build_tools(self) -> list[dict[str, Any]]:
        """Build tools configuration for web search.

        Returns:
            List of tool configurations
        """
        return [
            {
                "type": "web_search",
                "web_search": {
                    "enable": True,
                    "search_result": True,
                },
            }
        ]

    def _parse_response(
        self, content: str, options: EnrichmentOptions
    ) -> tuple[EnrichedProduct, list[Source]]:
        """Parse LLM response into structured data.

        Args:
            content: Raw response content
            options: Enrichment options

        Returns:
            Tuple of (EnrichedProduct, list of Sources)
        """
        import re

        sources: list[Source] = []
        data: dict[str, Any] = {}

        # Try to extract JSON from response
        try:
            # Remove markdown code blocks if present
            cleaned = content.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            elif cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()

            data = json.loads(cleaned)
        except json.JSONDecodeError:
            # Try to find JSON object in the response
            json_match = re.search(r"\{[\s\S]*\}", content)
            if json_match:
                json_str = json_match.group()
                try:
                    data = json.loads(json_str)
                except json.JSONDecodeError:
                    # Try to repair truncated JSON by extracting individual fields
                    logger.warning("attempting_json_repair", content_length=len(content))
                    data = self._extract_fields_manually(content, options)
            else:
                logger.warning("no_json_found_in_response", content_preview=content[:200])
                data = {}

        # Build EnrichedProduct from parsed data
        enriched = EnrichedProduct(
            description=data.get("description") if "description" in options.fields else None,
            features=data.get("features", []) if "features" in options.fields else [],
            specifications=(
                data.get("specifications", {}) if "specifications" in options.fields else {}
            ),
            seo_keywords=data.get("seo_keywords", []) if "seo_keywords" in options.fields else [],
            marketing_copy=(
                data.get("marketing_copy") if "marketing_copy" in options.fields else None
            ),
            pros=data.get("pros", []) if "pros" in options.fields else [],
            cons=data.get("cons", []) if "cons" in options.fields else [],
        )

        return enriched, sources

    def _extract_fields_manually(self, content: str, options: EnrichmentOptions) -> dict[str, Any]:
        """Extract fields manually from potentially truncated JSON.

        Args:
            content: Raw response content
            options: Enrichment options

        Returns:
            Dictionary with extracted fields
        """
        import re

        data: dict[str, Any] = {}

        # Extract description
        if "description" in options.fields:
            desc_match = re.search(r'"description"\s*:\s*"([^"]*(?:\\.[^"]*)*)"', content)
            if desc_match:
                data["description"] = desc_match.group(1).replace('\\"', '"')

        # Extract features array
        if "features" in options.fields:
            features_match = re.search(r'"features"\s*:\s*\[(.*?)\]', content, re.DOTALL)
            if features_match:
                features_str = features_match.group(1)
                features = re.findall(r'"([^"]*(?:\\.[^"]*)*)"', features_str)
                data["features"] = [f.replace('\\"', '"') for f in features]

        # Extract specifications object
        if "specifications" in options.fields:
            specs_match = re.search(r'"specifications"\s*:\s*\{([^}]*)\}', content, re.DOTALL)
            if specs_match:
                specs_str = specs_match.group(1)
                specs = {}
                for pair in re.finditer(r'"([^"]+)"\s*:\s*"([^"]*)"', specs_str):
                    specs[pair.group(1)] = pair.group(2)
                data["specifications"] = specs

        # Extract seo_keywords array
        if "seo_keywords" in options.fields:
            keywords_match = re.search(r'"seo_keywords"\s*:\s*\[(.*?)\]', content, re.DOTALL)
            if keywords_match:
                keywords_str = keywords_match.group(1)
                keywords = re.findall(r'"([^"]*(?:\\.[^"]*)*)"', keywords_str)
                data["seo_keywords"] = [k.replace('\\"', '"') for k in keywords]

        logger.info("manual_extraction_result", fields_extracted=list(data.keys()))
        return data

    @retry(
        retry=retry_if_exception_type((TimeoutError, ConnectionError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def enrich_product(
        self,
        product: ProductInput,
        options: EnrichmentOptions,
    ) -> tuple[EnrichedProduct, list[Source], int, int]:
        """Enrich a product using Zhipu AI.

        Args:
            product: Product to enrich
            options: Enrichment options

        Returns:
            Tuple of (EnrichedProduct, Sources, tokens_used, processing_time_ms)

        Raises:
            ZhipuAPIError: If API call fails
        """
        start_time = time.time()

        system_prompt = self._build_system_prompt(options)
        user_prompt = self._build_user_prompt(product, options)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        try:
            # Build request kwargs
            kwargs: dict[str, Any] = {
                "model": self._model,
                "messages": messages,
                "temperature": 0.3,
                "max_tokens": 4000,
            }

            # Add web search tool if enabled
            if options.include_web_search:
                kwargs["tools"] = self._build_tools()

            logger.debug(
                "zhipu_request",
                product_name=product.name,
                web_search=options.include_web_search,
            )

            response = await self._client.chat.completions.create(**kwargs)

            processing_time_ms = int((time.time() - start_time) * 1000)

            # Extract content from response
            content = response.choices[0].message.content or ""

            # Calculate tokens
            tokens_used = response.usage.total_tokens if response.usage else 0

            logger.info(
                "zhipu_response",
                product_name=product.name,
                tokens=tokens_used,
                processing_time_ms=processing_time_ms,
            )

            # Parse response
            enriched, sources = self._parse_response(content, options)

            return enriched, sources, tokens_used, processing_time_ms

        except Exception as e:
            processing_time_ms = int((time.time() - start_time) * 1000)
            logger.error(
                "zhipu_api_error",
                product_name=product.name,
                error=str(e),
                processing_time_ms=processing_time_ms,
            )
            raise ZhipuAPIError(
                message=f"Zhipu API request failed: {e!s}",
                details={"product_name": product.name},
            ) from e

    async def health_check(self) -> bool:
        """Check if Zhipu AI API is accessible.

        Returns:
            True if API is accessible, False otherwise
        """
        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=5,
            )
            return response.choices[0].message.content is not None
        except Exception as e:
            logger.warning("zhipu_health_check_failed", error=str(e))
            return False
