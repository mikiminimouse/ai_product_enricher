# AI Product Enricher

Production-ready сервис для обогащения продуктовых данных с мульти-LLM архитектурой.

## Архитектура

```
                    ┌─────────────────────────────────────┐
                    │         AI Product Enricher         │
                    │           FastAPI Server            │
                    └─────────────────┬───────────────────┘
                                      │
                         ┌────────────┴────────────┐
                         │   LLM Router Service    │
                         │   (по country_origin)   │
                         └────────────┬────────────┘
                                      │
            ┌─────────────────────────┼─────────────────────────┐
            │                         │                         │
            ▼                         │                         ▼
┌───────────────────────┐             │             ┌───────────────────────┐
│      Cloud.ru         │             │             │       Z.ai            │
│  GigaChat3-10B-A1.8B  │◄────────────┴────────────►│      GLM-4.7          │
│                       │                           │                       │
│  country_origin: RU   │                           │  country_origin: *    │
│  (российские товары)  │                           │  (зарубежные товары)  │
└───────────────────────┘                           └───────────────────────┘
```

**Маршрутизация LLM:**
| country_origin | LLM Provider | Модель |
|----------------|--------------|--------|
| `RU` / `RUS` | Cloud.ru | GigaChat3-10B-A1.8B |
| Любой другой / null | Z.ai | GLM-4.7 |

## Внешний API (для команды)

**Base URL:** `http://128.199.126.60:8000`

| Endpoint | Описание |
|----------|----------|
| `/docs` | Swagger UI |
| `/redoc` | ReDoc документация |
| `/api/v1/health` | Health check |
| `/api/v1/products/enrich` | Обогащение одного товара |
| `/api/v1/products/enrich/batch` | Пакетная обработка |

## Возможности

- **Мульти-LLM маршрутизация** — автоматический выбор провайдера по стране
- **Автоопределение manufacturer/trademark** из названия товара
- **Web Search** — актуальная информация о товарах (Z.ai)
- **Пакетная обработка** нескольких продуктов
- **Встроенное кэширование** результатов
- **RESTful API** с OpenAPI документацией
- **Структурированное логирование**
- **Docker-ready**

## Быстрый старт

### Требования

- Python 3.11+
- API ключ Zhipu AI (обязательно)
- API ключ Cloud.ru (опционально, для российских товаров)

### Установка

```bash
cd /root/ai_product_enricher

# Создание виртуального окружения
python -m venv .venv
source .venv/bin/activate

# Установка зависимостей
pip install -e ".[dev]"
```

### Конфигурация

Создайте файл `.env`:

```bash
# Zhipu AI (обязательно)
ZHIPUAI_API_KEY=your_zhipu_api_key

# Cloud.ru (опционально, для RU товаров)
CLOUDRU_API_KEY=your_cloudru_api_key

# Приложение
APP_ENV=production
LOG_LEVEL=INFO
```

### Запуск

```bash
# Development
uvicorn src.ai_product_enricher.main:app --reload

# Production
uvicorn src.ai_product_enricher.main:app --host 0.0.0.0 --port 8000
```

## API Примеры

### Health Check

```bash
curl http://128.199.126.60:8000/api/v1/health
```

Ответ:
```json
{
  "status": "healthy",
  "zhipu_api": "connected",
  "cloudru_api": "connected"
}
```

### Российский товар → Cloud.ru

```bash
curl -X POST http://128.199.126.60:8000/api/v1/products/enrich \
  -H "Content-Type: application/json" \
  -d '{
    "product": {
      "name": "Яндекс Станция Макс",
      "country_origin": "RU"
    }
  }'
```

Ответ (metadata):
```json
{
  "metadata": {
    "model_used": "ai-sage/GigaChat3-10B-A1.8B",
    "llm_provider": "cloudru"
  }
}
```

### Зарубежный товар → Z.ai

```bash
curl -X POST http://128.199.126.60:8000/api/v1/products/enrich \
  -H "Content-Type: application/json" \
  -d '{
    "product": {
      "name": "iPhone 15 Pro",
      "country_origin": "CN"
    }
  }'
```

