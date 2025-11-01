import logging

from app.common.exceptions import RepositoryNotFoundError
from app.models.game_state import GameState
from app.models.instances.character_instance import CharacterInstance
from app.models.instances.npc_instance import NPCInstance

from .base import BuildContext, EntityContextBuilder

logger = logging.getLogger(__name__)


class SpellContextBuilder(EntityContextBuilder):
    """Build known spells context using the spell repository.

    Builds spell context for any entity with spellcasting abilities.
    """

    MAX_SPELLS = 10

    def build(
        self,
        game_state: GameState,
        context: BuildContext,
        entity: CharacterInstance | NPCInstance,
    ) -> str | None:
        # Extract entity name based on type
        entity_name = entity.display_name if isinstance(entity, NPCInstance) else entity.sheet.name

        entity_state = entity.state
        if not entity_state.spellcasting or not entity_state.spellcasting.spells_known:
            return None

        spells = entity_state.spellcasting.spells_known
        context_parts = [f"Known Spells ({entity_name}):"]

        for spell_name in spells[: self.MAX_SPELLS]:
            try:
                spell_def = context.spell_repository.get(spell_name)
                context_parts.append(f"  • {spell_name} (Lvl {spell_def.level}): {spell_def.description[:100]}...")
            except RepositoryNotFoundError:
                # Allow AI game master to improvise with spells not in repository
                # Mark them clearly as non-standard for transparency
                logger.warning(f"Spell '{spell_name}' not found in spell repository")
                context_parts.append(f"  • {spell_name} [NOT IN REPOSITORY - Improvise mechanics as needed]")

        return "\n".join(context_parts)
