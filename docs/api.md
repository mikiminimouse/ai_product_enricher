# API Documentation

## Overview

AI Product Enricher API предоставляет endpoints для обогащения продуктовых данных с использованием Zhipu AI.

Base URL: `http://localhost:8000/api/v1`

## Authentication

На данный момент API не требует аутентификации. В production рекомендуется добавить API key authentication.

## Endpoints

### Health

#### GET /health

Проверка состояния сервиса.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "zhipu_api": "connected",
  "uptime_seconds": 3600,
  "cache": {
    "size": 10,
    "max_size": 1000,
    "hits": 50,
    "misses": 25,
    "hit_rate_percent": 66.67
  }
}
```

#### GET /ping

Простая проверка доступности.

**Response:**
```json
{
  "status": "pong"
}
```

#### GET /metrics

Метрики приложения.

**Response:**
```json
{
  "uptime_seconds": 3600,
  "cache": {...}
}
```

### Products

#### POST /products/enrich

Обогащение одного продукта.

**Request Body:**
```json
{
  "product": {
    "name": "iPhone 15 Pro Max",
    "category": "smartphones",
    "brand": "Apple",
    "description": "optional existing description",
    "sku": "IPHN15PM-256-BLK",
    "attributes": {"color": "black"}
  },
  "enrichment_options": {
    "include_web_search": true,
    "language": "ru",
    "fields": ["description", "features", "specifications", "seo_keywords"],
    "search_recency": "month",
    "max_features": 10,
    "max_keywords": 15
  }
}
```

**Product Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | Yes | Название продукта |
| category | string | No | Категория |
| brand | string | No | Бренд |
| description | string | No | Существующее описание |
| sku | string | No | Артикул |
| attributes | object | No | Дополнительные атрибуты |

**Enrichment Options:**
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| include_web_search | boolean | true | Использовать web search |
| language | string | "ru" | Язык результата (ISO 639-1) |
| fields | array | all | Поля для обогащения |
| search_recency | string | "month" | Актуальность поиска (day/week/month/year) |
| max_features | integer | 10 | Максимум features |
| max_keywords | integer | 15 | Максимум SEO keywords |

**Available Fields:**
- `description` - Описание продукта
- `features` - Ключевые особенности
- `specifications` - Технические характеристики
- `seo_keywords` - SEO ключевые слова
- `marketing_copy` - Маркетинговый текст
- `pros` - Преимущества
- `cons` - Недостатки

**Response:**
```json
{
  "success": true,
  "data": {
    "product": {
      "name": "iPhone 15 Pro Max",
      "category": "smartphones",
      "brand": "Apple",
      "sku": "IPHN15PM-256-BLK"
    },
    "enriched": {
      "description": "Флагманский смартфон Apple...",
      "features": ["Титановый корпус", "Камера 48MP", "A17 Pro чип"],
      "specifications": {
        "display": "6.7\" Super Retina XDR",
        "processor": "A17 Pro"
      },
      "seo_keywords": ["iphone 15 pro max купить"]
    },
    "sources": [
      {"title": "Apple Official", "url": "https://apple.com/...", "date": "2025-01-15"}
    ],
    "metadata": {
      "model_used": "GLM-4.7",
      "tokens_used": 1523,
      "processing_time_ms": 2340,
      "web_search_used": true,
      "cached": false,
      "timestamp": "2025-01-18T12:00:00Z"
    }
  }
}
```

#### POST /products/enrich/batch

Пакетная обработка нескольких продуктов.

**Request Body:**
```json
{
  "products": [
    {"name": "Product 1", "category": "cat1"},
    {"name": "Product 2", "category": "cat2"}
  ],
  "enrichment_options": {
    "include_web_search": true,
    "language": "en"
  },
  "batch_options": {
    "max_concurrent": 5,
    "fail_strategy": "continue",
    "timeout_per_product": 60
  }
}
```

**Batch Options:**
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| max_concurrent | integer | 5 | Максимум параллельных запросов (1-20) |
| fail_strategy | string | "continue" | Стратегия при ошибке (continue/stop) |
| timeout_per_product | integer | 60 | Таймаут на продукт в секундах |

**Response:**
```json
{
  "success": true,
  "data": {
    "results": [
      {
        "index": 0,
        "success": true,
        "result": {...},
        "error": null
      },
      {
        "index": 1,
        "success": false,
        "result": null,
        "error": "Timeout"
      }
    ],
    "summary": {
      "total": 2,
      "succeeded": 1,
      "failed": 1,
      "total_tokens": 1000,
      "total_time_ms": 5000
    }
  }
}
```

#### GET /products/cache/stats

Статистика кэша.

**Response:**
```json
{
  "size": 10,
  "max_size": 1000,
  "ttl_seconds": 3600,
  "hits": 50,
  "misses": 25,
  "hit_rate_percent": 66.67
}
```

#### POST /products/cache/clear

Очистка кэша.

**Response:**
```json
{
  "cleared": 10
}
```

## Error Responses

Все ошибки возвращаются в формате:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message",
    "details": {...}
  }
}
```

