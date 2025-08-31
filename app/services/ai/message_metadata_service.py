"""Service for extracting metadata from messages following Single Responsibility Principle."""

import logging
from collections.abc import Sequence

from app.models.game_state import GameState
from app.models.npc import NPCSheet

logger = logging.getLogger(__name__)


class MessageMetadataService:
    """Service responsible for extracting metadata from messages."""

    def extract_npc_mentions(self, content: str, npcs: Sequence[NPCSheet | str]) -> list[str]:
        """
        Extract NPC names mentioned in the message content.

        Args:
            content: The message content to search
            npcs: List of NPCs (either NPCSheet objects or string names)

        Returns:
            List of NPC names found in the content
        """
        mentioned_npcs = []
        content_lower = content.lower()

        try:
            for npc in npcs:
                if isinstance(npc, str):
                    name = npc
                elif hasattr(npc, "name"):
                    name = npc.name
                else:
                    # Fail fast - log error and skip
                    logger.error(f"Invalid NPC type in extract_npc_mentions: {type(npc)}")
                    continue

                # Check if NPC name appears in the message (case-insensitive)
                if name.lower() in content_lower and name not in mentioned_npcs:
                    mentioned_npcs.append(name)
        except Exception as e:
            # Fail fast - log the error but don't crash
            logger.error(f"Error extracting NPC mentions: {e}", exc_info=True)

        return mentioned_npcs

    def get_current_location(self, game_state: GameState) -> str:
        """
        Get the current location from game state.

        Args:
            game_state: Current game state

        Returns:
            Current location name
        """
        return game_state.location

    def get_combat_round(self, game_state: GameState) -> int | None:
        """
        Get the current combat round if in combat.

        Args:
            game_state: Current game state

        Returns:
            Current combat round number or None if not in combat
        """
        if game_state.combat and game_state.combat.is_active:
            return game_state.combat.round_number
        return None
