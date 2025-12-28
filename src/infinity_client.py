"""Client for communicating with Infinity embedding server."""

import asyncio
from typing import Any

import httpx


class InfinityError(Exception):
    """Custom exception for Infinity-related errors."""
    pass


class InfinityClient:
    """Client for Infinity embedding API."""
    
    def __init__(self, host: str, port: str):
        """
        Initialize Infinity client.
        
        Args:
            host: Infinity server host
            port: Infinity server port
        """
        self.base_url = f"http://{host}:{port}"
    
    async def get_embeddings(
        self,
        input_data: str | list[str],
        model: str,
        modality: str = "text"
    ) -> dict[str, Any]:
        """
        Get embeddings from Infinity server.
        
        Args:
            input_data: Text string(s) or image URL(s) to embed
            model: Model name to use
            modality: "text" or "image"
            
        Returns:
            OpenAI-compatible embeddings response
            
        Raises:
            InfinityError: If the request fails
        """
        url = f"{self.base_url}/embeddings"
        
        payload = {
            "model": model,
            "input": input_data,
            "encoding_format": "float"
        }
        
        if modality == "image":
            payload["modality"] = modality
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(url, json=payload)
                
                if not response.is_success:
                    raise InfinityError(
                        f"Infinity API error ({response.status_code}): {response.text}"
                    )
                
                return response.json()
                
        except httpx.HTTPError as e:
            raise InfinityError(f"Failed to connect to Infinity server: {e}")
        except asyncio.TimeoutError:
            raise InfinityError("Request to Infinity server timed out")
    
    async def get_embeddings_mixed(
        self,
        input_data: list[str],
        model: str,
        modalities: list[str]
    ) -> dict[str, Any]:
        """
        Get embeddings for mixed text/image inputs.
        
        Groups inputs by modality, makes separate requests, and merges results
        in the original order.
        
        Args:
            input_data: List of text strings or image URLs
            model: Model name to use
            modalities: List of modalities ("text" or "image") for each input
            
        Returns:
            OpenAI-compatible embeddings response with embeddings in original order
            
        Raises:
            InfinityError: If any request fails
        """
        if len(input_data) != len(modalities):
            raise InfinityError("input_data and modalities must have same length")
        
        # Group items by modality in single pass
        text_items: list[tuple[int, str]] = []
        image_items: list[tuple[int, str]] = []
        
        for idx, (data, mod) in enumerate(zip(input_data, modalities)):
            if mod == "image":
                image_items.append((idx, data))
            else:
                text_items.append((idx, data))
        
        tasks = []
        task_metadata: list[tuple[str, list[int]]] = []
        
        if text_items:
            indices, texts = zip(*text_items)
            tasks.append(self.get_embeddings(list(texts), model, "text"))
            task_metadata.append(("text", list(indices)))
        
        if image_items:
            indices, images = zip(*image_items)
            tasks.append(self.get_embeddings(list(images), model, "image"))
            task_metadata.append(("image", list(indices)))
        
        results = await asyncio.gather(*tasks)
        
        merged_embeddings: list[dict[str, Any]] = [{}] * len(input_data)
        
        for result, (modality, indices) in zip(results, task_metadata):
            for result_idx, original_idx in enumerate(indices):
                embedding_data = result["data"][result_idx].copy()
                embedding_data["index"] = original_idx
                merged_embeddings[original_idx] = embedding_data
        
        return {
            "object": "list",
            "data": merged_embeddings,
            "model": model,
            "usage": {
                "prompt_tokens": len(input_data),
                "total_tokens": len(input_data)
            }
        }
