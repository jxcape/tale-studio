"""
Tests for OpenAI LLM Gateway adapter.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import json

from adapters.gateways.openai_llm import OpenAILLMGateway
from usecases.interfaces import LLMGateway, LLMRequest, LLMResponse


class TestOpenAILLMGateway:
    """Tests for OpenAI LLM Gateway."""

    def test_implements_interface(self):
        """Should implement LLMGateway interface."""
        gateway = OpenAILLMGateway(api_key="test-key")
        assert isinstance(gateway, LLMGateway)

    @pytest.mark.asyncio
    async def test_complete_sends_request(self):
        """Should send completion request to OpenAI API."""
        # Arrange
        gateway = OpenAILLMGateway(api_key="test-key")
        request = LLMRequest(
            prompt="Hello, world!",
            temperature=0.5,
            max_tokens=100,
        )

        mock_response = {
            "choices": [{"message": {"content": "Hello! How can I help you?"}}],
            "model": "gpt-4o-mini",
            "usage": {"prompt_tokens": 10, "completion_tokens": 8, "total_tokens": 18},
        }

        with patch.object(gateway, "_client") as mock_client:
            mock_client.post = AsyncMock(return_value=MagicMock(
                json=lambda: mock_response,
                raise_for_status=lambda: None,
            ))

            # Act
            response = await gateway.complete(request)

            # Assert
            assert response.content == "Hello! How can I help you?"
            assert response.model == "gpt-4o-mini"
            mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_complete_with_system_prompt(self):
        """Should include system prompt in messages."""
        # Arrange
        gateway = OpenAILLMGateway(api_key="test-key")
        request = LLMRequest(
            prompt="Analyze this scene",
            system_prompt="You are a cinematographer",
            temperature=0.7,
        )

        mock_response = {
            "choices": [{"message": {"content": "Analysis result"}}],
            "model": "gpt-4o-mini",
            "usage": {"prompt_tokens": 20, "completion_tokens": 5, "total_tokens": 25},
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
            request_body = call_args[1]["json"]
            messages = request_body["messages"]

            # Should have system and user messages
            assert len(messages) == 2
            assert messages[0]["role"] == "system"
            assert messages[1]["role"] == "user"

    @pytest.mark.asyncio
    async def test_complete_json_parses_response(self):
        """Should parse JSON from LLM response."""
        # Arrange
        gateway = OpenAILLMGateway(api_key="test-key")
        request = LLMRequest(
            prompt="Return scenes as JSON",
            temperature=0.5,
        )
        schema = {"type": "object", "properties": {"scenes": {"type": "array"}}}

        json_content = {"scenes": [{"id": "scene_01", "type": "dialogue"}]}
        mock_response = {
            "choices": [{"message": {"content": json.dumps(json_content)}}],
            "model": "gpt-4o-mini",
            "usage": {"prompt_tokens": 15, "completion_tokens": 20, "total_tokens": 35},
        }

        with patch.object(gateway, "_client") as mock_client:
            mock_client.post = AsyncMock(return_value=MagicMock(
                json=lambda: mock_response,
                raise_for_status=lambda: None,
            ))

            # Act
            result = await gateway.complete_json(request, schema)

            # Assert
            assert result == json_content
            assert result["scenes"][0]["id"] == "scene_01"

    @pytest.mark.asyncio
    async def test_complete_json_handles_markdown_wrapped(self):
        """Should handle JSON wrapped in markdown code blocks."""
        # Arrange
        gateway = OpenAILLMGateway(api_key="test-key")
        request = LLMRequest(prompt="Return JSON")
        schema = {"type": "object"}

        json_content = {"key": "value"}
        wrapped_content = f"```json\n{json.dumps(json_content)}\n```"
        mock_response = {
            "choices": [{"message": {"content": wrapped_content}}],
            "model": "gpt-4o-mini",
            "usage": {"prompt_tokens": 10, "completion_tokens": 15, "total_tokens": 25},
        }

        with patch.object(gateway, "_client") as mock_client:
            mock_client.post = AsyncMock(return_value=MagicMock(
                json=lambda: mock_response,
                raise_for_status=lambda: None,
            ))

            # Act
            result = await gateway.complete_json(request, schema)

            # Assert
            assert result == json_content

    @pytest.mark.asyncio
    async def test_uses_custom_model(self):
        """Should use custom model when specified."""
        # Arrange
        gateway = OpenAILLMGateway(api_key="test-key", model="gpt-4o")
        request = LLMRequest(prompt="Test")

        mock_response = {
            "choices": [{"message": {"content": "Response"}}],
            "model": "gpt-4o",
            "usage": {"prompt_tokens": 5, "completion_tokens": 5, "total_tokens": 10},
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
            request_body = call_args[1]["json"]
            assert request_body["model"] == "gpt-4o"

    @pytest.mark.asyncio
    async def test_raises_on_api_error(self):
        """Should raise exception on API error."""
        # Arrange
        gateway = OpenAILLMGateway(api_key="test-key")
        request = LLMRequest(prompt="Test")

        with patch.object(gateway, "_client") as mock_client:
            mock_response = MagicMock()
            mock_response.raise_for_status.side_effect = Exception("API Error")
            mock_client.post = AsyncMock(return_value=mock_response)

            # Act & Assert
            with pytest.raises(Exception) as exc_info:
                await gateway.complete(request)

            assert "API Error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_complete_json_retries_on_invalid_json(self):
        """Should retry when JSON parsing fails."""
        # Arrange
        gateway = OpenAILLMGateway(api_key="test-key", max_retries=2)
        request = LLMRequest(prompt="Return JSON")
        schema = {"type": "object"}

        # First response: invalid JSON, second: valid
        responses = [
            {"choices": [{"message": {"content": "not valid json"}}],
             "model": "gpt-4o-mini", "usage": {}},
            {"choices": [{"message": {"content": '{"valid": true}'}}],
             "model": "gpt-4o-mini", "usage": {}},
        ]
        call_count = 0

        def get_response():
            nonlocal call_count
            resp = responses[min(call_count, len(responses) - 1)]
            call_count += 1
            return MagicMock(json=lambda: resp, raise_for_status=lambda: None)

        with patch.object(gateway, "_client") as mock_client:
            mock_client.post = AsyncMock(side_effect=lambda *a, **k: get_response())

            # Act
            result = await gateway.complete_json(request, schema)

            # Assert
            assert result == {"valid": True}
            assert mock_client.post.call_count == 2
