# AI Product Enricher - Claude Code Instructions

## Project Overview

Production-ready сервис для обогащения продуктовых данных с мульти-LLM архитектурой:
- **Z.ai (GLM-4.7)** — для зарубежных производителей (CN, US, KR и др.)
- **Cloud.ru (GigaChat)** — для российских производителей (RU)

Автоматическая маршрутизация по полю `country_origin`.

## Key Feature: Manufacturer & Trademark Extraction

Сервис автоматически определяет из названия товара:
- **Производитель (manufacturer)** - компания, которая физически производит товар
- **Торговая марка (trademark)** - бренд, под которым продаётся товар

Пример: для "iPhone 15 Pro" → manufacturer: "Foxconn", trademark: "Apple"

## Tech Stack

- Python 3.11+
- FastAPI
- Pydantic v2
- OpenAI SDK (для Zhipu AI и Cloud.ru)
- structlog (structured logging)
- pytest + pytest-asyncio
- tenacity (retry logic)

## Project Structure

```
src/ai_product_enricher/
├── api/v1/           # REST API endpoints
├── core/             # Config, logging, exceptions
├── models/           # Pydantic data models
├── services/         # Business logic
└── main.py           # FastAPI app entry point
```

## Key Components

### Models

**ProductInput** - Упрощённый ввод:
- `name: str` - Наименование товара из прайс-листа/госзакупок (обязательно)
- `description: str | None` - Дополнительное описание (опционально)
- `country_origin: str | None` - Страна происхождения (ISO 3166-1 alpha-2/3), определяет маршрутизацию LLM

**EnrichedProduct** - Результат обогащения:
- `manufacturer` - Компания-производитель
- `trademark` - Торговая марка/бренд
- `category` - Категория товара
- `model_name` - Модель/артикул
- `description` - Обогащённое описание
- `features` - Ключевые характеристики
- `specifications` - Технические характеристики
- `seo_keywords` - SEO ключевые слова

### Services

**LLM Clients:**
- `ZhipuAIClient`: Клиент для Z.ai (GLM-4.7) — зарубежные товары, поддержка web search
- `CloudruClient`: Клиент для Cloud.ru (GigaChat) — российские товары

**Business Logic:**
- `ProductEnricherService`: Маршрутизация и обогащение с кэшированием
- `CacheService`: In-memory TTL кэш

### LLM Routing Logic

```
country_origin == "RU" или "RUS" → Cloud.ru (GigaChat)
country_origin != "RU" или null → Z.ai (GLM-4.7)
```

При недоступности Cloud.ru — автоматический fallback на Z.ai.

### API Endpoints

- `POST /api/v1/products/enrich` - Обогащение одного продукта
- `POST /api/v1/products/enrich/batch` - Пакетная обработка
- `GET /api/v1/health` - Health check

## Development Commands

```bash
# Install dependencies
pip install -e ".[dev]"

# Run development server (только локально)
uvicorn src.ai_product_enricher.main:app --reload

# Run production server (доступен извне)
python -m src.ai_product_enricher.main

# Run tests
pytest

# Run with coverage
pytest --cov=src/ai_product_enricher

# Type checking
mypy src/

# Linting
ruff check src/
```

## Environment Variables

**Zhipu AI (обязательно):**
- `ZHIPUAI_API_KEY` - API ключ Z.ai
- `ZHIPUAI_BASE_URL` - Base URL (default: https://api.z.ai/api/coding/paas/v4)
- `ZHIPUAI_MODEL` - Модель (default: GLM-4.7)

**Cloud.ru (опционально, для российских товаров):**
- `CLOUDRU_API_KEY` - API ключ Cloud.ru
- `CLOUDRU_BASE_URL` - Base URL (default: https://foundation-models.api.cloud.ru/v1)
- `CLOUDRU_MODEL` - Модель (default: ai-sage/GigaChat3-10B-A1.8B)
- `CLOUDRU_TIMEOUT` - Таймаут в секундах (default: 60)

**Приложение:**
- `APP_ENV` - development/production (default: production)
- `APP_DEBUG` - Enable debug mode (default: false)
- `LOG_LEVEL` - Logging level (default: INFO)

## Testing

- Unit tests: `tests/unit/`
- Integration tests: `tests/integration/`
- Fixtures: `tests/conftest.py`

Mock Zhipu API in tests using `unittest.mock.patch`.

## API Request Examples

**Зарубежный товар (→ Z.ai):**
```json
{
  "product": {
    "name": "Apple iPhone 15 Pro Max 256GB Black Titanium",
    "country_origin": "CN"
  },
  "enrichment_options": {
    "include_web_search": true,
    "language": "ru",
    "fields": ["manufacturer", "trademark", "category", "description"]
  }
}
```

**Российский товар (→ Cloud.ru):**
```json
{
  "product": {
    "name": "Яндекс Станция Макс",
    "country_origin": "RU"
  },
  "enrichment_options": {
    "language": "ru",
    "fields": ["manufacturer", "trademark", "category", "description"]
  }
}
```

## API Response Format

Success:
```json
{
  "success": true,
  "data": {
    "product": {"name": "...", "country_origin": "CN"},
    "enriched": {
      "manufacturer": "Foxconn",
      "trademark": "Apple",
      "category": "Смартфоны",
      "description": "..."
    },
    "metadata": {
      "model_used": "GLM-4.7",
      "llm_provider": "zhipuai",
      "tokens_used": 500,
      "processing_time_ms": 1200,
      "web_search_used": true,
      "cached": false
    }
  }
}
```

Error:
```json
{"success": false, "error": {"code": "...", "message": "..."}}
```

## Caching Strategy

Cache key based on:
- product name (lowercase, case-insensitive)
- language
- fields
- web_search flag

Note: manufacturer/trademark не участвуют в ключе кэша, т.к. они извлекаются из name.

## Common Tasks

### Add new enrichment field
1. Add field to `EnrichedProduct` model in `models/enrichment.py`
2. Update system prompt in `services/zhipu_client.py` AND `services/cloudru_client.py`
3. Update `_parse_response` and `_extract_fields_manually` methods в обоих клиентах
4. Add tests

### Add new LLM provider
1. Create client in `services/` (следуя паттерну `LLMClient` Protocol)
2. Add configuration в `core/config.py`
3. Add exception в `core/exceptions.py`
4. Update routing logic в `services/enricher.py`
5. Add dependency в `api/dependencies.py`
6. Update health check endpoint

### Modify API response
1. Update models in `models/`
2. Update endpoint in `api/v1/products.py`
3. Update tests

### Add new endpoint
1. Create handler in `api/v1/`
2. Register in `api/router.py`
3. Add integration tests

## curl Examples

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Обогащение российского товара (→ Cloud.ru)
curl -X POST http://localhost:8000/api/v1/products/enrich \
  -H "Content-Type: application/json" \
  -d '{"product": {"name": "Яндекс Станция Макс", "country_origin": "RU"}}'

# Обогащение зарубежного товара (→ Z.ai)
curl -X POST http://localhost:8000/api/v1/products/enrich \
  -H "Content-Type: application/json" \
  -d '{"product": {"name": "iPhone 15 Pro", "country_origin": "CN"}}'

# Batch обработка
curl -X POST http://localhost:8000/api/v1/products/enrich/batch \
  -H "Content-Type: application/json" \
  -d '{"products": [{"name": "Product 1", "country_origin": "RU"}, {"name": "Product 2", "country_origin": "CN"}]}'
```
