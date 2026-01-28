"""Anchor entity for AVA Framework - the immutable core DNA of content."""
from dataclasses import dataclass, field

from domain.value_objects.ava import Mood, EmotionalArc


@dataclass
class NarrativeCore:
    """The narrative essence of the content."""

    theme: str  # Core theme (e.g., "loss and redemption")
    arc: str  # Narrative arc type (e.g., "rise", "fall", "rise-fall-rise")
    beats: list[str] = field(default_factory=list)  # Key story beats


@dataclass
class EmotionalCore:
    """The emotional essence of the content."""

    primary_mood: Mood
    emotional_arc: EmotionalArc
    tension_points: list[float] = field(default_factory=list)  # 0.0-1.0 normalized timeline


@dataclass
class StructuralCore:
    """The structural essence of the content."""

    tempo: str  # "slow", "medium", "fast"
    rhythm_pattern: str  # e.g., "4/4", "3/4"
    sections: list[str] = field(default_factory=list)  # e.g., ["intro", "verse", "chorus"]


@dataclass
class Anchor:
    """
    The Anchor layer of AVA Framework.

    Contains the immutable core DNA that must be preserved
    during the translation process.
    """

    narrative: NarrativeCore
    emotion: EmotionalCore
    structure: StructuralCore
