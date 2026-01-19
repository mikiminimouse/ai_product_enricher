# Инструкция по использованию API Product Enricher

## Архитектура мульти-LLM маршрутизации

Сервис автоматически выбирает оптимальную LLM-модель на основе страны происхождения товара:

| Страна | Провайдер | Модель |
|--------|-----------|--------|
| RU / RUS | Cloud.ru | GigaChat (ai-sage/GigaChat3-10B-A1.8B) |
| Остальные (CN, US, KR и др.) | Z.ai | GLM-4.7 |

## Доступ к API (для коллег)

API сервис доступен по внешнему адресу:

```
http://128.199.126.60:8000
```

### Интерактивная документация

- **Swagger UI**: http://128.199.126.60:8000/docs
- **ReDoc**: http://128.199.126.60:8000/redoc

### Быстрая проверка

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

---

## Обогащение продуктов

### Зарубежный товар (→ Z.ai)

```bash
curl -X POST http://128.199.126.60:8000/api/v1/products/enrich \
  -H "Content-Type: application/json" \
  -d '{
    "product": {
      "name": "Apple iPhone 15 Pro Max 256GB Black Titanium",
      "country_origin": "CN"
    },
    "enrichment_options": {
      "include_web_search": true,
      "language": "ru",
      "fields": ["manufacturer", "trademark", "category", "description"]
    }
  }'
```

### Российский товар (→ Cloud.ru)

```bash
curl -X POST http://128.199.126.60:8000/api/v1/products/enrich \
  -H "Content-Type: application/json" \
  -d '{
    "product": {
      "name": "Яндекс Станция Макс с Алисой",
      "country_origin": "RU"
    },
    "enrichment_options": {
      "language": "ru",
      "fields": ["manufacturer", "trademark", "category", "description"]
    }
  }'
```

### Минимальный запрос (без указания страны → Z.ai)

```bash
curl -X POST http://128.199.126.60:8000/api/v1/products/enrich \
  -H "Content-Type: application/json" \
  -d '{
    "product": {
      "name": "Смартфон Samsung Galaxy S24 Ultra"
    }
  }'
```

### Пример ответа

```json
{
  "success": true,
  "data": {
    "product": {
      "name": "Apple iPhone 15 Pro Max 256GB Black Titanium",
      "description": null,
      "country_origin": "CN"
    },
    "enriched": {
      "manufacturer": "Foxconn",
      "trademark": "Apple",
      "category": "Смартфоны",
      "model_name": "iPhone 15 Pro Max 256GB",
      "description": "Флагманский смартфон Apple с титановым корпусом..."
    },
    "metadata": {
      "model_used": "GLM-4.7",
      "llm_provider": "zhipuai",
      "tokens_used": 2381,
      "processing_time_ms": 47312,
      "web_search_used": true,
      "cached": false
    }
  }
}
```

---

## Пакетная обработка

Batch-запрос с товарами из разных стран (автоматическая маршрутизация):

```bash
curl -X POST http://128.199.126.60:8000/api/v1/products/enrich/batch \
  -H "Content-Type: application/json" \
  -d '{
    "products": [
      {"name": "Kaspersky Internet Security", "country_origin": "RU"},
      {"name": "Samsung Galaxy S24 Ultra", "country_origin": "KR"},
      {"name": "Xiaomi Mi Smart Band 8", "country_origin": "CN"}
    ],
    "enrichment_options": {
      "language": "ru",
      "fields": ["manufacturer", "trademark", "category"]
    },
    "batch_options": {
      "max_concurrent": 3,
      "fail_strategy": "continue"
    }
  }'
```

### Пример ответа batch

```json
{
  "success": true,
  "data": {
    "results": [
      {
        "index": 0,
        "success": true,
        "result": {
          "enriched": {"manufacturer": "Лаборатория Касперского", "trademark": "Kaspersky"},
          "metadata": {"llm_provider": "cloudru", "model_used": "ai-sage/GigaChat3-10B-A1.8B"}
        }
      },
      {
        "index": 1,
        "success": true,
        "result": {
          "enriched": {"manufacturer": "Samsung Electronics", "trademark": "Samsung"},
          "metadata": {"llm_provider": "zhipuai", "model_used": "GLM-4.7"}
        }
      }
    ],
    "summary": {"total": 3, "succeeded": 3, "failed": 0}
  }
}
```

---

## Использование с Python

```python
import requests

API_URL = "http://128.199.126.60:8000/api/v1/products/enrich"

def enrich_product(name: str, country_origin: str = None) -> dict:
    """Обогатить данные продукта с автоматическим выбором LLM."""
    payload = {
        "product": {
            "name": name,
            "country_origin": country_origin  # "RU" для Cloud.ru, иначе Z.ai
        },
        "enrichment_options": {
            "include_web_search": True,
            "language": "ru",
            "fields": ["manufacturer", "trademark", "category", "description"]
        }
    }
    response = requests.post(API_URL, json=payload)
    return response.json()

# Российский товар → Cloud.ru (GigaChat)
result_ru = enrich_product("Яндекс Станция Макс", country_origin="RU")
print(f"Провайдер: {result_ru['data']['metadata']['llm_provider']}")  # cloudru

# Зарубежный товар → Z.ai (GLM-4.7)
result_cn = enrich_product("iPhone 15 Pro", country_origin="CN")
print(f"Провайдер: {result_cn['data']['metadata']['llm_provider']}")  # zhipuai
```

---

## Входные параметры

### ProductInput

| Параметр | Тип | Обязательный | Описание |
|----------|-----|--------------|----------|
| `name` | string | Да | Наименование товара из прайс-листа |
| `description` | string | Нет | Дополнительное описание |
| `country_origin` | string | Нет | Страна происхождения (ISO 3166-1: RU, CN, US, KR и др.) |

### EnrichmentOptions

| Параметр | Тип | По умолчанию | Описание |
|----------|-----|--------------|----------|
| `include_web_search` | bool | true | Использовать веб-поиск (только Z.ai) |
| `language` | string | "ru" | Язык результата (ru, en, zh) |
| `fields` | list | все | Какие поля обогащать |
| `max_features` | int | 10 | Максимум характеристик |

---

## Выходные поля

### EnrichedProduct

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

### Metadata

| Поле | Описание |
|------|----------|
| `model_used` | Используемая модель (GLM-4.7 или ai-sage/GigaChat3-10B-A1.8B) |
| `llm_provider` | Провайдер LLM (zhipuai или cloudru) |
| `tokens_used` | Количество использованных токенов |
| `processing_time_ms` | Время обработки в миллисекундах |
| `web_search_used` | Был ли использован веб-поиск |
| `cached` | Был ли результат взят из кэша |

---

## Локальный запуск сервера

```bash
cd /root/ai_product_enricher
source .venv/bin/activate

# Запуск с внешним доступом
python -c "import uvicorn; uvicorn.run('src.ai_product_enricher.main:app', host='0.0.0.0', port=8000)"
```

После запуска:
- API: http://localhost:8000
- Swagger: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
