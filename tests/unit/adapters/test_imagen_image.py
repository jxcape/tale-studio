"""
Tests for Imagen Image Generator adapter.
"""
import base64
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from pathlib import Path
import tempfile

from adapters.gateways.imagen_image import ImagenImageGenerator
from usecases.interfaces import ImageGenerator, ImageRequest, ImageResponse


class TestImagenImageGenerator:
    """Tests for Imagen Image Generator."""

    def test_implements_interface(self):
        """Should implement ImageGenerator interface."""
        generator = ImagenImageGenerator(api_key="test-key")
        assert isinstance(generator, ImageGenerator)

    @pytest.mark.asyncio
    async def test_generate_sends_request(self):
        """Should send generation request to Imagen API."""
        # Arrange
        generator = ImagenImageGenerator(api_key="test-key")
        request = ImageRequest(
            prompt="A cyberpunk laboratory with neon lights",
            size="1024x1024",
            quality="standard",
        )

        fake_image_base64 = base64.b64encode(b"fake-image-data").decode()
        mock_response = {
            "predictions": [
                {
                    "bytesBase64Encoded": fake_image_base64,
                }
            ]
        }

        with patch.object(generator, "_client") as mock_client:
            mock_client.post = AsyncMock(return_value=MagicMock(
                json=lambda: mock_response,
                raise_for_status=lambda: None,
            ))

            # Act
            response = await generator.generate(request)

            # Assert
            assert response.url.startswith("data:image/png;base64,")
            assert response.revised_prompt is None
            mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_uses_correct_endpoint(self):
        """Should use correct Gemini API endpoint."""
        # Arrange
        generator = ImagenImageGenerator(
            api_key="test-key",
            model="imagen-4.0-generate-001",
        )
        request = ImageRequest(prompt="Test prompt")

        fake_image_base64 = base64.b64encode(b"fake-image-data").decode()
        mock_response = {
            "predictions": [{"bytesBase64Encoded": fake_image_base64}]
        }

        with patch.object(generator, "_client") as mock_client:
            mock_client.post = AsyncMock(return_value=MagicMock(
                json=lambda: mock_response,
                raise_for_status=lambda: None,
            ))

            # Act
            await generator.generate(request)

            # Assert
            call_args = mock_client.post.call_args
            endpoint = call_args[0][0]
            assert "generativelanguage.googleapis.com" in endpoint
            assert "imagen-4.0-generate-001" in endpoint
            assert ":predict" in endpoint

    @pytest.mark.asyncio
    async def test_generate_includes_prompt(self):
        """Should include prompt in request payload."""
        # Arrange
        generator = ImagenImageGenerator(api_key="test-key")
        request = ImageRequest(prompt="A beautiful sunset")

        fake_image_base64 = base64.b64encode(b"fake-image-data").decode()
        mock_response = {
            "predictions": [{"bytesBase64Encoded": fake_image_base64}]
        }

        with patch.object(generator, "_client") as mock_client:
            mock_client.post = AsyncMock(return_value=MagicMock(
                json=lambda: mock_response,
                raise_for_status=lambda: None,
            ))

            # Act
            await generator.generate(request)

            # Assert
            call_args = mock_client.post.call_args
            request_body = call_args[1]["json"]
            assert request_body["instances"][0]["prompt"] == "A beautiful sunset"

    @pytest.mark.asyncio
    async def test_size_to_aspect_ratio(self):
        """Should convert size to aspect ratio."""
        generator = ImagenImageGenerator(api_key="test-key")

        # Test various sizes
        assert generator._size_to_aspect_ratio("1024x1024") == "1:1"
        assert generator._size_to_aspect_ratio("1792x1024") == "16:9"
        assert generator._size_to_aspect_ratio("1024x1792") == "9:16"
        assert generator._size_to_aspect_ratio("unknown") == "1:1"  # default

    @pytest.mark.asyncio
    async def test_download_base64_data_uri(self):
        """Should decode and save base64 data URI."""
        # Arrange
        generator = ImagenImageGenerator(api_key="test-key")
        image_content = b"\x89PNG\r\n\x1a\n..."  # Fake PNG header
        image_base64 = base64.b64encode(image_content).decode()
        data_uri = f"data:image/png;base64,{image_base64}"

        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = str(Path(tmpdir) / "test_image.png")

            # Act
            result_path = await generator.download(data_uri, save_path)

            # Assert
            assert result_path == save_path
            assert Path(save_path).exists()
            assert Path(save_path).read_bytes() == image_content

    @pytest.mark.asyncio
    async def test_download_regular_url(self):
        """Should download from regular URL."""
        # Arrange
        generator = ImagenImageGenerator(api_key="test-key")
        image_url = "https://example.com/image.png"
        image_content = b"\x89PNG\r\n\x1a\n..."

        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = str(Path(tmpdir) / "test_image.png")

            with patch.object(generator, "_client") as mock_client:
                mock_response = MagicMock()
                mock_response.content = image_content
                mock_response.raise_for_status = lambda: None
                mock_client.get = AsyncMock(return_value=mock_response)

                # Act
                result_path = await generator.download(image_url, save_path)

                # Assert
                assert result_path == save_path
                assert Path(save_path).exists()
                assert Path(save_path).read_bytes() == image_content

    @pytest.mark.asyncio
    async def test_raises_on_empty_predictions(self):
        """Should raise exception when no predictions returned."""
        # Arrange
        generator = ImagenImageGenerator(api_key="test-key")
        request = ImageRequest(prompt="Test")

        mock_response = {"predictions": []}

        with patch.object(generator, "_client") as mock_client:
            mock_client.post = AsyncMock(return_value=MagicMock(
                json=lambda: mock_response,
                raise_for_status=lambda: None,
            ))

            # Act & Assert
            with pytest.raises(RuntimeError) as exc_info:
                await generator.generate(request)

            assert "No image data" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_raises_on_api_error(self):
        """Should raise exception on API error."""
        # Arrange
        generator = ImagenImageGenerator(api_key="test-key")
        request = ImageRequest(prompt="Test")

        with patch.object(generator, "_client") as mock_client:
            mock_response = MagicMock()
            mock_response.raise_for_status.side_effect = Exception("API Error")
            mock_client.post = AsyncMock(return_value=mock_response)

            # Act & Assert
            with pytest.raises(Exception) as exc_info:
                await generator.generate(request)

            assert "API Error" in str(exc_info.value)
