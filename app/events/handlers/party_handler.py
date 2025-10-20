"""Handler for party management commands."""

import logging

from app.events.base import BaseCommand, CommandResult
from app.events.commands.broadcast_commands import BroadcastGameUpdateCommand
from app.events.commands.party_commands import AddPartyMemberCommand, RemovePartyMemberCommand
from app.events.handlers.base_handler import BaseHandler
from app.interfaces.services.game import IPartyService
from app.models.game_state import GameState
from app.models.tool_results import AddPartyMemberResult, RemovePartyMemberResult

logger = logging.getLogger(__name__)


class PartyHandler(BaseHandler):
    """Handler for party management commands."""

    def __init__(self, party_service: IPartyService):
        self.party_service = party_service

    supported_commands = (
        AddPartyMemberCommand,
        RemovePartyMemberCommand,
    )

    async def handle(self, command: BaseCommand, game_state: GameState) -> CommandResult:
        """Handle party commands."""
        result = CommandResult()

        if isinstance(command, AddPartyMemberCommand):
            if not command.npc_id:
                raise ValueError("NPC ID cannot be empty")

            # Delegate to PartyService
            self.party_service.add_member(game_state, command.npc_id)

            # Get NPC for display info after successful addition
            npc = game_state.get_npc_by_id(command.npc_id)
            # Fallback should never happen
            npc_name = npc.display_name if npc else command.npc_id

            result.mutated = True
            result.data = AddPartyMemberResult(
                npc_id=command.npc_id,
                npc_name=npc_name,
                party_size=len(game_state.party.member_ids),
                message=f"{npc_name} has joined the party! ({len(game_state.party.member_ids)}/{game_state.party.max_size})",
            )

            # Broadcast update
            result.add_command(BroadcastGameUpdateCommand(game_id=command.game_id))
            logger.info(f"Added {npc_name} to party")

        elif isinstance(command, RemovePartyMemberCommand):
            if not command.npc_id:
                raise ValueError("NPC ID cannot be empty")

            # Get NPC for display info before removal
            npc = game_state.get_npc_by_id(command.npc_id)
            npc_name = npc.display_name if npc else command.npc_id

            # Delegate to PartyService (DRY)
            self.party_service.remove_member(game_state, command.npc_id)
            result.mutated = True
            result.data = RemovePartyMemberResult(
                npc_id=command.npc_id,
                npc_name=npc_name,
                party_size=len(game_state.party.member_ids),
                message=f"{npc_name} has left the party. ({len(game_state.party.member_ids)}/{game_state.party.max_size})",
            )

            # Broadcast update
            result.add_command(BroadcastGameUpdateCommand(game_id=command.game_id))
            logger.info(f"Removed {npc_name} from party")

        return result
