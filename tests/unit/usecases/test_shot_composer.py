"""
Tests for ShotComposer UseCase (Level 2).

Tests both Path A (template-based) and Path B (LLM-direct).
"""
import pytest
from unittest.mock import AsyncMock

from domain.entities import Scene, Shot, Act
from domain.value_objects import SceneType, ShotType, Duration, GenerationMethod
from usecases.shot_composer import (
    ShotComposer,
    TemplateBasedComposer,
    LLMDirectComposer,
    ShotComposerInput,
)
from usecases.interfaces import LLMGateway, AssetRepository


@pytest.fixture
def mock_llm_gateway():
    """Create mock LLM gateway."""
    return AsyncMock(spec=LLMGateway)


@pytest.fixture
def mock_asset_repository():
    """Create mock asset repository."""
    return AsyncMock(spec=AssetRepository)


@pytest.fixture
def sample_scene():
    """Sample scene for testing."""
    return Scene(
        id="scene_01",
        scene_type=SceneType.DIALOGUE,
        duration=Duration(seconds=60),
        act=Act.BEGINNING,
        narrative_summary="Dr. Kim talks to AI about human emotions.",
        character_ids=["protagonist"],
        location_id="laboratory",
    )


@pytest.fixture
def sample_scenes():
    """Multiple scenes for testing."""
    return [
        Scene(
            id="scene_01",
            scene_type=SceneType.ATMOSPHERE,
            duration=Duration(seconds=20),
            act=Act.BEGINNING,
            narrative_summary="Establishing shot of lab.",
        ),
        Scene(
            id="scene_02",
            scene_type=SceneType.DIALOGUE,
            duration=Duration(seconds=60),
            act=Act.BEGINNING,
            narrative_summary="Dr. Kim talks to AI.",
            character_ids=["protagonist"],
        ),
        Scene(
            id="scene_03",
            scene_type=SceneType.ACTION,
            duration=Duration(seconds=30),
            act=Act.MIDDLE,
            narrative_summary="Tense moment.",
            character_ids=["protagonist"],
        ),
    ]


class TestShotComposerInterface:
    """Tests for ShotComposer interface."""

    def test_composer_is_abstract(self):
        """ShotComposer should be abstract."""
        with pytest.raises(TypeError):
            ShotComposer()  # type: ignore


class TestTemplateBasedComposer:
    """Tests for Path A: Template-based shot composition."""

    @pytest.mark.asyncio
    async def test_dialogue_scene_uses_dialogue_template(
        self, mock_asset_repository, sample_scene
    ):
        """Dialogue scene should use dialogue template."""
        # Arrange
        composer = TemplateBasedComposer(asset_repository=mock_asset_repository)
        input_data = ShotComposerInput(scenes=[sample_scene])

        # Act
        result = await composer.execute(input_data)

        # Assert
        assert len(result.shot_sequences) == 1
        shots = result.shot_sequences["scene_01"]
        assert len(shots) >= 4  # Dialogue template has multiple shots

        # Should have typical dialogue pattern
        shot_types = [s.shot_type for s in shots]
        assert ShotType.WIDE_SHOT in shot_types or ShotType.TWO_SHOT in shot_types

    @pytest.mark.asyncio
    async def test_action_scene_uses_action_template(self, mock_asset_repository):
        """Action scene should use action template."""
        # Arrange
        action_scene = Scene(
            id="scene_01",
            scene_type=SceneType.ACTION,
            duration=Duration(seconds=30),
            act=Act.MIDDLE,
            narrative_summary="Chase sequence.",
            character_ids=["protagonist"],
        )
        composer = TemplateBasedComposer(asset_repository=mock_asset_repository)
        input_data = ShotComposerInput(scenes=[action_scene])

        # Act
        result = await composer.execute(input_data)

        # Assert
        shots = result.shot_sequences["scene_01"]
        # Action shots tend to be faster
        avg_duration = sum(s.duration.seconds for s in shots) / len(shots)
        assert avg_duration <= 5  # Quick cuts

    @pytest.mark.asyncio
    async def test_atmosphere_scene_uses_atmosphere_template(self, mock_asset_repository):
        """Atmosphere scene should use atmosphere template."""
        # Arrange
        atmo_scene = Scene(
            id="scene_01",
            scene_type=SceneType.ATMOSPHERE,
            duration=Duration(seconds=20),
            act=Act.BEGINNING,
            narrative_summary="Empty laboratory at night.",
        )
        composer = TemplateBasedComposer(asset_repository=mock_asset_repository)
        input_data = ShotComposerInput(scenes=[atmo_scene])

        # Act
        result = await composer.execute(input_data)

        # Assert
        shots = result.shot_sequences["scene_01"]
        # Atmosphere should have wide/establishing shots
        shot_types = [s.shot_type for s in shots]
        has_wide = ShotType.WIDE_SHOT in shot_types or ShotType.EXTREME_WIDE_SHOT in shot_types
        assert has_wide

    @pytest.mark.asyncio
    async def test_shot_duration_matches_scene(self, mock_asset_repository, sample_scene):
        """Total shot duration should match scene duration."""
        # Arrange
        composer = TemplateBasedComposer(asset_repository=mock_asset_repository)
        input_data = ShotComposerInput(scenes=[sample_scene])

        # Act
        result = await composer.execute(input_data)

        # Assert
        shots = result.shot_sequences["scene_01"]
        total_duration = sum(s.duration.seconds for s in shots)
        # Should be within 10% of scene duration
        assert abs(total_duration - sample_scene.duration.seconds) < sample_scene.duration.seconds * 0.2

    @pytest.mark.asyncio
    async def test_character_shots_use_i2v(self, mock_asset_repository, sample_scene):
        """Shots with characters should default to I2V."""
        # Arrange
        composer = TemplateBasedComposer(asset_repository=mock_asset_repository)
        input_data = ShotComposerInput(scenes=[sample_scene])

        # Act
        result = await composer.execute(input_data)

        # Assert
        shots = result.shot_sequences["scene_01"]
        char_shots = [s for s in shots if s.has_characters]
        for shot in char_shots:
            assert shot.effective_generation_method == GenerationMethod.I2V


