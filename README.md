# RunPod Infinity Serverless

Docker образ на базе [Infinity](https://github.com/michaelfeil/infinity) для развертывания embedding модели на RunPod Serverless с OpenAI-compatible API.

## Деплой на RunPod

### Вариант 1: GitHub Integration (рекомендуется)

1. Подключить GitHub аккаунт в [RunPod Settings](https://console.runpod.io/user/settings)
2. В [Serverless Console](https://www.console.runpod.io/serverless) нажать "New Endpoint"
3. В "Import Git Repository" выбрать этот репозиторий
4. Выбрать branch и указать путь к Dockerfile (если не в корне)
5. Подключить Network Volume к `/runpod-volume` для кэширования модели
6. (опционально) Настроить переменные окружения:
   ```
   MODEL_NAME=patrickjohncyh/fashion-clip
   INFINITY_HOST=0.0.0.0
   INFINITY_PORT=7997
   ```
7. Нажать "Deploy Endpoint"

RunPod автоматически соберет и задеплоит образ. При создании новых релизов в GitHub, endpoint будет автоматически обновляться.

**Автоматическое тестирование**: RunPod выполнит тесты из `.github/tests.json` перед деплоем.

### Вариант 2: Docker Hub

1. Создать Serverless Endpoint на [RunPod Console](https://www.runpod.io/console/serverless)
2. Указать Docker образ
3. Подключить Network Volume к `/runpod-volume` для кэширования модели
4. (опционально) Настроить переменные окружения:
   ```
   MODEL_NAME=patrickjohncyh/fashion-clip
   INFINITY_HOST=0.0.0.0
   INFINITY_PORT=7997
   ```

## API

### OpenAI-совместимый endpoint (рекомендуется)

#### Текстовые эмбеддинги

```bash
curl -X POST https://api.runpod.ai/v2/<ENDPOINT_ID>/openai/v1/embeddings \
  -H "Authorization: Bearer <API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{
    "input": ["A red dress", "Blue jeans"],
    "model": "patrickjohncyh/fashion-clip"
  }'
```

#### Эмбеддинги изображений (URL)

```bash
curl -X POST https://api.runpod.ai/v2/<ENDPOINT_ID>/openai/v1/embeddings \
  -H "Authorization: Bearer <API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{
    "input": ["https://example.com/image.jpg"],
    "model": "patrickjohncyh/fashion-clip"
  }'
```

#### Эмбеддинги изображений (Base64)

```bash
curl -X POST https://api.runpod.ai/v2/<ENDPOINT_ID>/openai/v1/embeddings \
  -H "Authorization: Bearer <API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{
    "input": ["data:image/jpeg;base64,/9j/4AAQSkZJRg..."],
    "model": "patrickjohncyh/fashion-clip"
  }'
```

#### Смешанный ввод (текст и изображения)

```bash
curl -X POST https://api.runpod.ai/v2/<ENDPOINT_ID>/openai/v1/embeddings \
  -H "Authorization: Bearer <API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{
    "input": [
      "A red dress",
      "https://example.com/image.jpg",
      "data:image/jpeg;base64,/9j/4AAQSkZJRg..."
    ],
    "model": "patrickjohncyh/fashion-clip"
  }'
```

#### Python с OpenAI SDK

```python
from openai import AsyncOpenAI

client = AsyncOpenAI(
    api_key="<YOUR_RUNPOD_API_KEY>",
    base_url="https://api.runpod.ai/v2/<ENDPOINT_ID>/openai/v1"
)

# Text embeddings
response = await client.embeddings.create(
    input=["A red dress", "Blue jeans"],
    model="patrickjohncyh/fashion-clip"
)

# Image embeddings (URL)
response = await client.embeddings.create(
    input=["https://example.com/image.jpg"],
    model="patrickjohncyh/fashion-clip"
)

# Mixed
response = await client.embeddings.create(
    input=[
        "A beautiful red dress",
        "https://example.com/product.jpg"
    ],
    model="patrickjohncyh/fashion-clip"
)
```

### Формат ответа (OpenAI-совместимый)

```json
{
  "object": "list",
  "model": "patrickjohncyh/fashion-clip",
  "data": [
    {
      "object": "embedding",
      "embedding": [0.005659, 0.031349, -0.092258, ...],
      "index": 0
    }
  ],
  "usage": {
    "prompt_tokens": 41,
    "total_tokens": 41
  },
  "id": "infinity-1017bbcf-08d3-48c6-b7f9-cd3dc6a849bb",
  "created": 1762520966
}
```

### Стандартный формат RunPod

Для обратной совместимости также поддерживается стандартный формат RunPod:

```bash
curl -X POST https://api.runpod.ai/v2/<ENDPOINT_ID>/runsync \
  -H "Authorization: Bearer <API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "model": "patrickjohncyh/fashion-clip",
      "input": ["Text 1", "Text 2"],
      "modality": "text"
    }
  }'
```

## Пример интеграции

```python
from openai import AsyncOpenAI

client = AsyncOpenAI(
    api_key="<YOUR_RUNPOD_API_KEY>",
    base_url="https://api.runpod.ai/v2/<ENDPOINT_ID>/openai/v1"
)



for item in response.data:
    print(f"Embedding {item.index}: {len(item.embedding)} dimensions")
```

## Переменные окружения

| Переменная | По умолчанию | Описание |
|-----------|-------------|----------|
| `MODEL_NAME` | `patrickjohncyh/fashion-clip` | HuggingFace model ID |
| `INFINITY_HOST` | `0.0.0.0` | Хост Infinity сервера |
| `INFINITY_PORT` | `7997` | Порт Infinity сервера |