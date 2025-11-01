"""Builder for roleplay information (background, personality, alignment, backstory, memories)."""

import logging
from datetime import datetime

from app.common.exceptions import RepositoryNotFoundError
from app.models.game_state import GameState
from app.models.instances.character_instance import CharacterInstance
from app.models.instances.npc_instance import NPCInstance

from .base import BuildContext, EntityContextBuilder

logger = logging.getLogger(__name__)


class RoleplayInfoBuilder(EntityContextBuilder):
    """Build roleplay information for a character or NPC.

    Includes:
    - Background and feature
    - Personality traits (traits, ideals, bonds, flaws)
    - Alignment
    - Languages
    - Backstory
    - Recent memories (for NPCs only)
    """

    MAX_MEMORIES = 3

    def build(
        self,
        game_state: GameState,
        context: BuildContext,
        entity: CharacterInstance | NPCInstance,
    ) -> str | None:
        # Extract character sheet based on entity type
        if isinstance(entity, NPCInstance):
            char_sheet = entity.sheet.character
            entity_name = entity.display_name
        else:  # CharacterInstance
            char_sheet = entity.sheet
            entity_name = char_sheet.name

        # Skip if no background specified
        if not char_sheet.background:
            return None

        context_parts = [f"Roleplay Info for {entity_name}:"]

        # Background
        if char_sheet.background:
            context_parts.append(f"• Background: {char_sheet.background}")
            try:
                background_def = context.background_repository.get(char_sheet.background)
                if background_def.feature:
                    context_parts.append(f"  Feature: {background_def.feature.name}")
                    context_parts.append(f"  {background_def.feature.description}")
            except RepositoryNotFoundError:
                logger.warning(f"Background '{char_sheet.background}' not found in repository")

        # Personality traits
        personality = char_sheet.personality
        if personality.traits:
            context_parts.append(f"• Traits: {', '.join(personality.traits)}")
        if personality.ideals:
            context_parts.append(f"• Ideals: {', '.join(personality.ideals)}")
        if personality.bonds:
            context_parts.append(f"• Bonds: {', '.join(personality.bonds)}")
        if personality.flaws:
            context_parts.append(f"• Flaws: {', '.join(personality.flaws)}")

        # Alignment
        if char_sheet.alignment:
            context_parts.append(f"• Alignment: {char_sheet.alignment}")

        # Languages
        if char_sheet.languages:
            context_parts.append(f"• Languages: {', '.join(char_sheet.languages)}")

        # Backstory
        if char_sheet.backstory:
            context_parts.append(f"• Backstory: {char_sheet.backstory}")

        # Recent memories (NPCs only)
        if isinstance(entity, NPCInstance) and entity.npc_memories:
            recent_memories = entity.npc_memories[-self.MAX_MEMORIES :]
            if recent_memories:
                context_parts.append("• Recent Memories:")
                for memory in reversed(recent_memories):
                    timestamp = self._format_timestamp(memory.created_at)
                    context_parts.append(f"  - [{timestamp}] {memory.summary}")

        return "\n".join(context_parts)

    @staticmethod
    def _format_timestamp(dt: datetime) -> str:
        """Format timestamp for memory entries."""
        return dt.strftime("%Y-%m-%d %H:%M")
