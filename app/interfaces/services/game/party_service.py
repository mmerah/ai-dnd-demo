"""Interface for party service."""

from abc import ABC, abstractmethod

from app.events.commands.location_commands import MoveNPCCommand
from app.models.game_state import GameState
from app.models.instances.npc_instance import NPCInstance


class IPartyService(ABC):
    """Party-specific operations and management logic.

    Responsible for managing party membership, validation, and generating
    follow commands when the player moves between locations.
    """

    @abstractmethod
    def add_member(self, game_state: GameState, npc_id: str) -> None:
        """Add an NPC to the party.

        Validates that:
        - NPC exists and is a major NPC
        - Party is not full (max 4 members)
        - NPC is not already in party
        - NPC is at same location as player

        Args:
            game_state: Current game state (modified in-place)
            npc_id: Instance ID of NPC to add

        Raises:
            ValueError: If validation fails (fail-fast)
        """
        pass

    @abstractmethod
    def remove_member(self, game_state: GameState, npc_id: str) -> None:
        """Remove an NPC from the party.

        Args:
            game_state: Current game state (modified in-place)
            npc_id: Instance ID of NPC to remove

        Raises:
            ValueError: If NPC is not in party
        """
        pass

    @abstractmethod
    def is_member(self, game_state: GameState, npc_id: str) -> bool:
        """Check if an NPC is in the party.

        Args:
            game_state: Current game state
            npc_id: Instance ID of NPC to check

        Returns:
            True if NPC is in party
        """
        pass

    @abstractmethod
    def list_members(self, game_state: GameState) -> list[NPCInstance]:
        """Get all party member NPCs.

        Args:
            game_state: Current game state

        Returns:
            List of NPC instances in the party
        """
        pass

    @abstractmethod
    def get_follow_commands(self, game_state: GameState, to_location_id: str) -> list[MoveNPCCommand]:
        """Generate move commands for party members to follow player.

        Only generates commands for members not already at the destination.

        Args:
            game_state: Current game state
            to_location_id: Destination location ID

        Returns:
            List of MoveNPCCommand for party members to follow
        """
        pass

    @abstractmethod
    def is_eligible(self, npc: NPCInstance) -> bool:
        """Check if an NPC is eligible to join the party.

        Only major NPCs can join the party.

        Args:
            npc: NPC instance to check

        Returns:
            True if NPC is eligible
        """
        pass
