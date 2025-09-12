"""Metadata service for extracting information from messages."""

import logging

from app.interfaces.services.game import IMetadataService
from app.models.game_state import GameState

logger = logging.getLogger(__name__)


class MetadataService(IMetadataService):
    """Handles all metadata extraction from messages and game state."""

    def extract_npcs_mentioned(self, content: str, known_npcs: list[str]) -> list[str]:
        mentioned_npcs = []
        content_lower = content.lower()

        for npc_name in known_npcs:
            # Check if NPC name appears in content (case-insensitive)
            if npc_name.lower() in content_lower and npc_name not in mentioned_npcs:
                mentioned_npcs.append(npc_name)

        return mentioned_npcs

    def get_current_location(self, game_state: GameState) -> str | None:
        return game_state.location

    def get_combat_round(self, game_state: GameState) -> int | None:
        if game_state.combat.is_active:
            return game_state.combat.round_number
        return None
