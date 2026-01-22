"""
Gemini LLM Gateway adapter.

Implements LLMGateway interface using Google Gemini API.
Supports APIKeyPool for automatic failover on 429 errors.
"""
import json
import re
import logging
from typing import Optional, TYPE_CHECKING

import httpx

from usecases.interfaces import LLMGateway, LLMRequest, LLMResponse

if TYPE_CHECKING:
    from infrastructure.api_key_pool import APIKeyPool

logger = logging.getLogger(__name__)


class GeminiLLMGateway(LLMGateway):
    """
    Google Gemini API adapter for LLM operations.

    Supports Gemini 2.0 Flash, 1.5 Pro, etc.
    Uses APIKeyPool for automatic key rotation and failover on 429 errors.
    """

    GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"

    def __init__(
        self,
        api_key: Optional[str] = None,
        key_pool: Optional["APIKeyPool"] = None,
        model: str = "gemini-2.0-flash",
        max_retries: int = 3,
        timeout: float = 60.0,
    ):
        """
        Initialize Gemini LLM gateway.

        Args:
            api_key: Single Google AI Studio API key (legacy, use key_pool instead).
            key_pool: APIKeyPool for automatic key rotation and failover.
            model: Model to use. Options:
                - gemini-2.0-flash (fast, recommended)
                - gemini-2.0-flash-lite (faster, cheaper)
                - gemini-1.5-pro (high quality)
                - gemini-1.5-flash (balanced)
            max_retries: Max retries for JSON parsing / API errors.
            timeout: HTTP request timeout.

        Note:
            Either api_key or key_pool must be provided.
            If both provided, key_pool takes precedence.
        """
        if not api_key and not key_pool:
            raise ValueError("Either api_key or key_pool must be provided")

        self._api_key = api_key
        self._key_pool = key_pool
        self._model = model
        self._max_retries = max_retries
        self._client = httpx.AsyncClient(
            timeout=timeout,
            headers={
                "Content-Type": "application/json",
            },
        )

    def _url(self, path: str, api_key: str) -> str:
        """Build URL with API key."""
        return f"{self.GEMINI_API_BASE}{path}?key={api_key}"

    async def complete(self, request: LLMRequest) -> LLMResponse:
        """Send completion request to Gemini API with automatic failover."""
        if self._key_pool:
            return await self._complete_with_pool(request)
        else:
            return await self._complete_single_key(request, self._api_key)

    async def _complete_with_pool(self, request: LLMRequest) -> LLMResponse:
        """Execute request with APIKeyPool for automatic failover on 429."""

        async def operation(api_key: str) -> LLMResponse:
            return await self._complete_single_key(request, api_key)

        return await self._key_pool.execute_with_retry(
            operation,
            max_retries=self._max_retries,
            on_success=self._key_pool.mark_used,
        )

    async def _complete_single_key(self, request: LLMRequest, api_key: str) -> LLMResponse:
        """Send completion request with a single API key."""
        contents = self._build_contents(request)

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": request.temperature,
                "maxOutputTokens": request.max_tokens,
            },
        }

        # Add system instruction if provided
        if request.system_prompt:
            payload["systemInstruction"] = {
                "parts": [{"text": request.system_prompt}]
            }

        endpoint = self._url(f"/models/{self._model}:generateContent", api_key)

        alias = self._key_pool.get_alias(api_key) if self._key_pool else "single"
        logger.info(f"[{alias}] Calling Gemini {self._model}...")

        response = await self._client.post(endpoint, json=payload)
        response.raise_for_status()

        data = response.json()

        # Extract content from response
        candidates = data.get("candidates", [])
        if not candidates:
            raise RuntimeError(f"No candidates in Gemini response: {data}")

        content = candidates[0].get("content", {})
        parts = content.get("parts", [])
        text = "".join(part.get("text", "") for part in parts)

        # Extract usage metadata
        usage_metadata = data.get("usageMetadata", {})
        usage = {
            "prompt_tokens": usage_metadata.get("promptTokenCount", 0),
            "completion_tokens": usage_metadata.get("candidatesTokenCount", 0),
            "total_tokens": usage_metadata.get("totalTokenCount", 0),
        }

        logger.info(f"[{alias}] Success. Tokens: {usage['total_tokens']}")

        return LLMResponse(
            content=text,
            model=self._model,
            usage=usage,
        )

    async def complete_json(self, request: LLMRequest, schema: dict) -> dict:
        """
        Send completion request expecting JSON response.

        Retries on parse failure up to max_retries times.
        """
        # Add JSON instruction to prompt
        json_request = LLMRequest(
            prompt=request.prompt + "\n\nRespond with valid JSON only.",
            system_prompt=request.system_prompt,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )

        for attempt in range(self._max_retries):
            response = await self.complete(json_request)
            try:
                return self._parse_json(response.content)
            except json.JSONDecodeError:
                if attempt == self._max_retries - 1:
                    raise
                continue

        raise ValueError("Failed to get valid JSON response")

    def _build_contents(self, request: LLMRequest) -> list[dict]:
        """Build contents array for Gemini API."""
        return [
            {
                "role": "user",
                "parts": [{"text": request.prompt}],
            }
        ]

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
