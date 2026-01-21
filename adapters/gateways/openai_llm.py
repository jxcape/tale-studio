"""
OpenAI LLM Gateway adapter.

Implements LLMGateway interface using OpenAI API.
"""
import json
import re
from typing import Optional

import httpx

from usecases.interfaces import LLMGateway, LLMRequest, LLMResponse


class OpenAILLMGateway(LLMGateway):
    """
    OpenAI API adapter for LLM operations.

    Supports GPT-4o, GPT-4o-mini, and other OpenAI models.
    """

    OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        max_retries: int = 3,
        timeout: float = 60.0,
    ):
        self._api_key = api_key
        self._model = model
        self._max_retries = max_retries
        self._client = httpx.AsyncClient(
            timeout=timeout,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )

    async def complete(self, request: LLMRequest) -> LLMResponse:
        """Send completion request to OpenAI API."""
        messages = self._build_messages(request)

        response = await self._client.post(
            self.OPENAI_API_URL,
            json={
                "model": self._model,
                "messages": messages,
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
            },
        )
        response.raise_for_status()

        data = response.json()
        content = data["choices"][0]["message"]["content"]

        return LLMResponse(
            content=content,
            model=data["model"],
            usage=data.get("usage", {}),
        )

    async def complete_json(self, request: LLMRequest, schema: dict) -> dict:
        """
        Send completion request expecting JSON response.

        Retries on parse failure up to max_retries times.
        """
        for attempt in range(self._max_retries):
            response = await self.complete(request)
            try:
                return self._parse_json(response.content)
            except json.JSONDecodeError:
                if attempt == self._max_retries - 1:
                    raise
                # Retry with hint
                continue

        # Should not reach here, but just in case
        raise ValueError("Failed to get valid JSON response")

    def _build_messages(self, request: LLMRequest) -> list[dict]:
        """Build messages array for OpenAI API."""
        messages = []

        if request.system_prompt:
            messages.append({
                "role": "system",
                "content": request.system_prompt,
            })

        messages.append({
            "role": "user",
            "content": request.prompt,
        })

        return messages

    def _parse_json(self, content: str) -> dict:
        """
        Parse JSON from LLM response.

        Handles markdown code blocks wrapping.
        """
        # Try direct parse first
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        # Try extracting from markdown code block
        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", content)
        if json_match:
            return json.loads(json_match.group(1))

        # Re-raise original error
        raise json.JSONDecodeError("Failed to parse JSON", content, 0)

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()
