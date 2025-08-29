"""Service for extracting metadata from messages following Single Responsibility Principle."""

from app.models.game_state import GameState
from app.models.npc import NPCSheet


class MessageMetadataService:
    """Service responsible for extracting metadata from messages."""

    def extract_npc_mentions(self, content: str, npcs: list[NPCSheet]) -> list[str]:
        """
        Extract NPC names mentioned in the message content.

        Args:
            content: The message content to search
            npcs: List of NPCs currently in the game

        Returns:
            List of NPC names found in the content
        """
        mentioned_npcs = []
        content_lower = content.lower()

        for npc in npcs:
            # Check if NPC name appears in the message (case-insensitive)
            if npc.name.lower() in content_lower:
                mentioned_npcs.append(npc.name)

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
