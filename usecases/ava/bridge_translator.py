"""Bridge Translator - converts Anchor to Expression using translation strategies."""
from typing import Optional

from domain.entities.ava import (
    Anchor,
    Expression,
    WorldExpression,
    ActorExpression,
    StyleExpression,
)
from domain.value_objects.ava import BridgeMode, Mood
from usecases.interfaces import CinematographyKnowledgeDB


class BridgeTranslator:
    """
    Translates an Anchor into an Expression using the Bridge layer.

    The Bridge layer is responsible for choosing how to visually represent
    the core DNA (Anchor) of the content.
    """

    # Mood to location mapping for intuitive translation
    MOOD_LOCATION_MAP = {
        Mood.MELANCHOLIC: "abandoned space, dim lighting, weathered surfaces",
        Mood.HOPEFUL: "open field, sunrise horizon, natural light",
        Mood.TENSE: "confined space, deep shadows, industrial setting",
        Mood.NOSTALGIC: "vintage interior, soft afternoon light, aged textures",
        Mood.EPIC: "vast landscape, dramatic sky, monumental scale",
        Mood.INTIMATE: "cozy interior, warm lighting, close quarters",
        Mood.CHAOTIC: "cluttered environment, harsh contrasts, dynamic angles",
        Mood.SERENE: "tranquil nature, soft diffused light, minimal elements",
    }

    # Mood to time of day mapping
    MOOD_TIME_MAP = {
        Mood.MELANCHOLIC: "dusk",
        Mood.HOPEFUL: "dawn",
        Mood.TENSE: "night",
        Mood.NOSTALGIC: "golden hour",
        Mood.EPIC: "golden hour",
        Mood.INTIMATE: "evening",
        Mood.CHAOTIC: "midday harsh",
        Mood.SERENE: "morning",
    }

    # Tempo to movement quality mapping
    TEMPO_MOVEMENT_MAP = {
        "slow": "fluid",
        "medium": "measured",
        "fast": "frantic",
    }

    def __init__(self, knowledge_db: CinematographyKnowledgeDB):
        """
        Initialize with a knowledge database.

        Args:
            knowledge_db: The cinematography knowledge database
        """
        self._kb = knowledge_db

    def translate(
        self,
        anchor: Anchor,
        mode: BridgeMode = BridgeMode.INTUITIVE,
    ) -> Expression:
        """
        Translate an Anchor into an Expression.

        Args:
            anchor: The Anchor to translate
            mode: The translation mode (only INTUITIVE supported in MVP)

        Returns:
            An Expression with visual specifications

        Raises:
            NotImplementedError: If mode is not INTUITIVE
        """
        if mode != BridgeMode.INTUITIVE:
            raise NotImplementedError(
                f"Mode {mode.value} not implemented in MVP. "
                "Only INTUITIVE mode is supported."
            )

        return self._translate_intuitive(anchor)

    def _translate_intuitive(self, anchor: Anchor) -> Expression:
        """Intuitive translation - direct emotional mapping."""
        mood = anchor.emotion.primary_mood
        mood_str = mood.value

        # Query Knowledge DB for techniques matching this mood
        camera_techniques = self._kb.query(
            "camera_language",
            moods=[mood_str],
            limit=1,
        )
        rendering_techniques = self._kb.query(
            "rendering_style",
            moods=[mood_str],
            limit=1,
        )
        shot_techniques = self._kb.query(
            "shot_grammar",
            moods=[mood_str],
            limit=2,
        )

        # Build World Expression
        world = WorldExpression(
            location=self.MOOD_LOCATION_MAP.get(mood, "neutral setting"),
            time_of_day=self.MOOD_TIME_MAP.get(mood, "day"),
            atmosphere=mood_str,
            weather=self._infer_weather(mood),
        )

        # Build Actor Expression
        actor = ActorExpression(
            character_hints=anchor.narrative.beats[:2] if anchor.narrative.beats else [],
            movement_quality=self.TEMPO_MOVEMENT_MAP.get(
                anchor.structure.tempo, "measured"
            ),
        )

        # Build Style Expression
        style = StyleExpression(
            rendering_style=(
                rendering_techniques[0].prompt_fragment
                if rendering_techniques else ""
            ),
            camera_language=(
                camera_techniques[0].prompt_fragment
                if camera_techniques else ""
            ),
            shot_grammar=[t.prompt_fragment for t in shot_techniques],
        )

        return Expression(
            world=world,
            actor=actor,
            style=style,
        )

    def _infer_weather(self, mood: Mood) -> Optional[str]:
        """Infer weather from mood (optional enhancement)."""
        weather_map = {
            Mood.MELANCHOLIC: "overcast, light rain",
            Mood.TENSE: "stormy, lightning distant",
            Mood.SERENE: "clear, gentle breeze",
            Mood.CHAOTIC: "heavy rain, strong wind",
        }
        return weather_map.get(mood)
