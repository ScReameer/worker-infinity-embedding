# RunPod Infinity Serverless

Docker образ на базе [Infinity](https://github.com/michaelfeil/infinity) для развертывания embedding модели на RunPod Serverless с OpenAI-compatible API.

## Быстрый старт

### Сборка и публикация

```bash
# Сборка образа
make build

# Публикация в Docker Hub
make push

# Или с кастомными параметрами
REGISTRY=myusername IMAGE_NAME=infinity IMAGE_TAG=v1.0 make push
```

### Деплой на RunPod

#### Опция 1: GitHub Integration (рекомендуется)

1. Подключите GitHub аккаунт в [RunPod Settings](https://console.runpod.io/user/settings)
2. В [Serverless Console](https://www.console.runpod.io/serverless) нажмите "New Endpoint"
3. В "Import Git Repository" выберите этот репозиторий
4. Выберите branch и укажите путь к Dockerfile (если не в корне)
5. Настройте GPU, workers, переменные окружения:
   ```
   MODEL_NAME=patrickjohncyh/fashion-clip
   INFINITY_HOST=localhost
   INFINITY_PORT=7997
   ```
6. Нажмите "Deploy Endpoint"

RunPod автоматически соберет и задеплоит образ. При создании новых релизов в GitHub, endpoint будет автоматически обновляться.

**Автоматическое тестирование**: RunPod выполнит тесты из `.github/tests.json` перед деплоем.

#### Опция 2: Docker Hub

1. Создайте Serverless Endpoint на [RunPod Console](https://www.runpod.io/console/serverless)
2. Укажите Docker образ: `screameer/infinity-serverless:latest`
3. Настройте переменные окружения:
   ```
   MODEL_NAME=patrickjohncyh/fashion-clip
   INFINITY_HOST=localhost
   INFINITY_PORT=7997
   ```
4. Выберите GPU (RTX 4090, A100) и настройте автоскейлинг

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

Обновите `.env`:

```env
CLIP_BASE_URL=https://api.runpod.ai/v2/<ENDPOINT_ID>
CLIP_API_KEY=<YOUR_RUNPOD_API_KEY>
CLIP_MODEL=patrickjohncyh/fashion-clip
```

Код в `tsa/embedding/infinity.py` автоматически определит RunPod endpoint и будет работать корректно.

## Структура проекта

```
runpod-infinity/
├── .github/
│   └── tests.json      # Автоматические тесты для RunPod
├── Dockerfile          # Docker образ на базе infinity:latest
├── Makefile           # Команды для сборки и публикации
├── entrypoint.sh      # Запуск Infinity + Handler
├── requirements.txt   # Зависимости (runpod, httpx)
├── test_input.json    # Пример данных для тестирования
├── src/
│   └── handler.py     # RunPod serverless handler
└── README.md          # Документация
```

## Переменные окружения

| Переменная | По умолчанию | Описание |
|-----------|-------------|----------|
| `MODEL_NAME` | `patrickjohncyh/fashion-clip` | HuggingFace model ID |
| `INFINITY_HOST` | `localhost` | Хост Infinity сервера |
| `INFINITY_PORT` | `7997` | Порт Infinity сервера |

## Локальное тестирование

```bash
# Запуск контейнера
make test

# Или напрямую
docker run -it --rm \
  -e MODEL_NAME="patrickjohncyh/fashion-clip" \
  screameer/infinity-serverless:latest
```

## Производительность

- **Cold Start**: ~10-30 секунд (загрузка модели)
- **Warm Inference**: ~50-200ms на запрос
- **Батчинг**: Автоматически через Infinity
- **Автоскейлинг**: Управляется RunPod

## Troubleshooting

**Handler не стартует**
- Проверьте логи в RunPod Console
- Убедитесь что `MODEL_NAME` указан корректно

**Timeout при первом запросе**
- Это нормально для cold start
- Увеличьте timeout в клиенте до 60s
- Используйте минимум 1 активный worker

**Неверный формат ответа**
- Убедитесь что используете `/runsync` endpoint
- Проверьте что `modality` указана для изображений

---

**Создано для**: TSUM Chat Backend  
**Лицензия**: MIT (Infinity, RunPod SDK)
