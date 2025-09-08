from app.interfaces.services.data import ISpellRepository
from app.models.game_state import GameState

from .base import ContextBuilder


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

        for spell_name in spells[:5]:  # Limit to avoid context overflow
            spell_def = self.spell_repository.get(spell_name)
            if spell_def:
                context_parts.append(f"  • {spell_name} (Level {spell_def.level}): {spell_def.description[:100]}...")
            else:
                context_parts.append(f"  • {spell_name}")

        return "\n".join(context_parts)
