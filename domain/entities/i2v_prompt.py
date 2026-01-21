"""
I2V (Image-to-Video) Prompt entity for video generation.

Separates static image prompt (Imagen) from motion prompt (Veo).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class I2VPrompt:
    """
    I2V Prompt entity for Image-to-Video generation.

    Contains two separate prompts:
    - imagen_prompt: For generating static keyframe image
    - veo_prompt: For animating the image with motion/camera
    """

    shot_id: str
    scene_id: str

    # Imagen prompt (static keyframe)
    imagen_prompt: str

    # Veo prompt (motion/camera)
    veo_prompt: str

    # Metadata
    duration_seconds: float = 8.0
    aspect_ratio: str = "16:9"

    # Style settings
    style_preset: Optional[str] = None
    negative_prompt: Optional[str] = None

    # Generation tracking
    imagen_generated: bool = False
    imagen_path: Optional[str] = None
    veo_generated: bool = False
    veo_path: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "shot_id": self.shot_id,
            "scene_id": self.scene_id,
            "imagen_prompt": self.imagen_prompt,
            "veo_prompt": self.veo_prompt,
            "duration_seconds": self.duration_seconds,
            "aspect_ratio": self.aspect_ratio,
            "style_preset": self.style_preset,
            "negative_prompt": self.negative_prompt,
            "imagen_generated": self.imagen_generated,
            "imagen_path": self.imagen_path,
            "veo_generated": self.veo_generated,
            "veo_path": self.veo_path,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "I2VPrompt":
        """Create from dictionary."""
        return cls(
            shot_id=data["shot_id"],
            scene_id=data["scene_id"],
            imagen_prompt=data["imagen_prompt"],
            veo_prompt=data["veo_prompt"],
            duration_seconds=data.get("duration_seconds", 8.0),
            aspect_ratio=data.get("aspect_ratio", "16:9"),
            style_preset=data.get("style_preset"),
            negative_prompt=data.get("negative_prompt"),
            imagen_generated=data.get("imagen_generated", False),
            imagen_path=data.get("imagen_path"),
            veo_generated=data.get("veo_generated", False),
            veo_path=data.get("veo_path"),
        )
