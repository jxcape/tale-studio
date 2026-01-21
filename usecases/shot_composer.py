"""
ShotComposer UseCase (Level 2).

Composes shot sequences from scenes.
Two implementations for A/B testing:
- Path A: TemplateBasedComposer
- Path B: LLMDirectComposer
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from domain.entities import Scene, Shot
from domain.value_objects import ShotType, Duration, GenerationMethod
from usecases.interfaces import LLMGateway, LLMRequest, AssetRepository


@dataclass
class ShotComposerInput:
    """Input for ShotComposer."""

    scenes: list[Scene]


@dataclass
class ShotComposerOutput:
    """Output from ShotComposer."""

    shot_sequences: dict[str, list[Shot]]  # scene_id -> shots


class ShotComposer(ABC):
    """Abstract base for shot composition."""

    @abstractmethod
    async def execute(self, input_data: ShotComposerInput) -> ShotComposerOutput:
        """Compose shots for scenes."""
        pass


# =============================================================================
# Path A: Template-Based Composer
# =============================================================================

# Shot templates by scene type
DIALOGUE_TEMPLATE = [
    {"type": ShotType.WIDE_SHOT, "duration_ratio": 0.15, "purpose": "Establish space"},
    {"type": ShotType.TWO_SHOT, "duration_ratio": 0.20, "purpose": "Show both speakers"},
    {"type": ShotType.OVER_THE_SHOULDER, "duration_ratio": 0.20, "purpose": "Speaker A"},
    {"type": ShotType.CLOSE_UP, "duration_ratio": 0.15, "purpose": "Reaction B"},
    {"type": ShotType.OVER_THE_SHOULDER, "duration_ratio": 0.20, "purpose": "Speaker B"},
    {"type": ShotType.TWO_SHOT, "duration_ratio": 0.10, "purpose": "Closing"},
]

ACTION_TEMPLATE = [
    {"type": ShotType.WIDE_SHOT, "duration_ratio": 0.15, "purpose": "Context"},
    {"type": ShotType.MEDIUM_SHOT, "duration_ratio": 0.20, "purpose": "Action 1"},
    {"type": ShotType.CLOSE_UP, "duration_ratio": 0.10, "purpose": "Detail"},
    {"type": ShotType.MEDIUM_SHOT, "duration_ratio": 0.20, "purpose": "Action 2"},
    {"type": ShotType.CLOSE_UP, "duration_ratio": 0.15, "purpose": "Reaction"},
    {"type": ShotType.WIDE_SHOT, "duration_ratio": 0.20, "purpose": "Resolution"},
]

ATMOSPHERE_TEMPLATE = [
    {"type": ShotType.EXTREME_WIDE_SHOT, "duration_ratio": 0.40, "purpose": "Establish"},
    {"type": ShotType.WIDE_SHOT, "duration_ratio": 0.35, "purpose": "Detail"},
    {"type": ShotType.MEDIUM_SHOT, "duration_ratio": 0.25, "purpose": "Focus element"},
]

MONOLOGUE_TEMPLATE = [
    {"type": ShotType.EXTREME_CLOSE_UP, "duration_ratio": 0.20, "purpose": "Eyes/emotion"},
    {"type": ShotType.CLOSE_UP, "duration_ratio": 0.40, "purpose": "Face"},
    {"type": ShotType.MEDIUM_SHOT, "duration_ratio": 0.25, "purpose": "Body language"},
    {"type": ShotType.WIDE_SHOT, "duration_ratio": 0.15, "purpose": "Isolation"},
]

TEMPLATES = {
    "dialogue": DIALOGUE_TEMPLATE,
    "action": ACTION_TEMPLATE,
    "atmosphere": ATMOSPHERE_TEMPLATE,
    "monologue": MONOLOGUE_TEMPLATE,
}


class TemplateBasedComposer(ShotComposer):
    """
    Path A: Template-based shot composition.

    Uses predefined shot patterns based on scene type.
    """

    def __init__(self, asset_repository: AssetRepository):
        self._repo = asset_repository

    async def execute(self, input_data: ShotComposerInput) -> ShotComposerOutput:
        """Compose shots using templates."""
        shot_sequences: dict[str, list[Shot]] = {}

        for scene in input_data.scenes:
            shots = self._compose_scene(scene)
            shot_sequences[scene.id] = shots
            await self._repo.save_shot_sequence(scene.id, shots)

        return ShotComposerOutput(shot_sequences=shot_sequences)

    def _compose_scene(self, scene: Scene) -> list[Shot]:
        """Compose shots for a single scene using template."""
        template = TEMPLATES.get(scene.scene_type.value, DIALOGUE_TEMPLATE)
        shots = []

        for i, shot_spec in enumerate(template, 1):
            duration_seconds = scene.duration.seconds * shot_spec["duration_ratio"]
            # Ensure minimum duration
            duration_seconds = max(duration_seconds, 2.0)

            shot = Shot(
                id=f"{scene.id}_shot_{i:02d}",
                scene_id=scene.id,
                shot_type=shot_spec["type"],
                duration=Duration(seconds=duration_seconds),
                purpose=shot_spec["purpose"],
                character_ids=scene.character_ids if shot_spec["type"].is_character_focused else [],
            )
            shots.append(shot)

        return shots


# =============================================================================
# Path B: LLM-Direct Composer
# =============================================================================

SHOT_COMPOSITION_PROMPT = """
You are a professional cinematographer. Compose a shot sequence for this scene.

