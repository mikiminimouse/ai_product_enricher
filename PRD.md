# Zhipu AI (BigModel) API: полная техническая документация для PRD

Zhipu AI предоставляет **полностью OpenAI-совместимый API** с уникальными возможностями — включая нативный web_search tool и модели GLM-4.7 с контекстом **200K токенов**. Платформа доступна в двух вариантах: BigModel для Китая (`open.bigmodel.cn`) и Z.AI для международных пользователей (`api.z.ai`). Интеграция возможна как через официальный `zhipuai` SDK, так и через стандартный `openai` Python-пакет без модификаций.

---

## API Authentication: ключи и авторизация

### Формат API-ключа

API-ключ Zhipu AI имеет структуру **`{id}.{secret}`** — две части, разделённые точкой. Например: `abc123def456.ghi789jkl012mno345pqr678`. Ключ можно получить в личном кабинете:

- **Китай**: https://open.bigmodel.cn/ → API Keys
- **International**: https://z.ai/model-api → API Keys

### Base URL endpoints

| Платформа | Base URL | Назначение |
|-----------|----------|------------|
| **BigModel (China)** | `https://open.bigmodel.cn/api/paas/v4/` | Основной endpoint для КНР |
| **Z.AI (International)** | `https://api.z.ai/api/paas/v4/` | Для международных пользователей |
| **Coding Plan** | `https://api.z.ai/api/coding/paas/v4` | Специализированный endpoint для IDE-интеграций |

Полный URL для chat completions: `{base_url}chat/completions`

### Authorization header

Zhipu AI использует стандартный **Bearer-токен** без дополнительной подписи:

```http
Content-Type: application/json
Authorization: Bearer <your_api_key>
```

JWT-генерация опциональна (legacy-метод для повышенной безопасности), но **не требуется** для работы API.

---

## OpenAI SDK compatibility: конфигурация для Python

Zhipu AI полностью совместим с **openai>=1.0** Python SDK. Достаточно указать правильные `base_url` и `api_key`:

```python
from openai import OpenAI

client = OpenAI(
    api_key="your-zhipuai-api-key",
    base_url="https://open.bigmodel.cn/api/paas/v4/"  # или https://api.z.ai/api/paas/v4/
)

completion = client.chat.completions.create(
    model="glm-4.7",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is AI?"}
    ],
    temperature=0.7,
    max_tokens=1024
)

print(completion.choices[0].message.content)
```

### Streaming через OpenAI SDK

