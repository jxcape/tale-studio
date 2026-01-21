"""
Tests for FileAssetRepository adapter.
"""
import pytest
import json
import tempfile
from pathlib import Path

from adapters.repositories.file_repository import FileAssetRepository
from usecases.interfaces import AssetRepository
from domain.entities import Character, Scene, Shot, Prompt, Act, CinematographySpec
from domain.value_objects import SceneType, ShotType, Duration


@pytest.fixture
def temp_base_dir():
    """Create temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def repository(temp_base_dir):
    """Create repository with temp directory."""
    return FileAssetRepository(base_dir=temp_base_dir)


@pytest.fixture
def sample_character():
    """Sample character for testing."""
    return Character(
        id="protagonist",
        name="Dr. Kim",
        age=45,
        gender="male",
        physical_description="Asian male, tired eyes",
        outfit="white lab coat",
    )


@pytest.fixture
def sample_scene():
    """Sample scene for testing."""
    return Scene(
        id="scene_01",
        scene_type=SceneType.DIALOGUE,
        duration=Duration(seconds=60),
        act=Act.BEGINNING,
        narrative_summary="Dr. Kim talks to AI",
        character_ids=["protagonist"],
        location_id="laboratory",
    )


@pytest.fixture
def sample_shot():
    """Sample shot for testing."""
    return Shot(
        id="scene_01_shot_01",
        scene_id="scene_01",
        shot_type=ShotType.CLOSE_UP,
        duration=Duration(seconds=5),
        purpose="Show emotion",
        character_ids=["protagonist"],
    )


@pytest.fixture
def sample_prompt():
    """Sample prompt for testing."""
    return Prompt(
        shot_id="scene_01_shot_01",
        shot_type=ShotType.CLOSE_UP,
        purpose="Show emotion",
        character_prompts=["45-year-old male, Asian, tired eyes, wearing white lab coat"],
        scene_context="Dr. Kim realizes the truth",
        cinematography=CinematographySpec(shot_framing="Close-up", camera_angle="Eye-level"),
        style_keywords=["Cinematic", "4K"],
        negative_prompts=["CGI", "cartoon"],
    )


class TestFileAssetRepository:
    """Tests for FileAssetRepository."""

    def test_implements_interface(self, repository):
        """Should implement AssetRepository interface."""
        assert isinstance(repository, AssetRepository)

    # Character tests
    @pytest.mark.asyncio
    async def test_save_and_get_character(self, repository, sample_character):
        """Should save and retrieve character."""
        # Act
        await repository.save_character(sample_character)
        result = await repository.get_character("protagonist")

        # Assert
        assert result is not None
        assert result.id == "protagonist"
        assert result.name == "Dr. Kim"
        assert result.age == 45

    @pytest.mark.asyncio
    async def test_get_nonexistent_character(self, repository):
        """Should return None for nonexistent character."""
        result = await repository.get_character("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_list_characters(self, repository, sample_character):
        """Should list all characters."""
        # Arrange
        await repository.save_character(sample_character)
        char2 = Character(
            id="antagonist",
            name="AI",
            age=1,
            gender="other",
            physical_description="Digital entity",
        )
        await repository.save_character(char2)

        # Act
        characters = await repository.list_characters()

        # Assert
        assert len(characters) == 2
        ids = {c.id for c in characters}
        assert "protagonist" in ids
        assert "antagonist" in ids

    # Scene tests
    @pytest.mark.asyncio
    async def test_save_and_get_scene(self, repository, sample_scene):
        """Should save and retrieve scene."""
        # Act
        await repository.save_scene(sample_scene)
        result = await repository.get_scene("scene_01")

        # Assert
        assert result is not None
        assert result.id == "scene_01"
        assert result.scene_type == SceneType.DIALOGUE
        assert result.duration.seconds == 60

    @pytest.mark.asyncio
    async def test_list_scenes(self, repository, sample_scene):
        """Should list all scenes in order."""
        # Arrange
        await repository.save_scene(sample_scene)
        scene2 = Scene(
            id="scene_02",
            scene_type=SceneType.ACTION,
            duration=Duration(seconds=30),
            act=Act.MIDDLE,
            narrative_summary="Chase sequence",
        )
        await repository.save_scene(scene2)

        # Act
        scenes = await repository.list_scenes()

        # Assert
        assert len(scenes) == 2
        assert scenes[0].id == "scene_01"
        assert scenes[1].id == "scene_02"

    @pytest.mark.asyncio
    async def test_save_scene_manifest(self, repository):
        """Should save complete scene manifest."""
        # Arrange
        scenes = [
            Scene(
                id=f"scene_{i:02d}",
                scene_type=SceneType.DIALOGUE,
                duration=Duration(seconds=30),
                act=Act.BEGINNING,
                narrative_summary=f"Scene {i}",
            )
            for i in range(1, 4)
        ]

        # Act
        await repository.save_scene_manifest(scenes)
        result = await repository.list_scenes()

        # Assert
        assert len(result) == 3

    # Shot tests
    @pytest.mark.asyncio
    async def test_save_and_get_shots(self, repository, sample_shot):
        """Should save and retrieve shots for scene."""
        # Act
        await repository.save_shot(sample_shot)
        result = await repository.get_shots_for_scene("scene_01")

        # Assert
        assert len(result) == 1
        assert result[0].id == "scene_01_shot_01"
        assert result[0].shot_type == ShotType.CLOSE_UP

    @pytest.mark.asyncio
    async def test_save_shot_sequence(self, repository):
        """Should save shot sequence for scene."""
        # Arrange
        shots = [
            Shot(
                id=f"scene_01_shot_{i:02d}",
                scene_id="scene_01",
                shot_type=ShotType.MEDIUM_SHOT,
                duration=Duration(seconds=5),
                purpose=f"Shot {i}",
            )
            for i in range(1, 4)
        ]

        # Act
        await repository.save_shot_sequence("scene_01", shots)
        result = await repository.get_shots_for_scene("scene_01")

        # Assert
        assert len(result) == 3
        assert result[0].id == "scene_01_shot_01"
        assert result[2].id == "scene_01_shot_03"

    # Prompt tests
    @pytest.mark.asyncio
    async def test_save_and_get_prompt(self, repository, sample_prompt):
        """Should save and retrieve prompt."""
        # Act
        await repository.save_prompt(sample_prompt)
        result = await repository.get_prompt("scene_01_shot_01")

        # Assert
        assert result is not None
        assert result.shot_id == "scene_01_shot_01"
        assert "Cinematic" in result.style_keywords

    @pytest.mark.asyncio
    async def test_get_nonexistent_prompt(self, repository):
        """Should return None for nonexistent prompt."""
        result = await repository.get_prompt("nonexistent")
        assert result is None

    # Directory structure tests
    @pytest.mark.asyncio
    async def test_creates_directory_structure(self, repository, sample_character):
        """Should create proper directory structure."""
        # Act
        await repository.save_character(sample_character)

        # Assert
        base_dir = repository._base_dir
        assert (base_dir / "characters").exists()

    @pytest.mark.asyncio
    async def test_persists_to_json_files(self, repository, sample_character, temp_base_dir):
        """Should save data as JSON files."""
        # Act
        await repository.save_character(sample_character)

        # Assert
        char_file = temp_base_dir / "characters" / "protagonist.json"
        assert char_file.exists()
        data = json.loads(char_file.read_text())
        assert data["name"] == "Dr. Kim"
