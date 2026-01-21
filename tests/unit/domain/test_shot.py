"""
Tests for Shot entity.
"""
import pytest

from domain.entities.shot import Shot
from domain.value_objects import Duration, ShotType, GenerationMethod
from domain.exceptions import DomainError


class TestShot:
    """Tests for Shot entity."""

    def test_create_shot_minimal(self):
        """Create shot with required fields only."""
        shot = Shot(
            id="scene_01_shot_01",
            scene_id="scene_01",
            shot_type=ShotType.WIDE_SHOT,
            duration=Duration(seconds=3),
            purpose="Establish the space",
        )
        assert shot.id == "scene_01_shot_01"
        assert shot.scene_id == "scene_01"
        assert shot.shot_type == ShotType.WIDE_SHOT
        assert shot.duration.seconds == 3
        assert shot.purpose == "Establish the space"

    def test_create_shot_with_characters(self):
        """Create shot with character anchors."""
        shot = Shot(
            id="scene_01_shot_02",
            scene_id="scene_01",
            shot_type=ShotType.CLOSE_UP,
            duration=Duration(seconds=2),
            purpose="Character reaction",
            character_ids=["protagonist"],
        )
        assert shot.character_ids == ["protagonist"]

    def test_create_shot_with_generation_method(self):
        """Create shot with explicit generation method."""
        shot = Shot(
            id="scene_01_shot_01",
            scene_id="scene_01",
            shot_type=ShotType.CLOSE_UP,
            duration=Duration(seconds=2),
            purpose="Focus on character",
            generation_method=GenerationMethod.I2V,
        )
        assert shot.generation_method == GenerationMethod.I2V

    def test_shot_auto_generation_method_with_characters(self):
        """Shot with characters should default to I2V."""
        shot = Shot(
            id="scene_01_shot_01",
            scene_id="scene_01",
            shot_type=ShotType.CLOSE_UP,
            duration=Duration(seconds=2),
            purpose="Character focus",
            character_ids=["protagonist"],
        )
        # Not explicitly set, should infer I2V
        assert shot.effective_generation_method == GenerationMethod.I2V

    def test_shot_auto_generation_method_without_characters(self):
        """Shot without characters should default to T2V."""
        shot = Shot(
            id="scene_01_shot_01",
            scene_id="scene_01",
            shot_type=ShotType.EXTREME_WIDE_SHOT,
            duration=Duration(seconds=5),
            purpose="Landscape",
        )
        assert shot.effective_generation_method == GenerationMethod.T2V

    def test_shot_explicit_method_overrides_inference(self):
        """Explicit generation method should override inference."""
        shot = Shot(
            id="scene_01_shot_01",
            scene_id="scene_01",
            shot_type=ShotType.WIDE_SHOT,
            duration=Duration(seconds=3),
            purpose="Wide with character, but force T2V",
            character_ids=["protagonist"],
            generation_method=GenerationMethod.T2V,  # Explicit override
        )
        assert shot.effective_generation_method == GenerationMethod.T2V

    def test_shot_number_extraction(self):
        """Extract shot number from ID."""
        shot = Shot(
            id="scene_02_shot_05",
            scene_id="scene_02",
            shot_type=ShotType.MEDIUM_SHOT,
            duration=Duration(seconds=4),
            purpose="Test",
        )
        assert shot.number == 5

    def test_shot_has_characters(self):
        """Check if shot has character anchors."""
        shot_with = Shot(
            id="scene_01_shot_01",
            scene_id="scene_01",
            shot_type=ShotType.CLOSE_UP,
            duration=Duration(seconds=2),
            purpose="With char",
            character_ids=["protagonist"],
        )
        shot_without = Shot(
            id="scene_01_shot_02",
            scene_id="scene_01",
            shot_type=ShotType.WIDE_SHOT,
            duration=Duration(seconds=3),
            purpose="No char",
        )
        assert shot_with.has_characters is True
        assert shot_without.has_characters is False

    def test_shot_requires_reference_image(self):
        """Check if shot requires reference image based on method."""
        shot_i2v = Shot(
            id="scene_01_shot_01",
            scene_id="scene_01",
            shot_type=ShotType.CLOSE_UP,
            duration=Duration(seconds=2),
            purpose="I2V shot",
            character_ids=["protagonist"],
        )
        shot_t2v = Shot(
            id="scene_01_shot_02",
            scene_id="scene_01",
            shot_type=ShotType.EXTREME_WIDE_SHOT,
            duration=Duration(seconds=5),
            purpose="T2V shot",
        )
        assert shot_i2v.requires_reference_image is True
        assert shot_t2v.requires_reference_image is False

    def test_shot_invalid_id_format(self):
        """Shot ID must follow format."""
        with pytest.raises(DomainError):
            Shot(
                id="invalid_shot",
                scene_id="scene_01",
                shot_type=ShotType.WIDE_SHOT,
                duration=Duration(seconds=3),
                purpose="Invalid",
            )

    def test_shot_scene_id_mismatch(self):
        """Shot ID must match scene_id."""
        with pytest.raises(DomainError):
            Shot(
                id="scene_02_shot_01",  # Says scene_02
                scene_id="scene_01",     # But linked to scene_01
                shot_type=ShotType.WIDE_SHOT,
                duration=Duration(seconds=3),
                purpose="Mismatch",
            )

    def test_shot_equality(self):
        """Shots with same ID are equal."""
        shot1 = Shot(
            id="scene_01_shot_01",
            scene_id="scene_01",
            shot_type=ShotType.WIDE_SHOT,
            duration=Duration(seconds=3),
            purpose="V1",
        )
        shot2 = Shot(
            id="scene_01_shot_01",
            scene_id="scene_01",
            shot_type=ShotType.CLOSE_UP,  # Different
            duration=Duration(seconds=5),  # Different
            purpose="V2",
        )
        shot3 = Shot(
            id="scene_01_shot_02",
            scene_id="scene_01",
            shot_type=ShotType.WIDE_SHOT,
            duration=Duration(seconds=3),
            purpose="V3",
        )
        assert shot1 == shot2
        assert shot1 != shot3

    def test_shot_to_dict(self):
        """Shot should be serializable to dict."""
        shot = Shot(
            id="scene_01_shot_01",
            scene_id="scene_01",
            shot_type=ShotType.CLOSE_UP,
            duration=Duration(seconds=2),
            purpose="Character focus",
            character_ids=["protagonist"],
            action_description="Looking thoughtfully",
        )
        data = shot.to_dict()
        assert data["id"] == "scene_01_shot_01"
        assert data["scene_id"] == "scene_01"
        assert data["shot_type"] == "CU"
        assert data["duration_seconds"] == 2
        assert data["purpose"] == "Character focus"
        assert data["character_ids"] == ["protagonist"]
        assert data["action_description"] == "Looking thoughtfully"
