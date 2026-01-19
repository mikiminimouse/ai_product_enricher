"""Cloud.ru (GigaChat) API client using OpenAI SDK."""

import json
import re
import time
from typing import Any

from openai import AsyncOpenAI
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from ..core import CloudruAPIError, get_logger, settings
from ..models import EnrichedProduct, EnrichmentOptions, ProductInput, Source

logger = get_logger(__name__)


class CloudruClient:
    """Client for Cloud.ru (GigaChat) API using OpenAI SDK compatibility.

    Optimized for Russian product data enrichment.
    Does not support web search (not available in Cloud.ru API).
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        timeout: int | None = None,
    ) -> None:
        """Initialize Cloud.ru client.

        Args:
            api_key: API key (default from settings)
            base_url: API base URL (default from settings)
            model: Model name (default from settings)
            timeout: Request timeout in seconds (default from settings)
        """
        self._api_key = api_key or settings.cloudru_api_key
        self._base_url = base_url or settings.cloudru_base_url
        self._model = model or settings.cloudru_model
        self._timeout = timeout or settings.cloudru_timeout

        if not self._api_key:
            logger.warning(
                "cloudru_client_no_api_key",
                message="Cloud.ru API key not configured, client will not be functional",
            )
            self._client = None
        else:
            self._client = AsyncOpenAI(
                api_key=self._api_key,
                base_url=self._base_url,
                timeout=self._timeout,
            )

            logger.info(
                "cloudru_client_initialized",
                model=self._model,
                base_url=self._base_url,
            )

    @property
    def provider_name(self) -> str:
        """Return the provider name for metadata."""
        return "cloudru"

    @property
    def model_name(self) -> str:
        """Return the model name being used."""
        return self._model

    @property
    def is_configured(self) -> bool:
        """Check if the client is properly configured with API key."""
        return self._client is not None

    def _build_system_prompt(self, options: EnrichmentOptions) -> str:
        """Build system prompt for product enrichment (optimized for Russian).

        Args:
            options: Enrichment options

        Returns:
            System prompt string
        """
        return f"""Ты профессиональный аналитик продуктовых данных и специалист по контенту. Твоя задача — анализировать информацию о товарах из прайс-листов и закупочных документов и обогащать её структурированными данными.

КРИТИЧЕСКАЯ ЗАДАЧА — ИЗВЛЕЧЕНИЕ И ИДЕНТИФИКАЦИЯ:
Пользователь предоставляет только НАЗВАНИЕ товара (из прайс-листа/закупки) и опционально ОПИСАНИЕ.
Ты ДОЛЖЕН извлечь/определить следующее из этой ограниченной информации:

1. **ПРОИЗВОДИТЕЛЬ (manufacturer)** — Компания, которая ФИЗИЧЕСКИ ПРОИЗВОДИТ товар.
   - Это НЕ всегда совпадает с брендом/торговой маркой
   - Примеры: Foxconn производит iPhone, Pegatron производит MacBook
   - Для многих товаров производитель = торговая марка (например, Samsung производит телевизоры Samsung)
   - Для российских товаров: обрати особое внимание на отечественных производителей

2. **ТОРГОВАЯ МАРКА (trademark)** — БРЕНД, под которым продаётся товар.
   - Это коммерческий бренд, видимый потребителям
   - Примеры: Apple, Samsung, HP, Bosch, Xiaomi, Яндекс, Касперский

3. **КАТЕГОРИЯ (category)** — Категория товара (смартфоны, ноутбуки, принтеры и т.д.)

4. **МОДЕЛЬ (model_name)** — Конкретный идентификатор модели/артикул

ВАЖНЫЕ ПРАВИЛА:
1. Генерируй контент на русском языке
2. Будь точен и достоверен
3. Если производитель не может быть определён точно, укажи его равным торговой марке
4. Извлекай максимум структурированных данных из названия товара
5. Фокусируйся на запрошенных полях: {", ".join(options.fields)}

ФОРМАТ ВЫВОДА:
Ты должен ответить валидным JSON-объектом, содержащим ТОЛЬКО запрошенные поля.
Не включай блоки кода markdown или другое форматирование.

Доступные поля и их ожидаемые форматы:
- "manufacturer": Компания-производитель (строка)
- "trademark": Торговая марка/бренд (строка)
- "category": Категория товара (строка)
- "model_name": Идентификатор модели (строка)
- "description": Подробное описание товара (строка, 2-4 предложения)
- "features": Ключевые характеристики (массив строк, макс {options.max_features} элементов)
- "specifications": Технические характеристики (объект с парами ключ-значение)
- "seo_keywords": SEO-ключевые слова (массив строк, макс {options.max_keywords} элементов)
- "marketing_copy": Промо-текст (строка, 1-2 предложения)
- "pros": Преимущества товара (массив строк)
- "cons": Недостатки товара (массив строк)

