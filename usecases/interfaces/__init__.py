"""
UseCase interfaces (Ports).

These are the abstractions that UseCase layer depends on.
Adapters implement these interfaces.
"""
from usecases.interfaces.asset_repository import AssetRepository
from usecases.interfaces.image_generator import (
    ImageGenerator,
    ImageRequest,
    ImageResponse,
)
from usecases.interfaces.llm_gateway import LLMGateway, LLMRequest, LLMResponse
from usecases.interfaces.video_generator import (
    VideoGenerator,
    VideoJob,
    VideoRequest,
    VideoStatus,
)

__all__ = [
    "AssetRepository",
    "ImageGenerator",
    "ImageRequest",
    "ImageResponse",
    "LLMGateway",
    "LLMRequest",
    "LLMResponse",
    "VideoGenerator",
    "VideoJob",
    "VideoRequest",
    "VideoStatus",
]