```python
stream = client.chat.completions.create(
    model="glm-4.7",
    messages=[{"role": "user", "content": "Tell me a story"}],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

### Поддерживаемые модели

| Модель | Параметры | Контекст | Описание |
|--------|-----------|----------|----------|
| **glm-4.7** | 355B | 200K | Флагман (январь 2025), лучший для coding/agents |
| **glm-4.6** | 355B MoE | 200K | Предыдущий флагман |
| **glm-4.5** | 355B/32B active | 128K | Agentic reasoning |
| **glm-4-plus** | — | 128K | Улучшенная базовая модель |
| **glm-4-air** | — | 128K | Лёгкая версия |
| **glm-4-air-250414** | — | 128K | Обновлённый air |
| **glm-4-flash** | — | 128K | Быстрый inference |
| **glm-4-long** | — | 1M | Расширенный контекст |
| **glm-4v** / **glm-4.6v** | — | 128K | Vision-модели |

**Важно**: `temperature` принимает значения в диапазоне **(0, 1)** — ровно `0` не поддерживается.

---

## Web Search tool: нативный поиск в интернете

### Формат tools parameter

```json
{
  "tools": [
    {
      "type": "web_search",
      "web_search": {
        "enable": "True",
        "search_engine": "search_pro",
        "search_result": "True",
        "search_prompt": "Summarize key information from {search_result}.",
        "count": "5",
        "search_domain_filter": "www.example.com",
        "search_recency_filter": "noLimit",
        "content_size": "high"
      }
    }
  ],
  "tool_choice": "auto"
}
```

### Параметры web_search

| Параметр | Тип | Описание | Значения |
|----------|-----|----------|----------|
| `enable` | string | Включить поиск | `"True"` / `"False"` |
| `search_engine` | string | Поисковый движок | `search_std`, `search_pro`, `search_pro_sogou`, `search_pro_quark` |
| `search_result` | string | Вернуть результаты | `"True"` / `"False"` |
| `search_prompt` | string | Промпт для обработки | Использует placeholder `{search_result}` |
| `count` | string | Количество результатов | `"1"` — `"50"` (по умолчанию `"10"`) |
| `content_size` | string | Размер summary | `"low"`, `"medium"`, `"high"` |

### tool_choice options

- `"auto"` — модель сама решает, когда искать
- `"none"` — поиск отключён
- Explicit tool specification для принудительного вызова

### Формат ответа с web_search

```json
{
  "choices": [{
    "message": {
      "content": "Ответ модели с интегрированными результатами поиска...",
      "role": "assistant"
    }
  }],
  "web_search": [
    {
      "title": "Заголовок страницы",
      "link": "https://example.com/page",
      "media": "Источник",
      "publish_date": "2025-01-15",
      "content": "Сниппет страницы",
      "refer": "ref_1"
    }
  ],
  "usage": {
    "prompt_tokens": 4199,
    "completion_tokens": 868,
    "total_tokens": 5067
  }
}
```

### Полный пример с web_search

```python
from openai import OpenAI

client = OpenAI(
    api_key="your-api-key",
    base_url="https://open.bigmodel.cn/api/paas/v4/"
)

response = client.chat.completions.create(
    model="glm-4-air",
    messages=[
        {"role": "user", "content": "What are the latest AI developments in 2025?"}
    ],
    tools=[{
        "type": "web_search",
        "web_search": {
            "enable": "True",
            "search_engine": "search_pro",
            "search_result": "True",
            "count": "5"
        }
    }],
    extra_body={"tool_choice": "auto"}
)

print(response.choices[0].message.content)
# Доступ к результатам поиска через response.web_search (если есть)
```

---

## Chat Completions API: формат запросов и ответов

### Messages format

```python
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "User question here"},
    {"role": "assistant", "content": "Previous assistant response"}
]
```

Поддерживаемые роли: `system`, `user`, `assistant`

### response_format для JSON output

```python
response = client.chat.completions.create(
    model="glm-4.7",
    messages=[
        {
            "role": "system",
            "content": '''Return JSON: {"sentiment": "positive/negative", "confidence": 0.95}'''
        },
        {"role": "user", "content": "Analyze: 'Great weather today!'"}
    ],
    response_format={"type": "json_object"}
)

import json
result = json.loads(response.choices[0].message.content)
```

Варианты `response_format.type`:
- `"text"` — обычный текст (по умолчанию)
- `"json_object"` — принудительный JSON-вывод

### Streaming vs non-streaming

**Non-streaming** (по умолчанию):
```python
response = client.chat.completions.create(
    model="glm-4.7",
    messages=[{"role": "user", "content": "Hello!"}],
    stream=False
)
```

**Streaming** (SSE):
```python
stream = client.chat.completions.create(
    model="glm-4.7",
    messages=[{"role": "user", "content": "Hello!"}],
    stream=True
)

for chunk in stream:
    content = chunk.choices[0].delta.content
    if content:
        print(content, end="", flush=True)
