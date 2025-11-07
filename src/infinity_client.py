"""Client for communicating with Infinity embedding server."""

import asyncio
from typing import Any, Dict, List, Union

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
        input_data: Union[str, List[str]],
        model: str,
        modality: str = "text"
    ) -> Dict[str, Any]:
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
                
                if response.status_code != 200:
                    raise InfinityError(
                        f"Infinity API error ({response.status_code}): {response.text}"
                    )
                
                return response.json()
                
        except httpx.HTTPError as e:
            raise InfinityError(f"Failed to connect to Infinity server: {e}")
        except asyncio.TimeoutError:
            raise InfinityError("Request to Infinity server timed out")
