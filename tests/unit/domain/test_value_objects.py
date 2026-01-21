"""
Tests for domain value objects.
"""
import pytest

from domain.value_objects.duration import Duration
from domain.value_objects.scene_type import SceneType
from domain.value_objects.shot_type import ShotType
from domain.value_objects.generation_method import GenerationMethod
from domain.exceptions import (
    InvalidDurationError,
    InvalidSceneTypeError,
    InvalidShotTypeError,
    InvalidGenerationMethodError,
)


class TestDuration:
    """Tests for Duration value object."""

    def test_create_duration_in_seconds(self):
        duration = Duration(seconds=30)
        assert duration.seconds == 30
        assert duration.minutes == 0.5

    def test_create_duration_from_minutes(self):
        duration = Duration.from_minutes(2.5)
        assert duration.seconds == 150
        assert duration.minutes == 2.5

    def test_duration_invalid_negative(self):
        with pytest.raises(InvalidDurationError):
            Duration(seconds=-1)

    def test_duration_invalid_zero(self):
        with pytest.raises(InvalidDurationError):
            Duration(seconds=0)

    def test_duration_equality(self):
        d1 = Duration(seconds=30)
        d2 = Duration(seconds=30)
        d3 = Duration(seconds=60)
        assert d1 == d2
        assert d1 != d3

    def test_duration_add(self):
        d1 = Duration(seconds=30)
        d2 = Duration(seconds=20)
        result = d1 + d2
        assert result.seconds == 50

    def test_duration_immutable(self):
        d = Duration(seconds=30)
        with pytest.raises(AttributeError):
            d.seconds = 60  # type: ignore


class TestSceneType:
    """Tests for SceneType value object."""

    def test_valid_scene_types(self):
        assert SceneType.DIALOGUE.value == "dialogue"
        assert SceneType.ACTION.value == "action"
        assert SceneType.MONOLOGUE.value == "monologue"
        assert SceneType.ATMOSPHERE.value == "atmosphere"

    def test_from_string_valid(self):
        scene_type = SceneType.from_string("dialogue")
        assert scene_type == SceneType.DIALOGUE

    def test_from_string_case_insensitive(self):
        scene_type = SceneType.from_string("DIALOGUE")
        assert scene_type == SceneType.DIALOGUE

    def test_from_string_invalid(self):
        with pytest.raises(InvalidSceneTypeError):
            SceneType.from_string("invalid_type")


class TestShotType:
    """Tests for ShotType value object."""

    def test_valid_shot_types(self):
        assert ShotType.EXTREME_CLOSE_UP.value == "ECU"
        assert ShotType.CLOSE_UP.value == "CU"
        assert ShotType.MEDIUM_SHOT.value == "MS"
        assert ShotType.FULL_SHOT.value == "FS"
        assert ShotType.WIDE_SHOT.value == "WS"
        assert ShotType.EXTREME_WIDE_SHOT.value == "EWS"
        assert ShotType.OVER_THE_SHOULDER.value == "OTS"
        assert ShotType.TWO_SHOT.value == "2S"

    def test_from_string_valid(self):
        shot_type = ShotType.from_string("CU")
        assert shot_type == ShotType.CLOSE_UP

    def test_from_string_alias(self):
        shot_type = ShotType.from_string("close_up")
        assert shot_type == ShotType.CLOSE_UP

    def test_from_string_invalid(self):
        with pytest.raises(InvalidShotTypeError):
            ShotType.from_string("invalid")

    def test_is_character_focused(self):
        """Character-focused shots should be I2V candidates."""
        assert ShotType.CLOSE_UP.is_character_focused is True
        assert ShotType.EXTREME_CLOSE_UP.is_character_focused is True
        assert ShotType.MEDIUM_SHOT.is_character_focused is True
        assert ShotType.WIDE_SHOT.is_character_focused is False
        assert ShotType.EXTREME_WIDE_SHOT.is_character_focused is False


class TestGenerationMethod:
    """Tests for GenerationMethod value object."""

    def test_valid_methods(self):
        assert GenerationMethod.T2V.value == "T2V"
        assert GenerationMethod.I2V.value == "I2V"

    def test_from_string_valid(self):
        method = GenerationMethod.from_string("T2V")
        assert method == GenerationMethod.T2V

    def test_from_string_invalid(self):
        with pytest.raises(InvalidGenerationMethodError):
            GenerationMethod.from_string("invalid")

    def test_requires_reference_image(self):
        assert GenerationMethod.T2V.requires_reference_image is False
        assert GenerationMethod.I2V.requires_reference_image is True
