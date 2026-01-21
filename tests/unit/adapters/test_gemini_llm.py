"""
Tests for Gemini LLM Gateway adapter.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from adapters.gateways.gemini_llm import GeminiLLMGateway
from usecases.interfaces import LLMGateway, LLMRequest, LLMResponse


class TestGeminiLLMGateway:
    """Tests for Gemini LLM Gateway."""

    def test_implements_interface(self):
        """Should implement LLMGateway interface."""
        gateway = GeminiLLMGateway(api_key="test-key")
        assert isinstance(gateway, LLMGateway)

    @pytest.mark.asyncio
    async def test_complete_sends_request(self):
        """Should send completion request to Gemini API."""
        # Arrange
        gateway = GeminiLLMGateway(api_key="test-key")
        request = LLMRequest(
            prompt="Describe a fantasy battle scene",
            temperature=0.7,
        )

        mock_response = {
            "candidates": [
                {
                    "content": {
                        "parts": [{"text": "A fierce dragon attacks the castle."}]
                    }
                }
            ],
            "usageMetadata": {
                "promptTokenCount": 10,
                "candidatesTokenCount": 20,
                "totalTokenCount": 30,
            },
        }

        with patch.object(gateway, "_client") as mock_client:
            mock_client.post = AsyncMock(return_value=MagicMock(
                json=lambda: mock_response,
                raise_for_status=lambda: None,
            ))

            # Act
            response = await gateway.complete(request)

            # Assert
            assert response.content == "A fierce dragon attacks the castle."
            assert response.usage["total_tokens"] == 30
            mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_complete_with_system_prompt(self):
        """Should include system instruction when provided."""
        # Arrange
        gateway = GeminiLLMGateway(api_key="test-key")
        request = LLMRequest(
            prompt="Create a scene",
            system_prompt="You are a cinematic director.",
            temperature=0.5,
        )

        mock_response = {
            "candidates": [
                {"content": {"parts": [{"text": "Scene description"}]}}
            ],
            "usageMetadata": {},
        }

        with patch.object(gateway, "_client") as mock_client:
            mock_client.post = AsyncMock(return_value=MagicMock(
                json=lambda: mock_response,
                raise_for_status=lambda: None,
            ))

            # Act
            await gateway.complete(request)

            # Assert
            call_args = mock_client.post.call_args
            payload = call_args[1]["json"]
            assert "systemInstruction" in payload
            assert payload["systemInstruction"]["parts"][0]["text"] == "You are a cinematic director."

    @pytest.mark.asyncio
    async def test_complete_uses_correct_endpoint(self):
        """Should use correct Gemini API endpoint."""
        # Arrange
        gateway = GeminiLLMGateway(
            api_key="test-key",
            model="gemini-2.0-flash",
        )
        request = LLMRequest(prompt="Test")

        mock_response = {
            "candidates": [{"content": {"parts": [{"text": "Response"}]}}],
            "usageMetadata": {},
        }

        with patch.object(gateway, "_client") as mock_client:
            mock_client.post = AsyncMock(return_value=MagicMock(
                json=lambda: mock_response,
                raise_for_status=lambda: None,
            ))

            # Act
            await gateway.complete(request)

            # Assert
            call_args = mock_client.post.call_args
            endpoint = call_args[0][0]
            assert "generativelanguage.googleapis.com" in endpoint
            assert "gemini-2.0-flash" in endpoint
            assert ":generateContent" in endpoint

    @pytest.mark.asyncio
    async def test_complete_json_parses_response(self):
        """Should parse JSON from response."""
        # Arrange
        gateway = GeminiLLMGateway(api_key="test-key")
        request = LLMRequest(prompt="Return JSON")

        mock_response = {
            "candidates": [
                {"content": {"parts": [{"text": '{"scene": "battle", "duration": 8}'}]}}
            ],
            "usageMetadata": {},
        }

        with patch.object(gateway, "_client") as mock_client:
            mock_client.post = AsyncMock(return_value=MagicMock(
                json=lambda: mock_response,
                raise_for_status=lambda: None,
            ))

            # Act
            result = await gateway.complete_json(request, schema={})

            # Assert
            assert result == {"scene": "battle", "duration": 8}

    @pytest.mark.asyncio
    async def test_complete_json_extracts_from_markdown(self):
        """Should extract JSON from markdown code block."""
        # Arrange
        gateway = GeminiLLMGateway(api_key="test-key")
        request = LLMRequest(prompt="Return JSON")

        mock_response = {
            "candidates": [
                {"content": {"parts": [{"text": '```json\n{"key": "value"}\n```'}]}}
            ],
            "usageMetadata": {},
        }

        with patch.object(gateway, "_client") as mock_client:
            mock_client.post = AsyncMock(return_value=MagicMock(
                json=lambda: mock_response,
                raise_for_status=lambda: None,
            ))

            # Act
            result = await gateway.complete_json(request, schema={})

            # Assert
            assert result == {"key": "value"}

    @pytest.mark.asyncio
    async def test_raises_on_empty_candidates(self):
        """Should raise exception when no candidates returned."""
        # Arrange
        gateway = GeminiLLMGateway(api_key="test-key")
        request = LLMRequest(prompt="Test")

        mock_response = {"candidates": []}

        with patch.object(gateway, "_client") as mock_client:
            mock_client.post = AsyncMock(return_value=MagicMock(
                json=lambda: mock_response,
                raise_for_status=lambda: None,
            ))

            # Act & Assert
            with pytest.raises(RuntimeError) as exc_info:
                await gateway.complete(request)

            assert "No candidates" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_multiple_parts_concatenated(self):
        """Should concatenate multiple parts in response."""
        # Arrange
        gateway = GeminiLLMGateway(api_key="test-key")
        request = LLMRequest(prompt="Test")

        mock_response = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"text": "First part. "},
                            {"text": "Second part."},
                        ]
                    }
                }
            ],
            "usageMetadata": {},
        }

        with patch.object(gateway, "_client") as mock_client:
            mock_client.post = AsyncMock(return_value=MagicMock(
                json=lambda: mock_response,
                raise_for_status=lambda: None,
            ))

            # Act
            response = await gateway.complete(request)

            # Assert
            assert response.content == "First part. Second part."
