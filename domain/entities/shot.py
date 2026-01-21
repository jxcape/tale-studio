"""
Shot entity.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from domain.exceptions import DomainError
from domain.value_objects import Duration, GenerationMethod, ShotType


SHOT_ID_PATTERN = re.compile(r"^scene_(\d+)_shot_(\d+)$")


@dataclass
class Shot:
    """
    Shot entity representing a single camera take.

    A shot is a continuous piece of footage from a single camera angle.
    Multiple shots make up a scene.
    """

    id: str
    scene_id: str
    shot_type: ShotType
    duration: Duration
    purpose: str
    character_ids: list[str] = field(default_factory=list)
    generation_method: Optional[GenerationMethod] = None
    action_description: Optional[str] = None

    def __post_init__(self):
        """Validate shot after initialization."""
        match = SHOT_ID_PATTERN.match(self.id)
        if not match:
            raise DomainError(
                f"Invalid shot ID format: {self.id}. "
                "Expected format: scene_XX_shot_YY (e.g., scene_01_shot_01)"
            )

        # Validate scene_id matches shot ID
        shot_scene_id = f"scene_{match.group(1).zfill(2)}"
        if shot_scene_id != self.scene_id:
            raise DomainError(
                f"Shot ID {self.id} does not match scene_id {self.scene_id}. "
                f"Expected scene_id to be {shot_scene_id}"
            )

    @property
    def number(self) -> int:
        """Extract shot number from ID."""
        match = SHOT_ID_PATTERN.match(self.id)
        if match:
            return int(match.group(2))
        return 0

    @property
    def has_characters(self) -> bool:
        """Check if shot has character anchors."""
        return len(self.character_ids) > 0

    @property
    def effective_generation_method(self) -> GenerationMethod:
        """
        Get effective generation method.

        If explicitly set, use that. Otherwise, infer from content:
        - Shots with characters → I2V
        - Shots without characters → T2V
        """
        if self.generation_method is not None:
            return self.generation_method

        if self.has_characters:
            return GenerationMethod.I2V
        return GenerationMethod.T2V

    @property
    def requires_reference_image(self) -> bool:
        """Check if shot requires reference image for generation."""
        return self.effective_generation_method.requires_reference_image

    def __eq__(self, other: object) -> bool:
        """Shots are equal if they have the same ID."""
        if not isinstance(other, Shot):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        """Hash based on ID."""
        return hash(self.id)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "scene_id": self.scene_id,
            "shot_type": self.shot_type.value,
            "duration_seconds": self.duration.seconds,
            "purpose": self.purpose,
            "character_ids": self.character_ids,
            "generation_method": self.effective_generation_method.value,
            "action_description": self.action_description,
        }
