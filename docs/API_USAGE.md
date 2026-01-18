# Инструкция по использованию API Product Enricher

## Запуск сервера

```bash
cd /root/ai_product_enricher
source .venv/bin/activate
uvicorn src.ai_product_enricher.main:app --host 0.0.0.0 --port 8000
```

После запуска сервер доступен по адресу: `http://localhost:8000`

## Проверка работоспособности

```bash
curl http://localhost:8000/api/v1/ping
# Ответ: {"status":"pong"}
```

## Обогащение одного продукта

### Минимальный запрос (только название)

```bash
curl -X POST http://localhost:8000/api/v1/products/enrich \
  -H "Content-Type: application/json" \
  -d '{
    "product": {
      "name": "Смартфон Apple iPhone 15 Pro Max 256GB Black Titanium"
    }
  }'
```

### Запрос с описанием и опциями

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
      "language": "ru",
      "fields": ["manufacturer", "trademark", "category", "description", "features"]
    }
  }'
```

### Пример ответа

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

## Пакетная обработка

```bash
curl -X POST http://localhost:8000/api/v1/products/enrich/batch \
  -H "Content-Type: application/json" \
  -d '{
    "products": [
      {"name": "Смартфон Samsung Galaxy S24 Ultra 512GB"},
      {"name": "Ноутбук ASUS ROG Strix G16 G614JI"},
      {"name": "Телевизор LG OLED55C4RLA 55 дюймов"}
    ],
    "enrichment_options": {
      "include_web_search": true,
      "language": "ru"
    },
    "batch_options": {
      "max_concurrent": 3,
      "fail_strategy": "continue"
    }
  }'
```

## Использование с Python

```python
import requests

API_URL = "http://localhost:8000/api/v1/products/enrich"

def enrich_product(name: str, description: str = None) -> dict:
    """Обогатить данные продукта из прайс-листа."""
    response = requests.post(API_URL, json={
        "product": {
            "name": name,
            "description": description
        },
        "enrichment_options": {
            "include_web_search": True,
            "language": "ru",
            "fields": ["manufacturer", "trademark", "category", "description", "features"]
        }
    })
    return response.json()

# Пример использования
result = enrich_product("Смартфон Apple iPhone 15 Pro Max 256GB")

if result["success"]:
    enriched = result["data"]["enriched"]
    print(f"Производитель: {enriched['manufacturer']}")
    print(f"Торговая марка: {enriched['trademark']}")
    print(f"Категория: {enriched['category']}")
    print(f"Описание: {enriched['description']}")
```

## Доступные поля для обогащения

| Поле | Описание |
|------|----------|
| `manufacturer` | Компания-производитель (физически производит товар) |
| `trademark` | Торговая марка/бренд |
| `category` | Категория товара |
| `model_name` | Модель/артикул |
| `description` | Расширенное описание |
| `features` | Ключевые характеристики (список) |
| `specifications` | Технические характеристики (словарь) |
| `seo_keywords` | SEO ключевые слова (список) |

## Опции обогащения

| Параметр | Тип | По умолчанию | Описание |
|----------|-----|--------------|----------|
| `include_web_search` | bool | true | Использовать веб-поиск |
| `language` | string | "ru" | Язык результата (ru, en, zh) |
| `fields` | list | все поля | Какие поля обогащать |
| `max_features` | int | 10 | Максимум характеристик |

## Интерактивная документация

При запущенном сервере доступна документация:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
