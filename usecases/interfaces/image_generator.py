"""
Image Generator interface (Port).

For T2I reference image generation.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class ImageRequest:
    """Request for image generation."""

    prompt: str
    size: str = "1024x1024"
    quality: str = "standard"
    style: Optional[str] = None


@dataclass
class ImageResponse:
    """Response from image generation."""

    url: str
    revised_prompt: Optional[str] = None


class ImageGenerator(ABC):
    """
    Interface for T2I image generation.

    Implementations: DALL-E 3, Midjourney, etc.
    """

    @abstractmethod
    async def generate(self, request: ImageRequest) -> ImageResponse:
        """
        Generate an image from prompt.

        Args:
            request: Image generation request.

        Returns:
            Generated image URL.
        """
        pass

    @abstractmethod
    async def download(self, url: str, save_path: str) -> str:
        """
        Download image from URL to local path.

        Args:
            url: Image URL.
            save_path: Local path to save.

        Returns:
            Local file path.
        """
        pass
