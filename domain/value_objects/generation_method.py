"""
GenerationMethod value object.
"""
from __future__ import annotations

from enum import Enum

from domain.exceptions import InvalidGenerationMethodError


class GenerationMethod(Enum):
    """Method for video generation."""

    T2V = "T2V"  # Text-to-Video
    I2V = "I2V"  # Image-to-Video

    @classmethod
    def from_string(cls, value: str) -> GenerationMethod:
        """Create GenerationMethod from string."""
        normalized = value.upper().strip()
        for method in cls:
            if method.value == normalized:
                return method
        raise InvalidGenerationMethodError(
            f"Invalid generation method: {value}. "
            f"Valid methods: {[m.value for m in cls]}"
        )

    @property
    def requires_reference_image(self) -> bool:
        """Check if this method requires a reference image."""
        return self == GenerationMethod.I2V
