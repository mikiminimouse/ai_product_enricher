# AI Product Enricher

> Production-ready сервис для обогащения продуктовых данных с мульти-LLM архитектурой

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)]
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)]
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)]

## Обзор

Сервис автоматически обогащает продуктовые данные, используя несколько LLM-провайдеров:
- **Z.ai (GLM-4.7)** — для зарубежных производителей (CN, US, KR и др.)
- **Cloud.ru (GigaChat)** — для российских производителей (RU)

Автоматическая маршрутизация по полю `country_origin`.

### Ключевая возможность: Manufacturer & Trademark Extraction

Сервис автоматически определяет из названия товара:
- **Производитель (manufacturer)** — компания, которая физически производит товар
- **Торговая марка (trademark)** — бренд, под которым продаётся товар

Пример: для "iPhone 15 Pro" → manufacturer: "Foxconn", trademark: "Apple"

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

### LLM Маршрутизация

| country_origin | LLM Provider | Модель |
|----------------|--------------|--------|
| `RU` / `RUS` | Cloud.ru | GigaChat3-10B-A1.8B |
| Любой другой / null | Z.ai | GLM-4.7 |

При недоступности Cloud.ru — автоматический fallback на Z.ai.

## Внешний API (для команды)

**Base URL:** `http://128.199.126.60:8000` (или `http://localhost:8000` для локальной разработки)

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
- **Встроенное кэширование** результатов (TTL 1 час)
- **RESTful API** с OpenAPI документацией
- **Gradio WebUI** — веб-интерфейс для тестирования и настройки
- **Конфигурируемые поля и промпты** — YAML-based конфигурация
- **Профили обогащения** — переключение между настройками
- **Структурированное логирование** (structlog)
- **Docker-ready**
- **Retry logic** с tenacity

## WebUI — Веб-интерфейс

Сервис включает Gradio WebUI для тестирования и настройки обогащения.

### Запуск WebUI

```bash
# Только WebUI (демо-режим, без enricher)
python -m src.ai_product_enricher.main_webui

# WebUI с enricher service (полный функционал)
python -m src.ai_product_enricher.main_webui --with-enricher

# С публичной ссылкой
python -m src.ai_product_enricher.main_webui --port 7860 --share
```

WebUI доступен на `http://localhost:7860`

### Вкладки WebUI

| Вкладка | Описание |
|---------|----------|
| **Тестирование** | Обогащение товаров, выбор полей, preview промптов |
| **Настройка полей** | Просмотр и редактирование определений полей |
| **Редактор промптов** | Редактирование Jinja2 шаблонов системных и пользовательских промптов |
| **Профили** | Создание, редактирование и переключение профилей обогащения |

### Структура конфигурации

```
config/
├── prompts/
│   ├── system/
│   │   ├── default.yaml          # Стандартный системный промпт
│   │   └── russian_products.yaml # Для российских товаров
│   └── user/
│       └── default.yaml          # Пользовательский промпт
├── fields/
│   ├── default.yaml              # Определения 11 полей
│   └── custom/                   # Кастомные поля
└── profiles/
    ├── default.yaml              # Профиль по умолчанию
    └── custom/                   # Кастомные профили
```

### Engine Layer

Конфигурируемая платформа включает три компонента:

| Компонент | Описание |
|-----------|----------|
| `FieldRegistry` | Реестр полей для извлечения с описаниями и примерами |
| `PromptEngine` | Движок Jinja2 шаблонов для генерации промптов |
| `ConfigurationManager` | Менеджер профилей обогащения |

```python
from src.ai_product_enricher.engine import (
    FieldRegistry,
    PromptEngine,
    ConfigurationManager,
)

# Инициализация
registry = FieldRegistry()
engine = PromptEngine()
config = ConfigurationManager()

# Получение полей
fields = registry.get_fields_for_extraction(["manufacturer", "category"])

# Генерация промпта
system_prompt = engine.render_system_prompt(
    template_name="default",
    field_names=["manufacturer", "trademark", "category"],
    web_search_enabled=True,
)

# Работа с профилями
profile = config.get_active_profile()
```

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
# Development (для отладки, в текущем терминале)
uvicorn src.ai_product_enricher.main:app --reload

