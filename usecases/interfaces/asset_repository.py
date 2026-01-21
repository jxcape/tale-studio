"""
Asset Repository interface (Port).

For storing and loading project assets.
"""
from abc import ABC, abstractmethod
from typing import Optional

from domain.entities import Character, Scene, Shot, Prompt


class AssetRepository(ABC):
    """
    Interface for asset storage.

    Implementations: YAML files, database, etc.
    """

    # Character operations
    @abstractmethod
    async def save_character(self, character: Character) -> None:
        """Save character to storage."""
        pass

    @abstractmethod
    async def get_character(self, character_id: str) -> Optional[Character]:
        """Get character by ID."""
        pass

    @abstractmethod
    async def list_characters(self) -> list[Character]:
        """List all characters."""
        pass

    # Scene operations
    @abstractmethod
    async def save_scene(self, scene: Scene) -> None:
        """Save scene to storage."""
        pass

    @abstractmethod
    async def get_scene(self, scene_id: str) -> Optional[Scene]:
        """Get scene by ID."""
        pass

    @abstractmethod
    async def list_scenes(self) -> list[Scene]:
        """List all scenes in order."""
        pass

    @abstractmethod
    async def save_scene_manifest(self, scenes: list[Scene]) -> None:
        """Save complete scene manifest."""
        pass

    # Shot operations
    @abstractmethod
    async def save_shot(self, shot: Shot) -> None:
        """Save shot to storage."""
        pass

    @abstractmethod
    async def get_shots_for_scene(self, scene_id: str) -> list[Shot]:
        """Get all shots for a scene."""
        pass

    @abstractmethod
    async def save_shot_sequence(self, scene_id: str, shots: list[Shot]) -> None:
        """Save shot sequence for a scene."""
        pass

    # Prompt operations
    @abstractmethod
    async def save_prompt(self, prompt: Prompt) -> None:
        """Save prompt to storage."""
        pass

    @abstractmethod
    async def get_prompt(self, shot_id: str) -> Optional[Prompt]:
        """Get prompt for a shot."""
        pass
