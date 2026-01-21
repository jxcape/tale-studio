"""
Character entity.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from domain.exceptions import DomainError


class ReferenceAngle(Enum):
    """Angle of character reference image."""

    FRONT = "front"
    SIDE = "side"
    THREE_QUARTER = "three_quarter"


VALID_GENDERS = {"male", "female", "non-binary", "other"}


@dataclass(frozen=True)
class ReferenceImage:
    """Reference image for character consistency."""

    angle: ReferenceAngle
    path: str

    @property
    def filename(self) -> str:
        """Get filename from path."""
        return os.path.basename(self.path)


@dataclass
class Character:
    """
    Character entity representing a person in the story.

    Characters have a fixed_prompt that ensures visual consistency
    across all shots featuring them.
    """

    id: str
    name: str
    age: int
    gender: str
    physical_description: str
    outfit: Optional[str] = None
    face_details: Optional[str] = None
    references: list[ReferenceImage] = field(default_factory=list)

    def __post_init__(self):
        """Validate character after initialization."""
        if self.age <= 0:
            raise DomainError(f"Age must be positive, got {self.age}")

        if self.gender.lower() not in VALID_GENDERS:
            raise DomainError(
                f"Invalid gender: {self.gender}. "
                f"Valid options: {VALID_GENDERS}"
            )

    @property
    def fixed_prompt(self) -> str:
        """
        Generate fixed prompt for character consistency.

        This prompt is injected into every shot featuring this character
        to maintain visual consistency.
        """
        parts = [
            f"{self.age}-year-old {self.gender}",
            self.physical_description,
        ]

        if self.outfit:
            parts.append(f"wearing {self.outfit}")

        if self.face_details:
            parts.append(self.face_details)

        return ", ".join(parts)

    def add_reference(self, angle: ReferenceAngle, path: str) -> None:
        """Add a reference image for this character."""
        ref = ReferenceImage(angle=angle, path=path)
        self.references.append(ref)

    def get_reference(self, angle: ReferenceAngle) -> Optional[ReferenceImage]:
        """Get reference image by angle."""
        for ref in self.references:
            if ref.angle == angle:
                return ref
        return None

    @property
    def has_references(self) -> bool:
        """Check if character has any reference images."""
        return len(self.references) > 0

    def __eq__(self, other: object) -> bool:
        """Characters are equal if they have the same ID."""
        if not isinstance(other, Character):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        """Hash based on ID."""
        return hash(self.id)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "age": self.age,
            "gender": self.gender,
            "physical_description": self.physical_description,
            "outfit": self.outfit,
            "face_details": self.face_details,
            "fixed_prompt": self.fixed_prompt,
            "references": [
                {"angle": ref.angle.value, "path": ref.path}
                for ref in self.references
            ],
        }
