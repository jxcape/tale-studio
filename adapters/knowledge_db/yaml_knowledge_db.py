"""YAML-based implementation of CinematographyKnowledgeDB."""
from pathlib import Path
from typing import Optional

import yaml

from usecases.interfaces import CinematographyKnowledgeDB, TechniqueEntry


class YAMLKnowledgeDB(CinematographyKnowledgeDB):
    """
    YAML file-based implementation of CinematographyKnowledgeDB.

    Loads technique data from YAML files and provides query interface.
    """

    VALID_CATEGORIES = {"camera_language", "rendering_style", "shot_grammar"}

    def __init__(self, data_dir: Path):
        """
        Initialize with data directory.

        Args:
            data_dir: Path to directory containing YAML files

        Raises:
            ValueError: If data_dir does not exist or is not a directory
        """
        self._data_dir = Path(data_dir).resolve()

        if not self._data_dir.exists():
            raise ValueError(f"Data directory does not exist: {self._data_dir}")
        if not self._data_dir.is_dir():
            raise ValueError(f"Data path is not a directory: {self._data_dir}")

        self._cache: dict[str, list[TechniqueEntry]] = {}

    def _load_category(self, category: str) -> list[TechniqueEntry]:
        """Load and cache a category from YAML file."""
        if category not in self.VALID_CATEGORIES:
            raise ValueError(f"Invalid category: {category}. Must be one of {self.VALID_CATEGORIES}")

        if category not in self._cache:
            path = self._data_dir / f"{category}.yaml"
            if not path.exists():
                raise FileNotFoundError(f"Knowledge file not found: {path}")

            try:
                with open(path, encoding="utf-8") as f:
                    data = yaml.safe_load(f)
            except yaml.YAMLError as e:
                raise ValueError(f"Invalid YAML in {category}.yaml: {e}") from e

            if not isinstance(data, dict) or "techniques" not in data:
                raise ValueError(f"Invalid structure in {category}.yaml: missing 'techniques' key")

            try:
                self._cache[category] = [
                    TechniqueEntry(
                        id=t["id"],
                        name=t["name"],
                        prompt_fragment=t["prompt_fragment"],
                        emotional_tags=t.get("emotional_tags", []),
                        shot_type_affinity=t.get("shot_type_affinity", []),
                        description=t.get("description", ""),
                    )
                    for t in data.get("techniques", [])
                ]
            except KeyError as e:
                raise ValueError(f"Missing required field in {category}.yaml: {e}") from e

        return self._cache[category]

    def query(
        self,
        category: str,
        moods: Optional[list[str]] = None,
        shot_type: Optional[str] = None,
        limit: int = 3,
    ) -> list[TechniqueEntry]:
        """
        Query techniques by category and optional filters.

        Args:
            category: "camera_language", "rendering_style", or "shot_grammar"
            moods: Filter by emotional tags (any match)
            shot_type: Filter by shot type affinity
            limit: Maximum number of results

        Returns:
            List of matching technique entries
        """
        entries = self._load_category(category)

        # Filter by moods (any match)
        if moods:
            entries = [
                e for e in entries
                if any(m in e.emotional_tags for m in moods)
            ]

        # Filter by shot type
        if shot_type:
            entries = [
                e for e in entries
                if shot_type in e.shot_type_affinity
            ]

        return entries[:limit]

    def get_by_id(
        self, category: str, technique_id: str
    ) -> Optional[TechniqueEntry]:
        """
        Get a specific technique by ID.

        Args:
            category: The category to search in
            technique_id: The technique ID

        Returns:
            The technique entry if found, None otherwise
        """
        entries = self._load_category(category)
        return next((e for e in entries if e.id == technique_id), None)

    def clear_cache(self) -> None:
        """Clear the cached data (useful for testing)."""
        self._cache.clear()