**Error Codes:**
| Code | HTTP Status | Description |
|------|-------------|-------------|
| VALIDATION_ERROR | 400/422 | Ошибка валидации входных данных |
| ZHIPU_API_ERROR | 502 | Ошибка Zhipu AI API |
| RATE_LIMIT_EXCEEDED | 429 | Превышен лимит запросов |
| ENRICHMENT_ERROR | 500 | Ошибка обогащения |
| INTERNAL_ERROR | 500 | Внутренняя ошибка сервера |

## Rate Limiting

По умолчанию: 100 запросов в минуту. Настраивается через `RATE_LIMIT_REQUESTS` и `RATE_LIMIT_PERIOD`.

## Caching

Результаты кэшируются на основе:
- Product name (case-insensitive)
- Product brand
- Product category
- Language
- Enrichment fields
- Web search flag

TTL по умолчанию: 1 час.

---

## Real Examples / Реальные примеры

Ниже приведены реальные примеры запросов и ответов для 5 различных продуктов.

### Example 1: Sony WH-1000XM5 (Headphones)

**Request:**
```bash
curl -X POST http://128.199.126.60/api/v1/products/enrich \
  -H "Content-Type: application/json" \
  -d '{
    "product": {
      "name": "Sony WH-1000XM5",
      "category": "headphones",
      "brand": "Sony"
    },
    "enrichment_options": {
      "include_web_search": false,
      "language": "ru",
      "fields": ["description", "features", "specifications"]
    }
  }'
```

**Response:**
```json
{
  "success": true,
  "data": {
    "product": {
      "name": "Sony WH-1000XM5",
      "category": "headphones",
      "brand": "Sony"
    },
    "enriched": {
      "description": "Беспроводные наушники Sony WH-1000XM5 — это флагманская модель с передовой системой активного шумоподавления и исключительным качеством звука. Оборудованные двумя мощными процессорами и восемью микрофонами, они автоматически адаптируются к окружающей среде, обеспечивая полную изоляцию от внешнего шума.",
      "features": [
        "Передовая система активного шумоподавления (Integrated Processor V1)",
        "До 30 часов автономной работы с включенным шумоподавлением",
        "Быстрая зарядка: 3 минуты дают до 3 часов прослушивания",
        "Поддержка кодека LDAC для передачи звука Hi-Res",
        "Технология DSEE Extreme для восстановления качества аудиофайлов",
        "Функция одновременного подключения к двум Bluetooth-устройствам"
      ],
      "specifications": {
        "Тип драйвера": "30 мм (купольный)",
        "Частотный диапазон": "4 Гц – 40 000 Гц",
        "Время работы от батареи": "до 30 часов",
        "Версия Bluetooth": "5.2",
        "Поддерживаемые кодеки": "LDAC, AAC, SBC",
        "Вес": "250 г"
      }
    },
    "metadata": {
      "model_used": "GLM-4.7",
      "tokens_used": 2300,
      "processing_time_ms": 36123,
      "web_search_used": false
    }
  }
}
```

---

### Example 2: MacBook Pro 16 M3 Max (Laptops)

**Request:**
```bash
curl -X POST http://128.199.126.60/api/v1/products/enrich \
  -H "Content-Type: application/json" \
  -d '{
    "product": {
      "name": "MacBook Pro 16 M3 Max",
      "category": "laptops",
      "brand": "Apple"
    },
    "enrichment_options": {
      "include_web_search": false,
      "language": "ru",
      "fields": ["description", "features", "specifications"]
    }
  }'
```

