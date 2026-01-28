"""Music metadata model for AVA Framework."""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class MusicSection:
    """Represents a section of a music track."""

    label: str  # "intro", "verse", "chorus", "bridge", "outro"
    start_time: float  # seconds
    end_time: float  # seconds
    energy_level: float = 0.5  # 0.0-1.0

    def __post_init__(self):
        if not 0.0 <= self.energy_level <= 1.0:
            raise ValueError(f"Energy level must be 0.0-1.0, got {self.energy_level}")
        if self.start_time < 0:
            raise ValueError(f"Start time must be >= 0, got {self.start_time}")
        if self.end_time <= self.start_time:
            raise ValueError(f"End time must be > start time")


@dataclass
class MusicMetadata:
    """Metadata for a music track used in video generation."""

    title: str
    artist: Optional[str] = None
    duration_seconds: Optional[float] = None
    bpm: Optional[int] = None
    key: Optional[str] = None  # e.g., "C major", "A minor"
    mood_tags: list[str] = field(default_factory=list)
    genre_tags: list[str] = field(default_factory=list)
    lyrics: Optional[str] = None
    sections: list[MusicSection] = field(default_factory=list)

    @property
    def has_lyrics(self) -> bool:
        """Check if lyrics are available."""
        return bool(self.lyrics and self.lyrics.strip())

    @property
    def primary_mood(self) -> Optional[str]:
        """Get the primary mood tag if available."""
        return self.mood_tags[0] if self.mood_tags else None

    def get_tempo_category(self) -> str:
        """Categorize tempo based on BPM."""
        if self.bpm is None:
            return "medium"
        if self.bpm < 80:
            return "slow"
        if self.bpm < 120:
            return "medium"
        return "fast"
