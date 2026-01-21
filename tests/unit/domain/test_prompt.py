"""
Tests for Prompt entity.
"""
import pytest

from domain.entities.prompt import Prompt, CinematographySpec
from domain.value_objects import ShotType


class TestCinematographySpec:
    """Tests for CinematographySpec value object."""

    def test_create_cinematography_spec(self):
        spec = CinematographySpec(
            shot_framing="Close-up",
            camera_angle="Eye-level",
            camera_movement="Static",
            lighting_type="Natural, soft window light",
        )
        assert spec.shot_framing == "Close-up"
        assert spec.camera_angle == "Eye-level"

    def test_cinematography_spec_to_prompt_string(self):
        """Spec should convert to prompt-ready string."""
        spec = CinematographySpec(
            shot_framing="Close-up",
            camera_angle="Eye-level",
            camera_movement="Slow push-in",
            lighting_type="Warm golden hour",
            lighting_quality="Soft, diffused",
        )
        prompt_str = spec.to_prompt_string()
        assert "Close-up" in prompt_str
        assert "Eye-level" in prompt_str
        assert "Slow push-in" in prompt_str
        assert "Warm golden hour" in prompt_str

    def test_cinematography_spec_minimal(self):
        """Spec with only required fields."""
        spec = CinematographySpec(
            shot_framing="Wide shot",
        )
        prompt_str = spec.to_prompt_string()
        assert "Wide shot" in prompt_str


class TestPrompt:
    """Tests for Prompt entity."""

    def test_create_prompt_minimal(self):
        """Create prompt with minimal fields."""
        prompt = Prompt(
            shot_id="scene_01_shot_01",
            shot_type=ShotType.WIDE_SHOT,
            purpose="Establish the space",
        )
        assert prompt.shot_id == "scene_01_shot_01"
        assert prompt.shot_type == ShotType.WIDE_SHOT

    def test_create_prompt_full(self):
        """Create prompt with all components."""
        cinematography = CinematographySpec(
            shot_framing="Close-up",
            camera_angle="Low angle",
            camera_movement="Dolly in",
            lighting_type="Dramatic side lighting",
        )
        prompt = Prompt(
            shot_id="scene_01_shot_01",
            shot_type=ShotType.CLOSE_UP,
            purpose="Show character emotion",
            character_prompts=["45-year-old male, tired eyes, white lab coat"],
            scene_context="Dr. Kim realizes the truth about the AI",
            cinematography=cinematography,
            style_keywords=["Cinematic", "4K", "Professional"],
            negative_prompts=["CGI", "3D render", "cartoon"],
        )
        assert len(prompt.character_prompts) == 1
        assert prompt.scene_context is not None
        assert prompt.cinematography is not None

    def test_prompt_build_final(self):
        """Build final prompt string from components."""
        cinematography = CinematographySpec(
            shot_framing="Close-up",
            camera_angle="Eye-level",
            lighting_type="Soft natural light",
        )
        prompt = Prompt(
            shot_id="scene_01_shot_02",
            shot_type=ShotType.CLOSE_UP,
            purpose="Character reaction",
            character_prompts=["45-year-old Asian male, round glasses, white lab coat"],
            scene_context="Dr. Kim looks at the screen with surprise",
            cinematography=cinematography,
            style_keywords=["Cinematic", "Raw photo", "4K"],
        )
        final = prompt.build()

        # Should contain key elements
        assert "Close-up" in final
        assert "45-year-old Asian male" in final
        assert "Dr. Kim looks at the screen" in final
        assert "Cinematic" in final

    def test_prompt_build_without_character(self):
        """Build prompt for atmosphere shot without characters."""
        prompt = Prompt(
            shot_id="scene_01_shot_01",
            shot_type=ShotType.EXTREME_WIDE_SHOT,
            purpose="Establishing shot",
            scene_context="Empty laboratory at night",
            cinematography=CinematographySpec(
                shot_framing="Extreme wide shot",
                lighting_type="Cool blue moonlight",
            ),
            style_keywords=["Cinematic", "Atmospheric"],
        )
        final = prompt.build()

        assert "Extreme wide shot" in final
        assert "Empty laboratory" in final
        # In compact mode, lighting_type is not included - that's intentional

    def test_prompt_build_with_negative(self):
        """Negative prompts should be included in non-compact mode."""
        prompt = Prompt(
            shot_id="scene_01_shot_01",
            shot_type=ShotType.MEDIUM_SHOT,
            purpose="Test",
            negative_prompts=["CGI", "cartoon", "anime"],
        )
        # Non-compact mode includes negative prompts
        final = prompt.build(compact=False)

        # Negative prompts typically prefixed
        assert "CGI" in final or "Negative:" in final

    def test_prompt_sections(self):
        """Prompt should have structured sections."""
        cinematography = CinematographySpec(
            shot_framing="Medium shot",
            camera_angle="Eye-level",
        )
        prompt = Prompt(
            shot_id="scene_01_shot_01",
            shot_type=ShotType.MEDIUM_SHOT,
            purpose="Dialogue",
            character_prompts=["Young woman, professional attire"],
            scene_context="Business meeting",
            cinematography=cinematography,
            style_keywords=["Professional", "Corporate"],
        )
        sections = prompt.get_sections()

        assert "shot" in sections
        assert "characters" in sections
        assert "context" in sections
        assert "cinematography" in sections
        assert "style" in sections

    def test_prompt_max_length(self):
        """Prompt should respect max length if specified."""
        prompt = Prompt(
            shot_id="scene_01_shot_01",
            shot_type=ShotType.WIDE_SHOT,
            purpose="Test",
            scene_context="A very long context " * 100,  # Long context
            style_keywords=["Word"] * 50,  # Many keywords
        )
        final = prompt.build(max_length=500)
        assert len(final) <= 500

    def test_prompt_equality(self):
        """Prompts with same shot_id are equal."""
        p1 = Prompt(
            shot_id="scene_01_shot_01",
            shot_type=ShotType.WIDE_SHOT,
            purpose="V1",
        )
        p2 = Prompt(
            shot_id="scene_01_shot_01",
            shot_type=ShotType.CLOSE_UP,  # Different
            purpose="V2",
        )
        p3 = Prompt(
            shot_id="scene_01_shot_02",
            shot_type=ShotType.WIDE_SHOT,
            purpose="V3",
        )
        assert p1 == p2
        assert p1 != p3

    def test_prompt_to_dict(self):
        """Prompt should be serializable to dict."""
        prompt = Prompt(
            shot_id="scene_01_shot_01",
            shot_type=ShotType.CLOSE_UP,
            purpose="Character focus",
            character_prompts=["Test character"],
            style_keywords=["Cinematic"],
        )
        data = prompt.to_dict()
        assert data["shot_id"] == "scene_01_shot_01"
        assert data["shot_type"] == "CU"
        assert "final_prompt" in data