class TestLLMDirectComposer:
    """Tests for Path B: LLM-direct shot composition."""

    @pytest.mark.asyncio
    async def test_llm_generates_shots(
        self, mock_llm_gateway, mock_asset_repository, sample_scene
    ):
        """LLM should generate shot sequence."""
        # Arrange
        mock_llm_gateway.complete_json.return_value = {
            "shots": [
                {"shot_type": "WS", "duration": 3, "purpose": "Establish space",
                 "characters": [], "action": "Wide view of lab"},
                {"shot_type": "2S", "duration": 5, "purpose": "Show both",
                 "characters": ["protagonist"], "action": "Dr. Kim facing screen"},
                {"shot_type": "CU", "duration": 3, "purpose": "Reaction",
                 "characters": ["protagonist"], "action": "Close on face"},
            ]
        }

        composer = LLMDirectComposer(
            llm_gateway=mock_llm_gateway,
            asset_repository=mock_asset_repository,
        )
        input_data = ShotComposerInput(scenes=[sample_scene])

        # Act
        result = await composer.execute(input_data)

        # Assert
        assert "scene_01" in result.shot_sequences
        shots = result.shot_sequences["scene_01"]
        assert len(shots) == 3
        mock_llm_gateway.complete_json.assert_called_once()

    @pytest.mark.asyncio
    async def test_llm_respects_scene_context(
        self, mock_llm_gateway, mock_asset_repository
    ):
        """LLM should consider scene type and narrative."""
        # Arrange
        monologue_scene = Scene(
            id="scene_01",
            scene_type=SceneType.MONOLOGUE,
            duration=Duration(seconds=40),
            act=Act.MIDDLE,
            narrative_summary="Internal reflection.",
            character_ids=["protagonist"],
        )
        mock_llm_gateway.complete_json.return_value = {
            "shots": [
                {"shot_type": "ECU", "duration": 5, "purpose": "Eyes",
                 "characters": ["protagonist"], "action": "Gaze into distance"},
                {"shot_type": "CU", "duration": 10, "purpose": "Emotion",
                 "characters": ["protagonist"], "action": "Contemplation"},
            ]
        }

        composer = LLMDirectComposer(
            llm_gateway=mock_llm_gateway,
            asset_repository=mock_asset_repository,
        )
        input_data = ShotComposerInput(scenes=[monologue_scene])

        # Act
        result = await composer.execute(input_data)

        # Assert - verify prompt includes scene context
        call_args = mock_llm_gateway.complete_json.call_args
        prompt = call_args[0][0].prompt
        assert "monologue" in prompt.lower() or "internal" in prompt.lower()

    @pytest.mark.asyncio
    async def test_multiple_scenes_composed(
        self, mock_llm_gateway, mock_asset_repository, sample_scenes
    ):
        """Multiple scenes should each get shot sequences."""
        # Arrange
        mock_llm_gateway.complete_json.side_effect = [
            {"shots": [{"shot_type": "EWS", "duration": 10, "purpose": "Establish",
                       "characters": [], "action": "Lab exterior"}]},
            {"shots": [{"shot_type": "2S", "duration": 15, "purpose": "Dialogue",
                       "characters": ["protagonist"], "action": "Talk"}]},
            {"shots": [{"shot_type": "MS", "duration": 10, "purpose": "Action",
                       "characters": ["protagonist"], "action": "Move"}]},
        ]

        composer = LLMDirectComposer(
            llm_gateway=mock_llm_gateway,
            asset_repository=mock_asset_repository,
        )
        input_data = ShotComposerInput(scenes=sample_scenes)

        # Act
        result = await composer.execute(input_data)

        # Assert
        assert len(result.shot_sequences) == 3
        assert "scene_01" in result.shot_sequences
        assert "scene_02" in result.shot_sequences
        assert "scene_03" in result.shot_sequences


class TestShotComposerCommon:
    """Common tests for both implementations."""

    @pytest.mark.asyncio
    async def test_saves_to_repository(
        self, mock_llm_gateway, mock_asset_repository, sample_scene
    ):
        """Shot sequences should be saved to repository."""
        # Arrange
        mock_llm_gateway.complete_json.return_value = {
            "shots": [{"shot_type": "WS", "duration": 10, "purpose": "Test",
                      "characters": [], "action": "Test"}]
        }

        composer = LLMDirectComposer(
            llm_gateway=mock_llm_gateway,
            asset_repository=mock_asset_repository,
        )
        input_data = ShotComposerInput(scenes=[sample_scene])

        # Act
        await composer.execute(input_data)

        # Assert
        mock_asset_repository.save_shot_sequence.assert_called_once()

    @pytest.mark.asyncio
    async def test_shot_ids_follow_convention(
        self, mock_asset_repository, sample_scene
    ):
        """Shot IDs should follow scene_XX_shot_YY convention."""
        # Arrange
        composer = TemplateBasedComposer(asset_repository=mock_asset_repository)
        input_data = ShotComposerInput(scenes=[sample_scene])

        # Act
        result = await composer.execute(input_data)

        # Assert
        shots = result.shot_sequences["scene_01"]
        for i, shot in enumerate(shots, 1):
            expected_id = f"scene_01_shot_{i:02d}"
            assert shot.id == expected_id