Scene ID: {scene_id}
Scene Type: {scene_type}
Duration: {duration} seconds
Narrative: {narrative}
Original Text: {original_text}
Characters: {characters}
Location: {location}

Create shots that:
1. Total duration matches scene duration
2. Use appropriate shot types for the scene type
3. Create visual rhythm and pacing
4. IMPORTANT: Preserve emotional tone, character names, dialogue, and specific imagery from the original text

Return JSON:
{{
    "shots": [
        {{
            "shot_type": "WS|CU|MS|ECU|EWS|OTS|2S",
            "duration": 5,
            "purpose": "Detailed description preserving character emotion and specific visual elements",
            "characters": ["character_id"],
            "action": "Specific action with emotional context from original story"
        }}
    ]
}}
"""


class LLMDirectComposer(ShotComposer):
    """
    Path B: LLM-direct shot composition.

    Uses LLM to generate shot sequences dynamically.
    """

    def __init__(self, llm_gateway: LLMGateway, asset_repository: AssetRepository):
        self._llm = llm_gateway
        self._repo = asset_repository

    async def execute(self, input_data: ShotComposerInput) -> ShotComposerOutput:
        """Compose shots using LLM."""
        shot_sequences: dict[str, list[Shot]] = {}

        for scene in input_data.scenes:
            shots = await self._compose_scene(scene)
            shot_sequences[scene.id] = shots
            await self._repo.save_shot_sequence(scene.id, shots)

        return ShotComposerOutput(shot_sequences=shot_sequences)

    async def _compose_scene(self, scene: Scene) -> list[Shot]:
        """Compose shots for a single scene using LLM."""
        prompt = SHOT_COMPOSITION_PROMPT.format(
            scene_id=scene.id,
            scene_type=scene.scene_type.value,
            duration=scene.duration.seconds,
            narrative=scene.narrative_summary,
            original_text=scene.original_text or "Not available",
            characters=", ".join(scene.character_ids) if scene.character_ids else "None",
            location=scene.location_id or "Unspecified",
        )

        response = await self._llm.complete_json(
            LLMRequest(prompt=prompt, temperature=0.7),
            schema={"type": "object", "properties": {"shots": {"type": "array"}}},
        )

        shots = []
        for i, shot_data in enumerate(response.get("shots", []), 1):
            shot = Shot(
                id=f"{scene.id}_shot_{i:02d}",
                scene_id=scene.id,
                shot_type=ShotType.from_string(shot_data["shot_type"]),
                duration=Duration(seconds=shot_data["duration"]),
                purpose=shot_data["purpose"],
                character_ids=shot_data.get("characters", []),
                action_description=shot_data.get("action"),
            )
            shots.append(shot)

        return shots
