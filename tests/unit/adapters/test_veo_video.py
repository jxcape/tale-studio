"""
Tests for Veo Video Generator adapter.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from pathlib import Path
import tempfile
import asyncio

from adapters.gateways.veo_video import VeoVideoGenerator
from usecases.interfaces import VideoGenerator, VideoRequest, VideoJob, VideoStatus


class TestVeoVideoGenerator:
    """Tests for Veo Video Generator."""

    def test_implements_interface(self):
        """Should implement VideoGenerator interface."""
        generator = VeoVideoGenerator(api_key="test-key")
        assert isinstance(generator, VideoGenerator)

    @pytest.mark.asyncio
    async def test_generate_t2v_starts_job(self):
        """Should start T2V generation job."""
        # Arrange
        generator = VeoVideoGenerator(api_key="test-key")
        request = VideoRequest(
            prompt="A scientist working in a laboratory",
            duration_seconds=5.0,
        )

        mock_response = {
            "name": "projects/test-project/locations/us-central1/operations/op-12345",
        }

        with patch.object(generator, "_client") as mock_client:
            mock_client.post = AsyncMock(return_value=MagicMock(
                json=lambda: mock_response,
                raise_for_status=lambda: None,
            ))

            # Act
            job = await generator.generate(request)

            # Assert
            assert job.job_id == "projects/test-project/locations/us-central1/operations/op-12345"
            assert job.status == VideoStatus.PROCESSING
            mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_i2v_includes_image(self):
        """Should include reference image for I2V generation."""
        # Arrange
        generator = VeoVideoGenerator(api_key="test-key")

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            f.write(b"\x89PNG\r\n\x1a\n...")
            image_path = f.name

        request = VideoRequest(
            prompt="Dr. Kim looks at the camera",
            duration_seconds=5.0,
            reference_image_path=image_path,
        )

        mock_response = {
            "name": "projects/test-project/locations/us-central1/operations/op-67890",
        }

        with patch.object(generator, "_client") as mock_client:
            mock_client.post = AsyncMock(return_value=MagicMock(
                json=lambda: mock_response,
                raise_for_status=lambda: None,
            ))

            # Act
            job = await generator.generate(request)

            # Assert
            assert job.job_id == "projects/test-project/locations/us-central1/operations/op-67890"
            call_args = mock_client.post.call_args
            request_body = call_args[1]["json"]
            # Image should be in instances[0]
            assert "image" in request_body["instances"][0]

        # Cleanup
        Path(image_path).unlink()

    @pytest.mark.asyncio
    async def test_get_status_processing(self):
        """Should return processing status for ongoing job."""
        # Arrange
        generator = VeoVideoGenerator(api_key="test-key")

        mock_response = {
            "name": "projects/test-project/locations/us-central1/operations/op-12345",
            "done": False,
            "metadata": {"progress": 50},
        }

        with patch.object(generator, "_client") as mock_client:
            mock_client.get = AsyncMock(return_value=MagicMock(
                json=lambda: mock_response,
                raise_for_status=lambda: None,
            ))

            # Act
            job = await generator.get_status("op-12345")

            # Assert
            assert job.status == VideoStatus.PROCESSING
            assert job.progress == 50

    @pytest.mark.asyncio
    async def test_get_status_completed(self):
        """Should return completed status with video URL."""
        # Arrange
        generator = VeoVideoGenerator(api_key="test-key")

        mock_response = {
            "name": "projects/test-project/locations/us-central1/operations/op-12345",
            "done": True,
            "response": {
                "generatedSamples": [
                    {"video": {"uri": "gs://bucket/video.mp4"}}
                ]
            },
        }

        with patch.object(generator, "_client") as mock_client:
            mock_client.get = AsyncMock(return_value=MagicMock(
                json=lambda: mock_response,
                raise_for_status=lambda: None,
            ))

            # Act
            job = await generator.get_status("op-12345")

            # Assert
            assert job.status == VideoStatus.COMPLETED
            assert job.video_url is not None

    @pytest.mark.asyncio
    async def test_get_status_failed(self):
        """Should return failed status with error message."""
        # Arrange
        generator = VeoVideoGenerator(api_key="test-key")

        mock_response = {
            "name": "projects/test-project/locations/us-central1/operations/op-12345",
            "done": True,
            "error": {"message": "Content policy violation"},
        }

        with patch.object(generator, "_client") as mock_client:
            mock_client.get = AsyncMock(return_value=MagicMock(
                json=lambda: mock_response,
                raise_for_status=lambda: None,
            ))

            # Act
            job = await generator.get_status("op-12345")

            # Assert
            assert job.status == VideoStatus.FAILED
            assert "policy" in job.error_message.lower()

    @pytest.mark.asyncio
    async def test_wait_for_completion_success(self):
        """Should poll until job completes."""
        # Arrange
        generator = VeoVideoGenerator(
            api_key="test-key",
            poll_interval=0.01,  # Fast polling for test
        )

        responses = [
            {"done": False, "metadata": {"progress": 30}},
            {"done": False, "metadata": {"progress": 70}},
            {"done": True, "response": {"generatedSamples": [{"video": {"uri": "gs://bucket/video.mp4"}}]}},
        ]
        call_count = 0

        def get_response():
            nonlocal call_count
            resp = responses[min(call_count, len(responses) - 1)]
            call_count += 1
            return MagicMock(json=lambda: resp, raise_for_status=lambda: None)

        with patch.object(generator, "_client") as mock_client:
            mock_client.get = AsyncMock(side_effect=lambda *a, **k: get_response())

            # Act
            job = await generator.wait_for_completion("op-12345", timeout_seconds=1)

            # Assert
            assert job.status == VideoStatus.COMPLETED
            assert mock_client.get.call_count == 3

    @pytest.mark.asyncio
    async def test_wait_for_completion_timeout(self):
        """Should raise TimeoutError when job takes too long."""
        # Arrange
        generator = VeoVideoGenerator(
            api_key="test-key",
            poll_interval=0.1,
        )

        mock_response = {"done": False, "metadata": {"progress": 10}}

        with patch.object(generator, "_client") as mock_client:
            mock_client.get = AsyncMock(return_value=MagicMock(
                json=lambda: mock_response,
                raise_for_status=lambda: None,
            ))

            # Act & Assert
            with pytest.raises(TimeoutError):
                await generator.wait_for_completion("op-12345", timeout_seconds=0.2)

    @pytest.mark.asyncio
    async def test_download_saves_video(self):
        """Should download video to specified path."""
        # Arrange
        generator = VeoVideoGenerator(api_key="test-key")
        video_url = "https://storage.googleapis.com/bucket/video.mp4"
        video_content = b"fake video content"

        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = str(Path(tmpdir) / "test_video.mp4")

            mock_response = MagicMock()
            mock_response.content = video_content
            mock_response.raise_for_status = lambda: None

            # Mock the httpx.AsyncClient context manager
            mock_client_instance = AsyncMock()
            mock_client_instance.get = AsyncMock(return_value=mock_response)
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=None)

            with patch("httpx.AsyncClient", return_value=mock_client_instance):
                # Act
                result_path = await generator.download(video_url, save_path)

                # Assert
                assert result_path == save_path
                assert Path(save_path).exists()
                assert Path(save_path).read_bytes() == video_content
