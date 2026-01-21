"""
UseCase Layer (Level 1-3).

Exports all use cases for the video generation pipeline.
"""

from usecases.scene_architect import (
    SceneArchitect,
    SceneArchitectInput,
    SceneArchitectOutput,
)
from usecases.shot_composer import (
    ShotComposer,
    TemplateBasedComposer,
    LLMDirectComposer,
    ShotComposerInput,
    ShotComposerOutput,
)
from usecases.prompt_builder import (
    PromptBuilder,
    PromptBuilderInput,
    PromptBuilderOutput,
)
from usecases.i2v_prompt_builder import (
    I2VPromptBuilder,
    I2VPromptBuilderInput,
    I2VPromptBuilderOutput,
    build_i2v_prompts,
)
from usecases.interfaces import (
    LLMGateway,
    LLMRequest,
    LLMResponse,
    ImageGenerator,
    ImageRequest,
    ImageResponse,
    VideoGenerator,
    VideoRequest,
    VideoJob,
    VideoStatus,
    AssetRepository,
)

__all__ = [
    # Level 1: Scene Architect
    "SceneArchitect",
    "SceneArchitectInput",
    "SceneArchitectOutput",
    # Level 2: Shot Composer
    "ShotComposer",
    "TemplateBasedComposer",
    "LLMDirectComposer",
    "ShotComposerInput",
    "ShotComposerOutput",
    # Level 3: Prompt Builder
    "PromptBuilder",
    "PromptBuilderInput",
    "PromptBuilderOutput",
    # Level 3: I2V Prompt Builder (LLM-based)
    "I2VPromptBuilder",
    "I2VPromptBuilderInput",
    "I2VPromptBuilderOutput",
    "build_i2v_prompts",
    # Ports (Interfaces)
    "LLMGateway",
    "LLMRequest",
    "LLMResponse",
    "ImageGenerator",
    "ImageRequest",
    "ImageResponse",
    "VideoGenerator",
    "VideoRequest",
    "VideoJob",
    "VideoStatus",
    "AssetRepository",
]