```

---

## Environment Variables: рекомендуемые переменные

| Переменная | SDK | Описание |
|------------|-----|----------|
| **`ZHIPUAI_API_KEY`** | Официальный zhipuai, LangChain, LlamaIndex | **Основная конвенция** |
| `ZHIPUAI_BASE_URL` | zhipuai SDK | Кастомный endpoint (опционально) |
| `ZHIPU_API_KEY` | Vercel AI SDK, community libs | Альтернативное именование |
| `ZHIPU_AI_API_KEY` | Spring AI (Java) | Java-специфичное |

**Рекомендуемая конфигурация** для `.env`:

```bash
ZHIPUAI_API_KEY=your-api-key-here
ZHIPUAI_BASE_URL=https://open.bigmodel.cn/api/paas/v4/
```

---

## Python SDK: официальный zhipuai package

### Установка

```bash
pip install zhipuai
```

Текущая версия: **2.1.5.20250825** | Python >= 3.8 (рекомендуется 3.9+)

### Основное использование

```python
from zhipuai import ZhipuAI

# Автоматически читает ZHIPUAI_API_KEY из environment
client = ZhipuAI()

# Или явное указание
client = ZhipuAI(
    api_key="your-api-key",
    base_url="https://open.bigmodel.cn/api/paas/v4/"
)

response = client.chat.completions.create(
    model="glm-4.7",
    messages=[
        {"role": "user", "content": "Hello!"}
    ]
)
print(response.choices[0].message.content)
```

### Chat completions с tools (function calling)

```python
from zhipuai import ZhipuAI

client = ZhipuAI()

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "City name"}
                },
                "required": ["location"]
            }
        }
    }
]

response = client.chat.completions.create(
    model="glm-4.7",
    messages=[{"role": "user", "content": "What's the weather in Tokyo?"}],
    tools=tools,
    tool_choice="auto"
)

# Проверка вызова функции
if response.choices[0].message.tool_calls:
    tool_call = response.choices[0].message.tool_calls[0]
    print(f"Function: {tool_call.function.name}")
    print(f"Arguments: {tool_call.function.arguments}")
```

### Расширенная конфигурация клиента

```python
from zhipuai import ZhipuAI
import httpx

client = ZhipuAI(
    api_key="your-api-key",
    timeout=httpx.Timeout(timeout=300.0, connect=8.0),
    max_retries=3,
    base_url="https://open.bigmodel.cn/api/paas/v4/"
)
```

### Error handling

```python
import zhipuai
from zhipuai import ZhipuAI

client = ZhipuAI()

try:
    response = client.chat.completions.create(
        model="glm-4.7",
        messages=[{"role": "user", "content": "Hello!"}]
    )
except zhipuai.APIAuthenticationError:
    print("Invalid API key (401)")
except zhipuai.APIReachLimitError:
    print("Rate limit exceeded (429)")
except zhipuai.APIStatusError as e:
    print(f"API error: {e}")
except zhipuai.APITimeoutError:
    print("Request timeout")
```

---

## Сравнение SDK-подходов

| Аспект | zhipuai SDK | openai SDK |
|--------|-------------|------------|
| **Установка** | `pip install zhipuai` | `pip install openai` |
| **Инициализация** | `ZhipuAI(api_key=...)` | `OpenAI(api_key=..., base_url=...)` |
| **Env variable** | `ZHIPUAI_API_KEY` | Требует явного указания |
| **Web search** | Нативная поддержка | Через `extra_body` или `tools` |
| **Специфичные features** | `reasoning_content`, `video_result` | Стандартный формат |
| **Рекомендация** | Для полного функционала Zhipu | Для унификации с другими LLM |

---

## Заключение: ключевые технические параметры для PRD

Zhipu AI представляет собой production-ready платформу с **полной OpenAI-совместимостью**. Для интеграции достаточно изменить `base_url` в существующем коде на `https://open.bigmodel.cn/api/paas/v4/`. Уникальное преимущество — нативный `web_search` tool без необходимости внешних сервисов. Модель **glm-4.7** с 200K-контекстом и 355B параметрами конкурентоспособна с GPT-4 и Claude 3.5. Рекомендуемый стек для нового проекта: `zhipuai` SDK с переменной окружения `ZHIPUAI_API_KEY`, что обеспечивает доступ ко всем специфичным возможностям платформы при сохранении привычного OpenAI-подобного интерфейса.