Ответ (metadata):
```json
{
  "metadata": {
    "model_used": "GLM-4.7",
    "llm_provider": "zhipuai",
    "web_search_used": true
  }
}
```

### Пакетная обработка

```bash
curl -X POST http://128.199.126.60:8000/api/v1/products/enrich/batch \
  -H "Content-Type: application/json" \
  -d '{
    "products": [
      {"name": "1С:Предприятие", "country_origin": "RU"},
      {"name": "Microsoft Office", "country_origin": "US"}
    ]
  }'
```

В batch-ответе каждый товар маршрутизируется к соответствующему LLM.

### Полный запрос с опциями

```bash
curl -X POST http://128.199.126.60:8000/api/v1/products/enrich \
  -H "Content-Type: application/json" \
  -d '{
    "product": {
      "name": "Samsung Galaxy S24 Ultra 512GB",
      "description": "Флагманский смартфон",
      "country_origin": "KR"
    },
    "enrichment_options": {
      "include_web_search": true,
      "language": "ru",
      "fields": ["manufacturer", "trademark", "category", "description", "features", "specifications"]
    }
  }'
```

## Поля обогащения

| Поле | Описание |
|------|----------|
| `manufacturer` | Компания-производитель (физически производит товар) |
| `trademark` | Торговая марка/бренд |
| `category` | Категория товара |
| `model_name` | Модель/артикул |
| `description` | Расширенное описание |
| `features` | Ключевые характеристики |
| `specifications` | Технические характеристики |
| `seo_keywords` | SEO ключевые слова |

## Конфигурация

### Zhipu AI (обязательно)

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `ZHIPUAI_API_KEY` | API ключ | (обязательно) |
| `ZHIPUAI_BASE_URL` | Base URL | https://api.z.ai/api/coding/paas/v4 |
| `ZHIPUAI_MODEL` | Модель | GLM-4.7 |

### Cloud.ru (опционально)

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `CLOUDRU_API_KEY` | API ключ | - |
| `CLOUDRU_BASE_URL` | Base URL | https://foundation-models.api.cloud.ru/v1 |
| `CLOUDRU_MODEL` | Модель | ai-sage/GigaChat3-10B-A1.8B |
| `CLOUDRU_TIMEOUT` | Таймаут (сек) | 60 |

### Приложение

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `APP_ENV` | Окружение | production |
| `APP_DEBUG` | Debug режим | false |
| `APP_PORT` | Порт | 8000 |
| `LOG_LEVEL` | Уровень логирования | INFO |
| `CACHE_TTL_SECONDS` | TTL кэша | 3600 |
| `CACHE_MAX_SIZE` | Размер кэша | 1000 |

## Docker

```bash
# Build
docker build -t ai-product-enricher .

# Run
docker run -p 8000:8000 \
  -e ZHIPUAI_API_KEY=your_key \
  -e CLOUDRU_API_KEY=your_key \
  ai-product-enricher

# Docker Compose
docker-compose up
```

## Тестирование

```bash
# Все тесты
pytest

# Unit тесты
pytest tests/unit -v

# Integration тесты
pytest tests/integration -v

# С coverage
pytest --cov=src/ai_product_enricher --cov-report=html
```

## Структура проекта

```
ai_product_enricher/
├── src/ai_product_enricher/
│   ├── api/              # API endpoints
│   │   └── v1/           # API версия 1
│   ├── core/             # Config, logging, exceptions
│   ├── models/           # Pydantic models
│   ├── services/         # Business logic
│   │   ├── enricher.py       # Маршрутизация LLM
│   │   ├── zhipu_client.py   # Z.ai клиент
│   │   ├── cloudru_client.py # Cloud.ru клиент
│   │   └── cache.py          # Кэш сервис
│   └── main.py           # FastAPI app
├── tests/
│   ├── unit/
│   └── integration/
├── docs/
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## Лицензия

MIT
