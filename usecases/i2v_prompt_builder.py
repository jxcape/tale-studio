"""
I2V PromptBuilder UseCase (Level 3 - LLM Based).

Builds Imagen + Veo prompts from shots using LLM.
"""
from dataclasses import dataclass, field
from typing import Optional

from domain.entities import Shot, Character, Scene, I2VPrompt
from usecases.interfaces import LLMGateway, LLMRequest, AssetRepository


@dataclass
class I2VPromptBuilderInput:
    """Input for I2V PromptBuilder."""

    shots: list[Shot]
    scenes: list[Scene]
    characters: list[Character] = field(default_factory=list)
    style_preset: Optional[str] = None
    duration_seconds: float = 8.0


@dataclass
class I2VPromptBuilderOutput:
    """Output from I2V PromptBuilder."""

    prompts: list[I2VPrompt]


# System prompt for I2V prompt generation
I2V_SYSTEM_PROMPT = """You are a professional cinematographer and prompt engineer for AI video generation.

Your task is to create detailed prompts for:
1. **Imagen** (static keyframe image) - Describe the visual composition at the START of the shot
2. **Veo** (motion/camera) - Describe how the image animates over the duration

Style guidelines:
- Lost Ark game cinematic style
- Korean MMO dark fantasy aesthetic
- Unreal Engine 5 quality rendering
- Dramatic rim lighting, volumetric fog
- Cinematic color grading (desaturated blues and oranges)

IMPORTANT:
- Imagen prompt: Static description only. What the camera sees at frame 0.
- Veo prompt: Motion and camera movement only. How things change over time.
- Be extremely detailed and specific.
- Include lighting, atmosphere, and emotional tone.
"""

I2V_GENERATION_PROMPT = """Generate I2V prompts for this shot:

## Scene Context
- Scene ID: {scene_id}
- Scene Narrative: {narrative}
- Location: {location}

## Shot Details
- Shot ID: {shot_id}
- Shot Type: {shot_type}
- Duration: {duration} seconds
- Purpose: {purpose}
- Action: {action}

## Characters in Shot
{characters}

## Style Preset
{style_preset}

---

Return a JSON object with this EXACT structure:
{{
    "imagen_prompt": "Detailed static image description for Imagen...",
    "veo_prompt": "Motion and camera movement description for Veo...",
    "negative_prompt": "Things to avoid..."
}}

Remember:
- imagen_prompt: STATIC frame, no motion words
- veo_prompt: ONLY motion/camera, no static descriptions
- Be specific about lighting, composition, and atmosphere
"""


class I2VPromptBuilder:
    """
    Level 3: LLM-Based I2V Prompt Builder.

    Uses LLM to generate detailed prompts for:
    - Imagen: Static keyframe image
    - Veo: Motion/camera animation
    """

    def __init__(
        self,
        llm_gateway: LLMGateway,
        asset_repository: AssetRepository,
    ):
        self._llm = llm_gateway
        self._repo = asset_repository

    async def execute(self, input_data: I2VPromptBuilderInput) -> I2VPromptBuilderOutput:
        """Build I2V prompts for all shots."""
        # Build lookups
        scene_lookup = {s.id: s for s in input_data.scenes}
        char_lookup = {c.id: c for c in input_data.characters}

        prompts = []
        for shot in input_data.shots:
            scene = scene_lookup.get(shot.scene_id)
            if not scene:
                continue

            # Get characters for this shot
            shot_characters = [
                char_lookup[cid] for cid in shot.character_ids if cid in char_lookup
            ]

            prompt = await self._build_prompt(
                shot=shot,
                scene=scene,
                characters=shot_characters,
                style_preset=input_data.style_preset,
                duration=input_data.duration_seconds,
            )
            prompts.append(prompt)

        return I2VPromptBuilderOutput(prompts=prompts)

    async def _build_prompt(
        self,
        shot: Shot,
        scene: Scene,
        characters: list[Character],
        style_preset: Optional[str],
        duration: float,
    ) -> I2VPrompt:
        """Build I2V prompt for a single shot using LLM."""
        # Format character info
        char_info = self._format_characters(characters)

        # Build the prompt
        user_prompt = I2V_GENERATION_PROMPT.format(
            scene_id=scene.id,
            narrative=scene.narrative_summary or "No narrative provided",
            location=scene.location_id or "Unspecified location",
            shot_id=shot.id,
            shot_type=shot.shot_type.value,
            duration=duration,
            purpose=shot.purpose or "General shot",
            action=shot.action_description or "No specific action",
            characters=char_info or "No characters in shot",
            style_preset=style_preset or "Lost Ark game cinematic style",
        )

        # Call LLM
        response = await self._llm.complete_json(
            LLMRequest(
                prompt=user_prompt,
                system_prompt=I2V_SYSTEM_PROMPT,
                temperature=0.7,
                max_tokens=2000,
            ),
            schema={
                "type": "object",
                "properties": {
                    "imagen_prompt": {"type": "string"},
                    "veo_prompt": {"type": "string"},
                    "negative_prompt": {"type": "string"},
                },
            },
        )

        return I2VPrompt(
            shot_id=shot.id,
            scene_id=scene.id,
            imagen_prompt=response.get("imagen_prompt", ""),
            veo_prompt=response.get("veo_prompt", ""),
            duration_seconds=duration,
            aspect_ratio="16:9",
            style_preset=style_preset,
            negative_prompt=response.get("negative_prompt"),
        )

    def _format_characters(self, characters: list[Character]) -> str:
        """Format character info for prompt."""
        if not characters:
            return ""

        lines = []
        for char in characters:
            lines.append(f"### {char.name}")
            if char.physical_description:
                lines.append(f"Appearance: {char.physical_description}")
            if char.outfit:
                lines.append(f"Outfit: {char.outfit}")
            if char.face_details:
                lines.append(f"Face: {char.face_details}")
            if char.fixed_prompt:
                lines.append(f"Fixed Prompt: {char.fixed_prompt}")
            lines.append("")

        return "\n".join(lines)


# Convenience function for quick generation
async def build_i2v_prompts(
    llm: LLMGateway,
    repo: AssetRepository,
    shots: list[Shot],
    scenes: list[Scene],
    characters: list[Character],
    style_preset: str = "Lost Ark game cinematic style",
) -> list[I2VPrompt]:
    """
    Convenience function to build I2V prompts.

    Args:
        llm: LLM gateway for prompt generation.
        repo: Asset repository for saving.
        shots: List of shots to generate prompts for.
        scenes: List of scenes (for context).
        characters: List of characters.
        style_preset: Style preset string.

    Returns:
        List of I2VPrompt objects.
    """
    builder = I2VPromptBuilder(llm, repo)
    input_data = I2VPromptBuilderInput(
        shots=shots,
        scenes=scenes,
        characters=characters,
        style_preset=style_preset,
    )
    output = await builder.execute(input_data)
    return output.prompts
