"""Metadata service for extracting information from messages."""

import logging

from app.interfaces.services.game import IMetadataService
from app.models.game_state import GameState

logger = logging.getLogger(__name__)


class MetadataService(IMetadataService):
    """
    Handles all metadata extraction from messages and game state.
    """

    def extract_npcs_mentioned(self, content: str, known_npcs: list[str]) -> list[str]:
        """Extract NPC names mentioned in content.

        Args:
            content: Message content to analyze
            known_npcs: List of known NPC names

        Returns:
            List of mentioned NPC names
        """
        mentioned_npcs = []
        content_lower = content.lower()

        for npc_name in known_npcs:
            # Check if NPC name appears in content (case-insensitive)
            if npc_name.lower() in content_lower and npc_name not in mentioned_npcs:
                mentioned_npcs.append(npc_name)

        return mentioned_npcs

    def get_current_location(self, game_state: GameState) -> str | None:
        """Get the current location

        Args:
            game_state: Current game state

        Returns:
            Current location or None if not available
        """
        return game_state.location

    def get_combat_round(self, game_state: GameState) -> int | None:
        """Get the current combat round if in combat.

        Args:
            game_state: Current game state

        Returns:
            Current combat round number or None if not in combat
        """
        if game_state.combat and game_state.combat.is_active:
            return game_state.combat.round_number
        return None
