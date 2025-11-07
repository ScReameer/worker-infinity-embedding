import asyncio
import os
import sys
import time
from typing import Any, Dict, List, Union, Optional

import httpx
import runpod

INFINITY_HOST = os.getenv("INFINITY_HOST", "0.0.0.0")
INFINITY_PORT = os.getenv("INFINITY_PORT", "7997")
INFINITY_BASE_URL = f"http://{INFINITY_HOST}:{INFINITY_PORT}"
DEFAULT_MODEL = os.getenv("MODEL_NAME", "patrickjohncyh/fashion-clip")


class InfinityError(Exception):
    """Custom exception for Infinity-related errors."""

    pass


def detect_modality(input_data: Union[str, List[str]], explicit_modality: Optional[str] = None) -> str:
    if explicit_modality:
        return explicit_modality
    
    def is_image_data(data: str) -> bool:
        if not isinstance(data, str):
            return False
            
        if data.startswith("data:image/"):
            return True
            
        if data.startswith(("http://", "https://")):
            image_extensions = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg", ".tiff", ".ico"]
            return any(ext in data.lower() for ext in image_extensions)
        
        return False
    
    if isinstance(input_data, str):
        return "image" if is_image_data(input_data) else "text"
    elif isinstance(input_data, list) and len(input_data) > 0:
        return "image" if is_image_data(input_data[0]) else "text"
    
    return "text"


async def call_infinity_embeddings(
    input_data: Union[str, List[str]], model: str = DEFAULT_MODEL, modality: str = "text"
) -> Dict[str, Any]:
    """
    Call Infinity embeddings endpoint.

    Args:
        input_data: Text string(s) or image URL(s) to embed
        model: Model name to use
        modality: "text" or "image"

    Returns:
        OpenAI-compatible embeddings response
    """
    url = f"{INFINITY_BASE_URL}/embeddings"

    payload = {"model": model, "input": input_data, "encoding_format": "float"}

    if modality == "image":
        payload["modality"] = modality

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, json=payload)
            
            if response.status_code != 200:
                print(f"[INFINITY] Error ({response.status_code}): {response.text}")
                raise InfinityError(f"Infinity API error ({response.status_code}): {response.text}")

            result = response.json()
            return result

    except httpx.HTTPError as e:
        print(f"[INFINITY] HTTP Error: {e}")
        raise InfinityError(f"Failed to connect to Infinity server: {e}")
    except asyncio.TimeoutError:
        raise InfinityError("Request to Infinity server timed out")


def create_error_response(message: str, error_type: str = "BadRequestError", code: int = 400) -> Dict[str, Any]:
    """Create OpenAI-compatible error response."""
    return {
        "error": {
            "message": message,
            "type": error_type,
            "code": code
        }
    }


async def async_handler(job: Dict[str, Any]) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Main handler for RunPod serverless requests.

    Supports both OpenAI-compatible routing and standard formats:
    
    OpenAI-compatible (RunPod routes automatically):
    When calling: https://api.runpod.ai/v2/<ID>/openai/v1/embeddings
    RunPod converts to: {"input": {"openai_route": "/v1/embeddings", "openai_input": {...}}}

    Standard format:
    {
        "input": {
            "model": "patrickjohncyh/fashion-clip",
            "input": "text to embed" or ["text1", "text2"] or ["https://image.url"],
            "modality": "text" or "image"  # optional, defaults to "text"
        }
    }

    Alternative format (direct):
    {
        "input": {
            "text": "text to embed" or ["text1", "text2"],
            "image": "https://image.url" or ["url1", "url2"],
            "model": "model-name"  # optional
        }
    }
    """
    try:
        job_input = job.get("input", {})

        # Check for RunPod's OpenAI routing
        if "openai_route" in job_input:
            openai_route = job_input.get("openai_route")
            openai_input = job_input.get("openai_input", {})

            if openai_route == "/v1/models":
                # Return available models in OpenAI format
                return {
                    "object": "list",
                    "data": [
                        {
                            "id": DEFAULT_MODEL,
                            "object": "model",
                            "owned_by": "infinity",
                            "created": int(time.time())
                        }
                    ]
                }

            elif openai_route == "/v1/embeddings":
                if not openai_input:
                    return create_error_response("Missing openai_input for embeddings request")
                
                model = openai_input.get("model", DEFAULT_MODEL)
                input_data = openai_input.get("input")
                
                if not input_data:
                    return create_error_response("Missing 'input' field in openai_input")

                explicit_modality = openai_input.get("modality")
                modality = detect_modality(input_data, explicit_modality)

                # Call Infinity and return response (already in OpenAI format)
                result = await call_infinity_embeddings(input_data=input_data, model=model, modality=modality)
                
                # CRITICAL: For OpenAI compatibility, RunPod expects return_as_list=True behavior
                # The original worker returns [result] for embeddings, not just result
                return [result]

            else:
                return create_error_response(f"Unsupported OpenAI route: {openai_route}")

        # Standard format handling (existing logic)
        elif "input" in job_input:
            input_data = job_input["input"]
            model = job_input.get("model", DEFAULT_MODEL)
            modality = job_input.get("modality", "text")
            result = await call_infinity_embeddings(input_data=input_data, model=model, modality=modality)
            return result

        elif "text" in job_input:
            text_data = job_input["text"]
            model = job_input.get("model", DEFAULT_MODEL)

            result = await call_infinity_embeddings(input_data=text_data, model=model, modality="text")
            return result

        elif "image" in job_input:
            image_data = job_input["image"]
            model = job_input.get("model", DEFAULT_MODEL)

            result = await call_infinity_embeddings(input_data=image_data, model=model, modality="image")
            return result

        else:
            return create_error_response(
                "Invalid input format. Expected 'openai_route', 'input', 'text', or 'image' field."
            )

    except InfinityError as e:
        return create_error_response(str(e), "InfinityError")

    except Exception as e:
        print(f"[HANDLER] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return create_error_response(f"Unexpected error: {str(e)}", type(e).__name__)


def check_infinity_server():
    """
    Check if Infinity server is running and accessible.
    This is called on startup to ensure the environment is properly configured.
    """
    import requests

    try:
        response = requests.get(f"{INFINITY_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print(f"✓ Infinity server is running at {INFINITY_BASE_URL}")
            return True
    except requests.exceptions.RequestException:
        pass

    try:
        response = requests.get(f"{INFINITY_BASE_URL}/", timeout=5)
        if response.status_code in [200, 404]:  # 404 is OK, means server is up
            print(f"✓ Infinity server is accessible at {INFINITY_BASE_URL}")
            return True
    except requests.exceptions.RequestException as e:
        print(f"✗ Cannot connect to Infinity server at {INFINITY_BASE_URL}", file=sys.stderr)
        print(f"  Error: {e}", file=sys.stderr)
        print("  Make sure INFINITY_HOST and INFINITY_PORT are set correctly", file=sys.stderr)
        return False

    return False


if __name__ == "__main__":
    if not check_infinity_server():
        print("Warning: Infinity server check failed. Handler may not work correctly.", file=sys.stderr)

    print("Starting RunPod serverless handler for Infinity")
    print(f"Default model: {DEFAULT_MODEL}")
    print(f"Infinity URL: {INFINITY_BASE_URL}")

    runpod.serverless.start(
        {
            "handler": async_handler,
            "return_aggregate_stream": False,
        }
    )
