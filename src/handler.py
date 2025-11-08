"""RunPod serverless handler for Infinity embedding server."""

import os
import time
from typing import Any

import runpod

from .infinity_client import InfinityClient, InfinityError
from .utils import create_error_response, detect_modalities_per_item

INFINITY_HOST = os.getenv("INFINITY_HOST", "0.0.0.0")
INFINITY_PORT = os.getenv("INFINITY_PORT", "7997")
DEFAULT_MODEL = os.getenv("MODEL_NAME", "patrickjohncyh/fashion-clip")

infinity_client = InfinityClient(INFINITY_HOST, INFINITY_PORT)


async def async_handler(
    job: dict[str, Any],
) -> dict[str, Any] | list[dict[str, Any]]:
    """
    Main handler for RunPod serverless requests.

    Supports OpenAI-compatible routing and standard formats:
    - OpenAI: https://api.runpod.ai/v2/<ID>/openai/v1/embeddings
    - Standard: {"input": {"model": "...", "input": "...", "modality": "..."}}

    Args:
        job: RunPod job dictionary

    Returns:
        Response dictionary or list of dictionaries for OpenAI compatibility
    """
    try:
        job_input = job.get("input", {})

        # OpenAI-compatible routing
        if "openai_route" in job_input:
            return await handle_openai_route(job_input)

        # Standard format handling
        return await handle_standard_format(job_input)

    except InfinityError as e:
        return create_error_response(str(e), "InfinityError")
    except Exception as e:
        print(f"[HANDLER] Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        return create_error_response(f"Unexpected error: {str(e)}", type(e).__name__)


async def handle_openai_route(
    job_input: dict[str, Any],
) -> dict[str, Any] | list[dict[str, Any]]:
    """
    Handle OpenAI-compatible routes.

    RunPod automatically converts /openai/v1/embeddings to:
    {"input": {"openai_route": "/v1/embeddings", "openai_input": {...}}}

    Args:
        job_input: Job input containing openai_route and openai_input

    Returns:
        Response in OpenAI format
    """
    openai_route = job_input.get("openai_route")
    openai_input = job_input.get("openai_input", {})

    if openai_route == "/v1/models":
        return {
            "object": "list",
            "data": [
                {
                    "id": DEFAULT_MODEL,
                    "object": "model",
                    "owned_by": "infinity",
                    "created": int(time.time()),
                }
            ],
        }

    elif openai_route == "/v1/embeddings":
        if not openai_input:
            return create_error_response("Missing openai_input for embeddings request")

        model = openai_input.get("model", DEFAULT_MODEL)
        input_data = openai_input.get("input")

        if not input_data:
            return create_error_response("Missing 'input' field in openai_input")

        if isinstance(input_data, str):
            input_data = [input_data]

        explicit_modality = openai_input.get("modality")

        if explicit_modality:
            # Use explicit modality for all items
            result = await infinity_client.get_embeddings(
                input_data, model, explicit_modality
            )
        else:
            # Auto-detect modality for each item
            modalities = detect_modalities_per_item(input_data)
            unique_modalities = set(modalities)

            if len(unique_modalities) == 1:
                # All same modality - single request
                modality = modalities[0]
                result = await infinity_client.get_embeddings(
                    input_data, model, modality
                )
            else:
                # Mixed modalities - use special handler
                result = await infinity_client.get_embeddings_mixed(
                    input_data, model, modalities
                )

        # Return as list for OpenAI compatibility (return_as_list=True behavior)
        return [result]

    else:
        return create_error_response(f"Unsupported OpenAI route: {openai_route}")


async def handle_standard_format(job_input: dict[str, Any]) -> dict[str, Any]:
    """
    Handle standard RunPod format requests.

    Supports multiple input formats:
    - {"input": "...", "model": "...", "modality": "..."}
    - {"text": "...", "model": "..."}
    - {"image": "...", "model": "..."}

    Args:
        job_input: Job input dictionary

    Returns:
        Embeddings response
    """
    model = job_input.get("model", DEFAULT_MODEL)

    # Format 1: input + modality
    if "input" in job_input:
        input_data = job_input["input"]
        modality = job_input.get("modality", "text")
        return await infinity_client.get_embeddings(input_data, model, modality)

    # Format 2: explicit text field
    elif "text" in job_input:
        text_data = job_input["text"]
        return await infinity_client.get_embeddings(text_data, model, "text")

    # Format 3: explicit image field
    elif "image" in job_input:
        image_data = job_input["image"]
        return await infinity_client.get_embeddings(image_data, model, "image")

    else:
        return create_error_response(
            "Invalid input format. Expected 'input', 'text', or 'image' field."
        )


if __name__ == "__main__":
    print("Starting RunPod serverless handler")
    print(f"Model: {DEFAULT_MODEL}")
    print(f"Infinity: http://{INFINITY_HOST}:{INFINITY_PORT}")

    runpod.serverless.start(
        {
            "handler": async_handler,
            "return_aggregate_stream": False,
        }
    )
