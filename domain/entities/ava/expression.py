"""Expression entity for AVA Framework - the visual output specification."""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class WorldExpression:
    """Visual specification for the world/environment."""

    location: str  # Location description
    time_of_day: str  # Time of day (dawn, day, dusk, night)
    atmosphere: str  # Atmospheric mood
    weather: Optional[str] = None  # Weather conditions


@dataclass
class ActorExpression:
    """Visual specification for actors/characters."""

    character_hints: list[str] = field(default_factory=list)  # Character descriptions
    movement_quality: str = "measured"  # "fluid", "static", "frantic", "measured"


@dataclass
class StyleExpression:
    """Visual specification for rendering and camera style."""

    rendering_style: str = ""  # From Knowledge DB
    camera_language: str = ""  # From Knowledge DB
    shot_grammar: list[str] = field(default_factory=list)  # From Knowledge DB


@dataclass
class Expression:
    """
    The Expression layer of AVA Framework.

    Contains the visual specification that feeds into
    the L1-L2-L3 pipeline.
    """

    world: WorldExpression
    actor: ActorExpression
    style: StyleExpression

    def to_pumpup_hints(self) -> dict:
        """Convert to hints format for StoryPumpup."""
        return {
            "time_of_day": self.world.time_of_day,
            "location": self.world.location,
            "atmosphere": self.world.atmosphere,
            "weather": self.world.weather,
            "movement_quality": self.actor.movement_quality,
        }
