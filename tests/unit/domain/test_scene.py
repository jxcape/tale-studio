"""
Tests for Scene entity.
"""
import pytest

from domain.entities.scene import Scene, Act
from domain.value_objects import Duration, SceneType
from domain.exceptions import DomainError


class TestAct:
    """Tests for Act enum."""

    def test_act_values(self):
        assert Act.BEGINNING.value == "beginning"
        assert Act.MIDDLE.value == "middle"
        assert Act.END.value == "end"

    def test_act_percentage(self):
        """Act should have expected percentage of total runtime."""
        assert Act.BEGINNING.percentage == 0.25
        assert Act.MIDDLE.percentage == 0.50
        assert Act.END.percentage == 0.25


class TestScene:
    """Tests for Scene entity."""

    def test_create_scene_minimal(self):
        """Create scene with required fields only."""
        scene = Scene(
            id="scene_01",
            scene_type=SceneType.DIALOGUE,
            duration=Duration(seconds=30),
            act=Act.BEGINNING,
            narrative_summary="Two characters meet.",
        )
        assert scene.id == "scene_01"
        assert scene.scene_type == SceneType.DIALOGUE
        assert scene.duration.seconds == 30
        assert scene.act == Act.BEGINNING
        assert scene.narrative_summary == "Two characters meet."

    def test_create_scene_with_characters(self):
        """Create scene with character references."""
        scene = Scene(
            id="scene_01",
            scene_type=SceneType.DIALOGUE,
            duration=Duration(seconds=30),
            act=Act.BEGINNING,
            narrative_summary="Dr. Kim talks to AI.",
            character_ids=["protagonist", "ai_character"],
        )
        assert scene.character_ids == ["protagonist", "ai_character"]

    def test_create_scene_with_location(self):
        """Create scene with location reference."""
        scene = Scene(
            id="scene_01",
            scene_type=SceneType.ATMOSPHERE,
            duration=Duration(seconds=20),
            act=Act.BEGINNING,
            narrative_summary="Establishing shot of lab.",
            location_id="main_lab",
        )
        assert scene.location_id == "main_lab"

    def test_scene_number_from_id(self):
        """Extract scene number from ID."""
        scene = Scene(
            id="scene_03",
            scene_type=SceneType.ACTION,
            duration=Duration(seconds=45),
            act=Act.MIDDLE,
            narrative_summary="Chase sequence.",
        )
        assert scene.number == 3

    def test_scene_has_characters(self):
        """Check if scene has characters."""
        scene_with = Scene(
            id="scene_01",
            scene_type=SceneType.DIALOGUE,
            duration=Duration(seconds=30),
            act=Act.BEGINNING,
            narrative_summary="Dialogue.",
            character_ids=["protagonist"],
        )
        scene_without = Scene(
            id="scene_02",
            scene_type=SceneType.ATMOSPHERE,
            duration=Duration(seconds=20),
            act=Act.BEGINNING,
            narrative_summary="Empty room.",
        )
        assert scene_with.has_characters is True
        assert scene_without.has_characters is False

    def test_scene_default_generation_method(self):
        """Scene should suggest generation method based on characters."""
        scene_with_chars = Scene(
            id="scene_01",
            scene_type=SceneType.DIALOGUE,
            duration=Duration(seconds=30),
            act=Act.BEGINNING,
            narrative_summary="Dialogue.",
            character_ids=["protagonist"],
        )
        scene_without_chars = Scene(
            id="scene_02",
            scene_type=SceneType.ATMOSPHERE,
            duration=Duration(seconds=20),
            act=Act.BEGINNING,
            narrative_summary="Empty room.",
        )
        # Scenes with characters suggest I2V
        assert scene_with_chars.suggested_generation_method.value == "I2V"
        # Scenes without characters suggest T2V
        assert scene_without_chars.suggested_generation_method.value == "T2V"

    def test_scene_equality(self):
        """Scenes with same ID are equal."""
        scene1 = Scene(
            id="scene_01",
            scene_type=SceneType.DIALOGUE,
            duration=Duration(seconds=30),
            act=Act.BEGINNING,
            narrative_summary="V1.",
        )
        scene2 = Scene(
            id="scene_01",
            scene_type=SceneType.ACTION,  # Different type
            duration=Duration(seconds=60),  # Different duration
            act=Act.MIDDLE,  # Different act
            narrative_summary="V2.",
        )
        scene3 = Scene(
            id="scene_02",
            scene_type=SceneType.DIALOGUE,
            duration=Duration(seconds=30),
            act=Act.BEGINNING,
            narrative_summary="V3.",
        )
        assert scene1 == scene2  # Same ID
        assert scene1 != scene3  # Different ID

    def test_scene_invalid_id_format(self):
        """Scene ID must follow format."""
        with pytest.raises(DomainError):
            Scene(
                id="invalid",  # Not "scene_XX" format
                scene_type=SceneType.DIALOGUE,
                duration=Duration(seconds=30),
                act=Act.BEGINNING,
                narrative_summary="Test.",
            )

    def test_scene_to_dict(self):
        """Scene should be serializable to dict."""
        scene = Scene(
            id="scene_01",
            scene_type=SceneType.DIALOGUE,
            duration=Duration(seconds=30),
            act=Act.BEGINNING,
            narrative_summary="Test scene.",
            character_ids=["protagonist"],
            location_id="main_lab",
        )
        data = scene.to_dict()
        assert data["id"] == "scene_01"
        assert data["scene_type"] == "dialogue"
        assert data["duration_seconds"] == 30
        assert data["act"] == "beginning"
        assert data["narrative_summary"] == "Test scene."
        assert data["character_ids"] == ["protagonist"]
        assert data["location_id"] == "main_lab"
