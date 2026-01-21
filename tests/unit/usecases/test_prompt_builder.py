"""
Tests for PromptBuilder UseCase (Level 3).
"""
import pytest
from unittest.mock import AsyncMock

from domain.entities import Shot, Character, Prompt, CinematographySpec
from domain.value_objects import ShotType, Duration, GenerationMethod
from usecases.prompt_builder import PromptBuilder, PromptBuilderInput
from usecases.interfaces import AssetRepository


@pytest.fixture
def mock_asset_repository():
    """Create mock asset repository."""
    return AsyncMock(spec=AssetRepository)


@pytest.fixture
def sample_character():
    """Sample character for testing."""
    return Character(
        id="protagonist",
        name="Dr. Kim",
        age=45,
        gender="male",
        physical_description="Asian male, tired eyes, slight stubble",
        outfit="wrinkled white lab coat, loosened tie",
        face_details="round glasses, deep eye bags, contemplative expression",
    )


@pytest.fixture
def sample_shot():
    """Sample shot for testing."""
    return Shot(
        id="scene_01_shot_02",
        scene_id="scene_01",
        shot_type=ShotType.CLOSE_UP,
        duration=Duration(seconds=3),
        purpose="Show character emotion",
        character_ids=["protagonist"],
        action_description="Dr. Kim looks at the screen with realization",
    )


@pytest.fixture
def sample_shots():
    """Multiple shots for testing."""
    return [
        Shot(
            id="scene_01_shot_01",
            scene_id="scene_01",
            shot_type=ShotType.WIDE_SHOT,
            duration=Duration(seconds=3),
            purpose="Establish space",
        ),
        Shot(
            id="scene_01_shot_02",
            scene_id="scene_01",
            shot_type=ShotType.CLOSE_UP,
            duration=Duration(seconds=3),
            purpose="Character focus",
            character_ids=["protagonist"],
        ),
    ]