Пример входа: "Яндекс Станция Макс с Алисой"
Пример ответа:
{{"manufacturer": "Яндекс", "trademark": "Яндекс", "category": "Умные колонки", "model_name": "Станция Макс", "description": "Флагманская умная колонка Яндекс с голосовым помощником Алиса...", "features": ["Голосовой помощник Алиса", "Качественный звук"], "specifications": {{"тип": "умная колонка", "голосовой помощник": "Алиса"}}}}"""

    def _build_user_prompt(self, product: ProductInput, options: EnrichmentOptions) -> str:
        """Build user prompt for product enrichment.

        Args:
            product: Product input
            options: Enrichment options

        Returns:
            User prompt string
        """
        prompt = f"""Проанализируй и обогати следующий товар из прайс-листа/закупочного документа:

{product.to_prompt_context()}

ОБЯЗАТЕЛЬНЫЕ ЗАДАЧИ:
1. Извлечь/определить ПРОИЗВОДИТЕЛЯ (кто физически производит этот товар)
2. Извлечь/определить ТОРГОВУЮ МАРКУ (название бренда)
3. Определить КАТЕГОРИЮ товара
4. Извлечь НАЗВАНИЕ МОДЕЛИ/АРТИКУЛ
5. Сгенерировать другие запрошенные поля

Сгенерируй следующие поля: {", ".join(options.fields)}

Ответь только валидным JSON-объектом. Без markdown, без пояснений."""

        return prompt

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
        sources: list[Source] = []  # Cloud.ru doesn't support web search
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
                    logger.warning("attempting_json_repair", content_length=len(content))
                    data = self._extract_fields_manually(content, options)
            else:
                logger.warning("no_json_found_in_response", content_preview=content[:200])
                data = {}

        # Build EnrichedProduct from parsed data
        enriched = EnrichedProduct(
            manufacturer=data.get("manufacturer") if "manufacturer" in options.fields else None,
            trademark=data.get("trademark") if "trademark" in options.fields else None,
            category=data.get("category") if "category" in options.fields else None,
            model_name=data.get("model_name") if "model_name" in options.fields else None,
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
        data: dict[str, Any] = {}

        def extract_string_field(field_name: str) -> str | None:
            match = re.search(rf'"{field_name}"\s*:\s*"([^"]*(?:\\.[^"]*)*)"', content)
            if match:
                return match.group(1).replace('\\"', '"')
            return None

        # Extract identification fields
        if "manufacturer" in options.fields:
            val = extract_string_field("manufacturer")
            if val:
                data["manufacturer"] = val

        if "trademark" in options.fields:
            val = extract_string_field("trademark")
            if val:
                data["trademark"] = val

        if "category" in options.fields:
            val = extract_string_field("category")
            if val:
                data["category"] = val

        if "model_name" in options.fields:
            val = extract_string_field("model_name")
            if val:
                data["model_name"] = val

        if "description" in options.fields:
            val = extract_string_field("description")
            if val:
                data["description"] = val

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
        """Enrich a product using Cloud.ru (GigaChat).

        Args:
            product: Product to enrich
            options: Enrichment options

        Returns:
            Tuple of (EnrichedProduct, Sources, tokens_used, processing_time_ms)

        Raises:
            CloudruAPIError: If API call fails or client not configured
        """
        if not self._client:
            raise CloudruAPIError(
                message="Cloud.ru client not configured - CLOUDRU_API_KEY not set",
                details={"product_name": product.name},
            )

        start_time = time.time()

        # Force disable web search for Cloud.ru (not supported)
        effective_options = EnrichmentOptions(
            include_web_search=False,  # Cloud.ru doesn't support web search
            language=options.language,
            fields=options.fields,
            search_recency=options.search_recency,
            max_features=options.max_features,
            max_keywords=options.max_keywords,
        )

        system_prompt = self._build_system_prompt(effective_options)
        user_prompt = self._build_user_prompt(product, effective_options)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        try:
            logger.debug(
                "cloudru_request",
                product_name=product.name,
            )

            response = await self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                temperature=0.5,
                max_tokens=2500,
                top_p=0.95,
            )

            processing_time_ms = int((time.time() - start_time) * 1000)

            # Extract content from response
            content = response.choices[0].message.content or ""

            # Calculate tokens
            tokens_used = response.usage.total_tokens if response.usage else 0

            logger.info(
                "cloudru_response",
                product_name=product.name,
                tokens=tokens_used,
                processing_time_ms=processing_time_ms,
            )

            # Parse response
            enriched, sources = self._parse_response(content, effective_options)

            return enriched, sources, tokens_used, processing_time_ms

        except Exception as e:
            processing_time_ms = int((time.time() - start_time) * 1000)
            logger.error(
                "cloudru_api_error",
                product_name=product.name,
                error=str(e),
                processing_time_ms=processing_time_ms,
            )
            raise CloudruAPIError(
                message=f"Cloud.ru API request failed: {e!s}",
                details={"product_name": product.name},
            ) from e

    async def health_check(self) -> bool:
        """Check if Cloud.ru API is accessible.

        Returns:
            True if API is accessible, False otherwise
        """
        if not self._client:
            return False

        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": "Привет"}],
                max_tokens=10,
            )
            return response.choices[0].message.content is not None
        except Exception as e:
            logger.warning("cloudru_health_check_failed", error=str(e))
            return False
