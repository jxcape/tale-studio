"""
Tests for SceneArchitect UseCase.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from domain.entities import Scene, Character, Act
from domain.value_objects import SceneType, Duration
from usecases.scene_architect import SceneArchitect, SceneArchitectInput
from usecases.interfaces import LLMGateway, LLMResponse, AssetRepository


@pytest.fixture
def mock_llm_gateway():
    """Create mock LLM gateway."""
    gateway = AsyncMock(spec=LLMGateway)
    return gateway


@pytest.fixture
def mock_asset_repository():
    """Create mock asset repository."""
    repo = AsyncMock(spec=AssetRepository)
    return repo


@pytest.fixture
def sample_input():
    """Sample input for scene architect."""
    return SceneArchitectInput(
        story="""
        외로운 AI 연구원 Dr. Kim은 자신이 만든 AI와 대화하며
        점점 인간성에 대해 깊이 고민하게 된다.
        결국 AI를 통해 자신의 진정한 감정을 발견한다.
        """,
        genre="drama",
        target_duration_minutes=3.0,
        character_hints=[
            {"name": "Dr. Kim", "role": "protagonist", "description": "45세 남성 연구원"},
        ],
    )


class TestSceneArchitect:
    """Tests for SceneArchitect UseCase."""

    @pytest.mark.asyncio
    async def test_analyze_story_extracts_scenes(
        self, mock_llm_gateway, mock_asset_repository, sample_input
    ):
        """SceneArchitect should extract scenes from story."""
        # Arrange - sample_input has character_hints, so LLM called twice
        mock_llm_gateway.complete_json.side_effect = [
            # First call: character definition
            {"characters": [{"id": "protagonist", "name": "Dr. Kim", "age": 45,
             "gender": "male", "physical_description": "Asian male"}]},
            # Second call: scene extraction
            {
                "scenes": [
                    {
                        "id": "scene_01",
                        "type": "atmosphere",
                        "duration_seconds": 20,
                        "act": "beginning",
                        "narrative": "연구실 전경, 밤",
                        "characters": [],
                        "location": "laboratory",
                    },
                    {
                        "id": "scene_02",
                        "type": "dialogue",
                        "duration_seconds": 60,
                        "act": "beginning",
                        "narrative": "Dr. Kim이 AI와 첫 대화",
                        "characters": ["protagonist"],
                        "location": "laboratory",
                    },
                    {
                        "id": "scene_03",
                        "type": "monologue",
                        "duration_seconds": 40,
                        "act": "middle",
                        "narrative": "Dr. Kim의 내면 독백",
                        "characters": ["protagonist"],
                        "location": "laboratory",
                    },
                    {
                        "id": "scene_04",
                        "type": "dialogue",
                        "duration_seconds": 60,
                        "act": "end",
                        "narrative": "깨달음의 순간",
                        "characters": ["protagonist"],
                        "location": "laboratory",
                    },
                ]
            },
        ]

        usecase = SceneArchitect(
            llm_gateway=mock_llm_gateway,
            asset_repository=mock_asset_repository,
        )

        # Act
        result = await usecase.execute(sample_input)

        # Assert
        assert len(result.scenes) == 4
        assert result.scenes[0].scene_type == SceneType.ATMOSPHERE
        assert result.scenes[1].scene_type == SceneType.DIALOGUE
        assert mock_llm_gateway.complete_json.call_count == 2  # characters + scenes

    @pytest.mark.asyncio
    async def test_defines_characters(
        self, mock_llm_gateway, mock_asset_repository, sample_input
    ):
        """SceneArchitect should define characters."""
        # Arrange
        mock_llm_gateway.complete_json.side_effect = [
            # First call: character definition
            {
                "characters": [
                    {
                        "id": "protagonist",
                        "name": "Dr. Kim",
                        "age": 45,
                        "gender": "male",
                        "physical_description": "Asian male, tired eyes, slight stubble",
                        "outfit": "wrinkled white lab coat",
                        "face_details": "round glasses, deep eye bags",
                    }
                ]
            },
            # Second call: scene extraction
            {
                "scenes": [
                    {
                        "id": "scene_01",
                        "type": "dialogue",
                        "duration_seconds": 60,
                        "act": "beginning",
                        "narrative": "Dr. Kim talks",
                        "characters": ["protagonist"],
                        "location": "lab",
                    }
                ]
            },
        ]

        usecase = SceneArchitect(
            llm_gateway=mock_llm_gateway,
            asset_repository=mock_asset_repository,
        )

        # Act
        result = await usecase.execute(sample_input)

        # Assert
        assert len(result.characters) == 1
        assert result.characters[0].name == "Dr. Kim"
        assert result.characters[0].age == 45
        assert "lab coat" in result.characters[0].fixed_prompt

    @pytest.mark.asyncio
    async def test_respects_target_duration(
        self, mock_llm_gateway, mock_asset_repository
    ):
        """Total scene duration should approximate target."""
        # Arrange
        target_minutes = 5.0
        input_data = SceneArchitectInput(
            story="A long story...",
            genre="action",
            target_duration_minutes=target_minutes,
        )

        mock_llm_gateway.complete_json.return_value = {
            "scenes": [
                {"id": f"scene_{i:02d}", "type": "action", "duration_seconds": 30,
                 "act": "middle", "narrative": f"Scene {i}", "characters": [], "location": "street"}
                for i in range(1, 11)  # 10 scenes × 30s = 300s = 5min
            ]
        }

        usecase = SceneArchitect(
            llm_gateway=mock_llm_gateway,
            asset_repository=mock_asset_repository,
        )

        # Act
        result = await usecase.execute(input_data)

        # Assert
        total_duration = sum(s.duration.seconds for s in result.scenes)
        assert abs(total_duration - target_minutes * 60) < 60  # Within 1 minute

    @pytest.mark.asyncio
    async def test_act_distribution(
        self, mock_llm_gateway, mock_asset_repository, sample_input
    ):
        """Scenes should follow act structure (25% / 50% / 25%)."""
        # Arrange
        mock_llm_gateway.complete_json.return_value = {
            "scenes": [
                {"id": "scene_01", "type": "atmosphere", "duration_seconds": 20,
                 "act": "beginning", "narrative": "Setup", "characters": [], "location": "lab"},
                {"id": "scene_02", "type": "dialogue", "duration_seconds": 25,
                 "act": "beginning", "narrative": "Intro", "characters": [], "location": "lab"},
                {"id": "scene_03", "type": "action", "duration_seconds": 45,
                 "act": "middle", "narrative": "Conflict 1", "characters": [], "location": "lab"},
                {"id": "scene_04", "type": "dialogue", "duration_seconds": 45,
                 "act": "middle", "narrative": "Conflict 2", "characters": [], "location": "lab"},
                {"id": "scene_05", "type": "monologue", "duration_seconds": 25,
                 "act": "end", "narrative": "Resolution", "characters": [], "location": "lab"},
                {"id": "scene_06", "type": "atmosphere", "duration_seconds": 20,
                 "act": "end", "narrative": "Ending", "characters": [], "location": "lab"},
            ]
        }

        usecase = SceneArchitect(
            llm_gateway=mock_llm_gateway,
            asset_repository=mock_asset_repository,
        )

        # Act
        result = await usecase.execute(sample_input)

        # Assert
        beginning = [s for s in result.scenes if s.act == Act.BEGINNING]
        middle = [s for s in result.scenes if s.act == Act.MIDDLE]
        end = [s for s in result.scenes if s.act == Act.END]

        assert len(beginning) >= 1
        assert len(middle) >= 1
        assert len(end) >= 1

    @pytest.mark.asyncio
    async def test_saves_to_repository(
        self, mock_llm_gateway, mock_asset_repository, sample_input
    ):
        """SceneArchitect should save results to repository."""
        # Arrange
        mock_llm_gateway.complete_json.return_value = {
            "scenes": [
                {"id": "scene_01", "type": "dialogue", "duration_seconds": 60,
                 "act": "beginning", "narrative": "Test", "characters": [], "location": "lab"}
            ]
        }

        usecase = SceneArchitect(
            llm_gateway=mock_llm_gateway,
            asset_repository=mock_asset_repository,
        )

        # Act
        await usecase.execute(sample_input)

        # Assert
        mock_asset_repository.save_scene_manifest.assert_called_once()

    @pytest.mark.asyncio
    async def test_handles_llm_error(
        self, mock_llm_gateway, mock_asset_repository, sample_input
    ):
        """SceneArchitect should handle LLM errors gracefully."""
        # Arrange
        mock_llm_gateway.complete_json.side_effect = Exception("LLM API Error")

        usecase = SceneArchitect(
            llm_gateway=mock_llm_gateway,
            asset_repository=mock_asset_repository,
        )

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await usecase.execute(sample_input)

        assert "LLM" in str(exc_info.value)