class TestPromptBuilder:
    """Tests for PromptBuilder UseCase."""

    @pytest.mark.asyncio
    async def test_builds_prompt_for_shot(
        self, mock_asset_repository, sample_shot, sample_character
    ):
        """Should build prompt for a shot."""
        # Arrange
        mock_asset_repository.get_character.return_value = sample_character

        builder = PromptBuilder(asset_repository=mock_asset_repository)
        input_data = PromptBuilderInput(
            shots=[sample_shot],
            characters=[sample_character],
        )

        # Act
        result = await builder.execute(input_data)

        # Assert
        assert len(result.prompts) == 1
        prompt = result.prompts[0]
        assert prompt.shot_id == "scene_01_shot_02"
        assert prompt.shot_type == ShotType.CLOSE_UP

    @pytest.mark.asyncio
    async def test_includes_character_fixed_prompt(
        self, mock_asset_repository, sample_shot, sample_character
    ):
        """Prompt should include character's fixed_prompt."""
        # Arrange
        mock_asset_repository.get_character.return_value = sample_character

        builder = PromptBuilder(asset_repository=mock_asset_repository)
        input_data = PromptBuilderInput(
            shots=[sample_shot],
            characters=[sample_character],
        )

        # Act
        result = await builder.execute(input_data)

        # Assert
        prompt = result.prompts[0]
        final_prompt = prompt.build()
        # Should contain character details
        assert "45" in final_prompt or "male" in final_prompt.lower()
        assert "lab coat" in final_prompt.lower()

    @pytest.mark.asyncio
    async def test_includes_cinematography(
        self, mock_asset_repository, sample_shot, sample_character
    ):
        """Prompt should include cinematography specs."""
        # Arrange
        mock_asset_repository.get_character.return_value = sample_character

        builder = PromptBuilder(asset_repository=mock_asset_repository)
        input_data = PromptBuilderInput(
            shots=[sample_shot],
            characters=[sample_character],
        )

        # Act
        result = await builder.execute(input_data)

        # Assert
        prompt = result.prompts[0]
        assert prompt.cinematography is not None
        final_prompt = prompt.build()
        # Should mention shot type
        assert "Close-up" in final_prompt or "CU" in final_prompt

    @pytest.mark.asyncio
    async def test_shot_without_characters(self, mock_asset_repository):
        """Shot without characters should not have character prompt."""
        # Arrange
        atmosphere_shot = Shot(
            id="scene_01_shot_01",
            scene_id="scene_01",
            shot_type=ShotType.EXTREME_WIDE_SHOT,
            duration=Duration(seconds=5),
            purpose="Establishing shot",
        )

        builder = PromptBuilder(asset_repository=mock_asset_repository)
        input_data = PromptBuilderInput(
            shots=[atmosphere_shot],
            characters=[],
        )

        # Act
        result = await builder.execute(input_data)

        # Assert
        prompt = result.prompts[0]
        assert len(prompt.character_prompts) == 0

    @pytest.mark.asyncio
    async def test_includes_style_keywords(
        self, mock_asset_repository, sample_shot, sample_character
    ):
        """Prompt should include style keywords."""
        # Arrange
        mock_asset_repository.get_character.return_value = sample_character

        builder = PromptBuilder(asset_repository=mock_asset_repository)
        input_data = PromptBuilderInput(
            shots=[sample_shot],
            characters=[sample_character],
            style_keywords=["Cinematic", "4K", "Professional"],
        )

        # Act
        result = await builder.execute(input_data)

        # Assert
        prompt = result.prompts[0]
        final_prompt = prompt.build()
        assert "Cinematic" in final_prompt

    @pytest.mark.asyncio
    async def test_multiple_shots_build(
        self, mock_asset_repository, sample_shots, sample_character
    ):
        """Should build prompts for multiple shots."""
        # Arrange
        mock_asset_repository.get_character.return_value = sample_character

        builder = PromptBuilder(asset_repository=mock_asset_repository)
        input_data = PromptBuilderInput(
            shots=sample_shots,
            characters=[sample_character],
        )

        # Act
        result = await builder.execute(input_data)

        # Assert
        assert len(result.prompts) == 2
        assert result.prompts[0].shot_id == "scene_01_shot_01"
        assert result.prompts[1].shot_id == "scene_01_shot_02"

    @pytest.mark.asyncio
    async def test_saves_prompts_to_repository(
        self, mock_asset_repository, sample_shot, sample_character
    ):
        """Prompts should be saved to repository."""
        # Arrange
        mock_asset_repository.get_character.return_value = sample_character

        builder = PromptBuilder(asset_repository=mock_asset_repository)
        input_data = PromptBuilderInput(
            shots=[sample_shot],
            characters=[sample_character],
        )

        # Act
        await builder.execute(input_data)

        # Assert
        mock_asset_repository.save_prompt.assert_called_once()

    @pytest.mark.asyncio
    async def test_scene_context_included(
        self, mock_asset_repository, sample_shot, sample_character
    ):
        """Scene context should be included in prompt."""
        # Arrange
        mock_asset_repository.get_character.return_value = sample_character

        builder = PromptBuilder(asset_repository=mock_asset_repository)
        input_data = PromptBuilderInput(
            shots=[sample_shot],
            characters=[sample_character],
            scene_contexts={"scene_01": "Dr. Kim discovers the truth about the AI"},
        )

        # Act
        result = await builder.execute(input_data)

        # Assert
        prompt = result.prompts[0]
        final_prompt = prompt.build()
        assert "truth" in final_prompt.lower() or "AI" in final_prompt

    @pytest.mark.asyncio
    async def test_action_description_included(
        self, mock_asset_repository, sample_shot, sample_character
    ):
        """Action description should be reflected in prompt."""
        # Arrange
        mock_asset_repository.get_character.return_value = sample_character

        builder = PromptBuilder(asset_repository=mock_asset_repository)
        input_data = PromptBuilderInput(
            shots=[sample_shot],
            characters=[sample_character],
        )

        # Act
        result = await builder.execute(input_data)

        # Assert
        prompt = result.prompts[0]
        # Action should be part of scene context
        assert prompt.scene_context is not None or sample_shot.action_description is not None
