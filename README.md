# AI Product Enricher

Production-ready сервис для обогащения продуктовых данных с использованием Zhipu AI (GLM-4.7) API с поддержкой web_search для получения актуальной информации о продуктах.

## Возможности

- **Упрощённый ввод** - принимает только наименование и описание из прайс-листа/госзакупок
- **Автоматическое определение производителя и торговой марки** из названия товара
- **Обогащение данных** с использованием Zhipu AI GLM-4.7 с web search
- **Пакетная обработка** нескольких продуктов
- **Встроенное кэширование** результатов
- **RESTful API** с документацией OpenAPI
- **Структурированное логирование**
- **Docker-ready**

## Ключевая особенность: Извлечение производителя и торговой марки

Сервис автоматически определяет:
- **Производитель (manufacturer)** - компания, которая *физически производит* товар (например, Foxconn для iPhone)
- **Торговая марка (trademark)** - бренд, под которым продаётся товар (например, Apple)

Пример:
```json
{
  "input": "Смартфон Apple iPhone 15 Pro Max 256GB Black Titanium",
  "output": {
    "manufacturer": "Foxconn",
    "trademark": "Apple",
    "category": "Смартфоны",
    "model_name": "iPhone 15 Pro Max 256GB"
  }
}
```

## Быстрый старт

### Требования

- Python 3.11+
- Zhipu AI API ключ

### Установка

```bash
# Клонирование
cd /root/ai_product_enricher

# Создание виртуального окружения
python -m venv .venv
source .venv/bin/activate

# Установка зависимостей
pip install -e ".[dev]"
```

### Конфигурация

Создайте файл `.env` на основе `.env.example`:

```bash
cp .env.example .env
```

Отредактируйте `.env` и укажите ваш API ключ:

```bash
ZHIPUAI_API_KEY=your_api_key_here
```

### Запуск

```bash
# Development mode
uvicorn src.ai_product_enricher.main:app --reload

# Production mode
uvicorn src.ai_product_enricher.main:app --host 0.0.0.0 --port 8000
```

### Docker

```bash
# Build
docker build -t ai-product-enricher .

# Run
docker run -p 8000:8000 -e ZHIPUAI_API_KEY=your_key ai-product-enricher

# Или с docker-compose
docker-compose up
```

## API

### Обогащение одного продукта

Упрощённый ввод - только наименование из прайс-листа:

```bash
curl -X POST http://localhost:8000/api/v1/products/enrich \
  -H "Content-Type: application/json" \
  -d '{
    "product": {
      "name": "Смартфон Apple iPhone 15 Pro Max 256GB Black Titanium"
    },
    "enrichment_options": {
      "include_web_search": true,
      "language": "ru",
      "fields": ["manufacturer", "trademark", "category", "description", "features"]
    }
  }'
```

С описанием (опционально):

```bash
curl -X POST http://localhost:8000/api/v1/products/enrich \
  -H "Content-Type: application/json" \
  -d '{
    "product": {
      "name": "Картридж HP 123XL черный оригинальный F6V19AE",
      "description": "Высокой емкости для принтеров HP DeskJet"
    },
    "enrichment_options": {
      "include_web_search": true,
      "language": "ru"
    }
  }'
```

### Ответ API

```json
{
  "success": true,
  "data": {
    "product": {
      "name": "Смартфон Apple iPhone 15 Pro Max 256GB Black Titanium",
      "description": null
    },
    "enriched": {
      "manufacturer": "Foxconn",
      "trademark": "Apple",
      "category": "Смартфоны",
      "model_name": "iPhone 15 Pro Max 256GB",
      "description": "Флагманский смартфон Apple с титановым корпусом...",
      "features": ["Чип A17 Pro", "Титановый корпус", "Камера 48MP"],
      "specifications": {},
      "seo_keywords": []
    },
    "sources": [],
    "metadata": {
      "model_used": "GLM-4.7",
      "tokens_used": 1943,
      "processing_time_ms": 19649,
      "web_search_used": true,
      "cached": false
    }
  }
}
```

### Пакетная обработка

```bash
curl -X POST http://localhost:8000/api/v1/products/enrich/batch \
  -H "Content-Type: application/json" \
  -d '{
    "products": [
      {"name": "Смартфон Samsung Galaxy S24 Ultra 512GB"},
      {"name": "Телевизор Samsung QE65S95DAUXRU 65 дюймов OLED 4K"}
    ],
    "enrichment_options": {
      "include_web_search": true,
      "language": "ru"
    },
    "batch_options": {
      "max_concurrent": 5
    }
  }'
```

### Health Check

```bash
curl http://localhost:8000/api/v1/health
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

## Документация API

При запуске в development режиме доступна интерактивная документация:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

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
│   ├── core/             # Core modules (config, logging, exceptions)
│   ├── models/           # Pydantic models
│   ├── services/         # Business logic
│   └── main.py           # FastAPI app
├── tests/                # Tests
│   ├── unit/
│   └── integration/
├── docs/                 # Documentation
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## Конфигурация

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `ZHIPUAI_API_KEY` | API ключ Zhipu AI | (обязательно) |
| `ZHIPUAI_BASE_URL` | Base URL API | https://api.z.ai/api/coding/paas/v4 |
| `ZHIPUAI_MODEL` | Модель для использования | GLM-4.7 |
| `APP_ENV` | Окружение (development/production) | production |
| `APP_DEBUG` | Debug режим | false |
| `APP_PORT` | Порт приложения | 8000 |
| `LOG_LEVEL` | Уровень логирования | INFO |
| `CACHE_TTL_SECONDS` | TTL кэша в секундах | 3600 |
| `CACHE_MAX_SIZE` | Максимальный размер кэша | 1000 |

## Лицензия

MIT
