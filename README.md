# RunPod Infinity Serverless

Docker образ на базе [Infinity](https://github.com/michaelfeil/infinity) для развертывания embedding модели на RunPod Serverless с OpenAI-compatible API.

High-throughput, OpenAI-compatible **text & image embedding** & reranker powered by [Infinity](https://github.com/michaelfeil/infinity)

**✨ New: Multimodal Support!** Now supports text and image embeddings (URLs & base64) with an explicit `modality` switch per request.

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

1. [Quickstart](#quickstart)
2. [Multimodal Features](#multimodal-features)
3. [Endpoint Configuration](#endpoint-configuration)
4. [API Specification](#api-specification)
   1. [List Models](#list-models)
   2. [Create Embeddings](#create-embeddings)
   3. [Rerank Documents](#rerank-documents)
5. [Usage](#usage)
   1. [List Models](#list-models-1)
   2. [Text Embeddings](#text-embeddings)
   3. [Image Embeddings](#image-embeddings)
   4. [Reranking](#reranking)
6. [Further Documentation](#further-documentation)
7. [Acknowledgements](#acknowledgements)

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

## Multimodal Features

### Supported Modalities

- ✅ **Text** – traditional text embeddings
- ✅ **Image URLs** – `http://` or `https://` links to images (`.jpg`, `.png`, `.gif`, etc.)
- ✅ **Base64 Images** – data URI format (`data:image/png;base64,...`)

Each request targets a single modality:

| Modality | How to request                                  | Notes                                             |
| -------- | ------------------------------------------------ | ------------------------------------------------- |
| `text`   | Default; or set `modality="text"`               | Works with any deployed embedding model           |
| `image`  | Set `modality="image"`                          | Requires a multimodal model (see below)           |
| `audio`  | Planned                                          | Returns a clear `NotImplementedError` for now     |

> **Tip:** For OpenAI-compatible requests, include `"modality": "…"` alongside `model` and `input`. For native `/runsync` requests, pass `modality` inside the `input` object. If omitted, the worker assumes `text`.

### Validation & Image Fetching Defaults

- All inputs are validated eagerly for the chosen modality with detailed, index-aware error messages.
- Image downloads run through a shared `httpx.AsyncClient` with tuned keep-alive limits, timeouts, and a desktop browser User-Agent—improving compatibility with CDNs that block generic clients. All of these knobs can be overridden using the `HTTP_CLIENT_*` environment variables listed below.

### Multimodal Models

To use image embeddings, deploy a multimodal model such as:
- `patrickjohncyh/fashion-clip` – Fashion-focused CLIP model
- `jinaai/jina-clip-v1` – General-purpose multimodal embeddings
- Any other CLIP-based model with `image_embed` support

> **Note:** Text-only models (like `BAAI/bge-small-en-v1.5`) will reject image inputs with a clear error message.

---

## Endpoint Configuration

All behaviour is controlled through environment variables:

| Variable                 | Required | Default | Description                                                                                                                                          |
| ------------------------ | -------- | ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| `MODEL_NAMES`            | **Yes**  | —       | One or more Hugging-Face model IDs. Separate multiple IDs with a semicolon.<br>Example: `BAAI/bge-small-en-v1.5;patrickjohncyh/fashion-clip`       |
| `BATCH_SIZES`            | No       | `32`    | Per-model batch size; semicolon-separated list matching `MODEL_NAMES`.<br>Example: `32;16`                                                          |
| `BACKEND`                | No       | `torch` | Inference engine for _all_ models: `torch`, `optimum`, or `ctranslate2`.                                                                            |
| `DTYPES`                 | No       | `auto`  | Precision per model (`auto`, `fp16`, `fp8`). Semicolon-separated, must match `MODEL_NAMES`.<br>Example: `auto;auto`                                 |
| `INFINITY_QUEUE_SIZE`    | No       | `48000` | Max items queueable inside the Infinity engine.                                                                                                     |
| `RUNPOD_MAX_CONCURRENCY` | No       | `300`   | Max concurrent requests the RunPod wrapper will accept.                                                                                             |
| `HTTP_CLIENT_USER_AGENT` | No       | `Mozilla/5.0 ... Chrome/120.0.0.0 Safari/537.36` | Override the browser-style User-Agent used for outbound image downloads.                                                                            |
| `HTTP_CLIENT_TIMEOUT`    | No       | `10.0`  | Request timeout (seconds) for outbound image fetches.                                                                                               |
| `HTTP_CLIENT_MAX_CONNECTIONS` | No | `50`    | Concurrent connection pool size for the shared `httpx` client.                                                                                      |
| `HTTP_CLIENT_MAX_KEEPALIVE_CONNECTIONS` | No | `20` | Max keep-alive sockets retained by the shared `httpx` client.                                                                                       |

---

## API Specification

Two flavours, one schema.

- **OpenAI-compatible** – drop-in replacement for `/v1/models`, `/v1/embeddings`, so you can use this endpoint instead of the API from OpenAI by replacing the base url with the URL of your endpoint: `https://api.runpod.ai/v2/<ENDPOINT_ID>/openai/v1` and use your [API key from RunPod](https://docs.runpod.io/get-started/api-keys) instead of the one from OpenAI
- **Standard RunPod** – call `/run` or `/runsync` with a JSON body under the `input` key.  
  Base URL: `https://api.runpod.ai/v2/<ENDPOINT_ID>`

Except for transport (path + wrapper object) the JSON you send/receive is identical. The tables below describe the shared payload.

### List Models

| Method | Path                | Body                                            |
| ------ | ------------------- | ----------------------------------------------- |
| `GET`  | `/openai/v1/models` | –                                               |
| `POST` | `/runsync`          | `{ "input": { "openai_route": "/v1/models" } }` |

#### Response

```jsonc
{
  "data": [
    { "id": "BAAI/bge-small-en-v1.5", "stats": {} },
    { "id": "intfloat/e5-large-v2", "stats": {} }
  ]
}
```

---

### Create Embeddings

#### Request Fields (shared)

| Field      | Type                | Required | Description                                                                                                                |
| ---------- | ------------------- | -------- | -------------------------------------------------------------------------------------------------------------------------- |
| `model`    | string              | **Yes**  | One of the IDs supplied via `MODEL_NAMES`.                                                                                 |
| `input`    | string &#124; array | **Yes**  | Text string(s) or image URL/base64 list matching the selected modality. Order is preserved.                               |
| `modality` | string              | No       | Required for images. Accepts `text` (default) or `image`. For OpenAI requests supply via `extra_body.modality`.           |

OpenAI route vs. Standard:

| Flavour  | Method | Path             | Body                                                                   |
| -------- | ------ | ---------------- | ---------------------------------------------------------------------- |
| OpenAI   | `POST` | `/v1/embeddings` | `{ "model": "…", "input": "…", "modality": "text" }` (modality optional for text) |
| Standard | `POST` | `/runsync`       | `{ "input": { "model": "…", "input": "…", "modality": "text" } }`             |

#### Response (both flavours)

```jsonc
{
  "object": "list",
  "model": "BAAI/bge-small-en-v1.5",
  "data": [
    { "object": "embedding", "embedding": [0.01, -0.02 /* … */], "index": 0 }
  ],
  "usage": { "prompt_tokens": 2, "total_tokens": 2 }
}
```

---

### Rerank Documents (Standard only)

| Field         | Type   | Required | Description                                                       |
| ------------- | ------ | -------- | ----------------------------------------------------------------- |
| `model`       | string | **Yes**  | Any deployed reranker model                                       |
| `query`       | string | **Yes**  | The search/query text                                             |
| `docs`        | array  | **Yes**  | List of documents to rerank                                       |
| `return_docs` | bool   | No       | If `true`, return the documents in ranked order (default `false`) |

Call pattern

```http
POST /runsync
Content-Type: application/json

{
  "input": {
    "model": "BAAI/bge-reranker-large",
    "query": "Which product has warranty coverage?",
    "docs": [
      "Product A comes with a 2-year warranty",
      "Product B is available in red and blue colors",
      "All electronics include a standard 1-year warranty"
    ],
    "return_docs": true
  }
}
```

Response contains either `scores` or the full `docs` list, depending on `return_docs`.

---

## Usage

Below are minimal `curl` snippets so you can copy-paste from any machine.

> Replace `<ENDPOINT_ID>` with your endpoint ID and `<API_KEY>` with a [RunPod API key](https://docs.runpod.io/get-started/api-keys).

### List Models

```bash
# OpenAI-compatible format
curl -H "Authorization: Bearer <API_KEY>" \
     https://api.runpod.ai/v2/<ENDPOINT_ID>/openai/v1/models

# Standard RunPod format
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"input":{"openai_route":"/v1/models"}}' \
  https://api.runpod.ai/v2/<ENDPOINT_ID>/runsync
```

### Text Embeddings

```bash
# OpenAI-compatible format
curl -X POST \
  -H "Authorization: Bearer <API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{"model":"BAAI/bge-small-en-v1.5","input":"Hello world","modality":"text"}' \
  https://api.runpod.ai/v2/<ENDPOINT_ID>/openai/v1/embeddings

# Standard RunPod format
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"input":{"model":"BAAI/bge-small-en-v1.5","input":"Hello world","modality":"text"}}' \
  https://api.runpod.ai/v2/<ENDPOINT_ID>/runsync
```

### Image Embeddings

```bash
# OpenAI-compatible format (image URL)
curl -X POST \
  -H "Authorization: Bearer <API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{"model":"patrickjohncyh/fashion-clip","input":"https://example.com/image.jpg","modality":"image"}' \
  https://api.runpod.ai/v2/<ENDPOINT_ID>/openai/v1/embeddings

# Standard RunPod format (base64 image)
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"input":{"model":"patrickjohncyh/fashion-clip","input":"data:image/png;base64,iVBORw0KG...","modality":"image"}}' \
  https://api.runpod.ai/v2/<ENDPOINT_ID>/runsync
```

> **Note:** Send one request per modality. If you need both text and image embeddings, issue two calls so each payload is validated consistently.

### Reranking

```bash
# OpenAI-compatible format
curl -X POST \
  -H "Authorization: Bearer <API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "BAAI/bge-reranker-large",
    "query": "Which product has warranty coverage?",
    "docs": [
      "Product A comes with a 2-year warranty",
      "Product B is available in red and blue colors",
      "All electronics include a standard 1-year warranty"
    ],
    "return_docs": true
  }' \
  https://api.runpod.ai/v2/<ENDPOINT_ID>/openai/v1/rerank

# Standard RunPod format
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "model": "BAAI/bge-reranker-large",
      "query": "Which product has warranty coverage?",
      "docs": [
        "Product A comes with a 2-year warranty",
        "Product B is available in red and blue colors",
        "All electronics include a standard 1-year warranty"
      ],
      "return_docs": true
    }
  }' \
  https://api.runpod.ai/v2/<ENDPOINT_ID>/runsync
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