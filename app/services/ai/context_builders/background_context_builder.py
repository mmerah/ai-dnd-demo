"""Builder for character background context."""

import logging

from app.common.exceptions import RepositoryNotFoundError
from app.models.game_state import GameState

from .base import BuildContext, ContextBuilder

logger = logging.getLogger(__name__)


class BackgroundContextBuilder(ContextBuilder):
    """Build character background context for authentic roleplay."""

    def build(self, game_state: GameState, context: BuildContext) -> str | None:
        char_sheet = game_state.character.sheet

        # Skip if no background specified
        if not char_sheet.background:
            return None

        try:
            background = context.background_repository.get(char_sheet.background)
        except RepositoryNotFoundError:
            logger.warning(f"Background '{char_sheet.background}' not found in repository")
            return None

        context_parts = [f"Background: {background.name}"]

        # Add feature if available
        if background.feature:
            context_parts.append(f"- Feature: {background.feature.name}")
            context_parts.append(f"  {background.feature.description}")

        # Add character's selected personality traits
        personality = char_sheet.personality

        if personality.traits:
            context_parts.append(f"- Personality Traits: {', '.join(personality.traits)}")

        if personality.ideals:
            context_parts.append(f"- Ideals: {', '.join(personality.ideals)}")

        if personality.bonds:
            context_parts.append(f"- Bonds: {', '.join(personality.bonds)}")

        if personality.flaws:
            context_parts.append(f"- Flaws: {', '.join(personality.flaws)}")

        return "\n".join(context_parts)
