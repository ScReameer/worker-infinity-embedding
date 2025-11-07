import asyncio
import os
import sys
from typing import Any, Dict, List, Union

import httpx
import runpod

INFINITY_HOST = os.getenv("INFINITY_HOST", "0.0.0.0")
INFINITY_PORT = os.getenv("INFINITY_PORT", "7997")
INFINITY_BASE_URL = f"http://{INFINITY_HOST}:{INFINITY_PORT}"
DEFAULT_MODEL = os.getenv("MODEL_NAME", "patrickjohncyh/fashion-clip")


class InfinityError(Exception):
    """Custom exception for Infinity-related errors."""

    pass


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
                raise InfinityError(f"Infinity API error ({response.status_code}): {response.text}")

            return response.json()

    except httpx.HTTPError as e:
        raise InfinityError(f"Failed to connect to Infinity server: {e}")
    except asyncio.TimeoutError:
        raise InfinityError("Request to Infinity server timed out")


async def async_handler(job: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main handler for RunPod serverless requests.

    Expected input format (OpenAI-compatible):
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

        if "input" in job_input:
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
            return {
                "error": "Invalid input format. Expected 'input', 'text', or 'image' field.",
                "details": "See handler documentation for correct format.",
            }

    except InfinityError as e:
        return {"error": str(e), "type": "InfinityError"}

    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}", "type": type(e).__name__}


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
