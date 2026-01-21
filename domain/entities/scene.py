"""
Scene entity.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from domain.exceptions import DomainError
from domain.value_objects import Duration, GenerationMethod, SceneType


class Act(Enum):
    """Story act structure."""

    BEGINNING = "beginning"
    MIDDLE = "middle"
    END = "end"

    @property
    def percentage(self) -> float:
        """Get expected percentage of total runtime."""
        percentages = {
            Act.BEGINNING: 0.25,
            Act.MIDDLE: 0.50,
            Act.END: 0.25,
        }
        return percentages[self]


SCENE_ID_PATTERN = re.compile(r"^scene_(\d+)$")


@dataclass
class Scene:
    """
    Scene entity representing a segment of the story.

    A scene is a continuous sequence of action in a single location.
    It contains one or more shots.
    """

    id: str
    scene_type: SceneType
    duration: Duration
    act: Act
    narrative_summary: str
    character_ids: list[str] = field(default_factory=list)
    location_id: Optional[str] = None
    original_text: Optional[str] = None  # Preserved quotes/phrases from original story

    def __post_init__(self):
        """Validate scene after initialization."""
        if not SCENE_ID_PATTERN.match(self.id):
            raise DomainError(
                f"Invalid scene ID format: {self.id}. "
                "Expected format: scene_XX (e.g., scene_01)"
            )

    @property
    def number(self) -> int:
        """Extract scene number from ID."""
        match = SCENE_ID_PATTERN.match(self.id)
        if match:
            return int(match.group(1))
        return 0

    @property
    def has_characters(self) -> bool:
        """Check if scene has character references."""
        return len(self.character_ids) > 0

    @property
    def suggested_generation_method(self) -> GenerationMethod:
        """Suggest generation method based on scene content."""
        if self.has_characters:
            return GenerationMethod.I2V
        return GenerationMethod.T2V

    def __eq__(self, other: object) -> bool:
        """Scenes are equal if they have the same ID."""
        if not isinstance(other, Scene):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        """Hash based on ID."""
        return hash(self.id)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "scene_type": self.scene_type.value,
            "duration_seconds": self.duration.seconds,
            "act": self.act.value,
            "narrative_summary": self.narrative_summary,
            "character_ids": self.character_ids,
            "location_id": self.location_id,
            "original_text": self.original_text,
        }
