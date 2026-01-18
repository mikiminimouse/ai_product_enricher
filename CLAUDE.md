# AI Product Enricher - Claude Code Instructions

## Project Overview

Production-ready сервис для обогащения продуктовых данных с использованием Zhipu AI (GLM-4.7) API с извлечением производителя и торговой марки.

## Key Feature: Manufacturer & Trademark Extraction

Сервис автоматически определяет из названия товара:
- **Производитель (manufacturer)** - компания, которая физически производит товар
- **Торговая марка (trademark)** - бренд, под которым продаётся товар

Пример: для "iPhone 15 Pro" → manufacturer: "Foxconn", trademark: "Apple"

## Tech Stack

- Python 3.11+
- FastAPI
- Pydantic v2
- OpenAI SDK (для Zhipu AI)
- structlog (structured logging)
- pytest + pytest-asyncio

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

- `ZhipuAIClient`: Клиент для Zhipu AI API через OpenAI SDK, извлекает manufacturer/trademark
- `ProductEnricherService`: Бизнес-логика обогащения
- `CacheService`: In-memory TTL кэш

### API Endpoints

- `POST /api/v1/products/enrich` - Обогащение одного продукта
- `POST /api/v1/products/enrich/batch` - Пакетная обработка
- `GET /api/v1/health` - Health check

## Development Commands

```bash
# Install dependencies
pip install -e ".[dev]"

# Run development server
uvicorn src.ai_product_enricher.main:app --reload

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

Required:
- `ZHIPUAI_API_KEY` - Zhipu AI API key

Optional:
- `APP_ENV` - development/production (default: production)
- `APP_DEBUG` - Enable debug mode (default: false)
- `LOG_LEVEL` - Logging level (default: INFO)

## Testing

- Unit tests: `tests/unit/`
- Integration tests: `tests/integration/`
- Fixtures: `tests/conftest.py`

Mock Zhipu API in tests using `unittest.mock.patch`.

## API Request Example

```json
{
  "product": {
    "name": "Смартфон Apple iPhone 15 Pro Max 256GB Black Titanium"
  },
  "enrichment_options": {
    "include_web_search": true,
    "language": "ru",
    "fields": ["manufacturer", "trademark", "category", "description", "features"]
  }
}
```

## API Response Format

Success:
```json
{
  "success": true,
  "data": {
    "product": {"name": "..."},
    "enriched": {
      "manufacturer": "Foxconn",
      "trademark": "Apple",
      "category": "Смартфоны",
      "description": "...",
      "features": [...]
    },
    "metadata": {...}
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
2. Update system prompt in `services/zhipu_client.py`
3. Update `_parse_response` and `_extract_fields_manually` methods
4. Add tests

### Modify API response
1. Update models in `models/`
2. Update endpoint in `api/v1/products.py`
3. Update tests

### Add new endpoint
1. Create handler in `api/v1/`
2. Register in `api/router.py`
3. Add integration tests
