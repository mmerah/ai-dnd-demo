"""Metadata service for extracting information from messages."""

import re

from app.interfaces.services import IMetadataService


class MetadataService(IMetadataService):
    """Extracts metadata from message content following Single Responsibility Principle.

    Only handles metadata extraction from text content.
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
