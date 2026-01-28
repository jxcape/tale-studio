"""Cinematography Knowledge DB interface for AVA Framework."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TechniqueEntry:
    """A single technique entry in the knowledge database."""

    id: str
    name: str
    prompt_fragment: str
    emotional_tags: list[str] = field(default_factory=list)
    shot_type_affinity: list[str] = field(default_factory=list)
    description: str = ""


class CinematographyKnowledgeDB(ABC):
    """Abstract interface for cinematography knowledge database."""

    @abstractmethod
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
            moods: Filter by emotional tags
            shot_type: Filter by shot type affinity (e.g., "CU", "MS", "WS")
            limit: Maximum number of results

        Returns:
            List of matching technique entries
        """
        pass

    @abstractmethod
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
        pass
