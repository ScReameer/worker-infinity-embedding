import base64
import io
import re
from PIL import Image


def _is_url(text: str) -> bool:
    """Check if string is a URL"""
    return text.startswith('http://') or text.startswith('https://')


def _is_base64_image(data: str) -> tuple[bool, Image.Image | None]:
    """
    Check if string is a base64-encoded image and decode it.
    Supports both data URI format (data:image/...) and raw base64.
    Returns (is_image, PIL_Image or None)
    """
    try:
        # Handle data URI format: data:image/png;base64,iVBORw0KG...
        if data.startswith('data:'):
            match = re.match(r'data:image/[^;]+;base64,(.+)', data)
            if match:
                base64_data = match.group(1)
            else:
                return False, None
        else:
            # Try raw base64
            base64_data = data
        
        img_bytes = base64.b64decode(base64_data)
        
        img = Image.open(io.BytesIO(img_bytes))
        img.load()  # Force load to validate it's a real image
        return True, img
    except Exception:
        
        return False, None


async def parse_input_item(item: str | bytes | Image.Image) -> tuple[str, str | Image.Image | bytes]:
    """
    Parse a single input item and determine if it's text or image.
    Returns: (type, processed_data)
    where type is 'text' or 'image'
    and processed_data is either the original text or PIL.Image/URL/bytes
    
    Note: infinity_emb handles URL downloading internally, so we just pass URLs through.
    """
    # Check if it's an image
    if isinstance(item, (Image.Image, bytes)):
        return 'image', item
    
    if isinstance(item, str):
        # URL images
        if _is_url(item):
            return 'image', item
        
        # Base64 images
        is_base64_img, img = _is_base64_image(item)
        if is_base64_img and img is not None:
            return 'image', img
    
    return 'text', item if isinstance(item, str) else str(item)
