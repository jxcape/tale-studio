"""
Tests for Character entity.
"""
import pytest

from domain.entities.character import Character, ReferenceImage, ReferenceAngle
from domain.exceptions import DomainError


class TestReferenceAngle:
    """Tests for ReferenceAngle enum."""

    def test_reference_angles(self):
        assert ReferenceAngle.FRONT.value == "front"
        assert ReferenceAngle.SIDE.value == "side"
        assert ReferenceAngle.THREE_QUARTER.value == "three_quarter"


class TestReferenceImage:
    """Tests for ReferenceImage value object."""

    def test_create_reference_image(self):
        ref = ReferenceImage(
            angle=ReferenceAngle.FRONT,
            path="/assets/characters/protagonist_front.png",
        )
        assert ref.angle == ReferenceAngle.FRONT
        assert ref.path == "/assets/characters/protagonist_front.png"

    def test_reference_image_filename(self):
        ref = ReferenceImage(
            angle=ReferenceAngle.FRONT,
            path="/assets/characters/protagonist_front.png",
        )
        assert ref.filename == "protagonist_front.png"


class TestCharacter:
    """Tests for Character entity."""

    def test_create_character_minimal(self):
        """Create character with required fields only."""
        char = Character(
            id="protagonist",
            name="Dr. Kim",
            age=45,
            gender="male",
            physical_description="Asian male, tired eyes",
        )
        assert char.id == "protagonist"
        assert char.name == "Dr. Kim"
        assert char.age == 45
        assert char.gender == "male"

    def test_create_character_full(self):
        """Create character with all fields."""
        char = Character(
            id="protagonist",
            name="Dr. Kim",
            age=45,
            gender="male",
            physical_description="Asian male, tired eyes, slight stubble",
            outfit="wrinkled white lab coat, loosened tie",
            face_details="round glasses, deep eye bags, contemplative expression",
        )
        assert char.outfit == "wrinkled white lab coat, loosened tie"
        assert char.face_details == "round glasses, deep eye bags, contemplative expression"

    def test_character_fixed_prompt(self):
        """Character should generate fixed_prompt for consistency."""
        char = Character(
            id="protagonist",
            name="Dr. Kim",
            age=45,
            gender="male",
            physical_description="Asian male, tired eyes",
            outfit="white lab coat",
            face_details="round glasses",
        )
        prompt = char.fixed_prompt
        # Should contain key attributes
        assert "45" in prompt or "forty-five" in prompt.lower()
        assert "male" in prompt.lower()
        assert "Asian" in prompt or "asian" in prompt
        assert "white lab coat" in prompt
        assert "round glasses" in prompt

    def test_character_fixed_prompt_minimal(self):
        """fixed_prompt should work with minimal info."""
        char = Character(
            id="extra",
            name="Passerby",
            age=30,
            gender="female",
            physical_description="Woman walking by",
        )
        prompt = char.fixed_prompt
        assert "30" in prompt or "thirty" in prompt.lower()
        assert "female" in prompt.lower() or "woman" in prompt.lower()

    def test_add_reference_image(self):
        """Add reference image to character."""
        char = Character(
            id="protagonist",
            name="Dr. Kim",
            age=45,
            gender="male",
            physical_description="Asian male",
        )
        char.add_reference(
            angle=ReferenceAngle.FRONT,
            path="/assets/characters/protagonist_front.png",
        )
        assert len(char.references) == 1
        assert char.references[0].angle == ReferenceAngle.FRONT

    def test_add_multiple_references(self):
        """Add multiple reference images (multi-angle)."""
        char = Character(
            id="protagonist",
            name="Dr. Kim",
            age=45,
            gender="male",
            physical_description="Asian male",
        )
        char.add_reference(ReferenceAngle.FRONT, "/path/front.png")
        char.add_reference(ReferenceAngle.SIDE, "/path/side.png")
        char.add_reference(ReferenceAngle.THREE_QUARTER, "/path/3q.png")
        assert len(char.references) == 3

    def test_get_reference_by_angle(self):
        """Get reference image by specific angle."""
        char = Character(
            id="protagonist",
            name="Dr. Kim",
            age=45,
            gender="male",
            physical_description="Asian male",
        )
        char.add_reference(ReferenceAngle.FRONT, "/path/front.png")
        char.add_reference(ReferenceAngle.SIDE, "/path/side.png")

        front = char.get_reference(ReferenceAngle.FRONT)
        assert front is not None
        assert front.path == "/path/front.png"

        back = char.get_reference(ReferenceAngle.THREE_QUARTER)
        assert back is None

    def test_has_references(self):
        """Check if character has reference images."""
        char = Character(
            id="protagonist",
            name="Dr. Kim",
            age=45,
            gender="male",
            physical_description="Asian male",
        )
        assert char.has_references is False

        char.add_reference(ReferenceAngle.FRONT, "/path/front.png")
        assert char.has_references is True

    def test_character_equality(self):
        """Characters with same ID are equal."""
        char1 = Character(
            id="protagonist",
            name="Dr. Kim",
            age=45,
            gender="male",
            physical_description="V1",
        )
        char2 = Character(
            id="protagonist",
            name="Kim",  # Different name
            age=50,  # Different age
            gender="male",
            physical_description="V2",
        )
        char3 = Character(
            id="antagonist",
            name="Dr. Kim",
            age=45,
            gender="male",
            physical_description="V3",
        )
        assert char1 == char2
        assert char1 != char3

    def test_character_to_dict(self):
        """Character should be serializable to dict."""
        char = Character(
            id="protagonist",
            name="Dr. Kim",
            age=45,
            gender="male",
            physical_description="Asian male, tired eyes",
            outfit="white lab coat",
            face_details="round glasses",
        )
        char.add_reference(ReferenceAngle.FRONT, "/path/front.png")

        data = char.to_dict()
        assert data["id"] == "protagonist"
        assert data["name"] == "Dr. Kim"
        assert data["age"] == 45
        assert data["gender"] == "male"
        assert "fixed_prompt" in data
        assert len(data["references"]) == 1
        assert data["references"][0]["angle"] == "front"

    def test_character_invalid_age(self):
        """Age must be positive."""
        with pytest.raises(DomainError):
            Character(
                id="invalid",
                name="Test",
                age=-5,
                gender="male",
                physical_description="Test",
            )

    def test_character_invalid_gender(self):
        """Gender must be valid."""
        with pytest.raises(DomainError):
            Character(
                id="invalid",
                name="Test",
                age=30,
                gender="invalid",
                physical_description="Test",
            )
