"""
File-based Asset Repository adapter.

Implements AssetRepository interface using JSON files.
"""
import json
from pathlib import Path
from typing import Optional, Any, Union

from domain.entities import Character, Scene, Shot, Prompt, Act, CinematographySpec
from domain.value_objects import SceneType, ShotType, Duration, GenerationMethod
from usecases.interfaces import AssetRepository


class FileAssetRepository(AssetRepository):
    """
    File-based implementation of AssetRepository.

    Stores assets as JSON files in a directory structure:
    - characters/{id}.json
    - scenes/{id}.json
    - shots/{scene_id}/{shot_id}.json
    - prompts/{shot_id}.json
    """

    def __init__(self, base_dir: Union[Path, str]):
        self._base_dir = Path(base_dir)
        self._ensure_directories()

    def _ensure_directories(self):
        """Create required directories."""
        (self._base_dir / "characters").mkdir(parents=True, exist_ok=True)
        (self._base_dir / "scenes").mkdir(parents=True, exist_ok=True)
        (self._base_dir / "shots").mkdir(parents=True, exist_ok=True)
        (self._base_dir / "prompts").mkdir(parents=True, exist_ok=True)

    # Character operations
    async def save_character(self, character: Character) -> None:
        """Save character to JSON file."""
        path = self._base_dir / "characters" / f"{character.id}.json"
        data = self._character_to_dict(character)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False))

    async def get_character(self, character_id: str) -> Optional[Character]:
        """Get character by ID."""
        path = self._base_dir / "characters" / f"{character_id}.json"
        if not path.exists():
            return None
        data = json.loads(path.read_text())
        return self._dict_to_character(data)

    async def list_characters(self) -> list[Character]:
        """List all characters."""
        characters = []
        char_dir = self._base_dir / "characters"
        for path in sorted(char_dir.glob("*.json")):
            data = json.loads(path.read_text())
            characters.append(self._dict_to_character(data))
        return characters

    # Scene operations
    async def save_scene(self, scene: Scene) -> None:
        """Save scene to JSON file."""
        path = self._base_dir / "scenes" / f"{scene.id}.json"
        data = self._scene_to_dict(scene)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False))

    async def get_scene(self, scene_id: str) -> Optional[Scene]:
        """Get scene by ID."""
        path = self._base_dir / "scenes" / f"{scene_id}.json"
        if not path.exists():
            return None
        data = json.loads(path.read_text())
        return self._dict_to_scene(data)

    async def list_scenes(self) -> list[Scene]:
        """List all scenes in order."""
        scenes = []
        scene_dir = self._base_dir / "scenes"
        for path in sorted(scene_dir.glob("*.json")):
            data = json.loads(path.read_text())
            scenes.append(self._dict_to_scene(data))
        return scenes

    async def save_scene_manifest(self, scenes: list[Scene]) -> None:
        """Save complete scene manifest."""
        for scene in scenes:
            await self.save_scene(scene)

    # Shot operations
    async def save_shot(self, shot: Shot) -> None:
        """Save shot to JSON file."""
        shot_dir = self._base_dir / "shots" / shot.scene_id
        shot_dir.mkdir(parents=True, exist_ok=True)
        path = shot_dir / f"{shot.id}.json"
        data = self._shot_to_dict(shot)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False))

    async def get_shots_for_scene(self, scene_id: str) -> list[Shot]:
        """Get all shots for a scene."""
        shots = []
        shot_dir = self._base_dir / "shots" / scene_id
        if not shot_dir.exists():
            return []
        for path in sorted(shot_dir.glob("*.json")):
            data = json.loads(path.read_text())
            shots.append(self._dict_to_shot(data))
        return shots

    async def save_shot_sequence(self, scene_id: str, shots: list[Shot]) -> None:
        """Save shot sequence for a scene."""
        for shot in shots:
            await self.save_shot(shot)

    # Prompt operations
    async def save_prompt(self, prompt: Prompt) -> None:
        """Save prompt to JSON file."""
        path = self._base_dir / "prompts" / f"{prompt.shot_id}.json"
        data = self._prompt_to_dict(prompt)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False))

    async def get_prompt(self, shot_id: str) -> Optional[Prompt]:
        """Get prompt for a shot."""
        path = self._base_dir / "prompts" / f"{shot_id}.json"
        if not path.exists():
            return None
        data = json.loads(path.read_text())
        return self._dict_to_prompt(data)

    # Serialization helpers
    def _character_to_dict(self, character: Character) -> dict:
        """Convert Character to dict."""
        return {
            "id": character.id,
            "name": character.name,
            "age": character.age,
            "gender": character.gender,
            "physical_description": character.physical_description,
            "outfit": character.outfit,
            "face_details": character.face_details,
            "references": [
                {"path": r.path, "angle": r.angle}
                for r in character.references
            ],
        }

    def _dict_to_character(self, data: dict) -> Character:
        """Convert dict to Character."""
        from domain.entities.character import ReferenceImage
        references = [
            ReferenceImage(path=r["path"], angle=r["angle"])
            for r in data.get("references", [])
        ]
        return Character(
            id=data["id"],
            name=data["name"],
            age=data["age"],
            gender=data["gender"],
            physical_description=data["physical_description"],
            outfit=data.get("outfit"),
            face_details=data.get("face_details"),
            references=references,
        )

    def _scene_to_dict(self, scene: Scene) -> dict:
        """Convert Scene to dict."""
        return {
            "id": scene.id,
            "scene_type": scene.scene_type.value,
            "duration_seconds": scene.duration.seconds,
            "act": scene.act.value,
            "narrative_summary": scene.narrative_summary,
            "character_ids": scene.character_ids,
            "location_id": scene.location_id,
        }

    def _dict_to_scene(self, data: dict) -> Scene:
        """Convert dict to Scene."""
        return Scene(
            id=data["id"],
            scene_type=SceneType(data["scene_type"]),
            duration=Duration(seconds=data["duration_seconds"]),
            act=Act(data["act"]),
            narrative_summary=data["narrative_summary"],
            character_ids=data.get("character_ids", []),
            location_id=data.get("location_id"),
        )

    def _shot_to_dict(self, shot: Shot) -> dict:
        """Convert Shot to dict."""
        return {
            "id": shot.id,
            "scene_id": shot.scene_id,
            "shot_type": shot.shot_type.value,
            "duration_seconds": shot.duration.seconds,
            "purpose": shot.purpose,
            "character_ids": shot.character_ids,
            "action_description": shot.action_description,
            "generation_method": (
                shot.generation_method.value
                if shot.generation_method
                else None
            ),
        }

    def _dict_to_shot(self, data: dict) -> Shot:
        """Convert dict to Shot."""
        method = data.get("generation_method")
        return Shot(
            id=data["id"],
            scene_id=data["scene_id"],
            shot_type=ShotType(data["shot_type"]),
            duration=Duration(seconds=data["duration_seconds"]),
            purpose=data["purpose"],
            character_ids=data.get("character_ids", []),
            action_description=data.get("action_description"),
            generation_method=(
                GenerationMethod(method) if method else None
            ),
        )

    def _prompt_to_dict(self, prompt: Prompt) -> dict:
        """Convert Prompt to dict."""
        cinematography = None
        if prompt.cinematography:
            cinematography = {
                "shot_framing": prompt.cinematography.shot_framing,
                "camera_angle": prompt.cinematography.camera_angle,
                "camera_movement": prompt.cinematography.camera_movement,
                "lighting_type": prompt.cinematography.lighting_type,
            }
        return {
            "shot_id": prompt.shot_id,
            "shot_type": prompt.shot_type.value,
            "purpose": prompt.purpose,
            "character_prompts": prompt.character_prompts,
            "scene_context": prompt.scene_context,
            "cinematography": cinematography,
            "style_keywords": prompt.style_keywords,
            "negative_prompts": prompt.negative_prompts,
        }

    def _dict_to_prompt(self, data: dict) -> Prompt:
        """Convert dict to Prompt."""
        cinematography = None
        if data.get("cinematography"):
            c = data["cinematography"]
            cinematography = CinematographySpec(
                shot_framing=c.get("shot_framing"),
                camera_angle=c.get("camera_angle"),
                camera_movement=c.get("camera_movement"),
                lighting_type=c.get("lighting_type"),
            )
        return Prompt(
            shot_id=data["shot_id"],
            shot_type=ShotType(data["shot_type"]),
            purpose=data["purpose"],
            character_prompts=data.get("character_prompts", []),
            scene_context=data.get("scene_context"),
            cinematography=cinematography,
            style_keywords=data.get("style_keywords", []),
            negative_prompts=data.get("negative_prompts", []),
        )