**Response:**
```json
{
  "success": true,
  "data": {
    "product": {
      "name": "MacBook Pro 16 M3 Max",
      "category": "laptops",
      "brand": "Apple"
    },
    "enriched": {
      "description": "MacBook Pro 16 с чипом M3 Max — это самый мощный портативный компьютер Apple, созданный для решения профессиональных задач самой высокой сложности. Он оснащен великолепным экраном Liquid Retina XDR с диагональю 16,2 дюйма и обеспечивает исключительную производительность для монтажа видео, разработки ПО и 3D-рендеринга.",
      "features": [
        "Чип Apple M3 Max с 16-ядерным процессором и до 40-ядерным графическим ядром",
        "Дисплей Liquid Retina XDR (16,2\", 3456x2234, ProMotion 120 Гц)",
        "Поддержка объединенной памяти объемом до 128 ГБ",
        "Шестиколоночная аудиосистема с сабвуферами",
        "Полный набор портов: 3 Thunderbolt 4, HDMI, MagSafe 3, SDXC",
        "Клавиатура Magic Keyboard с подсветкой и Touch ID"
      ],
      "specifications": {
        "Процессор": "Apple M3 Max (CPU до 16 ядер)",
        "Графика": "До 40 ядер GPU",
        "Экран": "16.2 дюйма Liquid Retina XDR, 3456 x 2234, HDR",
        "Память": "До 128 ГБ unified memory",
        "Накопитель": "SSD до 8 ТБ",
        "Батарея": "Литий-полимерная, 100 Вт⋅ч, до 22 часов работы",
        "Вес": "2,14 кг"
      }
    },
    "metadata": {
      "model_used": "GLM-4.7",
      "tokens_used": 2510,
      "processing_time_ms": 51049,
      "web_search_used": false
    }
  }
}
```

---

### Example 3: Dyson V15 Detect (Vacuum Cleaners)

**Request:**
```bash
curl -X POST http://128.199.126.60/api/v1/products/enrich \
  -H "Content-Type: application/json" \
  -d '{
    "product": {
      "name": "Dyson V15 Detect",
      "category": "vacuum cleaners",
      "brand": "Dyson"
    },
    "enrichment_options": {
      "include_web_search": false,
      "language": "ru",
      "fields": ["description", "features", "specifications"]
    }
  }'
```

**Response:**
```json
{
  "success": true,
  "data": {
    "product": {
      "name": "Dyson V15 Detect",
      "category": "vacuum cleaners",
      "brand": "Dyson"
    },
    "enriched": {
      "description": "Беспроводной пылесос Dyson V15 Detect оснащен революционной технологией лазерного обнаружения пыли, которая подсвечивает невидимые микрочастицы на твердых полах. Интеллектуальный пьезо-датчик подсчитывает и измеряет загрязнения до 15 000 раз в секунду, автоматически регулируя мощность всасывания для оптимальной уборки.",
      "features": [
        "Лазерный детектор пыли для отображения микрочастиц",
        "Пьезо-сенсор для автоматической регулировки мощности",
        "Цветной LCD-экран с отчетом о частицах в реальном времени",
        "Мощный цифровой двигатель V15 Dyson Hyperdymium™",
        "Фильтрация HEPA H13 с полной герметизацией",
        "Время автономной работы до 60 минут"
      ],
      "specifications": {
        "Тип": "беспроводной вертикальный пылесос",
        "Мощность всасывания": "230 Вт (Air Watts)",
        "Напряжение": "25.2 В",
        "Вес": "3.0 кг",
        "Емкость пылесборника": "0.76 л",
        "Время работы": "до 60 минут",
        "Фильтрация": "HEPA H13"
      }
    },
    "metadata": {
      "model_used": "GLM-4.7",
      "tokens_used": 2435,
      "processing_time_ms": 39158,
      "web_search_used": false
    }
  }
}
```

---

### Example 4: PlayStation 5 Pro (Gaming Consoles)

**Request:**
```bash
curl -X POST http://128.199.126.60/api/v1/products/enrich \
  -H "Content-Type: application/json" \
  -d '{
    "product": {
      "name": "PlayStation 5 Pro",
      "category": "gaming consoles",
      "brand": "Sony"
    },
    "enrichment_options": {
      "include_web_search": false,
      "language": "ru",
      "fields": ["description", "features", "specifications"]
    }
  }'
```

