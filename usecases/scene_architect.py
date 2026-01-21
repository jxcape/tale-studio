"""
SceneArchitect UseCase (Level 1).

Analyzes story and extracts scenes with character definitions.
"""
from dataclasses import dataclass, field
from typing import Optional

from domain.entities import Scene, Character, Act
from domain.value_objects import SceneType, Duration
from usecases.interfaces import LLMGateway, LLMRequest, AssetRepository


@dataclass
class CharacterHint:
    """Hint for character definition from user."""

    name: str
    role: str
    description: Optional[str] = None


@dataclass
class SceneArchitectInput:
    """Input for SceneArchitect UseCase."""

    story: str
    genre: str
    target_duration_minutes: float
    character_hints: list[dict] = field(default_factory=list)


@dataclass
class SceneArchitectOutput:
    """Output from SceneArchitect UseCase."""

    scenes: list[Scene]
    characters: list[Character]
    total_duration_seconds: float


SCENE_EXTRACTION_PROMPT = """
You are a professional screenwriter. Analyze the following story and break it into scenes.

Story:
{story}

Genre: {genre}
Target Duration: {duration_minutes} minutes

Requirements:
1. Create scenes that fit the target duration
2. Follow the 3-act structure: Beginning (25%), Middle (50%), End (25%)
3. Each scene should have a clear purpose and narrative
4. IMPORTANT: Preserve the emotional tone, specific imagery, and poetic expressions from the original story

Return a JSON object with this structure:
{{
    "scenes": [
        {{
            "id": "scene_01",
            "type": "dialogue|action|monologue|atmosphere",
            "duration_seconds": 30,
            "act": "beginning|middle|end",
            "narrative": "Detailed description preserving emotional tone, specific imagery, character names, dialogue, and key visual elements from the original story",
            "characters": ["character_id1", "character_id2"],
            "location": "location description",
            "original_text": "Relevant quotes or key phrases from the original story"
        }}
    ]
}}
"""

CHARACTER_DEFINITION_PROMPT = """
You are a character designer. Based on the story and hints, define detailed characters.

Story:
{story}

Character Hints:
{hints}

Return a JSON object with this structure:
{{
    "characters": [
        {{
            "id": "protagonist",
            "name": "Character Name",
            "age": 45,
            "gender": "male|female|non-binary|other",
            "physical_description": "Detailed physical appearance",
            "outfit": "What they typically wear",
            "face_details": "Specific facial features"
        }}
    ]
}}
"""


class SceneArchitect:
    """
    Level 1: Scene Architect UseCase.

    Responsibilities:
    - Analyze story and extract scenes
    - Define characters with fixed_prompt for consistency
    - Calculate scene distribution following act structure
    """

    def __init__(
        self,
        llm_gateway: LLMGateway,
        asset_repository: AssetRepository,
    ):
        self._llm = llm_gateway
        self._repo = asset_repository

    async def execute(self, input_data: SceneArchitectInput) -> SceneArchitectOutput:
        """
        Execute scene architecture.

        Args:
            input_data: Story and parameters.

        Returns:
            Extracted scenes and characters.
        """
        # Step 1: Define characters if hints provided
        characters = []
        if input_data.character_hints:
            characters = await self._define_characters(
                input_data.story, input_data.character_hints
            )

        # Step 2: Extract scenes (with character IDs for proper linking)
        character_ids = [c.id for c in characters]
        scenes = await self._extract_scenes(
            story=input_data.story,
            genre=input_data.genre,
            duration_minutes=input_data.target_duration_minutes,
            character_ids=character_ids,
        )

        # Step 3: Save to repository
        await self._repo.save_scene_manifest(scenes)
        for character in characters:
            await self._repo.save_character(character)

        # Calculate total duration
        total_duration = sum(s.duration.seconds for s in scenes)

        return SceneArchitectOutput(
            scenes=scenes,
            characters=characters,
            total_duration_seconds=total_duration,
        )

    async def _define_characters(
        self, story: str, hints: list[dict]
    ) -> list[Character]:
        """Define characters based on story and hints."""
        hints_str = "\n".join(
            f"- {h.get('name', 'Unknown')}: {h.get('role', '')} - {h.get('description', '')}"
            for h in hints
        )

        prompt = CHARACTER_DEFINITION_PROMPT.format(story=story, hints=hints_str)

        response = await self._llm.complete_json(
            LLMRequest(prompt=prompt, temperature=0.7),
            schema={"type": "object", "properties": {"characters": {"type": "array"}}},
        )

        characters = []
        for char_data in response.get("characters", []):
            character = Character(
                id=char_data["id"],
                name=char_data["name"],
                age=char_data["age"],
                gender=char_data["gender"],
                physical_description=char_data["physical_description"],
                outfit=char_data.get("outfit"),
                face_details=char_data.get("face_details"),
            )
            characters.append(character)

        return characters

    async def _extract_scenes(
        self, story: str, genre: str, duration_minutes: float, character_ids: list[str] = None
    ) -> list[Scene]:
        """Extract scenes from story."""
        # Add character IDs info if available
        character_info = ""
        if character_ids:
            character_info = f"\n\nAvailable Character IDs (use these exact IDs in 'characters' array): {', '.join(character_ids)}"

        prompt = SCENE_EXTRACTION_PROMPT.format(
            story=story, genre=genre, duration_minutes=duration_minutes
        ) + character_info

        response = await self._llm.complete_json(
            LLMRequest(prompt=prompt, temperature=0.7),
            schema={"type": "object", "properties": {"scenes": {"type": "array"}}},
        )

        scenes = []
        for scene_data in response.get("scenes", []):
            scene = Scene(
                id=scene_data["id"],
                scene_type=SceneType.from_string(scene_data["type"]),
                duration=Duration(seconds=scene_data["duration_seconds"]),
                act=Act(scene_data["act"]),
                narrative_summary=scene_data["narrative"],
                character_ids=scene_data.get("characters", []),
                location_id=scene_data.get("location"),
                original_text=scene_data.get("original_text"),
            )
            scenes.append(scene)

        return scenes
