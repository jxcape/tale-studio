"""
SceneType value object.
"""
from __future__ import annotations

from enum import Enum

from domain.exceptions import InvalidSceneTypeError


class SceneType(Enum):
    """Type of scene in the story."""

    DIALOGUE = "dialogue"
    ACTION = "action"
    MONOLOGUE = "monologue"
    ATMOSPHERE = "atmosphere"

    @classmethod
    def from_string(cls, value: str) -> SceneType:
        """Create SceneType from string."""
        normalized = value.lower().strip()
        for scene_type in cls:
            if scene_type.value == normalized:
                return scene_type
        raise InvalidSceneTypeError(
            f"Invalid scene type: {value}. "
            f"Valid types: {[t.value for t in cls]}"
        )