**Response:**
```json
{
  "success": true,
  "data": {
    "product": {
      "name": "PlayStation 5 Pro",
      "category": "gaming consoles",
      "brand": "Sony"
    },
    "enriched": {
      "description": "PlayStation 5 Pro — это усовершенствованная игровая консоль от Sony, созданная для вывода графики сверхвысокого разрешения и плавной частоты кадров. Она предлагает значительно увеличенную вычислительную мощность, ультрабыстрый SSD объемом 2 ТБ и передовые технологии AI-апскейлинга.",
      "features": [
        "Увеличенная производительность GPU для разрешения 4K и выше",
        "Технология PlayStation Spectral Super Resolution (PSSR) на базе AI",
        "Улучшенная трассировка лучей (Ray Tracing) в 2-3 раза быстрее",
        "Сверхбыстрый SSD на 2 ТБ",
        "Поддержка Wi-Fi 7 для скоростной игры по сети",
        "Полная обратная совместимость с играми PS4 и PS5"
      ],
      "specifications": {
        "Центральный процессор": "AMD Zen 2, 8 ядер / 16 потоков (частота до 4.4 ГГц)",
        "Графический процессор": "AMD RDNA 2, 16.7 TFLOPs, 60 вычислительных блоков",
        "Оперативная память": "16 ГБ GDDR6",
        "Внутреннее хранилище": "2 ТБ SSD",
        "Видеовыход": "HDMI 2.1 (4K 120Гц, 8K)",
        "Беспроводная связь": "Wi-Fi 7, Bluetooth 5.3",
        "Вес": "Приблизительно 4.5 кг"
      }
    },
    "metadata": {
      "model_used": "GLM-4.7",
      "tokens_used": 2268,
      "processing_time_ms": 43622,
      "web_search_used": false
    }
  }
}
```

---

### Example 5: DJI Mini 4 Pro (Drones)

**Request:**
```bash
curl -X POST http://128.199.126.60/api/v1/products/enrich \
  -H "Content-Type: application/json" \
  -d '{
    "product": {
      "name": "DJI Mini 4 Pro",
      "category": "drones",
      "brand": "DJI"
    },
    "enrichment_options": {
      "include_web_search": false,
      "language": "ru",
      "fields": ["description", "features", "specifications"]
    }
  }'
```

**Response:**
```json
{
  "success": true,
  "data": {
    "product": {
      "name": "DJI Mini 4 Pro",
      "category": "drones",
      "brand": "DJI"
    },
    "enriched": {
      "description": "DJI Mini 4 Pro — это компактный и легкий квадрокоптер весом менее 249 г, оснащенный всенаправленной системой избегания препятствий для максимальной безопасности полетов. Дрон снимает потрясающее видео 4K/60 HDR и фото разрешением 20 МП, а система передачи видео OcuSync 4.0 обеспечивает стабильное соединение на расстоянии до 20 км.",
      "features": [
        "Вес менее 249 г, не требующий регистрации",
        "Всенаправленное зрение и избегание препятствий",
        "Запись видео 4K/60 HDR и фото 20 МП",
        "Система передачи видео OcuSync 4.0 с дальностью до 20 км",
        "Умное отслеживание ActiveTrack 360",
        "Время полета до 34 минут (до 45 минут с аккумулятором Plus)"
      ],
      "specifications": {
        "Вес": "249 г",
        "Габариты (сложенный)": "148×90×64 мм",
        "Габариты (разложенный)": "300×410×105 мм",
        "Максимальное разрешение видео": "4K/60fps",
        "Фотокамера": "20 МП, 1/1.3 дюйма",
        "Максимальное время полета": "34 минуты",
        "Максимальная дальность передачи": "20 км (FCC)",
        "Тип подвеса": "3-осевой (механический)"
      }
    },
    "metadata": {
      "model_used": "GLM-4.7",
      "tokens_used": 2639,
      "processing_time_ms": 115304,
      "web_search_used": false
    }
  }
}
```

---

## Performance Notes

| Product | Tokens Used | Processing Time |
|---------|-------------|-----------------|
| Sony WH-1000XM5 | 2300 | ~36 sec |
| MacBook Pro 16 M3 Max | 2510 | ~51 sec |
| Dyson V15 Detect | 2435 | ~39 sec |
| PlayStation 5 Pro | 2268 | ~44 sec |
| DJI Mini 4 Pro | 2639 | ~115 sec |

Average processing time: ~57 seconds per product (without web search).
