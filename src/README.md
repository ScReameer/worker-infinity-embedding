# Source Code Structure

## Modules

### `handler.py`
Main RunPod serverless handler. Entry point for all requests.

**Key functions:**
- `async_handler()` - Main request handler
- `handle_openai_route()` - Processes OpenAI-compatible API calls
- `handle_standard_format()` - Processes standard RunPod format requests

### `infinity_client.py`
Client for communicating with the Infinity embedding server.

**Classes:**
- `InfinityClient` - Async client for Infinity API
- `InfinityError` - Custom exception for Infinity errors

### `utils.py`
Utility functions used across the handler.

**Functions:**
- `detect_modality()` - Auto-detect if input is text or image
- `create_error_response()` - Generate OpenAI-compatible error responses

## Architecture

```
┌─────────────────────┐
│   RunPod Request    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│    handler.py       │
│  ┌───────────────┐  │
│  │ async_handler │  │
│  └───────┬───────┘  │
│          │          │
│    ┌─────▼──────┐   │
│    │ OpenAI or  │   │
│    │ Standard?  │   │
│    └─────┬──────┘   │
│          │          │
│   ┌──────▼────────┐ │
│   │ detect_modal  │ │◄── utils.py
│   │   ity()       │ │
│   └──────┬────────┘ │
│          │          │
└──────────┼──────────┘
           │
           ▼
┌─────────────────────┐
│ infinity_client.py  │
│  ┌───────────────┐  │
│  │ InfinityClient│  │
│  │.get_embeddings│  │
│  └───────┬───────┘  │
└──────────┼──────────┘
           │
           ▼
┌─────────────────────┐
│  Infinity Server    │
│   (Port 7997)       │
└─────────────────────┘
```

## Request Flow

### OpenAI-Compatible Request
1. Request arrives at `/openai/v1/embeddings`
2. RunPod transforms to `{"input": {"openai_route": "/v1/embeddings", "openai_input": {...}}}`
3. `handle_openai_route()` processes the request
4. `detect_modality()` determines if input is text/image
5. `InfinityClient.get_embeddings()` calls Infinity server
6. Response wrapped in list `[result]` for OpenAI compatibility

### Standard Request
1. Request arrives at `/runsync` or `/run`
2. `handle_standard_format()` processes the request
3. Detects input format (input/text/image)
4. `InfinityClient.get_embeddings()` calls Infinity server
5. Direct response returned

## Error Handling

All errors are caught and converted to OpenAI-compatible format:
```json
{
  "error": {
    "message": "Error description",
    "type": "ErrorType",
    "code": 400
  }
}
```
