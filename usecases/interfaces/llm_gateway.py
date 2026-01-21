"""
LLM Gateway interface (Port).

UseCase layer depends on this interface, not concrete implementations.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class LLMRequest:
    """Request to LLM."""

    prompt: str
    system_prompt: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2000


@dataclass
class LLMResponse:
    """Response from LLM."""

    content: str
    model: str
    usage: dict


class LLMGateway(ABC):
    """
    Interface for LLM operations.

    Implementations: OpenAI GPT, Claude, etc.
    """

    @abstractmethod
    async def complete(self, request: LLMRequest) -> LLMResponse:
        """
        Send a completion request to LLM.

        Args:
            request: LLM request with prompt and parameters.

        Returns:
            LLM response with generated content.
        """
        pass

    @abstractmethod
    async def complete_json(self, request: LLMRequest, schema: dict) -> dict:
        """
        Send a completion request expecting JSON response.

        Args:
            request: LLM request.
            schema: Expected JSON schema for validation.

        Returns:
            Parsed JSON response.
        """
        pass
