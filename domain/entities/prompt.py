"""
Prompt entity for video generation.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from domain.value_objects import ShotType


@dataclass
class CinematographySpec:
    """
    Cinematography specification from L3 DB.

    Contains technical details for the shot.
    """

    shot_framing: str
    camera_angle: Optional[str] = None
    camera_movement: Optional[str] = None
    lighting_type: Optional[str] = None
    lighting_quality: Optional[str] = None
    color_grade: Optional[str] = None
    atmosphere_fx: Optional[str] = None

    def to_prompt_string(self) -> str:
        """Convert to prompt-ready string."""
        parts = [self.shot_framing]

        if self.camera_angle:
            parts.append(f"{self.camera_angle} angle")
        if self.camera_movement:
            parts.append(self.camera_movement)
        if self.lighting_type:
            parts.append(self.lighting_type)
        if self.lighting_quality:
            parts.append(self.lighting_quality)
        if self.color_grade:
            parts.append(f"{self.color_grade} color grade")
        if self.atmosphere_fx:
            parts.append(self.atmosphere_fx)

        return ", ".join(parts)


@dataclass
class Prompt:
    """
    Prompt entity representing the final prompt for video generation.

    Combines multiple components:
    - Shot description
    - Character fixed_prompts
    - Scene context
    - Cinematography specs from L3 DB
    - Style keywords
    - Negative prompts
    """

    shot_id: str
    shot_type: ShotType
    purpose: str
    character_prompts: list[str] = field(default_factory=list)
    scene_context: Optional[str] = None
    cinematography: Optional[CinematographySpec] = None
    style_keywords: list[str] = field(default_factory=list)
    negative_prompts: list[str] = field(default_factory=list)

    def get_sections(self) -> dict[str, str]:
        """Get prompt broken into sections."""
        sections = {
            "shot": f"{self.shot_type.value} shot, {self.purpose}",
        }

        if self.character_prompts:
            sections["characters"] = ". ".join(self.character_prompts)

        if self.scene_context:
            sections["context"] = self.scene_context

        if self.cinematography:
            sections["cinematography"] = self.cinematography.to_prompt_string()

        if self.style_keywords:
            sections["style"] = ", ".join(self.style_keywords)

        if self.negative_prompts:
            sections["negative"] = ", ".join(self.negative_prompts)

        return sections

    def build(self, max_length: int = 400, compact: bool = True) -> str:
        """
        Build final prompt string.

        Based on cinematic_pipeline_decisions.md learnings:
        - Minimize prompt length (300~400 chars)
        - Remove VFX instructions
        - Focus on scene context and natural motion
        - Avoid redundancy

        Args:
            max_length: Maximum length for the prompt (default 400).
            compact: If True, omit redundant elements like negative prompts.

        Returns:
            Final prompt string ready for API.
        """
        parts = []

        # Scene context first (most important for narrative preservation)
        if self.scene_context:
            parts.append(self.scene_context)

        # Shot framing (brief)
        if self.cinematography:
            # Only include essential framing info
            framing = self.cinematography.shot_framing
            if self.cinematography.camera_movement:
                framing += f", {self.cinematography.camera_movement}"
            parts.append(framing)
        else:
            parts.append(f"{self.shot_type.value} shot")

        # Characters (only fixed_prompt, no prefix)
        if self.character_prompts:
            # Join character prompts directly without "Characters:" prefix
            parts.extend(self.character_prompts)

        # Style keywords (minimal - only if compact mode off)
        if not compact and self.style_keywords:
            # Filter to essential style keywords
            essential_styles = [s for s in self.style_keywords if s.lower() not in ["cinematic", "4k quality"]]
            if essential_styles:
                parts.append(", ".join(essential_styles[:2]))  # Max 2

        # Build main prompt
        main_prompt = ". ".join(parts)

        # Add standard cinematic suffix (always useful)
        if compact:
            main_prompt += ". Natural subtle movements. Cinematic."

        # Negative prompts only in non-compact mode
        if not compact and self.negative_prompts:
            main_prompt += f". Negative: {', '.join(self.negative_prompts[:3])}"  # Max 3

        # Truncate if needed
        if len(main_prompt) > max_length:
            main_prompt = main_prompt[: max_length - 3] + "..."

        return main_prompt

    def __eq__(self, other: object) -> bool:
        """Prompts are equal if they have the same shot_id."""
        if not isinstance(other, Prompt):
            return False
        return self.shot_id == other.shot_id

    def __hash__(self) -> int:
        """Hash based on shot_id."""
        return hash(self.shot_id)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "shot_id": self.shot_id,
            "shot_type": self.shot_type.value,
            "purpose": self.purpose,
            "character_prompts": self.character_prompts,
            "scene_context": self.scene_context,
            "cinematography": (
                self.cinematography.to_prompt_string() if self.cinematography else None
            ),
            "style_keywords": self.style_keywords,
            "negative_prompts": self.negative_prompts,
            "final_prompt": self.build(),
        }
