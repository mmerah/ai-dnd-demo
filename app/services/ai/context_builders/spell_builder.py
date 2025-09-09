import logging

from app.common.exceptions import RepositoryNotFoundError
from app.interfaces.services.data import ISpellRepository
from app.models.game_state import GameState

from .base import ContextBuilder

logger = logging.getLogger(__name__)


class SpellContextBuilder(ContextBuilder):
    """Build known spells context using the spell repository, if any."""

    def __init__(self, spell_repository: ISpellRepository) -> None:
        self.spell_repository = spell_repository

    def build(self, game_state: GameState) -> str | None:
        char_state = game_state.character.state
        if not char_state.spellcasting or not char_state.spellcasting.spells_known:
            return None

        spells = char_state.spellcasting.spells_known
        context_parts = ["Known Spells:"]

        for spell_name in spells[:10]:  # Limit to avoid context overflow
            try:
                spell_def = self.spell_repository.get(spell_name)
                context_parts.append(f"  • {spell_name} (Level {spell_def.level}): {spell_def.description[:100]}...")
            except RepositoryNotFoundError:
                # Allow AI game master to improvise with spells not in repository
                # Mark them clearly as non-standard for transparency
                logger.warning(f"Spell '{spell_name}' not found in spell repository")
                context_parts.append(f"  • {spell_name} [NOT IN REPOSITORY - Improvise mechanics as needed]")

        return "\n".join(context_parts)
