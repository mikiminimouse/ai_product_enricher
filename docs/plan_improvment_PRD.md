# PRD и Инструкция по реализации: AI Product Enricher v2.0

## Документ для выполнения через Claude Code

---

# ЧАСТЬ 1: PRODUCT REQUIREMENTS DOCUMENT (PRD)

## 1. Резюме проекта

**Название проекта:** AI Product Enricher v2.0 — Configurable Enrichment Platform

**Цель:** Трансформировать существующий сервис обогащения продуктовых данных из системы с hardcoded логикой в гибкую, конфигурируемую платформу с WebUI для управления промптами, полями и профилями без изменения кода.

**Ключевые deliverables:**
1. Configuration Engine Layer (FieldRegistry, PromptEngine, ConfigurationManager)
2. Gradio WebUI для тестирования и настройки
3. YAML-based конфигурационные файлы
4. Интеграция с существующими LLM клиентами

---

## 2. Текущее состояние системы

### 2.1 Структура проекта (AS-IS)

```
ai_product_enricher/
├── src/ai_product_enricher/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── health.py
│   │   │   └── products.py
│   │   ├── dependencies.py
│   │   └── router.py
│   ├── core/
│   │   ├── config.py
│   │   ├── exceptions.py
│   │   └── logging.py
│   ├── models/
│   │   ├── common.py
│   │   ├── enrichment.py
│   │   └── product.py
│   ├── services/
│   │   ├── cache.py
│   │   ├── cloudru_client.py
│   │   ├── enricher.py
│   │   ├── llm_base.py
│   │   └── zhipu_client.py
│   └── main.py
├── tests/
├── config/ (НЕ СУЩЕСТВУЕТ)
├── pyproject.toml
└── README.md
```

### 2.2 Критические проблемы текущей архитектуры

**Проблема 1: Hardcoded системный промпт**
- Файл: `src/ai_product_enricher/services/zhipu_client.py`, метод `_build_system_prompt()`
- Строки 68-110: 40+ строк жёстко закодированного текста
- Невозможно изменить без деплоя

**Проблема 2: Фиксированные поля**
- Файл: `src/ai_product_enricher/models/enrichment.py`, класс `EnrichedProduct`
- 11 полей жёстко определены в Pydantic модели
- Добавление нового поля требует изменения кода

**Проблема 3: Отсутствие UI для тестирования**
- Нет возможности экспериментировать с промптами
- Нет A/B тестирования конфигураций
- Нет визуализации результатов

**Проблема 4: Дублирование логики**
- `zhipu_client.py` и `cloudru_client.py` содержат похожий код промптов
- Нет единого источника истины для конфигурации

---

## 3. Целевое состояние системы (TO-BE)

### 3.1 Новая структура проекта

```
ai_product_enricher/
├── config/                                    # ← НОВОЕ
│   ├── prompts/
│   │   ├── system/
│   │   │   ├── default.yaml
│   │   │   └── russian_products.yaml
│   │   ├── user/
│   │   │   └── default.yaml
│   │   └── templates/
│   │       └── base.jinja2
│   ├── fields/
│   │   ├── default.yaml
│   │   └── custom/
│   │       └── .gitkeep
│   └── profiles/
│       ├── default.yaml
│       └── custom/
│           └── .gitkeep
│
├── src/ai_product_enricher/
│   ├── engine/                                # ← НОВОЕ
│   │   ├── __init__.py
│   │   ├── field_registry.py
│   │   ├── prompt_engine.py
│   │   └── config_manager.py
│   │
│   ├── webui/                                 # ← НОВОЕ
│   │   ├── __init__.py
│   │   └── app.py
│   │
│   ├── api/                                   # Существующее
│   ├── core/                                  # Существующее
│   ├── models/                                # Модифицируется
│   ├── services/                              # Модифицируется
│   ├── main.py                                # Модифицируется
│   └── main_webui.py                          # ← НОВОЕ
│
└── tests/
    └── unit/
        ├── test_field_registry.py             # ← НОВОЕ
        ├── test_prompt_engine.py              # ← НОВОЕ
        └── test_config_manager.py             # ← НОВОЕ
```

### 3.2 Архитектурная диаграмма

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER INTERFACES                                 │
│  ┌─────────────────────────────┐    ┌─────────────────────────────────────┐ │
│  │     REST API (FastAPI)      │    │      Gradio WebUI (:7860)           │ │
│  │         :8000               │    │  - Test Sandbox                     │ │
│  │  - /api/v1/products/enrich  │    │  - Field Editor                     │ │
│  │  - /api/v1/health           │    │  - Prompt Editor                    │ │
│  └──────────────┬──────────────┘    │  - Profile Manager                  │ │
│                 │                    └──────────────┬──────────────────────┘ │
└─────────────────┼───────────────────────────────────┼───────────────────────┘
                  │                                   │
                  ▼                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ENGINE LAYER (NEW)                                 │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐  │
│  │    FieldRegistry    │  │    PromptEngine     │  │ ConfigurationManager│  │
│  │  - load YAML fields │  │  - render Jinja2    │  │  - manage profiles  │  │
│  │  - dynamic fields   │  │  - system/user      │  │  - save/load YAML   │  │
│  │  - validation       │  │  - field injection  │  │  - active profile   │  │
│  └─────────────────────┘  └─────────────────────┘  └─────────────────────┘  │
│                 │                   │                        │              │
│                 └───────────────────┼────────────────────────┘              │
│                                     ▼                                        │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                    YAML Configuration Files                          │   │
│  │   config/prompts/*.yaml  │  config/fields/*.yaml  │  config/profiles │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SERVICE LAYER (MODIFIED)                           │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                     ProductEnricherService                              ││
│  │   - uses PromptEngine for prompts                                       ││
│  │   - uses FieldRegistry for field definitions                            ││
│  │   - uses ConfigurationManager for profiles                              ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                 │                                   │                        │
│                 ▼                                   ▼                        │
│  ┌─────────────────────────┐          ┌─────────────────────────┐          │
│  │     ZhipuAIClient       │          │     CloudruClient       │          │
│  │   (receives rendered    │          │   (receives rendered    │          │
│  │    prompts from engine) │          │    prompts from engine) │          │
│  └─────────────────────────┘          └─────────────────────────┘          │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Детальные требования к компонентам

### 4.1 FieldRegistry

**Назначение:** Динамическое управление определениями полей для извлечения

**Функциональные требования:**
- FR-1.1: Загрузка определений полей из YAML файлов
- FR-1.2: Поддержка кастомных полей, добавляемых через UI
- FR-1.3: Валидация определений полей
- FR-1.4: Сохранение кастомных полей в отдельный файл
- FR-1.5: Поддержка типов: string, object, array
- FR-1.6: Поддержка примеров и подсказок для извлечения

**Структура данных FieldDefinition:**
```yaml
name: "manufacturer"
display_name: "Производитель"
description: |
  Компания, которая ФИЗИЧЕСКИ производит товар.
  Это НЕ всегда совпадает с брендом/торговой маркой.
type: "string"
required: false
examples:
  - input: "Apple iPhone 15 Pro"
    output: "Foxconn Technology Group"
extraction_hints:
  - "Ищи информацию о контрактном производителе"
  - "Если не найдено, используй торговую марку"
validation:
  max_length: 200
```

### 4.2 PromptEngine

**Назначение:** Рендеринг промптов из Jinja2 шаблонов с инъекцией полей

**Функциональные требования:**
- FR-2.1: Загрузка шаблонов из YAML файлов
- FR-2.2: Рендеринг с Jinja2
- FR-2.3: Автоматическая инъекция определений полей в промпт
- FR-2.4: Поддержка системных и пользовательских промптов
- FR-2.5: Сохранение новых/изменённых шаблонов
- FR-2.6: Предпросмотр с тестовыми данными

**Структура шаблона:**
```yaml
version: "1.0"
name: "default"
description: "Системный промпт по умолчанию"
template: |
  You are a professional product data analyst.
  Generate content in {{ language_name }} language.
  
  ## FIELDS TO EXTRACT
  {% for field in fields %}
  ### {{ field.display_name }} ({{ field.name }})
  {{ field.description }}
  {% if field.examples %}
  Examples:
  {% for ex in field.examples %}
  - "{{ ex.input }}" → "{{ ex.output }}"
  {% endfor %}
  {% endif %}
  {% endfor %}
  
  Respond with valid JSON only.
```

### 4.3 ConfigurationManager

**Назначение:** Управление профилями конфигурации

**Функциональные требования:**
- FR-3.1: Загрузка профилей из YAML
- FR-3.2: Создание новых профилей
- FR-3.3: Клонирование профилей
- FR-3.4: Удаление кастомных профилей
- FR-3.5: Переключение активного профиля
- FR-3.6: Защита default профиля от удаления

**Структура профиля:**
```yaml
version: "1.0"
name: "default"
description: "Стандартный профиль обогащения"
prompts:
  system: "default"
  user: "default"
fields:
  preset: "default"
  enabled:
    - manufacturer
    - trademark
    - category
    - description
    - features
    - specifications
llm:
  temperature: 0.3
  max_tokens: 4000
cache:
  enabled: true
  ttl_seconds: 3600
```

### 4.4 Gradio WebUI

**Назначение:** Веб-интерфейс для тестирования и настройки

**Функциональные требования:**
- FR-4.1: Вкладка "Тестирование" — sandbox для обогащения
- FR-4.2: Вкладка "Настройка полей" — CRUD для полей
- FR-4.3: Вкладка "Редактор промптов" — редактирование шаблонов
- FR-4.4: Вкладка "Профили" — управление профилями
- FR-4.5: Вкладка "Сравнение" — A/B тестирование
- FR-4.6: Предпросмотр сгенерированных промптов
- FR-4.7: Отображение metadata (токены, время, провайдер)

---

## 5. Нефункциональные требования

**NFR-1: Обратная совместимость**
- Существующий REST API должен работать без изменений
- Существующие тесты должны проходить

**NFR-2: Производительность**
- Загрузка конфигурации при старте < 1 секунды
- Рендеринг промпта < 10 мс

**NFR-3: Надёжность**
- При ошибке загрузки конфигурации — использовать fallback defaults
- Валидация YAML при загрузке

**NFR-4: Расширяемость**
- Легко добавлять новые типы полей
- Легко добавлять новые переменные в шаблоны

---

# ЧАСТЬ 2: ИНСТРУКЦИЯ ПО РЕАЛИЗАЦИИ

## 6. План выполнения по фазам

### ФАЗА 1: Создание конфигурационных файлов

**Шаг 1.1: Создать структуру директорий**

```bash
mkdir -p config/prompts/system
mkdir -p config/prompts/user
mkdir -p config/prompts/templates
mkdir -p config/fields/custom
mkdir -p config/profiles/custom
```

**Шаг 1.2: Создать config/fields/default.yaml**

```yaml
# config/fields/default.yaml
version: "1.0"
name: "default"
description: "Стандартный набор полей для обогащения продуктов"

fields:
  manufacturer:
    display_name: "Производитель"
    description: |
      Компания, которая ФИЗИЧЕСКИ производит товар.
      Это НЕ всегда совпадает с брендом/торговой маркой.
      Примеры: Foxconn производит iPhone, Pegatron производит MacBook.
      Для многих товаров производитель = торговая марка.
    type: "string"
    required: false
    examples:
      - input: "Apple iPhone 15 Pro"
        output: "Foxconn Technology Group"
      - input: "Samsung Galaxy S24"
        output: "Samsung Electronics"
    extraction_hints:
      - "Ищи информацию о контрактном производителе"
      - "Если не найдено, используй торговую марку"
    validation:
      max_length: 200

  trademark:
    display_name: "Торговая марка"
    description: |
      Бренд, под которым продаётся товар.
      Это коммерческое название, видимое потребителям.
      Примеры: Apple, Samsung, Sony, LG, Xiaomi.
    type: "string"
    required: false
    examples:
      - input: "Смартфон Apple iPhone 15 Pro Max"
        output: "Apple"
      - input: "Ноутбук ASUS ROG Strix"
        output: "ASUS"
    extraction_hints:
      - "Обычно указан в начале названия товара"
      - "Известные бренды: Apple, Samsung, Sony, LG, Xiaomi, Huawei, HP, Dell, Lenovo"
    validation:
      max_length: 100

  category:
    display_name: "Категория"
    description: "Категория товара в товарной номенклатуре"
    type: "string"
    required: false
    examples:
      - input: "iPhone 15 Pro"
        output: "Смартфоны"
      - input: "MacBook Pro 16"
        output: "Ноутбуки"
    extraction_hints:
      - "Определи тип товара по названию и описанию"
    validation:
      max_length: 100

  model_name:
    display_name: "Модель"
    description: "Конкретный идентификатор модели/артикул товара"
    type: "string"
    required: false
    examples:
      - input: "Смартфон Apple iPhone 15 Pro Max 256GB Black Titanium"
        output: "iPhone 15 Pro Max 256GB"
    extraction_hints:
      - "Извлеки модель без бренда и общего типа товара"
    validation:
      max_length: 200

  description:
    display_name: "Описание"
    description: "Подробное описание товара (2-4 предложения)"
    type: "string"
    required: false
    examples:
      - input: "iPhone 15 Pro"
        output: "Флагманский смартфон Apple с титановым корпусом и чипом A17 Pro. Оснащён продвинутой системой камер и дисплеем Super Retina XDR."
    extraction_hints:
      - "Напиши информативное описание для покупателя"
      - "Упомяни ключевые преимущества"
    validation:
      min_length: 50
      max_length: 1000

  features:
    display_name: "Характеристики"
    description: "Ключевые особенности и характеристики товара (список)"
    type: "array"
    required: false
    examples:
      - input: "iPhone 15 Pro"
        output:
          - "Титановый корпус"
          - "Чип A17 Pro"
          - "Камера 48 МП"
          - "Dynamic Island"
    extraction_hints:
      - "Выдели 5-10 ключевых особенностей"
      - "Используй короткие фразы"
    validation:
      max_items: 15

  specifications:
    display_name: "Технические характеристики"
    description: "Технические параметры в формате словаря"
    type: "object"
    required: false
    examples:
      - input: "iPhone 15 Pro 256GB"
        output:
          storage: "256GB"
          display: "6.1 inch Super Retina XDR"
          processor: "A17 Pro"
    extraction_hints:
      - "Извлеки технические параметры из названия и описания"
    validation: {}

  seo_keywords:
    display_name: "SEO ключевые слова"
    description: "Ключевые слова для поисковой оптимизации"
    type: "array"
    required: false
    examples:
      - input: "iPhone 15 Pro"
        output:
          - "iphone 15 pro купить"
          - "apple смартфон"
          - "айфон 15 про цена"
    extraction_hints:
      - "Сгенерируй релевантные поисковые запросы"
      - "Включи варианты написания"
    validation:
      max_items: 20

  marketing_copy:
    display_name: "Маркетинговый текст"
    description: "Промо-текст для рекламы (1-2 предложения)"
    type: "string"
    required: false
    examples:
      - input: "iPhone 15 Pro"
        output: "Откройте новую эру мобильных технологий с iPhone 15 Pro — мощь, элегантность и инновации в титановом корпусе."
    extraction_hints:
      - "Напиши привлекательный рекламный текст"
    validation:
      max_length: 300

  pros:
    display_name: "Преимущества"
    description: "Достоинства товара"
    type: "array"
    required: false
    examples:
      - input: "iPhone 15 Pro"
        output:
          - "Премиальные материалы"
          - "Мощный процессор"
          - "Отличная камера"
    extraction_hints:
      - "Укажи реальные преимущества товара"
    validation:
      max_items: 10

  cons:
    display_name: "Недостатки"
    description: "Недостатки товара"
    type: "array"
    required: false
    examples:
      - input: "iPhone 15 Pro"
        output:
          - "Высокая цена"
          - "Нет слота для карты памяти"
    extraction_hints:
      - "Укажи объективные недостатки"
    validation:
      max_items: 10
```

**Шаг 1.3: Создать config/prompts/system/default.yaml**

```yaml
# config/prompts/system/default.yaml
version: "1.0"
name: "default"
description: "Системный промпт по умолчанию для обогащения продуктов"

template: |
  You are a professional product data analyst and content specialist.
  Your task is to analyze product information from price lists or procurement documents and enrich it with structured data.
  
  ## LANGUAGE
  Generate all content in {{ language_name }} language.
  
  ## CRITICAL TASK - EXTRACT AND IDENTIFY
  The user provides only a product NAME (from price list/procurement) and optionally a free-form DESCRIPTION.
  You MUST extract/determine the following fields from this limited information.
  
  ## FIELDS TO EXTRACT
  You must extract the following fields:
  
  {% for field in fields %}
  ### {{ field.display_name }} ({{ field.name }})
  {{ field.description }}
  
  {% if field.examples %}
  Examples:
  {% for example in field.examples %}
  - Input: "{{ example.input }}" → Output: {{ example.output | tojson }}
  {% endfor %}
  {% endif %}
  
  {% if field.extraction_hints %}
  Extraction hints:
  {% for hint in field.extraction_hints %}
  - {{ hint }}
  {% endfor %}
  {% endif %}
  
  {% endfor %}
  
  ## OUTPUT FORMAT
  You must respond with a valid JSON object containing ONLY the requested fields.
  Do not include markdown code blocks or any other formatting.
  Do not include explanations outside the JSON.
  
  {% if additional_instructions %}
  ## ADDITIONAL INSTRUCTIONS
  {{ additional_instructions }}
  {% endif %}

variables:
  - name: "language_name"
    description: "Язык для генерации контента"
    default: "Russian"
  - name: "fields"
    description: "Список полей для извлечения"
    type: "list"
  - name: "additional_instructions"
    description: "Дополнительные инструкции"
    default: ""
```

**Шаг 1.4: Создать config/prompts/system/russian_products.yaml**

```yaml
# config/prompts/system/russian_products.yaml
version: "1.0"
name: "russian_products"
description: "Системный промпт для российских товаров (Cloud.ru)"

template: |
  Ты профессиональный аналитик продуктовых данных и специалист по контенту.
  Твоя задача — анализировать информацию о товарах из прайс-листов и закупочных документов и обогащать её структурированными данными.
  
  ## ЯЗЫК
  Генерируй весь контент на русском языке.
  
  ## КРИТИЧЕСКАЯ ЗАДАЧА — ИЗВЛЕЧЕНИЕ И ИДЕНТИФИКАЦИЯ
  Пользователь предоставляет только НАЗВАНИЕ товара (из прайс-листа/закупки) и опционально ОПИСАНИЕ.
  Ты ДОЛЖЕН извлечь/определить следующие поля из этой ограниченной информации.
  
  ## ПОЛЯ ДЛЯ ИЗВЛЕЧЕНИЯ
  Ты должен извлечь следующие поля:
  
  {% for field in fields %}
  ### {{ field.display_name }} ({{ field.name }})
  {{ field.description }}
  
  {% if field.examples %}
  Примеры:
  {% for example in field.examples %}
  - Вход: "{{ example.input }}" → Выход: {{ example.output | tojson }}
  {% endfor %}
  {% endif %}
  
  {% if field.extraction_hints %}
  Подсказки для извлечения:
  {% for hint in field.extraction_hints %}
  - {{ hint }}
  {% endfor %}
  {% endif %}
  
  {% endfor %}
  
  ## ФОРМАТ ВЫВОДА
  Ты должен ответить валидным JSON-объектом, содержащим ТОЛЬКО запрошенные поля.
  Не включай блоки кода markdown или другое форматирование.
  Не включай пояснения вне JSON.

variables:
  - name: "fields"
    description: "Список полей для извлечения"
    type: "list"
```

**Шаг 1.5: Создать config/prompts/user/default.yaml**

```yaml
# config/prompts/user/default.yaml
version: "1.0"
name: "default"
description: "Пользовательский промпт по умолчанию"

template: |
  Analyze and enrich the following product from a price list/procurement document:
  
  {{ product_context }}
  
  {% if context_data %}
  Additional context provided by user:
  {% for key, value in context_data.items() %}
  {{ key }}: {{ value }}
  {% endfor %}
  {% endif %}
  
  REQUIRED TASKS:
  1. Extract/determine the MANUFACTURER (who physically makes this product)
  2. Extract/determine the TRADEMARK (brand name)
  3. Determine the product CATEGORY
  4. Extract the MODEL NAME/NUMBER
  5. Generate other requested fields
  
  Generate the following fields: {{ fields_list }}
  
  Respond with a valid JSON object only. No markdown, no explanations.

variables:
  - name: "product_context"
    description: "Контекст продукта (название, описание)"
  - name: "context_data"
    description: "Дополнительные данные от пользователя"
    type: "dict"
  - name: "fields_list"
    description: "Список полей через запятую"
```

**Шаг 1.6: Создать config/profiles/default.yaml**

```yaml
# config/profiles/default.yaml
version: "1.0"
name: "default"
description: "Стандартный профиль обогащения продуктов"

prompts:
  system: "default"
  user: "default"

fields:
  preset: "default"
  enabled:
    - manufacturer
    - trademark
    - category
    - model_name
    - description
    - features
    - specifications
    - seo_keywords
  custom: []

llm:
  temperature: 0.3
  max_tokens: 4000
  top_p: 0.95

cache:
  enabled: true
  ttl_seconds: 3600

extraction_rules: "default"
```

**Шаг 1.7: Создать .gitkeep файлы**

```bash
touch config/fields/custom/.gitkeep
touch config/profiles/custom/.gitkeep
```

---

### ФАЗА 2: Создание Engine Layer

**Шаг 2.1: Создать src/ai_product_enricher/engine/__init__.py**

```python
"""Configuration engine for AI Product Enricher."""

from .field_registry import FieldDefinition, FieldExample, FieldRegistry, FieldSet
from .prompt_engine import PromptEngine, PromptTemplate
from .config_manager import (
    CacheConfig,
    ConfigurationManager,
    EnrichmentProfile,
    FieldsConfig,
    LLMConfig,
    PromptsConfig,
)

__all__ = [
    # Field Registry
    "FieldRegistry",
    "FieldSet",
    "FieldDefinition",
    "FieldExample",
    # Prompt Engine
    "PromptEngine",
    "PromptTemplate",
    # Config Manager
    "ConfigurationManager",
    "EnrichmentProfile",
    "PromptsConfig",
    "FieldsConfig",
    "LLMConfig",
    "CacheConfig",
]
```

**Шаг 2.2: Создать src/ai_product_enricher/engine/field_registry.py**

```python
"""Dynamic field management for product enrichment."""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from ..core import get_logger

logger = get_logger(__name__)


class FieldExample(BaseModel):
    """Example for field extraction."""

    input: str
    output: str | list[str] | dict[str, Any]


class FieldDefinition(BaseModel):
    """Definition of an enrichment field."""

    name: str = ""
    display_name: str
    description: str
    type: str = "string"  # string, object, array
    required: bool = False
    examples: list[FieldExample] = Field(default_factory=list)
    extraction_hints: list[str] = Field(default_factory=list)
    allowed_values: list[str] | None = None
    validation: dict[str, Any] = Field(default_factory=dict)
    schema: dict[str, Any] | None = None  # For object/array types


class FieldSet(BaseModel):
    """A set of field definitions."""

    version: str = "1.0"
    name: str
    description: str = ""
    fields: dict[str, FieldDefinition] = Field(default_factory=dict)


class FieldRegistry:
    """Registry for managing dynamic field definitions.
    
    Loads field definitions from YAML files and provides methods
    to access and manage them dynamically.
    """

    def __init__(self, config_dir: Path | str = "config/fields"):
        """Initialize the field registry.
        
        Args:
            config_dir: Directory containing field definition YAML files
        """
        self.config_dir = Path(config_dir)
        self._field_sets: dict[str, FieldSet] = {}
        self._custom_fields: dict[str, FieldDefinition] = {}
        self._load_field_sets()

    def _load_field_sets(self) -> None:
        """Load all field set definitions from config directory."""
        if not self.config_dir.exists():
            logger.warning(
                "field_config_dir_not_found",
                config_dir=str(self.config_dir),
            )
            self._create_default_field_set()
            return

        # Load main field sets
        for yaml_file in self.config_dir.glob("*.yaml"):
            self._load_field_set_file(yaml_file)

        # Load custom field sets
        custom_dir = self.config_dir / "custom"
        if custom_dir.exists():
            for yaml_file in custom_dir.glob("*.yaml"):
                self._load_field_set_file(yaml_file)

        # Ensure default exists
        if "default" not in self._field_sets:
            self._create_default_field_set()

        logger.info(
            "field_sets_loaded",
            count=len(self._field_sets),
            names=list(self._field_sets.keys()),
        )

    def _load_field_set_file(self, yaml_file: Path) -> None:
        """Load a single field set from a YAML file."""
        try:
            with open(yaml_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not data:
                return

            # Convert fields dict to FieldDefinition objects
            fields = {}
            for name, field_data in data.get("fields", {}).items():
                if name == "custom_fields":
                    continue
                if isinstance(field_data, dict):
                    field_data["name"] = name
                    try:
                        fields[name] = FieldDefinition(**field_data)
                    except Exception as e:
                        logger.warning(
                            "field_definition_error",
                            field=name,
                            error=str(e),
                        )

            field_set = FieldSet(
                version=data.get("version", "1.0"),
                name=data.get("name", yaml_file.stem),
                description=data.get("description", ""),
                fields=fields,
            )
            self._field_sets[field_set.name] = field_set

            logger.debug(
                "field_set_loaded",
                name=field_set.name,
                fields_count=len(fields),
            )

        except Exception as e:
            logger.error(
                "field_set_load_error",
                file=str(yaml_file),
                error=str(e),
            )

    def _create_default_field_set(self) -> None:
        """Create a default field set with basic fields."""
        default_fields = {
            "manufacturer": FieldDefinition(
                name="manufacturer",
                display_name="Производитель",
                description="Компания, которая физически производит товар",
                type="string",
            ),
            "trademark": FieldDefinition(
                name="trademark",
                display_name="Торговая марка",
                description="Бренд, под которым продаётся товар",
                type="string",
            ),
            "category": FieldDefinition(
                name="category",
                display_name="Категория",
                description="Категория товара",
                type="string",
            ),
            "model_name": FieldDefinition(
                name="model_name",
                display_name="Модель",
                description="Идентификатор модели",
                type="string",
            ),
            "description": FieldDefinition(
                name="description",
                display_name="Описание",
                description="Подробное описание товара",
                type="string",
            ),
            "features": FieldDefinition(
                name="features",
                display_name="Характеристики",
                description="Ключевые особенности товара",
                type="array",
            ),
            "specifications": FieldDefinition(
                name="specifications",
                display_name="Технические характеристики",
                description="Технические параметры",
                type="object",
            ),
            "seo_keywords": FieldDefinition(
                name="seo_keywords",
                display_name="SEO ключевые слова",
                description="Ключевые слова для поиска",
                type="array",
            ),
        }

        self._field_sets["default"] = FieldSet(
            name="default",
            description="Default field set",
            fields=default_fields,
        )

    def get_field_set(self, name: str = "default") -> FieldSet | None:
        """Get a field set by name.
        
        Args:
            name: Name of the field set
            
        Returns:
            FieldSet or None if not found
        """
        return self._field_sets.get(name)

    def get_field(
        self, field_name: str, set_name: str = "default"
    ) -> FieldDefinition | None:
        """Get a specific field definition.
        
        Args:
            field_name: Name of the field
            set_name: Name of the field set
            
        Returns:
            FieldDefinition or None if not found
        """
        # Check custom fields first
        if field_name in self._custom_fields:
            return self._custom_fields[field_name]

        # Then check field sets
        field_set = self._field_sets.get(set_name)
        if field_set:
            return field_set.fields.get(field_name)

        return None

    def add_custom_field(self, field: FieldDefinition) -> None:
        """Add a custom field definition.
        
        Args:
            field: Field definition to add
        """
        self._custom_fields[field.name] = field
        logger.info("custom_field_added", field_name=field.name)

    def remove_custom_field(self, name: str) -> bool:
        """Remove a custom field.
        
        Args:
            name: Name of the field to remove
            
        Returns:
            True if removed, False if not found
        """
        if name in self._custom_fields:
            del self._custom_fields[name]
            logger.info("custom_field_removed", field_name=name)
            return True
        return False

    def get_fields_for_extraction(
        self,
        field_names: list[str],
        set_name: str = "default",
    ) -> list[FieldDefinition]:
        """Get field definitions for specified field names.
        
        Args:
            field_names: List of field names to get
            set_name: Name of the field set to use
            
        Returns:
            List of FieldDefinition objects
        """
        field_set = self._field_sets.get(set_name)
        result = []

        for name in field_names:
            # Check custom fields first
            if name in self._custom_fields:
                result.append(self._custom_fields[name])
            # Then check field set
            elif field_set and name in field_set.fields:
                result.append(field_set.fields[name])

        return result

    def list_available_fields(self, set_name: str = "default") -> list[str]:
        """List all available field names.
        
        Args:
            set_name: Name of the field set
            
        Returns:
            List of field names
        """
        fields = set(self._custom_fields.keys())
        field_set = self._field_sets.get(set_name)
        if field_set:
            fields.update(field_set.fields.keys())
        return sorted(list(fields))

    def list_field_sets(self) -> list[str]:
        """List all available field set names."""
        return list(self._field_sets.keys())

    def save_custom_fields(self, filepath: Path | str | None = None) -> None:
        """Save custom fields to a YAML file.
        
        Args:
            filepath: Path to save to (default: config/fields/custom/user_defined.yaml)
        """
        if filepath is None:
            filepath = self.config_dir / "custom" / "user_defined.yaml"
        else:
            filepath = Path(filepath)

        filepath.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "version": "1.0",
            "name": "custom",
            "description": "User-defined custom fields",
            "fields": {
                name: field.model_dump(exclude_none=True)
                for name, field in self._custom_fields.items()
            },
        }

        with open(filepath, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False)

        logger.info(
            "custom_fields_saved",
            filepath=str(filepath),
            count=len(self._custom_fields),
        )

    def load_custom_fields(self, filepath: Path | str) -> None:
        """Load custom fields from a YAML file.
        
        Args:
            filepath: Path to load from
        """
        filepath = Path(filepath)
        if not filepath.exists():
            return

        with open(filepath, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not data:
            return

        for name, field_data in data.get("fields", {}).items():
            field_data["name"] = name
            try:
                self._custom_fields[name] = FieldDefinition(**field_data)
            except Exception as e:
                logger.warning(
                    "custom_field_load_error",
                    field=name,
                    error=str(e),
                )

        logger.info(
            "custom_fields_loaded",
            filepath=str(filepath),
            count=len(self._custom_fields),
        )
```

**Шаг 2.3: Создать src/ai_product_enricher/engine/prompt_engine.py**

```python
"""Prompt template engine with Jinja2 support."""

from pathlib import Path
from typing import Any

import yaml
from jinja2 import Environment, BaseLoader, TemplateError
from pydantic import BaseModel, Field

from ..core import get_logger
from .field_registry import FieldDefinition, FieldRegistry

logger = get_logger(__name__)


class PromptVariable(BaseModel):
    """Definition of a template variable."""

    name: str
    description: str = ""
    type: str = "string"
    default: Any = None


class PromptTemplate(BaseModel):
    """A prompt template definition."""

    version: str = "1.0"
    name: str
    description: str = ""
    template: str
    variables: list[PromptVariable] = Field(default_factory=list)


class PromptEngine:
    """Engine for rendering prompt templates.
    
    Loads Jinja2-based prompt templates from YAML files and renders them
    with field definitions and other context variables.
    """

    LANGUAGE_NAMES = {
        "ru": "Russian",
        "en": "English",
        "zh": "Chinese",
        "es": "Spanish",
        "de": "German",
        "fr": "French",
        "ja": "Japanese",
        "ko": "Korean",
    }

    def __init__(
        self,
        prompts_dir: Path | str = "config/prompts",
        field_registry: FieldRegistry | None = None,
    ):
        """Initialize the prompt engine.
        
        Args:
            prompts_dir: Directory containing prompt templates
            field_registry: Field registry for field definitions
        """
        self.prompts_dir = Path(prompts_dir)
        self.field_registry = field_registry or FieldRegistry()
        self._templates: dict[str, dict[str, PromptTemplate]] = {
            "system": {},
            "user": {},
        }
        self._jinja_env = Environment(
            loader=BaseLoader(),
            trim_blocks=True,
            lstrip_blocks=True,
            autoescape=False,
        )
        # Add custom filters
        self._jinja_env.filters["tojson"] = lambda x: yaml.dump(
            x, default_flow_style=True, allow_unicode=True
        ).strip()
        
        self._load_templates()

    def _load_templates(self) -> None:
        """Load all prompt templates from config directory."""
        for prompt_type in ["system", "user"]:
            type_dir = self.prompts_dir / prompt_type
            if not type_dir.exists():
                logger.warning(
                    "prompt_dir_not_found",
                    prompt_type=prompt_type,
                    dir=str(type_dir),
                )
                continue

            for yaml_file in type_dir.glob("*.yaml"):
                self._load_template_file(prompt_type, yaml_file)

        # Ensure defaults exist
        self._ensure_default_templates()

        logger.info(
            "prompt_templates_loaded",
            system_count=len(self._templates["system"]),
            user_count=len(self._templates["user"]),
        )

    def _load_template_file(self, prompt_type: str, yaml_file: Path) -> None:
        """Load a single template from a YAML file."""
        try:
            with open(yaml_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not data:
                return

            # Parse variables
            variables = []
            for var_data in data.get("variables", []):
                if isinstance(var_data, dict):
                    variables.append(PromptVariable(**var_data))

            template = PromptTemplate(
                version=data.get("version", "1.0"),
                name=data.get("name", yaml_file.stem),
                description=data.get("description", ""),
                template=data.get("template", ""),
                variables=variables,
            )
            self._templates[prompt_type][template.name] = template

            logger.debug(
                "prompt_template_loaded",
                type=prompt_type,
                name=template.name,
            )

        except Exception as e:
            logger.error(
                "prompt_template_load_error",
                file=str(yaml_file),
                error=str(e),
            )

    def _ensure_default_templates(self) -> None:
        """Ensure default templates exist."""
        if "default" not in self._templates["system"]:
            self._templates["system"]["default"] = PromptTemplate(
                name="default",
                description="Default system prompt",
                template=self._get_fallback_system_template(),
            )

        if "default" not in self._templates["user"]:
            self._templates["user"]["default"] = PromptTemplate(
                name="default",
                description="Default user prompt",
                template=self._get_fallback_user_template(),
            )

    def _get_fallback_system_template(self) -> str:
        """Return fallback system template."""
        return """You are a professional product data analyst.
Your task is to analyze product information and extract structured data.

Generate all content in {{ language_name }} language.

## FIELDS TO EXTRACT
{% for field in fields %}
### {{ field.display_name }} ({{ field.name }})
{{ field.description }}
{% endfor %}

Respond with a valid JSON object containing ONLY the requested fields.
Do not include markdown code blocks."""

    def _get_fallback_user_template(self) -> str:
        """Return fallback user template."""
        return """Analyze and enrich the following product:

{{ product_context }}

Generate the following fields: {{ fields_list }}

Respond with a valid JSON object only."""

    def render_system_prompt(
        self,
        template_name: str = "default",
        language: str = "ru",
        field_names: list[str] | None = None,
        field_set: str = "default",
        additional_instructions: str = "",
        **extra_vars: Any,
    ) -> str:
        """Render a system prompt template.
        
        Args:
            template_name: Name of the template to use
            language: Language code for content generation
            field_names: List of field names to include
            field_set: Name of the field set to use
            additional_instructions: Extra instructions to append
            **extra_vars: Additional template variables
            
        Returns:
            Rendered prompt string
        """
        template = self._templates["system"].get(template_name)
        if not template:
            logger.warning(
                "system_template_not_found",
                template_name=template_name,
            )
            template = self._templates["system"]["default"]

        # Get field definitions
        if field_names is None:
            field_names = self.field_registry.list_available_fields(field_set)

        fields = self.field_registry.get_fields_for_extraction(field_names, field_set)

        # Prepare context
        context = {
            "language_name": self.LANGUAGE_NAMES.get(language, language),
            "language": language,
            "fields": [f.model_dump() for f in fields],
            "additional_instructions": additional_instructions,
            **extra_vars,
        }

        return self._render_template(template.template, context)

    def render_user_prompt(
        self,
        template_name: str = "default",
        product_name: str = "",
        product_description: str | None = None,
        field_names: list[str] | None = None,
        context_data: dict[str, Any] | None = None,
        **extra_vars: Any,
    ) -> str:
        """Render a user prompt template.
        
        Args:
            template_name: Name of the template to use
            product_name: Name of the product
            product_description: Optional description
            field_names: List of field names requested
            context_data: Additional context data
            **extra_vars: Additional template variables
            
        Returns:
            Rendered prompt string
        """
        template = self._templates["user"].get(template_name)
        if not template:
            logger.warning(
                "user_template_not_found",
                template_name=template_name,
            )
            template = self._templates["user"]["default"]

        # Build product context
        product_context_lines = [f"Product Name: {product_name}"]
        if product_description:
            product_context_lines.append(f"Description: {product_description}")

        context = {
            "product_name": product_name,
            "product_description": product_description or "",
            "product_context": "\n".join(product_context_lines),
            "field_names": field_names or [],
            "fields_list": ", ".join(field_names) if field_names else "all available",
            "context_data": context_data or {},
            **extra_vars,
        }

        return self._render_template(template.template, context)

    def _render_template(self, template_str: str, context: dict[str, Any]) -> str:
        """Render a Jinja2 template string.
        
        Args:
            template_str: Template string
            context: Context variables
            
        Returns:
            Rendered string
        """
        try:
            jinja_template = self._jinja_env.from_string(template_str)
            return jinja_template.render(**context)
        except TemplateError as e:
            logger.error("template_render_error", error=str(e))
            raise

    def get_available_templates(self, prompt_type: str = "system") -> list[str]:
        """List available template names.
        
        Args:
            prompt_type: "system" or "user"
            
        Returns:
            List of template names
        """
        return list(self._templates.get(prompt_type, {}).keys())

    def get_template(
        self, prompt_type: str, name: str
    ) -> PromptTemplate | None:
        """Get a specific template.
        
        Args:
            prompt_type: "system" or "user"
            name: Template name
            
        Returns:
            PromptTemplate or None
        """
        return self._templates.get(prompt_type, {}).get(name)

    def save_template(
        self,
        prompt_type: str,
        name: str,
        template: str,
        description: str = "",
    ) -> None:
        """Save a new or updated template.
        
        Args:
            prompt_type: "system" or "user"
            name: Template name
            template: Template content
            description: Template description
        """
        template_obj = PromptTemplate(
            version="1.0",
            name=name,
            description=description,
            template=template,
        )

        # Save to file
        filepath = self.prompts_dir / prompt_type / f"{name}.yaml"
        filepath.parent.mkdir(parents=True, exist_ok=True)

        data = template_obj.model_dump()
        with open(filepath, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False)

        # Update cache
        self._templates[prompt_type][name] = template_obj

        logger.info(
            "prompt_template_saved",
            type=prompt_type,
            name=name,
            filepath=str(filepath),
        )

    def preview_template(
        self,
        prompt_type: str,
        template_content: str,
        language: str = "ru",
    ) -> str:
        """Preview a template with test data.
        
        Args:
            prompt_type: "system" or "user"
            template_content: Template content to preview
            language: Language for preview
            
        Returns:
            Rendered preview string
        """
        # Test data
        test_fields = [
            {
                "name": "manufacturer",
                "display_name": "Производитель",
                "description": "Компания-производитель",
                "examples": [{"input": "iPhone", "output": "Foxconn"}],
                "extraction_hints": ["Ищи контрактного производителя"],
            },
            {
                "name": "trademark",
                "display_name": "Торговая марка",
                "description": "Бренд товара",
                "examples": [{"input": "iPhone", "output": "Apple"}],
                "extraction_hints": [],
            },
        ]

        if prompt_type == "system":
            context = {
                "language_name": self.LANGUAGE_NAMES.get(language, language),
                "language": language,
                "fields": test_fields,
                "additional_instructions": "",
            }
        else:
            context = {
                "product_name": "Тестовый товар iPhone 15 Pro",
                "product_description": "Описание товара",
                "product_context": "Product Name: Тестовый товар iPhone 15 Pro",
                "field_names": ["manufacturer", "trademark"],
                "fields_list": "manufacturer, trademark",
                "context_data": {},
            }

        return self._render_template(template_content, context)
```

**Шаг 2.4: Создать src/ai_product_enricher/engine/config_manager.py**

```python
"""Configuration management for enrichment profiles."""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from ..core import get_logger

logger = get_logger(__name__)


class LLMConfig(BaseModel):
    """LLM-specific configuration."""

    temperature: float = 0.3
    max_tokens: int = 4000
    top_p: float = 0.95


class CacheConfig(BaseModel):
    """Cache configuration."""

    enabled: bool = True
    ttl_seconds: int = 3600


class PromptsConfig(BaseModel):
    """Prompts configuration."""

    system: str = "default"
    user: str = "default"


class FieldsConfig(BaseModel):
    """Fields configuration."""

    preset: str = "default"
    enabled: list[str] = Field(default_factory=lambda: [
        "manufacturer",
        "trademark",
        "category",
        "model_name",
        "description",
        "features",
        "specifications",
        "seo_keywords",
    ])
    custom: list[dict[str, Any]] = Field(default_factory=list)


class EnrichmentProfile(BaseModel):
    """Complete enrichment profile."""

    version: str = "1.0"
    name: str
    description: str = ""
    prompts: PromptsConfig = Field(default_factory=PromptsConfig)
    fields: FieldsConfig = Field(default_factory=FieldsConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)
    extraction_rules: str = "default"


class ConfigurationManager:
    """Manager for enrichment configuration profiles.
    
    Handles loading, saving, and switching between different
    enrichment configuration profiles.
    """

    def __init__(self, config_dir: Path | str = "config"):
        """Initialize the configuration manager.
        
        Args:
            config_dir: Root configuration directory
        """
        self.config_dir = Path(config_dir)
        self._profiles: dict[str, EnrichmentProfile] = {}
        self._active_profile: str = "default"
        self._load_profiles()

    def _load_profiles(self) -> None:
        """Load all profiles from config directory."""
        profiles_dir = self.config_dir / "profiles"

        # Always create default profile first
        self._profiles["default"] = self._create_default_profile()

        if not profiles_dir.exists():
            logger.warning(
                "profiles_dir_not_found",
                dir=str(profiles_dir),
            )
            return

        # Load main profiles
        for yaml_file in profiles_dir.glob("*.yaml"):
            self._load_profile_file(yaml_file)

        # Load custom profiles
        custom_dir = profiles_dir / "custom"
        if custom_dir.exists():
            for yaml_file in custom_dir.glob("*.yaml"):
                self._load_profile_file(yaml_file)

        logger.info(
            "profiles_loaded",
            count=len(self._profiles),
            names=list(self._profiles.keys()),
        )

    def _load_profile_file(self, yaml_file: Path) -> None:
        """Load a single profile from a YAML file."""
        try:
            with open(yaml_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not data:
                return

            # Parse nested configs
            prompts_data = data.get("prompts", {})
            fields_data = data.get("fields", {})
            llm_data = data.get("llm", {})
            cache_data = data.get("cache", {})

            profile = EnrichmentProfile(
                version=data.get("version", "1.0"),
                name=data.get("name", yaml_file.stem),
                description=data.get("description", ""),
                prompts=PromptsConfig(**prompts_data) if prompts_data else PromptsConfig(),
                fields=FieldsConfig(**fields_data) if fields_data else FieldsConfig(),
                llm=LLMConfig(**llm_data) if llm_data else LLMConfig(),
                cache=CacheConfig(**cache_data) if cache_data else CacheConfig(),
                extraction_rules=data.get("extraction_rules", "default"),
            )
            self._profiles[profile.name] = profile

            logger.debug(
                "profile_loaded",
                name=profile.name,
                file=str(yaml_file),
            )

        except Exception as e:
            logger.error(
                "profile_load_error",
                file=str(yaml_file),
                error=str(e),
            )

    def _create_default_profile(self) -> EnrichmentProfile:
        """Create a default profile."""
        return EnrichmentProfile(
            name="default",
            description="Default enrichment profile",
        )

    def get_profile(self, name: str | None = None) -> EnrichmentProfile:
        """Get a profile by name or the active profile.
        
        Args:
            name: Profile name (None for active profile)
            
        Returns:
            EnrichmentProfile
            
        Raises:
            ValueError: If profile not found
        """
        profile_name = name or self._active_profile
        profile = self._profiles.get(profile_name)
        if not profile:
            raise ValueError(f"Profile '{profile_name}' not found")
        return profile

    def get_active_profile(self) -> EnrichmentProfile:
        """Get the currently active profile."""
        return self.get_profile(self._active_profile)

    def set_active_profile(self, name: str) -> None:
        """Set the active profile.
        
        Args:
            name: Profile name
            
        Raises:
            ValueError: If profile not found
        """
        if name not in self._profiles:
            raise ValueError(f"Profile '{name}' not found")
        self._active_profile = name
        logger.info("active_profile_changed", profile=name)

    def list_profiles(self) -> list[str]:
        """List all available profile names."""
        return list(self._profiles.keys())

    def save_profile(
        self,
        profile: EnrichmentProfile,
        custom: bool = True,
    ) -> None:
        """Save a profile to disk.
        
        Args:
            profile: Profile to save
            custom: Whether to save in custom directory
        """
        if custom:
            filepath = self.config_dir / "profiles" / "custom" / f"{profile.name}.yaml"
        else:
            filepath = self.config_dir / "profiles" / f"{profile.name}.yaml"

        filepath.parent.mkdir(parents=True, exist_ok=True)

        data = profile.model_dump()
        with open(filepath, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False)

        self._profiles[profile.name] = profile

        logger.info(
            "profile_saved",
            name=profile.name,
            filepath=str(filepath),
        )

    def delete_profile(self, name: str) -> bool:
        """Delete a custom profile.
        
        Args:
            name: Profile name
            
        Returns:
            True if deleted
            
        Raises:
            ValueError: If trying to delete default profile
        """
        if name == "default":
            raise ValueError("Cannot delete default profile")

        # Try to delete file
        filepath = self.config_dir / "profiles" / "custom" / f"{name}.yaml"
        if filepath.exists():
            filepath.unlink()

        # Also try main profiles dir
        filepath = self.config_dir / "profiles" / f"{name}.yaml"
        if filepath.exists():
            filepath.unlink()

        if name in self._profiles:
            del self._profiles[name]
            logger.info("profile_deleted", name=name)
            return True

        return False

    def create_profile_from_current(
        self,
        name: str,
        description: str = "",
    ) -> EnrichmentProfile:
        """Create a new profile based on the active profile.
        
        Args:
            name: New profile name
            description: Profile description
            
        Returns:
            New EnrichmentProfile
        """
        current = self.get_active_profile()
        new_profile = EnrichmentProfile(
            name=name,
            description=description,
            prompts=current.prompts.model_copy(),
            fields=current.fields.model_copy(),
            llm=current.llm.model_copy(),
            cache=current.cache.model_copy(),
            extraction_rules=current.extraction_rules,
        )
        self.save_profile(new_profile)
        return new_profile

    def update_profile(
        self,
        name: str,
        **updates: Any,
    ) -> EnrichmentProfile:
        """Update an existing profile.
        
        Args:
            name: Profile name
            **updates: Fields to update
            
        Returns:
            Updated profile
        """
        profile = self.get_profile(name)
        profile_dict = profile.model_dump()

        for key, value in updates.items():
            if key in profile_dict:
                if isinstance(value, dict) and isinstance(profile_dict[key], dict):
                    profile_dict[key].update(value)
                else:
                    profile_dict[key] = value

        updated_profile = EnrichmentProfile(**profile_dict)
        self.save_profile(updated_profile, custom=(name != "default"))
        return updated_profile
```

---

### ФАЗА 3: Создание WebUI

**Шаг 3.1: Создать src/ai_product_enricher/webui/__init__.py**

```python
"""Gradio WebUI for AI Product Enricher."""

from .app import EnricherWebUI, create_app

__all__ = ["EnricherWebUI", "create_app"]
```

**Шаг 3.2: Создать src/ai_product_enricher/webui/app.py**

```python
"""Gradio WebUI for AI Product Enricher configuration and testing."""

import asyncio
from typing import Any

import gradio as gr

from ..core import get_logger
from ..engine import (
    ConfigurationManager,
    EnrichmentProfile,
    FieldDefinition,
    FieldExample,
    FieldRegistry,
    FieldsConfig,
    LLMConfig,
    CacheConfig,
    PromptsConfig,
    PromptEngine,
)

logger = get_logger(__name__)


class EnricherWebUI:
    """Gradio-based WebUI for Product Enricher configuration and testing."""

    def __init__(
        self,
        field_registry: FieldRegistry | None = None,
        prompt_engine: PromptEngine | None = None,
        config_manager: ConfigurationManager | None = None,
        enricher_service: Any = None,
    ):
        """Initialize the WebUI.
        
        Args:
            field_registry: Field registry instance
            prompt_engine: Prompt engine instance
            config_manager: Configuration manager instance
            enricher_service: Optional enricher service for actual enrichment
        """
        self.field_registry = field_registry or FieldRegistry()
        self.prompt_engine = prompt_engine or PromptEngine(
            field_registry=self.field_registry
        )
        self.config_manager = config_manager or ConfigurationManager()
        self.enricher_service = enricher_service

        self.app = self._build_ui()

    def _build_ui(self) -> gr.Blocks:
        """Build the Gradio interface."""
        with gr.Blocks(
            title="AI Product Enricher - Configuration & Testing",
            theme=gr.themes.Soft(),
            css="""
            .container { max-width: 1400px; margin: auto; }
            .output-json { max-height: 400px; overflow-y: auto; }
            """
        ) as app:
            gr.Markdown(
                "# 🛠️ AI Product Enricher - Configuration & Testing\n"
                "Настройка полей, промптов и тестирование обогащения продуктов"
            )

            with gr.Tabs():
                with gr.Tab("🧪 Тестирование", id="testing"):
                    self._build_test_tab()

                with gr.Tab("📋 Настройка полей", id="fields"):
                    self._build_fields_tab()

                with gr.Tab("✍️ Редактор промптов", id="prompts"):
                    self._build_prompts_tab()

                with gr.Tab("⚙️ Профили", id="profiles"):
                    self._build_profiles_tab()

        return app

    def _build_test_tab(self) -> None:
        """Build the testing sandbox tab."""
        with gr.Row():
            # Left column - Input
            with gr.Column(scale=1):
                gr.Markdown("### 📥 Входные данные")

                profile_dropdown = gr.Dropdown(
                    label="Профиль конфигурации",
                    choices=self.config_manager.list_profiles(),
                    value="default",
                    interactive=True,
                )

                product_name = gr.Textbox(
                    label="Название товара *",
                    placeholder="Смартфон Apple iPhone 15 Pro Max 256GB Black Titanium",
                    lines=2,
                )

                product_description = gr.Textbox(
                    label="Описание (опционально)",
                    placeholder="Дополнительное описание товара из прайс-листа...",
                    lines=3,
                )

                country_origin = gr.Dropdown(
                    label="Страна происхождения",
                    choices=["", "RU", "CN", "US", "KR", "JP", "DE", "TW"],
                    value="",
                    info="RU → Cloud.ru, остальные → Z.ai",
                )

                gr.Markdown("#### 🏷️ Дополнительный контекст")

                with gr.Row():
                    ctx_field_name = gr.Textbox(
                        label="Имя поля",
                        placeholder="brand_code",
                        scale=1,
                    )
                    ctx_field_value = gr.Textbox(
                        label="Значение",
                        placeholder="ABC123",
                        scale=2,
                    )
                    add_ctx_btn = gr.Button("➕", scale=0, min_width=50)

                context_state = gr.State({})
                context_display = gr.JSON(
                    label="Добавленный контекст",
                    value={},
                )

                gr.Markdown("#### 📑 Поля для извлечения")

                field_checkboxes = gr.CheckboxGroup(
                    label="Выберите поля",
                    choices=self.field_registry.list_available_fields(),
                    value=["manufacturer", "trademark", "category", "description", "features"],
                )

                with gr.Row():
                    language = gr.Radio(
                        label="Язык",
                        choices=["ru", "en", "zh"],
                        value="ru",
                        scale=1,
                    )
                    web_search = gr.Checkbox(
                        label="Web Search",
                        value=True,
                        scale=0,
                    )

                enrich_btn = gr.Button(
                    "🚀 Обогатить",
                    variant="primary",
                    size="lg",
                )

            # Right column - Output
            with gr.Column(scale=1):
                gr.Markdown("### 📤 Результат")

                result_json = gr.JSON(
                    label="Результат обогащения",
                    elem_classes=["output-json"],
                )

                with gr.Accordion("📊 Метаданные", open=False):
                    metadata_json = gr.JSON(label="Metadata")

                with gr.Accordion("📝 Сгенерированные промпты", open=False):
                    system_prompt_preview = gr.Textbox(
                        label="System Prompt",
                        lines=12,
                        interactive=False,
                        show_copy_button=True,
                    )
                    user_prompt_preview = gr.Textbox(
                        label="User Prompt",
                        lines=6,
                        interactive=False,
                        show_copy_button=True,
                    )

        # Event handlers
        def add_context_field(name: str, value: str, current: dict) -> tuple[dict, dict]:
            if name and value:
                current = current.copy()
                current[name] = value
            return current, current

        add_ctx_btn.click(
            add_context_field,
            inputs=[ctx_field_name, ctx_field_value, context_state],
            outputs=[context_state, context_display],
        )

        def run_enrichment(
            profile: str,
            name: str,
            description: str,
            country: str,
            custom_ctx: dict,
            fields: list[str],
            lang: str,
            use_web_search: bool,
        ) -> tuple[dict, dict, str, str]:
            """Run enrichment and return results."""
            if not name:
                return {"error": "Название товара обязательно"}, {}, "", ""

            try:
                # Get profile
                prof = self.config_manager.get_profile(profile)

                # Generate prompts
                system_prompt = self.prompt_engine.render_system_prompt(
                    template_name=prof.prompts.system,
                    language=lang,
                    field_names=fields,
                    field_set=prof.fields.preset,
                )

                user_prompt = self.prompt_engine.render_user_prompt(
                    template_name=prof.prompts.user,
                    product_name=name,
                    product_description=description,
                    field_names=fields,
                    context_data=custom_ctx,
                )

                # Run actual enrichment if service available
                result = {}
                metadata = {}

                if self.enricher_service:
                    try:
                        from ..models import ProductInput, EnrichmentOptions

                        product = ProductInput(
                            name=name,
                            description=description or None,
                            country_origin=country or None,
                        )

                        options = EnrichmentOptions(
                            include_web_search=use_web_search,
                            language=lang,
                            fields=fields,
                        )

                        # Run async enrichment
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            enrichment_result = loop.run_until_complete(
                                self.enricher_service.enrich_product(product, options)
                            )
                            result = enrichment_result.enriched.model_dump()
                            metadata = enrichment_result.metadata.model_dump()
                        finally:
                            loop.close()

                    except Exception as e:
                        result = {"error": str(e)}
                        logger.error("enrichment_error", error=str(e))
                else:
                    result = {
                        "info": "Enricher service not connected",
                        "prompts_generated": True,
                    }

                return result, metadata, system_prompt, user_prompt

            except Exception as e:
                logger.error("run_enrichment_error", error=str(e))
                return {"error": str(e)}, {}, "", ""

        enrich_btn.click(
            run_enrichment,
            inputs=[
                profile_dropdown,
                product_name,
                product_description,
                country_origin,
                context_state,
                field_checkboxes,
                language,
                web_search,
            ],
            outputs=[
                result_json,
                metadata_json,
                system_prompt_preview,
                user_prompt_preview,
            ],
        )

    def _build_fields_tab(self) -> None:
        """Build the field configuration tab."""
        with gr.Row():
            # Left - Field list
            with gr.Column(scale=1):
                gr.Markdown("### 📋 Доступные поля")

                field_set_dropdown = gr.Dropdown(
                    label="Набор полей",
                    choices=self.field_registry.list_field_sets(),
                    value="default",
                )

                fields_table = gr.Dataframe(
                    headers=["Имя", "Отображаемое имя", "Тип", "Обязательное"],
                    label="Поля",
                    interactive=False,
                    wrap=True,
                )

                refresh_fields_btn = gr.Button("🔄 Обновить список")

            # Right - Field editor
            with gr.Column(scale=1):
                gr.Markdown("### ✏️ Редактор поля")

                field_name_input = gr.Textbox(
                    label="Имя поля (латиница) *",
                    placeholder="my_custom_field",
                )

                field_display_name_input = gr.Textbox(
                    label="Отображаемое имя *",
                    placeholder="Моё кастомное поле",
                )

                field_type_input = gr.Dropdown(
                    label="Тип",
                    choices=["string", "array", "object"],
                    value="string",
                )

                field_description_input = gr.Textbox(
                    label="Описание для LLM *",
                    placeholder="Подробное описание того, что представляет это поле и как его извлекать...",
                    lines=4,
                )

                field_required_input = gr.Checkbox(label="Обязательное поле")

                gr.Markdown("#### 📝 Примеры")

                with gr.Row():
                    example_input = gr.Textbox(
                        label="Пример входа",
                        placeholder="iPhone 15 Pro",
                    )
                    example_output = gr.Textbox(
                        label="Пример выхода",
                        placeholder="Apple",
                    )
                    add_example_btn = gr.Button("➕", min_width=50)

                examples_state = gr.State([])
                examples_display = gr.JSON(label="Примеры", value=[])

                gr.Markdown("#### 💡 Подсказки для извлечения")

                with gr.Row():
                    hint_input = gr.Textbox(
                        label="Подсказка",
                        placeholder="Ищи в начале названия товара",
                    )
                    add_hint_btn = gr.Button("➕", min_width=50)

                hints_state = gr.State([])
                hints_display = gr.JSON(label="Подсказки", value=[])

                with gr.Row():
                    save_field_btn = gr.Button(
                        "💾 Сохранить поле",
                        variant="primary",
                    )
                    clear_field_btn = gr.Button("🗑️ Очистить форму")

                field_status = gr.Textbox(
                    label="Статус",
                    interactive=False,
                )

        # Event handlers
        def load_fields_table(field_set: str) -> list[list[str]]:
            fs = self.field_registry.get_field_set(field_set)
            if not fs:
                return []

            data = []
            for name, field in fs.fields.items():
                data.append([
                    name,
                    field.display_name,
                    field.type,
                    "✓" if field.required else "",
                ])
            return data

        refresh_fields_btn.click(
            load_fields_table,
            inputs=[field_set_dropdown],
            outputs=[fields_table],
        )

        field_set_dropdown.change(
            load_fields_table,
            inputs=[field_set_dropdown],
            outputs=[fields_table],
        )

        def add_example(inp: str, out: str, current: list) -> tuple[list, list]:
            if inp and out:
                current = current.copy()
                current.append({"input": inp, "output": out})
            return current, current

        add_example_btn.click(
            add_example,
            inputs=[example_input, example_output, examples_state],
            outputs=[examples_state, examples_display],
        )

        def add_hint(hint: str, current: list) -> tuple[list, list]:
            if hint:
                current = current.copy()
                current.append(hint)
            return current, current

        add_hint_btn.click(
            add_hint,
            inputs=[hint_input, hints_state],
            outputs=[hints_state, hints_display],
        )

        def save_field(
            name: str,
            display_name: str,
            field_type: str,
            description: str,
            required: bool,
            examples: list,
            hints: list,
        ) -> str:
            if not name:
                return "❌ Ошибка: имя поля обязательно"
            if not display_name:
                return "❌ Ошибка: отображаемое имя обязательно"
            if not description:
                return "❌ Ошибка: описание обязательно"

            try:
                field = FieldDefinition(
                    name=name,
                    display_name=display_name,
                    description=description,
                    type=field_type,
                    required=required,
                    examples=[FieldExample(**e) for e in examples] if examples else [],
                    extraction_hints=hints or [],
                )

                self.field_registry.add_custom_field(field)
                self.field_registry.save_custom_fields()

                return f"✅ Поле '{name}' сохранено"

            except Exception as e:
                return f"❌ Ошибка: {e}"

        save_field_btn.click(
            save_field,
            inputs=[
                field_name_input,
                field_display_name_input,
                field_type_input,
                field_description_input,
                field_required_input,
                examples_state,
                hints_state,
            ],
            outputs=[field_status],
        )

        def clear_form() -> tuple:
            return "", "", "string", "", False, [], [], [], []

        clear_field_btn.click(
            clear_form,
            outputs=[
                field_name_input,
                field_display_name_input,
                field_type_input,
                field_description_input,
                field_required_input,
                examples_state,
                examples_display,
                hints_state,
                hints_display,
            ],
        )

        # Load initial data
        app.load(
            load_fields_table,
            inputs=[field_set_dropdown],
            outputs=[fields_table],
        )

    def _build_prompts_tab(self) -> None:
        """Build the prompt editor tab."""
        with gr.Row():
            # Left - Template selection
            with gr.Column(scale=1):
                gr.Markdown("### 📄 Шаблоны промптов")

                prompt_type = gr.Radio(
                    label="Тип промпта",
                    choices=["system", "user"],
                    value="system",
                )

                template_dropdown = gr.Dropdown(
                    label="Шаблон",
                    choices=self.prompt_engine.get_available_templates("system"),
                    value="default",
                )

                load_template_btn = gr.Button("📂 Загрузить шаблон")

                gr.Markdown("---")
                gr.Markdown("### 📖 Справка по переменным")
                gr.Markdown("""
                **System prompt:**
                - `{{ language_name }}` - Название языка
                - `{{ fields }}` - Список полей
                - `{{ additional_instructions }}` - Доп. инструкции
                
                **User prompt:**
                - `{{ product_name }}` - Название товара
                - `{{ product_description }}` - Описание
                - `{{ product_context }}` - Полный контекст
                - `{{ fields_list }}` - Список полей
                - `{{ context_data }}` - Доп. данные
                """)

            # Right - Editor
            with gr.Column(scale=2):
                gr.Markdown("### ✏️ Редактор")

                template_name_input = gr.Textbox(label="Имя шаблона")
                template_description_input = gr.Textbox(label="Описание")

                template_editor = gr.Code(
                    label="Шаблон (Jinja2)",
                    language="jinja2",
                    lines=20,
                )

                with gr.Row():
                    save_template_btn = gr.Button(
                        "💾 Сохранить",
                        variant="primary",
                    )
                    preview_template_btn = gr.Button("👁️ Предпросмотр")

                template_status = gr.Textbox(
                    label="Статус",
                    interactive=False,
                )

                preview_output = gr.Textbox(
                    label="Предпросмотр (с тестовыми данными)",
                    lines=15,
                    interactive=False,
                    show_copy_button=True,
                )

        # Event handlers
        def update_template_list(ptype: str) -> gr.Dropdown:
            templates = self.prompt_engine.get_available_templates(ptype)
            return gr.Dropdown(
                choices=templates,
                value=templates[0] if templates else None,
            )

        prompt_type.change(
            update_template_list,
            inputs=[prompt_type],
            outputs=[template_dropdown],
        )

        def load_template(ptype: str, name: str) -> tuple[str, str, str]:
            template = self.prompt_engine.get_template(ptype, name)
            if template:
                return template.name, template.description, template.template
            return "", "", ""

        load_template_btn.click(
            load_template,
            inputs=[prompt_type, template_dropdown],
            outputs=[template_name_input, template_description_input, template_editor],
        )

        def preview_template(ptype: str, content: str) -> str:
            try:
                return self.prompt_engine.preview_template(ptype, content)
            except Exception as e:
                return f"Ошибка рендеринга: {e}"

        preview_template_btn.click(
            preview_template,
            inputs=[prompt_type, template_editor],
            outputs=[preview_output],
        )

        def save_template(ptype: str, name: str, description: str, content: str) -> str:
            if not name:
                return "❌ Ошибка: имя шаблона обязательно"
            if not content:
                return "❌ Ошибка: содержимое шаблона обязательно"

            try:
                self.prompt_engine.save_template(ptype, name, content, description)
                return f"✅ Шаблон '{name}' сохранён"
            except Exception as e:
                return f"❌ Ошибка: {e}"

        save_template_btn.click(
            save_template,
            inputs=[
                prompt_type,
                template_name_input,
                template_description_input,
                template_editor,
            ],
            outputs=[template_status],
        )

    def _build_profiles_tab(self) -> None:
        """Build the profiles management tab."""
        with gr.Row():
            # Left - Profile list
            with gr.Column(scale=1):
                gr.Markdown("### 📁 Профили конфигурации")

                profiles_dropdown = gr.Dropdown(
                    label="Выберите профиль",
                    choices=self.config_manager.list_profiles(),
                    value="default",
                )

                load_profile_btn = gr.Button("📂 Загрузить профиль")

                gr.Markdown("---")
                gr.Markdown("### ➕ Создать новый профиль")

                new_profile_name = gr.Textbox(
                    label="Имя нового профиля",
                    placeholder="my_profile",
                )
                new_profile_desc = gr.Textbox(
                    label="Описание",
                    placeholder="Описание профиля...",
                )

                create_profile_btn = gr.Button(
                    "➕ Создать на основе текущего",
                    variant="secondary",
                )

            # Right - Profile settings
            with gr.Column(scale=2):
                gr.Markdown("### ⚙️ Настройки профиля")

                with gr.Accordion("📝 Промпты", open=True):
                    profile_system_prompt = gr.Dropdown(
                        label="Системный промпт",
                        choices=self.prompt_engine.get_available_templates("system"),
                        value="default",
                    )
                    profile_user_prompt = gr.Dropdown(
                        label="Пользовательский промпт",
                        choices=self.prompt_engine.get_available_templates("user"),
                        value="default",
                    )

                with gr.Accordion("📋 Поля", open=True):
                    profile_field_set = gr.Dropdown(
                        label="Набор полей",
                        choices=self.field_registry.list_field_sets(),
                        value="default",
                    )
                    profile_enabled_fields = gr.CheckboxGroup(
                        label="Включённые поля",
                        choices=self.field_registry.list_available_fields(),
                        value=[
                            "manufacturer",
                            "trademark",
                            "category",
                            "description",
                            "features",
                        ],
                    )

                with gr.Accordion("🤖 LLM настройки", open=False):
                    profile_temperature = gr.Slider(
                        label="Temperature",
                        minimum=0.1,
                        maximum=1.0,
                        value=0.3,
                        step=0.1,
                    )
                    profile_max_tokens = gr.Number(
                        label="Max Tokens",
                        value=4000,
                        precision=0,
                    )

                with gr.Accordion("💾 Кэширование", open=False):
                    profile_cache_enabled = gr.Checkbox(
                        label="Включить кэш",
                        value=True,
                    )
                    profile_cache_ttl = gr.Number(
                        label="TTL (секунды)",
                        value=3600,
                        precision=0,
                    )

                save_profile_btn = gr.Button(
                    "💾 Сохранить профиль",
                    variant="primary",
                )

                profile_status = gr.Textbox(
                    label="Статус",
                    interactive=False,
                )

        # Event handlers
        def load_profile(name: str) -> tuple:
            try:
                profile = self.config_manager.get_profile(name)
                return (
                    profile.prompts.system,
                    profile.prompts.user,
                    profile.fields.preset,
                    profile.fields.enabled,
                    profile.llm.temperature,
                    profile.llm.max_tokens,
                    profile.cache.enabled,
                    profile.cache.ttl_seconds,
                    f"✅ Профиль '{name}' загружен",
                )
            except Exception as e:
                return (
                    "default",
                    "default",
                    "default",
                    [],
                    0.3,
                    4000,
                    True,
                    3600,
                    f"❌ Ошибка: {e}",
                )

        load_profile_btn.click(
            load_profile,
            inputs=[profiles_dropdown],
            outputs=[
                profile_system_prompt,
                profile_user_prompt,
                profile_field_set,
                profile_enabled_fields,
                profile_temperature,
                profile_max_tokens,
                profile_cache_enabled,
                profile_cache_ttl,
                profile_status,
            ],
        )

        def save_profile(
            name: str,
            sys_prompt: str,
            user_prompt: str,
            field_set: str,
            enabled_fields: list[str],
            temp: float,
            max_tok: int,
            cache_en: bool,
            cache_ttl: int,
        ) -> str:
            try:
                profile = EnrichmentProfile(
                    name=name,
                    prompts=PromptsConfig(system=sys_prompt, user=user_prompt),
                    fields=FieldsConfig(preset=field_set, enabled=enabled_fields),
                    llm=LLMConfig(temperature=temp, max_tokens=int(max_tok)),
                    cache=CacheConfig(enabled=cache_en, ttl_seconds=int(cache_ttl)),
                )
                self.config_manager.save_profile(profile, custom=(name != "default"))
                return f"✅ Профиль '{name}' сохранён"
            except Exception as e:
                return f"❌ Ошибка: {e}"

        save_profile_btn.click(
            save_profile,
            inputs=[
                profiles_dropdown,
                profile_system_prompt,
                profile_user_prompt,
                profile_field_set,
                profile_enabled_fields,
                profile_temperature,
                profile_max_tokens,
                profile_cache_enabled,
                profile_cache_ttl,
            ],
            outputs=[profile_status],
        )

        def create_new_profile(name: str, desc: str) -> tuple[str, gr.Dropdown]:
            if not name:
                return "❌ Ошибка: имя профиля обязательно", gr.Dropdown()
            try:
                self.config_manager.create_profile_from_current(name, desc)
                profiles = self.config_manager.list_profiles()
                return (
                    f"✅ Профиль '{name}' создан",
                    gr.Dropdown(choices=profiles, value=name),
                )
            except Exception as e:
                return f"❌ Ошибка: {e}", gr.Dropdown()

        create_profile_btn.click(
            create_new_profile,
            inputs=[new_profile_name, new_profile_desc],
            outputs=[profile_status, profiles_dropdown],
        )

    def launch(self, **kwargs) -> None:
        """Launch the Gradio app.
        
        Args:
            **kwargs: Arguments to pass to gr.Blocks.launch()
        """
        self.app.launch(**kwargs)


def create_app(
    enricher_service: Any = None,
    config_dir: str = "config",
) -> gr.Blocks:
    """Create and return the Gradio app.
    
    Args:
        enricher_service: Optional enricher service instance
        config_dir: Configuration directory path
        
    Returns:
        Gradio Blocks app
    """
    field_registry = FieldRegistry(config_dir=f"{config_dir}/fields")
    prompt_engine = PromptEngine(
        prompts_dir=f"{config_dir}/prompts",
        field_registry=field_registry,
    )
    config_manager = ConfigurationManager(config_dir=config_dir)

    ui = EnricherWebUI(
        field_registry=field_registry,
        prompt_engine=prompt_engine,
        config_manager=config_manager,
        enricher_service=enricher_service,
    )
    return ui.app
```

**Шаг 3.3: Создать src/ai_product_enricher/main_webui.py**

```python
"""Entry point for Gradio WebUI."""

import argparse

from ai_product_enricher.webui import EnricherWebUI
from ai_product_enricher.engine import (
    FieldRegistry,
    PromptEngine,
    ConfigurationManager,
)
from ai_product_enricher.core import setup_logging, get_logger

# Initialize logging
setup_logging()
logger = get_logger(__name__)


def main():
    """Main entry point for WebUI."""
    parser = argparse.ArgumentParser(description="AI Product Enricher WebUI")
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind to",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=7860,
        help="Port to bind to",
    )
    parser.add_argument(
        "--share",
        action="store_true",
        help="Create public URL",
    )
    parser.add_argument(
        "--config-dir",
        type=str,
        default="config",
        help="Configuration directory",
    )
    parser.add_argument(
        "--with-enricher",
        action="store_true",
        help="Connect to enricher service",
    )

    args = parser.parse_args()

    logger.info(
        "starting_webui",
        host=args.host,
        port=args.port,
        config_dir=args.config_dir,
    )

    # Initialize components
    field_registry = FieldRegistry(config_dir=f"{args.config_dir}/fields")
    prompt_engine = PromptEngine(
        prompts_dir=f"{args.config_dir}/prompts",
        field_registry=field_registry,
    )
    config_manager = ConfigurationManager(config_dir=args.config_dir)

    # Optionally connect enricher service
    enricher_service = None
    if args.with_enricher:
        try:
            from ai_product_enricher.services import ProductEnricherService
            enricher_service = ProductEnricherService()
            logger.info("enricher_service_connected")
        except Exception as e:
            logger.warning("enricher_service_connection_failed", error=str(e))

    # Create and launch WebUI
    ui = EnricherWebUI(
        field_registry=field_registry,
        prompt_engine=prompt_engine,
        config_manager=config_manager,
        enricher_service=enricher_service,
    )

    ui.launch(
        server_name=args.host,
        server_port=args.port,
        share=args.share,
    )


if __name__ == "__main__":
    main()
```

---

### ФАЗА 4: Обновление зависимостей и тестов

**Шаг 4.1: Обновить pyproject.toml — добавить gradio**

Добавить в секцию `dependencies`:

```toml
dependencies = [
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
    "httpx>=0.26.0",
    "openai>=1.10.0",
    "tenacity>=8.2.0",
    "structlog>=24.1.0",
    "cachetools>=5.3.0",
    "pyyaml>=6.0.0",
    "jinja2>=3.1.0",
    "gradio>=4.0.0",
]
```

**Шаг 4.2: Создать tests/unit/test_field_registry.py**

```python
"""Unit tests for FieldRegistry."""

import tempfile
from pathlib import Path

import pytest
import yaml

from ai_product_enricher.engine import FieldDefinition, FieldRegistry


class TestFieldRegistry:
    """Tests for FieldRegistry."""

    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary config directory with test data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fields_dir = Path(tmpdir) / "fields"
            fields_dir.mkdir(parents=True)

            # Create test field set
            test_fields = {
                "version": "1.0",
                "name": "test",
                "description": "Test fields",
                "fields": {
                    "test_field": {
                        "display_name": "Test Field",
                        "description": "A test field",
                        "type": "string",
                        "required": False,
                    },
                    "another_field": {
                        "display_name": "Another Field",
                        "description": "Another test field",
                        "type": "array",
                    },
                },
            }

            with open(fields_dir / "test.yaml", "w") as f:
                yaml.dump(test_fields, f)

            yield fields_dir

    def test_load_field_sets(self, temp_config_dir):
        """Test loading field sets from YAML."""
        registry = FieldRegistry(config_dir=temp_config_dir)

        assert "test" in registry.list_field_sets()
        field_set = registry.get_field_set("test")
        assert field_set is not None
        assert "test_field" in field_set.fields

    def test_get_field(self, temp_config_dir):
        """Test getting a specific field."""
        registry = FieldRegistry(config_dir=temp_config_dir)

        field = registry.get_field("test_field", "test")
        assert field is not None
        assert field.display_name == "Test Field"
        assert field.type == "string"

    def test_add_custom_field(self, temp_config_dir):
        """Test adding custom fields."""
        registry = FieldRegistry(config_dir=temp_config_dir)

        custom = FieldDefinition(
            name="custom_field",
            display_name="Custom Field",
            description="A custom field",
            type="object",
        )
        registry.add_custom_field(custom)

        assert "custom_field" in registry.list_available_fields("test")
        retrieved = registry.get_field("custom_field")
        assert retrieved is not None
        assert retrieved.type == "object"

    def test_get_fields_for_extraction(self, temp_config_dir):
        """Test getting multiple fields for extraction."""
        registry = FieldRegistry(config_dir=temp_config_dir)

        fields = registry.get_fields_for_extraction(
            ["test_field", "another_field"],
            "test",
        )
        assert len(fields) == 2
        names = [f.name for f in fields]
        assert "test_field" in names
        assert "another_field" in names

    def test_default_field_set_created(self):
        """Test that default field set is created if no config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = FieldRegistry(config_dir=Path(tmpdir) / "nonexistent")

            assert "default" in registry.list_field_sets()
            field_set = registry.get_field_set("default")
            assert field_set is not None
            assert "manufacturer" in field_set.fields

    def test_save_and_load_custom_fields(self, temp_config_dir):
        """Test saving and loading custom fields."""
        registry = FieldRegistry(config_dir=temp_config_dir)

        custom = FieldDefinition(
            name="saveable_field",
            display_name="Saveable Field",
            description="A saveable field",
            type="string",
        )
        registry.add_custom_field(custom)

        # Save
        custom_dir = temp_config_dir / "custom"
        custom_dir.mkdir(exist_ok=True)
        save_path = custom_dir / "custom_fields.yaml"
        registry.save_custom_fields(save_path)

        # Load in new registry
        new_registry = FieldRegistry(config_dir=temp_config_dir)
        new_registry.load_custom_fields(save_path)

        assert "saveable_field" in new_registry.list_available_fields()
```

**Шаг 4.3: Создать tests/unit/test_prompt_engine.py**

```python
"""Unit tests for PromptEngine."""

import tempfile
from pathlib import Path

import pytest
import yaml

from ai_product_enricher.engine import FieldRegistry, PromptEngine


class TestPromptEngine:
    """Tests for PromptEngine."""

    @pytest.fixture
    def temp_config(self):
        """Create temporary config with prompts and fields."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create prompts directory
            prompts_dir = Path(tmpdir) / "prompts"
            (prompts_dir / "system").mkdir(parents=True)
            (prompts_dir / "user").mkdir(parents=True)

            # Create system prompt
            system_prompt = {
                "version": "1.0",
                "name": "test_system",
                "description": "Test system prompt",
                "template": """You are an assistant.
Language: {{ language_name }}
Fields:
{% for field in fields %}
- {{ field.display_name }}: {{ field.description }}
{% endfor %}""",
            }
            with open(prompts_dir / "system" / "test_system.yaml", "w") as f:
                yaml.dump(system_prompt, f)

            # Create user prompt
            user_prompt = {
                "version": "1.0",
                "name": "test_user",
                "description": "Test user prompt",
                "template": """Product: {{ product_name }}
Extract: {{ fields_list }}""",
            }
            with open(prompts_dir / "user" / "test_user.yaml", "w") as f:
                yaml.dump(user_prompt, f)

            # Create fields directory
            fields_dir = Path(tmpdir) / "fields"
            fields_dir.mkdir(parents=True)

            test_fields = {
                "version": "1.0",
                "name": "default",
                "fields": {
                    "test_field": {
                        "display_name": "Test Field",
                        "description": "Test description",
                        "type": "string",
                    },
                },
            }
            with open(fields_dir / "default.yaml", "w") as f:
                yaml.dump(test_fields, f)

            yield tmpdir

    def test_load_templates(self, temp_config):
        """Test loading prompt templates."""
        field_registry = FieldRegistry(config_dir=f"{temp_config}/fields")
        engine = PromptEngine(
            prompts_dir=f"{temp_config}/prompts",
            field_registry=field_registry,
        )

        assert "test_system" in engine.get_available_templates("system")
        assert "test_user" in engine.get_available_templates("user")

    def test_render_system_prompt(self, temp_config):
        """Test rendering system prompt."""
        field_registry = FieldRegistry(config_dir=f"{temp_config}/fields")
        engine = PromptEngine(
            prompts_dir=f"{temp_config}/prompts",
            field_registry=field_registry,
        )

        result = engine.render_system_prompt(
            template_name="test_system",
            language="en",
            field_names=["test_field"],
        )

        assert "English" in result
        assert "Test Field" in result
        assert "Test description" in result

    def test_render_user_prompt(self, temp_config):
        """Test rendering user prompt."""
        field_registry = FieldRegistry(config_dir=f"{temp_config}/fields")
        engine = PromptEngine(
            prompts_dir=f"{temp_config}/prompts",
            field_registry=field_registry,
        )

        result = engine.render_user_prompt(
            template_name="test_user",
            product_name="Test Product",
            field_names=["test_field"],
        )

        assert "Test Product" in result
        assert "test_field" in result

    def test_default_templates_created(self):
        """Test that default templates are created if missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = PromptEngine(prompts_dir=Path(tmpdir) / "nonexistent")

            assert "default" in engine.get_available_templates("system")
            assert "default" in engine.get_available_templates("user")

    def test_save_template(self, temp_config):
        """Test saving a new template."""
        field_registry = FieldRegistry(config_dir=f"{temp_config}/fields")
        engine = PromptEngine(
            prompts_dir=f"{temp_config}/prompts",
            field_registry=field_registry,
        )

        engine.save_template(
            prompt_type="system",
            name="new_template",
            template="New template: {{ language_name }}",
            description="A new template",
        )

        assert "new_template" in engine.get_available_templates("system")

        # Verify file exists
        filepath = Path(temp_config) / "prompts" / "system" / "new_template.yaml"
        assert filepath.exists()

    def test_preview_template(self, temp_config):
        """Test template preview with test data."""
        field_registry = FieldRegistry(config_dir=f"{temp_config}/fields")
        engine = PromptEngine(
            prompts_dir=f"{temp_config}/prompts",
            field_registry=field_registry,
        )

        result = engine.preview_template(
            prompt_type="system",
            template_content="Language: {{ language_name }}",
            language="ru",
        )

        assert "Russian" in result
```

**Шаг 4.4: Создать tests/unit/test_config_manager.py**

```python
"""Unit tests for ConfigurationManager."""

import tempfile
from pathlib import Path

import pytest
import yaml

from ai_product_enricher.engine import ConfigurationManager, EnrichmentProfile


class TestConfigurationManager:
    """Tests for ConfigurationManager."""

    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary config directory with test profile."""
        with tempfile.TemporaryDirectory() as tmpdir:
            profiles_dir = Path(tmpdir) / "profiles"
            profiles_dir.mkdir(parents=True)
            (profiles_dir / "custom").mkdir()

            # Create test profile
            test_profile = {
                "version": "1.0",
                "name": "test_profile",
                "description": "Test profile",
                "prompts": {
                    "system": "default",
                    "user": "default",
                },
                "fields": {
                    "preset": "default",
                    "enabled": ["manufacturer", "trademark"],
                },
                "llm": {
                    "temperature": 0.5,
                    "max_tokens": 2000,
                },
                "cache": {
                    "enabled": True,
                    "ttl_seconds": 1800,
                },
            }

            with open(profiles_dir / "test_profile.yaml", "w") as f:
                yaml.dump(test_profile, f)

            yield tmpdir

    def test_load_profiles(self, temp_config_dir):
        """Test loading profiles from YAML."""
        manager = ConfigurationManager(config_dir=temp_config_dir)

        assert "default" in manager.list_profiles()
        assert "test_profile" in manager.list_profiles()

    def test_get_profile(self, temp_config_dir):
        """Test getting a specific profile."""
        manager = ConfigurationManager(config_dir=temp_config_dir)

        profile = manager.get_profile("test_profile")
        assert profile.name == "test_profile"
        assert profile.llm.temperature == 0.5
        assert profile.llm.max_tokens == 2000
        assert profile.fields.enabled == ["manufacturer", "trademark"]

    def test_default_profile_always_exists(self):
        """Test that default profile exists even without config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ConfigurationManager(config_dir=tmpdir)

            assert "default" in manager.list_profiles()
            profile = manager.get_profile("default")
            assert profile is not None

    def test_set_active_profile(self, temp_config_dir):
        """Test setting active profile."""
        manager = ConfigurationManager(config_dir=temp_config_dir)

        manager.set_active_profile("test_profile")
        active = manager.get_active_profile()
        assert active.name == "test_profile"

    def test_set_invalid_active_profile(self, temp_config_dir):
        """Test setting non-existent profile raises error."""
        manager = ConfigurationManager(config_dir=temp_config_dir)

        with pytest.raises(ValueError):
            manager.set_active_profile("nonexistent")

    def test_save_profile(self, temp_config_dir):
        """Test saving a new profile."""
        manager = ConfigurationManager(config_dir=temp_config_dir)

        new_profile = EnrichmentProfile(
            name="new_profile",
            description="New test profile",
        )
        manager.save_profile(new_profile)

        assert "new_profile" in manager.list_profiles()

        # Verify file exists
        filepath = Path(temp_config_dir) / "profiles" / "custom" / "new_profile.yaml"
        assert filepath.exists()

    def test_delete_profile(self, temp_config_dir):
        """Test deleting a custom profile."""
        manager = ConfigurationManager(config_dir=temp_config_dir)

        # First save a profile
        new_profile = EnrichmentProfile(name="to_delete")
        manager.save_profile(new_profile)
        assert "to_delete" in manager.list_profiles()

        # Delete it
        result = manager.delete_profile("to_delete")
        assert result is True
        assert "to_delete" not in manager.list_profiles()

    def test_cannot_delete_default(self, temp_config_dir):
        """Test that default profile cannot be deleted."""
        manager = ConfigurationManager(config_dir=temp_config_dir)

        with pytest.raises(ValueError):
            manager.delete_profile("default")

    def test_create_profile_from_current(self, temp_config_dir):
        """Test creating profile based on active profile."""
        manager = ConfigurationManager(config_dir=temp_config_dir)

        manager.set_active_profile("test_profile")
        new_profile = manager.create_profile_from_current(
            "cloned_profile",
            "Cloned from test",
        )

        assert new_profile.name == "cloned_profile"
        assert new_profile.llm.temperature == 0.5  # Copied from test_profile
        assert "cloned_profile" in manager.list_profiles()
```

---

### ФАЗА 5: Финальные шаги

**Шаг 5.1: Создать .gitkeep файлы**

```bash
touch config/fields/custom/.gitkeep
touch config/profiles/custom/.gitkeep
```

**Шаг 5.2: Обновить README.md — добавить секцию WebUI**

Добавить в README.md:

```markdown
## WebUI

Сервис включает Gradio WebUI для тестирования и настройки.

### Запуск WebUI

```bash
# Только WebUI (без enricher service)
python -m src.ai_product_enricher.main_webui

# WebUI с подключением к enricher service
python -m src.ai_product_enricher.main_webui --with-enricher

# С указанием порта
python -m src.ai_product_enricher.main_webui --port 7860

# С публичным URL (через Gradio share)
python -m src.ai_product_enricher.main_webui --share
```

### Функции WebUI

- **🧪 Тестирование** — песочница для тестирования обогащения
- **📋 Настройка полей** — создание и редактирование полей для извлечения
- **✍️ Редактор промптов** — редактирование Jinja2 шаблонов промптов
- **⚙️ Профили** — управление профилями конфигурации

### Конфигурационные файлы

```
config/
├── prompts/          # Шаблоны промптов
│   ├── system/       # Системные промпты
│   └── user/         # Пользовательские промпты
├── fields/           # Определения полей
│   ├── default.yaml  # Стандартные поля
│   └── custom/       # Кастомные поля
└── profiles/         # Профили конфигурации
    ├── default.yaml  # Профиль по умолчанию
    └── custom/       # Кастомные профили
```
```

---

## 7. Критерии успеха

### Функциональные критерии

1. ✅ WebUI запускается без ошибок на порту 7860
2. ✅ Можно создавать и сохранять кастомные поля
3. ✅ Можно редактировать и сохранять промпты
4. ✅ Можно создавать и переключать профили
5. ✅ Песочница генерирует правильные промпты
6. ✅ Если подключен enricher service — выполняется реальное обогащение

### Технические критерии

1. ✅ Все существующие тесты проходят
2. ✅ Новые unit-тесты для engine layer проходят
3. ✅ REST API работает как прежде
4. ✅ Загрузка YAML конфигурации < 1 секунды

---

## 8. Порядок выполнения команд

```bash
# 1. Создать структуру директорий
mkdir -p config/prompts/system
mkdir -p config/prompts/user
mkdir -p config/fields/custom
mkdir -p config/profiles/custom
mkdir -p src/ai_product_enricher/engine
mkdir -p src/ai_product_enricher/webui

# 2. Создать конфигурационные файлы
# config/fields/default.yaml
# config/prompts/system/default.yaml
# config/prompts/system/russian_products.yaml
# config/prompts/user/default.yaml
# config/profiles/default.yaml

# 3. Создать engine layer
# src/ai_product_enricher/engine/__init__.py
# src/ai_product_enricher/engine/field_registry.py
# src/ai_product_enricher/engine/prompt_engine.py
# src/ai_product_enricher/engine/config_manager.py

# 4. Создать WebUI
# src/ai_product_enricher/webui/__init__.py
# src/ai_product_enricher/webui/app.py
# src/ai_product_enricher/main_webui.py

# 5. Создать тесты
# tests/unit/test_field_registry.py
# tests/unit/test_prompt_engine.py
# tests/unit/test_config_manager.py

# 6. Обновить pyproject.toml (добавить gradio, pyyaml, jinja2)

# 7. Создать .gitkeep файлы
touch config/fields/custom/.gitkeep
touch config/profiles/custom/.gitkeep

# 8. Установить зависимости
pip install -e ".[dev]"

# 9. Запустить тесты
pytest tests/unit/test_field_registry.py -v
pytest tests/unit/test_prompt_engine.py -v
pytest tests/unit/test_config_manager.py -v

# 10. Запустить WebUI
python -m src.ai_product_enricher.main_webui
```

---

# ЧАСТЬ 3: ПРОМПТ ДЛЯ CLAUDE CODE

Скопируйте следующий промпт в Claude Code для выполнения реализации:

---

## ПРОМПТ ДЛЯ ВЫПОЛНЕНИЯ

```
Я хочу реализовать улучшения в проекте AI Product Enricher согласно PRD документу.

## КОНТЕКСТ ПРОЕКТА

Это FastAPI сервис для обогащения продуктовых данных с помощью LLM (Zhipu AI и Cloud.ru).
Текущая проблема: промпты и поля hardcoded в коде.

## ЦЕЛЬ

Создать конфигурируемую систему с:
1. YAML-based конфигурацией полей и промптов
2. Engine Layer (FieldRegistry, PromptEngine, ConfigurationManager)
3. Gradio WebUI для тестирования и настройки

## ПЛАН ВЫПОЛНЕНИЯ

Выполни следующие шаги последовательно:

### ШАГ 1: Создать структуру директорий

```bash
mkdir -p config/prompts/system
mkdir -p config/prompts/user
mkdir -p config/fields/custom
mkdir -p config/profiles/custom
mkdir -p src/ai_product_enricher/engine
mkdir -p src/ai_product_enricher/webui
touch config/fields/custom/.gitkeep
touch config/profiles/custom/.gitkeep
```

### ШАГ 2: Создать конфигурационные файлы

Создай следующие YAML файлы с содержимым из PRD:
- config/fields/default.yaml
- config/prompts/system/default.yaml
- config/prompts/system/russian_products.yaml
- config/prompts/user/default.yaml
- config/profiles/default.yaml

### ШАГ 3: Создать Engine Layer

Создай Python модули с кодом из PRD:
- src/ai_product_enricher/engine/__init__.py
- src/ai_product_enricher/engine/field_registry.py
- src/ai_product_enricher/engine/prompt_engine.py
- src/ai_product_enricher/engine/config_manager.py

### ШАГ 4: Создать WebUI

Создай Gradio приложение:
- src/ai_product_enricher/webui/__init__.py
- src/ai_product_enricher/webui/app.py
- src/ai_product_enricher/main_webui.py

### ШАГ 5: написать тесты

Создай тесты для engine layer:
- tests/unit/test_field_registry.py
- tests/unit/test_prompt_engine.py
- tests/unit/test_config_manager.py

### ШАГ 6: обновить pyproject.toml

Обнови pyproject.toml:
- добавить gradio, pyyaml, jinja2         

внеси небольшие коректоирови в план, промтв и описания будут только на русском языке пожтому в PromptEngine жестко настрой и зафиксируй LANGUAGE_NAMES =  "ru": "Russian", но оставь опуцию origin country в нужных случаях,  внеси правки в план аккуратно и не потряй ничено из наработок в контексте.