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
from app.interfaces.services.data import IItemRepository, IMonsterRepository
from app.interfaces.services.game import IGameService
from app.interfaces.services.scenario import IScenarioService
from app.models.game_state import GameState
from app.models.location import DangerLevel
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
        game_service: IGameService,
        scenario_service: IScenarioService,
        monster_repository: IMonsterRepository,
        item_repository: IItemRepository,
    ):
        super().__init__(game_service)
        self.scenario_service = scenario_service
        self.monster_repository = monster_repository
        self.item_repository = item_repository

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

            # Get location from scenario to compute name and description
            if game_state.scenario_id:
                scenario = game_state.scenario_instance.sheet
                target_location = scenario.get_location(command.location_id)
                if not target_location:
                    raise ValueError(f"Location '{command.location_id}' not found in scenario '{scenario.id}'")

                # Compute location_name and description from scenario if not provided
                location_name = command.location_name or target_location.name
                description = command.description or target_location.get_description("first_visit")
            else:
                # Non-scenario location, require name and description
                if not command.location_name:
                    raise ValueError("Location name cannot be empty for non-scenario location")
                if not command.description:
                    raise ValueError("Location description cannot be empty for non-scenario location")
                location_name = command.location_name
                description = command.description

            # TODO(MVP2): Validate traversal from current location using scenario connections

            # Update game state location
            game_state.change_location(
                new_location_id=command.location_id,
                new_location_name=location_name,
                description=description,
            )

            # Initialize location state with NPCs from scenario if available
            if game_state.scenario_id:
                scenario = game_state.scenario_instance.sheet
                location = scenario.get_location(command.location_id)
                if location:
                    # Initialize from scenario only if not yet visited
                    self.game_service.initialize_location_from_scenario(game_state, location)

            # Save game state
            self.game_service.save_game(game_state)

            result.data = ChangeLocationResult(
                location_id=command.location_id,
                location_name=location_name,
                description=description,
                message=f"Moved to {location_name}",
            )

            # Broadcast update
            result.add_command(BroadcastGameUpdateCommand(game_id=command.game_id))

            logger.info(f"Location changed to: {location_name}")

        elif isinstance(command, DiscoverSecretCommand):
            # Validate secret ID
            if not command.secret_id:
                raise ValueError("Secret ID cannot be empty")

            # Update location state
            if not game_state.scenario_instance.is_in_known_location():
                raise ValueError("Cannot discover secret: current location is unknown")
            current_loc = game_state.scenario_instance.current_location_id
            location_state = game_state.get_location_state(current_loc)
            location_state.discover_secret(command.secret_id)

            # Use provided description or default to the secret ID
            secret_description = command.secret_description or f"Secret '{command.secret_id}'"

            # Save game state
            self.game_service.save_game(game_state)

            result.data = DiscoverSecretResult(
                secret_id=command.secret_id,
                description=secret_description,
                message=f"Discovered secret: {secret_description}",
            )

            # Broadcast update
            result.add_command(BroadcastGameUpdateCommand(game_id=command.game_id))

            logger.info(f"Secret discovered: {command.secret_id}")

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

            # Validate target location exists in scenario
            scenario = game_state.scenario_instance.sheet
            target = scenario.get_location(command.to_location_id)
            if not target:
                raise ValueError(f"Target location '{command.to_location_id}' not found in scenario")

            # Move NPC using GameState
            _ = game_state.move_npc(command.npc_id, command.to_location_id)

            # Save and broadcast
            self.game_service.save_game(game_state)

            result.data = MoveNPCResult(
                npc_id=command.npc_id,
                npc_name=npc.display_name,
                from_location_id=prev_loc,
                to_location_id=command.to_location_id,
                message=f"Moved {npc.display_name} to {target.name}",
            )

            result.add_command(BroadcastGameUpdateCommand(game_id=command.game_id))
            logger.info(f"Moved NPC {npc.display_name} to {target.name}")

        elif isinstance(command, UpdateLocationStateCommand):
            # Use current location if not specified, but validate it's known
            location_id = command.location_id or game_state.scenario_instance.current_location_id
            if not location_id or location_id == "unknown-location":
                raise ValueError("Cannot update state for unknown or unspecified location")
            location_state = game_state.get_location_state(location_id)
            updates = []

            # Update danger level
            if command.danger_level:
                try:
                    location_state.danger_level = DangerLevel(command.danger_level)
                    updates.append(f"Danger level: {command.danger_level}")
                except ValueError as e:
                    raise ValueError(f"Invalid danger level: {command.danger_level}") from e

            # Complete encounter
            if command.complete_encounter:
                location_state.complete_encounter(command.complete_encounter)
                updates.append(f"Completed encounter: {command.complete_encounter}")

            # Add effect
            if command.add_effect and command.add_effect not in location_state.active_effects:
                location_state.active_effects.append(command.add_effect)
                updates.append(f"Added effect: {command.add_effect}")

            # Save game state
            self.game_service.save_game(game_state)

            result.data = UpdateLocationStateResult(
                location_id=location_id,
                updates=updates,
                message=f"Location state updated: {', '.join(updates)}",
            )

            # Broadcast update
            result.add_command(BroadcastGameUpdateCommand(game_id=command.game_id))

            logger.info(f"Location state updated: {updates}")

        return result
