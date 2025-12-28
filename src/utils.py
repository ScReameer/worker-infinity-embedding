import time
from http import HTTPStatus
from typing import Annotated, Any, Dict, Iterable, List, Literal, Optional, Union

import numpy as np
import numpy.typing as npt
from pydantic import BaseModel, Field, conlist

from typing import Any


def is_image_data(data: str) -> bool:
    """
    Check if a string represents image data.
    
    Args:
        data: String to check
        
    Returns:
        True if data is an image URL or base64 image
    """
    if not isinstance(data, str):
        return False
        
    # Base64 images
    if data.startswith("data:image/"):
        return True
        
    # Image URLs
    if data.startswith(("http://", "https://")):
        image_extensions = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg", ".tiff", ".ico"]
        return any(ext in data.lower() for ext in image_extensions)
    
    return False


def detect_modalities_per_item(input_data: list[str]) -> list[str]:
    """
    Detect modality for each item in the input list individually.
    
    This is used for mixed text/image inputs where each item may have different modality.
    
    Args:
        input_data: List of strings (text, URLs, or base64 images)
        
    Returns:
        List of modalities ("text" or "image") for each input item
    """
    return ["image" if is_image_data(item) else "text" for item in input_data]


def group_by_modality(input_data: list[str], modalities: list[str]) -> tuple[list[tuple[int, str]], list[tuple[int, str]]]:
    """
    Group input items by their modality, preserving original indices.
    
    Args:
        input_data: List of input strings
        modalities: List of modalities corresponding to input_data
        
    Returns:
        Tuple of (text_items, image_items) where each item is (original_index, data)
    """
    text_items = []
    image_items = []
    
    for idx, (data, modality) in enumerate(zip(input_data, modalities)):
        if modality == "image":
            image_items.append((idx, data))
        else:
            text_items.append((idx, data))
    
    return text_items, image_items


def create_error_response(message: str, error_type: str = "BadRequestError", code: int = 400) -> dict[str, Any]:
    """
    Create an OpenAI-compatible error response.
    
    Args:
        message: Error message
        error_type: Type of error
        code: HTTP status code
        
    Returns:
        Error response dictionary
    """
    return {
        "error": {
            "message": message,
            "type": error_type,
            "code": code
        }
    }
