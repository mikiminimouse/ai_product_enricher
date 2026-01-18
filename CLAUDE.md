# AI Product Enricher - Claude Code Instructions

## Project Overview

Production-ready сервис для обогащения продуктовых данных с использованием Zhipu AI (GLM-4.7) API.

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

### Configuration (core/config.py)
- Pydantic Settings с environment variables
- Settings загружаются из `.env`

### Services
- `ZhipuAIClient`: Клиент для Zhipu AI API через OpenAI SDK
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

## API Response Format

Success:
```json
{"success": true, "data": {...}}
```

Error:
```json
{"success": false, "error": {"code": "...", "message": "..."}}
```

## Caching Strategy

Cache key based on:
- product name (lowercase)
- brand
- category
- language
- fields
- web_search flag

## Common Tasks

### Add new enrichment field
1. Add field to `EnrichedProduct` model in `models/enrichment.py`
2. Update system prompt in `services/zhipu_client.py`
3. Add tests

### Modify API response
1. Update models in `models/`
2. Update endpoint in `api/v1/products.py`
3. Update tests

### Add new endpoint
1. Create handler in `api/v1/`
2. Register in `api/router.py`
3. Add integration tests
