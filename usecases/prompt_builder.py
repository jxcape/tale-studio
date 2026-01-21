"""
PromptBuilder UseCase (Level 3).

Builds final prompts from shots, characters, and cinematography DB.
"""
from dataclasses import dataclass, field
from typing import Optional

from domain.entities import Shot, Character, Prompt, CinematographySpec
from domain.value_objects import ShotType
from usecases.interfaces import AssetRepository


@dataclass
class PromptBuilderInput:
    """Input for PromptBuilder."""

    shots: list[Shot]
    characters: list[Character] = field(default_factory=list)
    scene_contexts: dict[str, str] = field(default_factory=dict)  # scene_id -> context
    style_keywords: list[str] = field(default_factory=list)
    negative_prompts: list[str] = field(default_factory=list)


@dataclass
class PromptBuilderOutput:
    """Output from PromptBuilder."""

    prompts: list[Prompt]


# Cinematography DB - minimal version for MVP
CINEMATOGRAPHY_DB = {
    ShotType.EXTREME_CLOSE_UP: CinematographySpec(
        shot_framing="Extreme close-up",
        camera_angle="Eye-level",
        lighting_type="Soft, dramatic",
    ),
    ShotType.CLOSE_UP: CinematographySpec(
        shot_framing="Close-up",
        camera_angle="Eye-level",
        lighting_type="Soft, natural",
    ),
    ShotType.MEDIUM_SHOT: CinematographySpec(
        shot_framing="Medium shot",
        camera_angle="Eye-level",
        camera_movement="Static or slow push-in",
    ),
    ShotType.FULL_SHOT: CinematographySpec(
        shot_framing="Full shot",
        camera_angle="Slightly low",
    ),
    ShotType.WIDE_SHOT: CinematographySpec(
        shot_framing="Wide shot",
        camera_angle="Eye-level",
        lighting_type="Natural, ambient",
    ),
    ShotType.EXTREME_WIDE_SHOT: CinematographySpec(
        shot_framing="Extreme wide shot",
        camera_angle="Eye-level or high",
        lighting_type="Natural, atmospheric",
    ),
    ShotType.OVER_THE_SHOULDER: CinematographySpec(
        shot_framing="Over-the-shoulder",
        camera_angle="Eye-level",
        camera_movement="Static",
    ),
    ShotType.TWO_SHOT: CinematographySpec(
        shot_framing="Two-shot",
        camera_angle="Eye-level",
        lighting_type="Balanced",
    ),
}

DEFAULT_STYLE_KEYWORDS = ["Cinematic", "Professional camera work", "4K quality"]
DEFAULT_NEGATIVE_PROMPTS = ["CGI", "3D render", "cartoon", "anime", "deformed"]


class PromptBuilder:
    """
    Level 3: Prompt Builder UseCase.

    Responsibilities:
    - Build final prompts from shots
    - Inject character fixed_prompts
    - Apply cinematography specs from DB
    - Add style keywords and negative prompts
    """

    def __init__(self, asset_repository: AssetRepository):
        self._repo = asset_repository

    async def execute(self, input_data: PromptBuilderInput) -> PromptBuilderOutput:
        """Build prompts for all shots."""
        # Build character lookup
        char_lookup = {c.id: c for c in input_data.characters}

        prompts = []
        for shot in input_data.shots:
            prompt = self._build_prompt(
                shot=shot,
                char_lookup=char_lookup,
                scene_context=input_data.scene_contexts.get(shot.scene_id),
                style_keywords=input_data.style_keywords or DEFAULT_STYLE_KEYWORDS,
                negative_prompts=input_data.negative_prompts or DEFAULT_NEGATIVE_PROMPTS,
            )
            prompts.append(prompt)
            await self._repo.save_prompt(prompt)

        return PromptBuilderOutput(prompts=prompts)

    def _build_prompt(
        self,
        shot: Shot,
        char_lookup: dict[str, Character],
        scene_context: Optional[str],
        style_keywords: list[str],
        negative_prompts: list[str],
    ) -> Prompt:
        """Build prompt for a single shot."""
        # Get character fixed_prompts
        character_prompts = []
        for char_id in shot.character_ids:
            if char_id in char_lookup:
                character_prompts.append(char_lookup[char_id].fixed_prompt)

        # Get cinematography from DB
        cinematography = CINEMATOGRAPHY_DB.get(shot.shot_type)

        # Build scene context
        context = scene_context
        if shot.action_description and not context:
            context = shot.action_description
        elif shot.action_description and context:
            context = f"{context}. {shot.action_description}"

        return Prompt(
            shot_id=shot.id,
            shot_type=shot.shot_type,
            purpose=shot.purpose,
            character_prompts=character_prompts,
            scene_context=context,
            cinematography=cinematography,
            style_keywords=style_keywords,
            negative_prompts=negative_prompts,
        )