# Production (демон в фоне, не падает при закрытии терминала)
# Управление через systemd:
sudo systemctl start ai-product-enricher    # запуск
sudo systemctl stop ai-product-enricher     # остановка
sudo systemctl restart ai-product-enricher  # перезапуск
sudo systemctl status ai-product-enricher   # статус

# Или через удобный скрипт:
./manage_server.sh start    # запуск
./manage_server.sh stop     # остановка
./manage_server.sh restart  # перезапуск
./manage_server.sh status   # статус
./manage_server.sh logs     # логи
```

## API Примеры

### Health Check

```bash
curl http://localhost:8000/api/v1/health
```

Ответ:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "zhipu_api": "connected",
  "cloudru_api": "connected",
  "uptime_seconds": 85568,
  "cache": {
    "size": 0,
    "max_size": 1000,
    "ttl_seconds": 3600,
    "hits": 0,
    "misses": 0,
    "hit_rate_percent": 0.0
  }
}
```

### Российский товар → Cloud.ru

```bash
curl -X POST http://localhost:8000/api/v1/products/enrich \
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
    "llm_provider": "cloudru",
    "tokens_used": 2134,
    "processing_time_ms": 940,
    "web_search_used": false,
    "cached": false
  }
}
```

### Зарубежный товар → Z.ai

```bash
curl -X POST http://localhost:8000/api/v1/products/enrich \
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
    "tokens_used": 2360,
    "processing_time_ms": 34058,
    "web_search_used": true,
    "cached": false
  }
}
```

### Пакетная обработка

```bash
curl -X POST http://localhost:8000/api/v1/products/enrich/batch \
  -H "Content-Type: application/json" \
  -d '{
    "products": [
      {"name": "1С:Предприятие", "country_origin": "RU"},
      {"name": "Microsoft Office", "country_origin": "US"}
    ]
  }'
```

В batch-ответе каждый товар автоматически маршрутизируется к соответствующему LLM:
- `1С:Предприятие` (RU) → Cloud.ru
- `Microsoft Office` (US) → Z.ai

### Полный запрос с опциями

```bash
curl -X POST http://localhost:8000/api/v1/products/enrich \
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

## API Формат данных

### Входные данные (ProductInput)

| Поле | Тип | Обязательный | Описание |
|------|-----|--------------|----------|
| `name` | str | ✓ | Наименование товара из прайс-листа/госзакупок |
| `description` | str \| None | | Дополнительное описание |
| `country_origin` | str \| None | | Страна происхождения (ISO 3166-1 alpha-2/3) |

### Выходные данные (EnrichedProduct)

| Поле | Описание |
|------|----------|
| `manufacturer` | Компания-производитель (физически производит) |
| `trademark` | Торговая марка/бренд |
| `category` | Категория товара |
| `model_name` | Модель/артикул |
| `description` | Обогащённое описание |
| `features` | Ключевые характеристики (список) |
| `specifications` | Технические характеристики (словарь) |
| `seo_keywords` | SEO ключевые слова (список) |

### Metadata

| Поле | Описание |
|------|----------|
| `model_used` | Использованная модель |
| `llm_provider` | `zhipuai` или `cloudru` |
| `tokens_used` | Количество токенов |
| `processing_time_ms` | Время обработки в мс |
| `web_search_used` | Использовался ли web search |
| `cached` | Результат из кэша |
| `timestamp` | Время обработки (ISO 8601) |

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

### Docker Compose пример

```yaml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ZHIPUAI_API_KEY=${ZHIPUAI_API_KEY}
      - CLOUDRU_API_KEY=${CLOUDRU_API_KEY}
      - APP_ENV=production
      - LOG_LEVEL=INFO
    restart: unless-stopped
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

