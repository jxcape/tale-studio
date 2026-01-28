"""Expression Adapter - converts Expression to SceneArchitectInput."""
from typing import Optional

from domain.entities.ava import Expression
from usecases.scene_architect import SceneArchitectInput


class ExpressionAdapter:
    """
    Adapts an AVA Expression to the existing pipeline's SceneArchitectInput.

    This is the bridge between the AVA Framework and the existing
    L1-L2-L3 pipeline.
    """

    # Atmosphere to genre mapping
    ATMOSPHERE_GENRE_MAP = {
        "melancholic": "drama",
        "hopeful": "drama",
        "tense": "thriller",
        "nostalgic": "drama",
        "epic": "action",
        "intimate": "drama",
        "chaotic": "action",
        "serene": "drama",
    }

    def to_scene_input(
        self,
        expression: Expression,
        story: str,
        duration_minutes: float = 2.0,
    ) -> SceneArchitectInput:
        """
        Convert an Expression to SceneArchitectInput.

        Args:
            expression: The AVA Expression to convert
            story: The story text (from lyrics, pumpup, or generated)
            duration_minutes: Target video duration in minutes

        Returns:
            A SceneArchitectInput ready for the L1 pipeline
        """
        return SceneArchitectInput(
            story=story,
            genre=self._infer_genre(expression),
            target_duration_minutes=duration_minutes,
            character_hints=self._build_character_hints(expression),
        )

    def _infer_genre(self, expression: Expression) -> str:
        """Infer genre from expression atmosphere."""
        atmosphere = expression.world.atmosphere
        return self.ATMOSPHERE_GENRE_MAP.get(atmosphere, "drama")

    def _build_character_hints(self, expression: Expression) -> list[dict]:
        """Build character hints from expression."""
        hints = []
        for i, hint in enumerate(expression.actor.character_hints):
            hints.append({
                "name": f"Character_{i+1}",
                "role": "auto",
                "description": hint,
            })
        return hints

    def build_enhanced_story(
        self,
        expression: Expression,
        story_seed: Optional[str] = None,
    ) -> str:
        """
        Build an enhanced story using Expression hints.

        If no story_seed is provided, generates a basic story
        from the Expression.

        Args:
            expression: The AVA Expression
            story_seed: Optional story seed (e.g., from lyrics)

        Returns:
            An enhanced story with visual context
        """
        if story_seed:
            # Enhance existing story with visual context
            return self._enhance_story(expression, story_seed)
        else:
            # Generate basic story from expression
            return self._generate_story(expression)

    def _enhance_story(self, expression: Expression, story_seed: str) -> str:
        """Enhance an existing story with visual context."""
        # Prepend visual context
        context = f"{expression.world.time_of_day.capitalize()}. "
        context += f"{expression.world.location}. "
        if expression.world.weather:
            context += f"{expression.world.weather}. "

        return f"{context}\n\n{story_seed}"

    def _generate_story(self, expression: Expression) -> str:
        """Generate a basic story from expression."""
        lines = [
            f"{expression.world.time_of_day.capitalize()}.",
            f"{expression.world.location}.",
        ]

        if expression.world.weather:
            lines.append(f"{expression.world.weather}.")

        lines.append(f"The atmosphere is {expression.world.atmosphere}.")

        if expression.actor.character_hints:
            lines.append("")
            for hint in expression.actor.character_hints:
                lines.append(hint)

        return "\n".join(lines)
