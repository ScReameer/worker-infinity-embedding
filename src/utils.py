"""Utility functions for the RunPod Infinity embedding handler."""

from typing import Any, Dict, List, Union, Optional


def detect_modality(input_data: Union[str, List[str]], explicit_modality: Optional[str] = None) -> str:
    """
    Detect the modality (text or image) for input data.
    
    Supports:
    - Explicit modality specification
    - Image URLs (http/https with image extensions)
    - Base64 images (data:image/...)
    - Arrays (checks first element)
    
    Args:
        input_data: Input data (string or list of strings)
        explicit_modality: Explicitly specified modality
        
    Returns:
        "image" or "text"
    """
    if explicit_modality:
        return explicit_modality
    
    def is_image_data(data: str) -> bool:
        """Check if a string represents image data."""
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
    
    if isinstance(input_data, str):
        return "image" if is_image_data(input_data) else "text"
    elif isinstance(input_data, list) and len(input_data) > 0:
        return "image" if is_image_data(input_data[0]) else "text"
    
    return "text"


def create_error_response(message: str, error_type: str = "BadRequestError", code: int = 400) -> Dict[str, Any]:
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
