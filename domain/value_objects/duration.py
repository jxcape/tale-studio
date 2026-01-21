"""
Duration value object.
"""
from __future__ import annotations

from dataclasses import dataclass

from domain.exceptions import InvalidDurationError


@dataclass(frozen=True)
class Duration:
    """Immutable duration value object."""

    seconds: float

    def __post_init__(self):
        if self.seconds <= 0:
            raise InvalidDurationError(f"Duration must be positive, got {self.seconds}")

    @classmethod
    def from_minutes(cls, minutes: float) -> Duration:
        """Create Duration from minutes."""
        return cls(seconds=minutes * 60)

    @property
    def minutes(self) -> float:
        """Get duration in minutes."""
        return self.seconds / 60

    def __add__(self, other: Duration) -> Duration:
        """Add two durations."""
        return Duration(seconds=self.seconds + other.seconds)

    def __repr__(self) -> str:
        return f"Duration({self.seconds}s)"
