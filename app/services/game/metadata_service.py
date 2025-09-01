"""Metadata service for extracting information from messages."""

import logging
import re
from collections.abc import Sequence

from app.interfaces.services import IMetadataService
from app.models.game_state import GameState
from app.models.npc import NPCSheet

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

    def extract_location(self, content: str, current_location: str | None) -> str | None:
        """Extract location from content.

        Args:
            content: Message content to analyze
            current_location: Current location for context

        Returns:
            Extracted location or None
        """
        # Look for common location transition phrases
        location_patterns = [
            r"(?:arrive at|enter|reach|approach|move to|head to|travel to|walk into|step into)\s+(?:the\s+)?([A-Z][a-zA-Z\s]+)",
            r"You (?:are|stand|find yourself) (?:in|at|inside|within)\s+(?:the\s+)?([A-Z][a-zA-Z\s]+)",
            r"Welcome to\s+(?:the\s+)?([A-Z][a-zA-Z\s]+)",
        ]

        for pattern in location_patterns:
            match = re.search(pattern, content)
            if match:
                location = match.group(1).strip()
                # Clean up common endings
                location = re.sub(r"\s*[.!?,]$", "", location)
                return location

        # If no new location found, return current location
        return current_location

    def extract_combat_round(self, content: str, in_combat: bool) -> int | None:
        """Extract combat round from content.

        Args:
            content: Message content to analyze
            in_combat: Whether currently in combat

        Returns:
            Combat round number or None
        """
        if not in_combat:
            return None

        # Look for round mentions
        round_patterns = [
            r"Round\s+(\d+)",
            r"round\s+(\d+)",
            r"Combat\s+Round:\s*(\d+)",
            r"Beginning\s+round\s+(\d+)",
            r"Start\s+of\s+round\s+(\d+)",
        ]

        for pattern in round_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    continue

        return None

    def extract_npc_mentions(self, content: str, npcs: Sequence[NPCSheet | str]) -> list[str]:
        """Extract NPC mentions from content with flexible NPC types.

        Args:
            content: Message content to analyze
            npcs: List of NPCs (either NPCSheet objects or string names)

        Returns:
            List of NPC names found in the content
        """
        # Convert NPCSheets to names
        npc_names = []
        for npc in npcs:
            if isinstance(npc, str):
                npc_names.append(npc)
            elif hasattr(npc, "name"):
                npc_names.append(npc.name)
            else:
                # Log error but continue
                logger.error(f"Invalid NPC type in extract_npc_mentions: {type(npc)}")
                continue

        # Use existing method
        return self.extract_npcs_mentioned(content, npc_names)

    def get_current_location(self, game_state: GameState) -> str:
        """Get the current location from game state.

        Args:
            game_state: Current game state

        Returns:
            Current location name
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
