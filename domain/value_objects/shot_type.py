"""
ShotType value object.
"""
from __future__ import annotations

from enum import Enum

from domain.exceptions import InvalidShotTypeError


class ShotType(Enum):
    """Type of camera shot."""

    EXTREME_CLOSE_UP = "ECU"
    CLOSE_UP = "CU"
    MEDIUM_SHOT = "MS"
    FULL_SHOT = "FS"
    WIDE_SHOT = "WS"
    EXTREME_WIDE_SHOT = "EWS"
    OVER_THE_SHOULDER = "OTS"
    TWO_SHOT = "2S"

    # Aliases for string parsing
    _ALIASES: dict[str, str] = {
        "extreme_close_up": "ECU",
        "close_up": "CU",
        "medium_shot": "MS",
        "full_shot": "FS",
        "wide_shot": "WS",
        "extreme_wide_shot": "EWS",
        "over_the_shoulder": "OTS",
        "two_shot": "2S",
        "ots": "OTS",
        "ecu": "ECU",
        "cu": "CU",
        "ms": "MS",
        "fs": "FS",
        "ws": "WS",
        "ews": "EWS",
        "2s": "2S",
    }

    @classmethod
    def from_string(cls, value: str) -> ShotType:
        """Create ShotType from string."""
        normalized = value.lower().strip()

        # Check aliases
        if normalized in cls._ALIASES.value:
            normalized = cls._ALIASES.value[normalized]

        # Check direct match
        for shot_type in cls:
            if shot_type.value == normalized.upper():
                return shot_type

        raise InvalidShotTypeError(
            f"Invalid shot type: {value}. "
            f"Valid types: {[t.value for t in cls if not t.name.startswith('_')]}"
        )

    @property
    def is_character_focused(self) -> bool:
        """Check if this shot type focuses on characters (I2V candidate)."""
        character_focused = {
            ShotType.EXTREME_CLOSE_UP,
            ShotType.CLOSE_UP,
            ShotType.MEDIUM_SHOT,
            ShotType.OVER_THE_SHOULDER,
            ShotType.TWO_SHOT,
        }
        return self in character_focused
