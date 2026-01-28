"""EmotionalArc value object for AVA Framework."""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class EmotionalArc:
    """Represents emotional tension over time."""

    tension_curve: tuple[float, ...] = field(default_factory=lambda: (0.5,))
    peaks: tuple[float, ...] = field(default_factory=tuple)

    def __post_init__(self):
        # Validate all values are 0.0-1.0
        for val in self.tension_curve:
            if not 0.0 <= val <= 1.0:
                raise ValueError(f"Tension value must be 0.0-1.0, got {val}")
        for val in self.peaks:
            if not 0.0 <= val <= 1.0:
                raise ValueError(f"Peak value must be 0.0-1.0, got {val}")