# С покрытием и отчётом
pytest --cov=src/ai_product_enricher --cov-report=term-missing
```

### Тестовые данные

Fixtures находятся в `tests/conftest.py`:
- `mock_product_input` — тестовый ввод
- `mock_enriched_product` — тестовый вывод
- `mock_zhipu_response` — мок Z.ai API

## Структура проекта

```
ai_product_enricher/
├── config/                   # Конфигурационные файлы
│   ├── prompts/              # Шаблоны промптов
│   │   ├── system/           # Системные промпты
│   │   └── user/             # Пользовательские промпты
│   ├── fields/               # Определения полей
│   │   └── custom/           # Кастомные поля
│   └── profiles/             # Профили обогащения
│       └── custom/           # Кастомные профили
├── src/ai_product_enricher/
│   ├── api/              # API endpoints
│   │   ├── v1/           # API версия 1
│   │   │   └── products.py   # Эндпоинты продуктов
│   │   ├── dependencies.py    # Зависимости
│   │   └── router.py          # Роутер
│   ├── core/             # Config, logging, exceptions
│   │   ├── config.py          # Конфигурация
│   │   ├── logging.py         # Логирование
│   │   └── exceptions.py      # Исключения
│   ├── engine/           # Configuration Engine Layer
│   │   ├── field_registry.py  # Реестр полей
│   │   ├── prompt_engine.py   # Движок промптов
│   │   └── config_manager.py  # Менеджер профилей
│   ├── models/           # Pydantic models
│   │   ├── enrichment.py      # Модели обогащения
│   │   └── schemas.py         # API схемы
│   ├── services/         # Business logic
│   │   ├── enricher.py        # Маршрутизация LLM
│   │   ├── zhipu_client.py    # Z.ai клиент
│   │   ├── cloudru_client.py  # Cloud.ru клиент
│   │   └── cache.py           # Кэш сервис
│   ├── webui/            # Gradio WebUI
│   │   └── app.py             # WebUI приложение
│   ├── main.py           # FastAPI app
│   └── main_webui.py     # WebUI entry point
├── tests/
│   ├── unit/            # Unit тесты
│   ├── integration/     # Integration тесты
│   └── conftest.py      # Fixtures
├── docs/                # Документация
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

## Кэширование

Кэш ключ основывается на:
- product name (lowercase, case-insensitive)
- language
- fields
- web_search flag

**Примечание:** manufacturer/trademark не участвуют в ключе кэша, т.к. извлекаются из name.

TTL по умолчанию: 3600 секунд (1 час)
Максимальный размер: 1000 записей

## Development

```bash
# Type checking
mypy src/

# Linting
ruff check src/

# Format
ruff format src/

# Запуск с автозагрузкой
uvicorn src.ai_product_enricher.main:app --reload --log-level debug
```

## AI Co-Authorship

Этот проект разработан при содействии AI:

| AI | Роль |
|----|------|
| **Claude Opus 4.5** (Anthropic) | Архитектура, код, документация, тесты |
| **Zhipu AI GLM-4.7** | Обогащение данных зарубежных товаров |
| **Cloud.ru GigaChat** | Обогащение данных российских товаров |

### Соавторство коммитов

Все коммиты содержат соавторство:
```
Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
```

### Используемые технологии

- **LLM Providers**: Zhipu AI, Cloud.ru
- **API Framework**: FastAPI
- **Data Validation**: Pydantic v2
- **Testing**: pytest + pytest-asyncio
- **Logging**: structlog
- **Retry**: tenacity
- **Container**: Docker

## Troubleshooting

### Cloud.ru недоступен

Если Cloud.ru недоступен, сервис автоматически fallback'ится на Z.ai:
```python
# В логах:
"Failed to enrich with Cloud.ru, falling back to Zhipu AI"
```

### Timeout ошибки

Увеличьте `CLOUDRU_TIMEOUT` в `.env`:
```bash
CLOUDRU_TIMEOUT=120  # 2 минуты
```

### Кэш не работает

Проверьте конфигурацию:
```bash
LOG_LEVEL=DEBUG  # Включите DEBUG для логов кэша
```

## Лицензия

MIT License - см. файл LICENSE

---

**Версия:** 1.0.0
**Статус:** Production-ready
**Tech Stack:** Python 3.11+, FastAPI, Pydantic v2, OpenAI SDK
