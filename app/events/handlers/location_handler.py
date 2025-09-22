"""Handler for location and navigation commands."""

import logging

from app.events.base import BaseCommand, CommandResult
from app.events.commands.broadcast_commands import BroadcastGameUpdateCommand
from app.events.commands.location_commands import (
    ChangeLocationCommand,
    DiscoverSecretCommand,
    MoveNPCCommand,
    UpdateLocationStateCommand,
)
from app.events.handlers.base_handler import BaseHandler
from app.interfaces.services.game import ILocationService
from app.interfaces.services.memory import IMemoryService
from app.models.game_state import GameState
from app.models.memory import MemoryEventKind, WorldEventContext
from app.models.tool_results import (
    ChangeLocationResult,
    DiscoverSecretResult,
    MoveNPCResult,
    UpdateLocationStateResult,
)

logger = logging.getLogger(__name__)


class LocationHandler(BaseHandler):
    """Handler for location and navigation commands."""

    def __init__(
        self,
        location_service: ILocationService,
        memory_service: IMemoryService,
    ):
        self.location_service = location_service
        self.memory_service = memory_service

    supported_commands = (
        ChangeLocationCommand,
        DiscoverSecretCommand,
        MoveNPCCommand,
        UpdateLocationStateCommand,
    )

    async def handle(self, command: BaseCommand, game_state: GameState) -> CommandResult:
        """Handle location commands."""
        result = CommandResult()

        if isinstance(command, ChangeLocationCommand):
            # Fail-fast validation
            if not command.location_id:
                raise ValueError("Location ID cannot be empty")

            # Validate traversal if in a known location
            if game_state.scenario_instance.is_in_known_location():
                current_location_id = game_state.scenario_instance.current_location_id
                self.location_service.validate_traversal(game_state, current_location_id, command.location_id)

            await self.memory_service.on_location_exit(game_state)

            # Move the player
            self.location_service.move_entity(
                game_state,
                entity_id=game_state.character.instance_id,
                to_location_id=command.location_id,
                location_name=command.location_name,
                description=command.description,
            )

            result.mutated = True

            result.data = ChangeLocationResult(
                location_id=command.location_id,
                location_name=game_state.location,
                description=game_state.description,
                message=f"Moved to {game_state.location}",
            )

            # Broadcast update
            result.add_command(BroadcastGameUpdateCommand(game_id=command.game_id))
            logger.debug(f"Location changed to: {command.location_name}")

        elif isinstance(command, DiscoverSecretCommand):
            secret_description = self.location_service.discover_secret(
                game_state,
                command.secret_id,
                command.secret_description,
            )

            result.mutated = True

            result.data = DiscoverSecretResult(
                secret_id=command.secret_id,
                description=secret_description,
                message=f"Discovered secret: {secret_description}",
            )

            # Broadcast update
            result.add_command(BroadcastGameUpdateCommand(game_id=command.game_id))
            logger.debug(f"Secret discovered: {command.secret_id}")

        elif isinstance(command, MoveNPCCommand):
            # Validate IDs
            if not command.npc_id:
                raise ValueError("NPC ID cannot be empty")
            if not command.to_location_id:
                raise ValueError("Target location ID cannot be empty")

            # Get NPC to check it exists and get previous location
            npc = game_state.get_npc_by_id(command.npc_id)
            if not npc:
                raise ValueError(f"NPC with id '{command.npc_id}' not found")
            prev_loc = npc.current_location_id

            self.location_service.move_entity(
                game_state,
                entity_id=command.npc_id,
                to_location_id=command.to_location_id,
            )

            # Get target location name for result
            scenario = game_state.scenario_instance.sheet
            target = scenario.get_location(command.to_location_id)
            target_name = target.name if target else command.to_location_id

            result.mutated = True

            result.data = MoveNPCResult(
                npc_id=command.npc_id,
                npc_name=npc.display_name,
                from_location_id=prev_loc,
                to_location_id=command.to_location_id,
                message=f"Moved {npc.display_name} to {target_name}",
            )

            result.add_command(BroadcastGameUpdateCommand(game_id=command.game_id))
            logger.debug(f"Moved NPC {npc.display_name} to {target_name}")

        elif isinstance(command, UpdateLocationStateCommand):
            location_id, updates = self.location_service.update_location_state(
                game_state,
                location_id=command.location_id,
                danger_level=command.danger_level,
                complete_encounter=command.complete_encounter,
                add_effect=command.add_effect,
            )

            # Mutated if any update applied
            result.mutated = len(updates) > 0

            result.data = UpdateLocationStateResult(
                location_id=location_id,
                updates=updates,
                message=f"Location (ID: {location_id}) state updated: {', '.join(updates)}",
            )

            # Broadcast update
            result.add_command(BroadcastGameUpdateCommand(game_id=command.game_id))
            logger.debug(f"Location state updated: {updates}")

            context = WorldEventContext(location_id=location_id)
            if command.danger_level and command.danger_level.lower() == "cleared":
                await self.memory_service.on_world_event(
                    game_state,
                    event_kind=MemoryEventKind.LOCATION_CLEARED,
                    context=context,
                )

            if command.complete_encounter:
                encounter_context = WorldEventContext(
                    location_id=location_id,
                    encounter_id=command.complete_encounter,
                )
                await self.memory_service.on_world_event(
                    game_state,
                    event_kind=MemoryEventKind.ENCOUNTER_COMPLETED,
                    context=encounter_context,
                )

        return result
