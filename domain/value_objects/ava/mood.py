"""Mood value object for AVA Framework."""
from enum import Enum


class Mood(Enum):
    """Emotional mood categories for content."""

    MELANCHOLIC = "melancholic"
    HOPEFUL = "hopeful"
    TENSE = "tense"
    NOSTALGIC = "nostalgic"
    EPIC = "epic"
    INTIMATE = "intimate"
    CHAOTIC = "chaotic"
    SERENE = "serene"
