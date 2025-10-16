"""PartyService: encapsulates party management logic."""

from __future__ import annotations

import logging

from app.events.commands.location_commands import MoveNPCCommand
from app.interfaces.services.game import IPartyService
from app.models.game_state import GameState
from app.models.instances.npc_instance import NPCInstance
from app.models.npc import NPCImportance

logger = logging.getLogger(__name__)


class PartyService(IPartyService):
    """Default implementation for party-related operations."""

    def add_member(self, game_state: GameState, npc_id: str) -> None:
        # Cannot modify party during combat
        if game_state.combat.is_active:
            raise ValueError("Cannot add party members during active combat")

        # Validate NPC exists
        npc = game_state.get_npc_by_id(npc_id)
        if not npc:
            raise ValueError(f"NPC with id '{npc_id}' not found")

        # Validate major NPC only
        if not self.is_eligible(npc):
            raise ValueError(f"Only major NPCs can join the party. {npc.display_name} is a minor NPC.")

        # Validate same location
        if npc.current_location_id != game_state.scenario_instance.current_location_id:
            raise ValueError(
                f"NPC must be at the same location as the player. "
                f"{npc.display_name} is at '{npc.current_location_id}', "
                f"player is at '{game_state.scenario_instance.current_location_id}'"
            )

        # Validate not full and not duplicate (PartyState handles this)
        try:
            game_state.party.add_member(npc_id)
            logger.info(f"Added {npc.display_name} to party")
        except ValueError as e:
            raise ValueError(f"Cannot add {npc.display_name} to party: {e}") from e

    def remove_member(self, game_state: GameState, npc_id: str) -> None:
        # Cannot modify party during combat
        if game_state.combat.is_active:
            raise ValueError("Cannot remove party members during active combat")

        # Validate NPC is in party (PartyState handles this)
        npc = game_state.get_npc_by_id(npc_id)
        npc_name = npc.display_name if npc else npc_id
        try:
            game_state.party.remove_member(npc_id)
            logger.info(f"Removed {npc_name} from party")
        except ValueError as e:
            raise ValueError(f"Cannot remove {npc_name} from party: {e}") from e

    def is_member(self, game_state: GameState, npc_id: str) -> bool:
        return game_state.party.has_member(npc_id)

    def list_members(self, game_state: GameState) -> list[NPCInstance]:
        members: list[NPCInstance] = []
        for npc_id in game_state.party.member_ids:
            npc = game_state.get_npc_by_id(npc_id)
            if npc:
                members.append(npc)
            else:
                logger.warning(f"Party member {npc_id} not found in game state NPCs")
        return members

    def get_follow_commands(self, game_state: GameState, to_location_id: str) -> list[MoveNPCCommand]:
        commands: list[MoveNPCCommand] = []
        for npc_id in game_state.party.member_ids:
            npc = game_state.get_npc_by_id(npc_id)
            if not npc:
                logger.warning(f"Party member {npc_id} not found, skipping follow command")
                continue

            # Only move if not already at destination
            if npc.current_location_id != to_location_id:
                commands.append(
                    MoveNPCCommand(
                        game_id=game_state.game_id,
                        npc_id=npc_id,
                        to_location_id=to_location_id,
                    )
                )
                logger.debug(f"Generated follow command for {npc.display_name} to {to_location_id}")

        return commands

    def is_eligible(self, npc: NPCInstance) -> bool:
        return npc.importance == NPCImportance.MAJOR
