"""
Video Generator interface (Port).

For T2V and I2V video generation.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class VideoStatus(Enum):
    """Status of video generation job."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class VideoRequest:
    """Request for video generation."""

    prompt: str
    duration_seconds: float = 5.0
    reference_image_path: Optional[str] = None  # For I2V
    aspect_ratio: str = "16:9"


@dataclass
class VideoJob:
    """Video generation job status."""

    job_id: str
    status: VideoStatus
    progress: float = 0.0  # 0-100
    video_url: Optional[str] = None
    error_message: Optional[str] = None


class VideoGenerator(ABC):
    """
    Interface for T2V/I2V video generation.

    Implementations: Veo, Sora, Runway, etc.
    """

    @abstractmethod
    async def generate(self, request: VideoRequest) -> VideoJob:
        """
        Start video generation job.

        Args:
            request: Video generation request.

        Returns:
            Job with initial status (usually pending/processing).
        """
        pass

    @abstractmethod
    async def get_status(self, job_id: str) -> VideoJob:
        """
        Get status of video generation job.

        Args:
            job_id: Job ID from generate().

        Returns:
            Current job status.
        """
        pass

    @abstractmethod
    async def wait_for_completion(
        self, job_id: str, timeout_seconds: float = 300
    ) -> VideoJob:
        """
        Wait for job to complete.

        Args:
            job_id: Job ID.
            timeout_seconds: Maximum wait time.

        Returns:
            Final job status.

        Raises:
            TimeoutError: If job doesn't complete in time.
        """
        pass

    @abstractmethod
    async def download(self, video_url: str, save_path: str) -> str:
        """
        Download video from URL to local path.

        Args:
            video_url: Video URL.
            save_path: Local path to save.

        Returns:
            Local file path.
        """
        pass
