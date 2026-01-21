"""
Domain value objects.
"""
from domain.value_objects.duration import Duration
from domain.value_objects.generation_method import GenerationMethod
from domain.value_objects.scene_type import SceneType
from domain.value_objects.shot_type import ShotType
from domain.value_objects.style_heuristics import (
    StyleType,
    StyleHeuristics,
    SkinTextureSpec,
    MetalTextureSpec,
    LightingSpec,
    LightingMood,
    ColorSpec,
    CameraSpec,
    VFXSpec,
    MotionSpec,
)

__all__ = [
    "Duration",
    "GenerationMethod",
    "SceneType",
    "ShotType",
    "StyleType",
    "StyleHeuristics",
    "SkinTextureSpec",
    "MetalTextureSpec",
    "LightingSpec",
    "LightingMood",
    "ColorSpec",
    "CameraSpec",
    "VFXSpec",
    "MotionSpec",
]
