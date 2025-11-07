# RunPod Infinity Serverless

Docker образ на базе [Infinity](https://github.com/michaelfeil/infinity) для развертывания embedding модели на RunPod Serverless с OpenAI-compatible API.

## Быстрый старт
### Деплой на RunPod

#### Вариант 1: GitHub Integration (рекомендуется)

1. Подключить GitHub аккаунт в [RunPod Settings](https://console.runpod.io/user/settings)
2. В [Serverless Console](https://www.console.runpod.io/serverless) нажать "New Endpoint"
3. В "Import Git Repository" выбрать этот репозиторий
4. Выбрать branch и указать путь к Dockerfile (если не в корне)
5. Настроить GPU, workers, переменные окружения:
   ```
   MODEL_NAME=patrickjohncyh/fashion-clip
   INFINITY_HOST=localhost
   INFINITY_PORT=7997
   ```
6. Нажать "Deploy Endpoint"

RunPod автоматически соберет и задеплоит образ. При создании новых релизов в GitHub, endpoint будет автоматически обновляться.

**Автоматическое тестирование**: RunPod выполнит тесты из `.github/tests.json` перед деплоем.

#### Вариант 2: Docker Hub

1. Создать Serverless Endpoint на [RunPod Console](https://www.runpod.io/console/serverless)
2. Указать Docker образ: `<USERNAME>/<REPO>:<TAG>`
3. Настроить переменные окружения:
   ```
   MODEL_NAME=patrickjohncyh/fashion-clip
   INFINITY_HOST=localhost
   INFINITY_PORT=7997
   ```

### Использование API

#### Текстовые эмбеддинги

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

#### Изображения (CLIP)

```bash
curl -X POST https://api.runpod.ai/v2/<ENDPOINT_ID>/runsync \
  -H "Authorization: Bearer <API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "model": "patrickjohncyh/fashion-clip",
      "input": "https://example.com/image.jpg",
      "modality": "image"
    }
  }'
```

#### Ответ (OpenAI-compatible)

```json
{
  "object": "list",
  "model": "patrickjohncyh/fashion-clip",
  "data": [
    {
      "object": "embedding",
      "embedding": [0.012, -0.034, ...],
      "index": 0
    }
  ],
  "usage": {
    "prompt_tokens": 10,
    "total_tokens": 10
  }
}
```

## Интеграция с tsa/embedding/infinity.py

Обновить `.env`:

```env
CLIP_BASE_URL=https://api.runpod.ai/v2/<ENDPOINT_ID>
CLIP_API_KEY=<YOUR_RUNPOD_API_KEY>
CLIP_MODEL=patrickjohncyh/fashion-clip
```

## Переменные окружения

| Переменная | По умолчанию | Описание |
|-----------|-------------|----------|
| `MODEL_NAME` | `patrickjohncyh/fashion-clip` | HuggingFace model ID |
| `INFINITY_HOST` | `localhost` | Хост Infinity сервера |
| `INFINITY_PORT` | `7997` | Порт Infinity сервера |