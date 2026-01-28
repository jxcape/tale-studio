"""MusicToVideoAdapter - Facade for music-to-video pipeline."""
from pathlib import Path
from typing import Optional

from domain.entities.ava import Anchor, Expression
from domain.entities.music import MusicMetadata
from domain.value_objects.ava import BridgeMode
from usecases.ava import BridgeTranslator, ExpressionAdapter
from usecases.interfaces import CinematographyKnowledgeDB
from usecases.music import MusicToAnchor
from usecases.scene_architect import SceneArchitectInput


class MusicToVideoAdapter:
    """
    Facade that orchestrates the music-to-video conversion pipeline.

    Flow: MusicMetadata -> Anchor -> Expression -> SceneArchitectInput

    This adapter bridges the AVA Framework with the existing L1-L2-L3
    video generation pipeline.
    """

    def __init__(self, knowledge_db: CinematographyKnowledgeDB):
        """
        Initialize with a knowledge database.

        Args:
            knowledge_db: The cinematography knowledge database
        """
        self._music_to_anchor = MusicToAnchor()
        self._bridge = BridgeTranslator(knowledge_db)
        self._expression_adapter = ExpressionAdapter()

    @classmethod
    def from_yaml_db(cls, data_dir: Path) -> "MusicToVideoAdapter":
        """
        Factory method to create adapter with YAML knowledge database.

        Args:
            data_dir: Path to knowledge database YAML files

        Returns:
            Configured MusicToVideoAdapter instance
        """
        from adapters.knowledge_db import YAMLKnowledgeDB

        knowledge_db = YAMLKnowledgeDB(data_dir)
        return cls(knowledge_db)

    def execute(
        self,
        music: MusicMetadata,
        story_seed: Optional[str] = None,
        mode: BridgeMode = BridgeMode.INTUITIVE,
    ) -> SceneArchitectInput:
        """
        Convert music metadata to SceneArchitectInput.

        Args:
            music: The music metadata
            story_seed: Optional story text (e.g., lyrics or user input)
            mode: Translation mode (only INTUITIVE in MVP)

        Returns:
            SceneArchitectInput ready for the L1 pipeline
        """
        # Step 1: Music -> Anchor
        anchor = self._music_to_anchor.execute(music)

        # Step 2: Anchor -> Expression
        expression = self._bridge.translate(anchor, mode)

        # Step 3: Build story
        if story_seed:
            story = self._expression_adapter.build_enhanced_story(
                expression, story_seed
            )
        else:
            story = self._expression_adapter.build_enhanced_story(expression)

        # Step 4: Expression + story -> SceneArchitectInput
        duration_minutes = (music.duration_seconds or 120.0) / 60.0

        return self._expression_adapter.to_scene_input(
            expression=expression,
            story=story,
            duration_minutes=duration_minutes,
        )

    def get_expression(
        self,
        music: MusicMetadata,
        mode: BridgeMode = BridgeMode.INTUITIVE,
    ) -> Expression:
        """
        Get the Expression without converting to SceneArchitectInput.

        Useful for debugging or when you need intermediate results.

        Args:
            music: The music metadata
            mode: Translation mode

        Returns:
            The Expression generated from the music
        """
        anchor = self._music_to_anchor.execute(music)
        return self._bridge.translate(anchor, mode)

    def get_anchor(self, music: MusicMetadata) -> Anchor:
        """
        Get the Anchor without further processing.

        Useful for debugging or when you need intermediate results.

        Args:
            music: The music metadata

        Returns:
            The Anchor generated from the music
        """
        return self._music_to_anchor.execute(music)
