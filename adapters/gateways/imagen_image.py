"""
Imagen Image Generator adapter.

Implements ImageGenerator interface using Google Imagen API (Gemini API).
"""
import base64
from pathlib import Path
from typing import Optional

import httpx

from usecases.interfaces import ImageGenerator, ImageRequest, ImageResponse


class ImagenImageGenerator(ImageGenerator):
    """
    Google Imagen adapter for image generation via Gemini API.

    Used for T2I reference image generation.
    No project_id required - uses API key only.
    """

    GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"

    def __init__(
        self,
        api_key: str,
        model: str = "imagen-4.0-generate-001",
        timeout: float = 120.0,
    ):
        """
        Initialize Imagen generator.

        Args:
            api_key: Google AI Studio API key.
            model: Imagen model to use. Options:
                - imagen-4.0-generate-001
                - imagen-4.0-ultra-generate-001 (higher quality)
                - imagen-4.0-fast-generate-001 (faster)
            timeout: HTTP request timeout.
        """
        self._api_key = api_key
        self._model = model
        self._client = httpx.AsyncClient(
            timeout=timeout,
            headers={
                "Content-Type": "application/json",
            },
        )

    def _url(self, path: str) -> str:
        """Build URL with API key."""
        return f"{self.GEMINI_API_BASE}{path}?key={self._api_key}"

    async def generate(self, request: ImageRequest) -> ImageResponse:
        """Generate an image using Imagen."""
        # Parse size to aspect ratio
        aspect_ratio = self._size_to_aspect_ratio(request.size)

        payload = {
            "instances": [
                {
                    "prompt": request.prompt,
                }
            ],
            "parameters": {
                "sampleCount": 1,
                "aspectRatio": aspect_ratio,
            },
        }

        endpoint = self._url(f"/models/{self._model}:predict")

        response = await self._client.post(endpoint, json=payload)
        response.raise_for_status()

        data = response.json()

        # Try different response formats
        image_base64 = None

        # Format 1: predictions array
        predictions = data.get("predictions", [])
        if predictions:
            image_base64 = predictions[0].get("bytesBase64Encoded")

        # Format 2: images array
        if not image_base64:
            images = data.get("images", [])
            if images:
                image_base64 = images[0].get("bytesBase64Encoded")

        # Format 3: generatedImages array
        if not image_base64:
            generated = data.get("generatedImages", [])
            if generated:
                image_base64 = generated[0].get("image", {}).get("bytesBase64Encoded")

        if not image_base64:
            raise RuntimeError(f"No image data in Imagen response: {data.keys()}")

        # Store base64 data for later download
        # We use a data URI as a pseudo-URL
        data_uri = f"data:image/png;base64,{image_base64}"

        return ImageResponse(
            url=data_uri,
            revised_prompt=None,  # Imagen doesn't return revised prompt
        )

    async def download(self, url: str, save_path: str) -> str:
        """Download image from URL to local path."""
        path = Path(save_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        # Handle base64 data URI
        if url.startswith("data:"):
            # Parse data URI: data:image/png;base64,<data>
            _, encoded = url.split(",", 1)
            image_bytes = base64.b64decode(encoded)
            path.write_bytes(image_bytes)
        else:
            # Handle regular URL
            response = await self._client.get(url)
            response.raise_for_status()
            path.write_bytes(response.content)

        return str(path)

    def _size_to_aspect_ratio(self, size: str) -> str:
        """Convert size string to Imagen aspect ratio."""
        # Imagen supports: 1:1, 3:4, 4:3, 9:16, 16:9
        size_mapping = {
            "1024x1024": "1:1",
            "1792x1024": "16:9",
            "1024x1792": "9:16",
            "1536x1024": "3:2",
            "1024x1536": "2:3",
        }
        return size_mapping.get(size, "1:1")

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()
