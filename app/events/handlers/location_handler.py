"""Handler for location and navigation commands."""

import logging

from app.events.base import BaseCommand, CommandResult
from app.events.commands.broadcast_commands import BroadcastGameUpdateCommand
from app.events.commands.location_commands import (
    ChangeLocationCommand,
    DiscoverSecretCommand,
    UpdateLocationStateCommand,
)
from app.events.handlers.base_handler import BaseHandler
from app.interfaces.services import (
    IGameService,
    IItemRepository,
    IMonsterRepository,
    IScenarioService,
)
from app.models.game_state import GameState
from app.models.location import DangerLevel
from app.models.tool_results import (
    ChangeLocationResult,
    DiscoverSecretResult,
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

    async def handle(self, command: BaseCommand, game_state: GameState) -> CommandResult:
        """Handle location commands."""
        result = CommandResult()

        if isinstance(command, ChangeLocationCommand):
            # Update game state location
            game_state.change_location(
                new_location_id=command.location_id,
                new_location_name=command.location_name,
                description=command.description,
            )

            # Initialize location state with NPCs from scenario if available
            if game_state.scenario_id:
                scenario = self.scenario_service.get_scenario(game_state.scenario_id)
                if scenario:
                    location = scenario.get_location(command.location_id)
                    if location:
                        # Initialize from scenario only if not yet visited
                        self.game_service.initialize_location_from_scenario(game_state, location)

            # Save game state
            self.game_service.save_game(game_state)

            result.data = ChangeLocationResult(
                location_id=command.location_id,
                location_name=command.location_name,
                description=command.description,
                message=f"Moved to {command.location_name}",
            )

            # Broadcast update
            result.add_command(BroadcastGameUpdateCommand(game_id=command.game_id))

            logger.info(f"Location changed to: {command.location_name}")

        elif isinstance(command, DiscoverSecretCommand):
            # Update location state
            if game_state.current_location_id:
                location_state = game_state.get_location_state(game_state.current_location_id)
                location_state.discover_secret(command.secret_id)

                # Save game state
                self.game_service.save_game(game_state)

                result.data = DiscoverSecretResult(
                    secret_id=command.secret_id,
                    description=command.secret_description,
                    message=f"Discovered secret: {command.secret_description}",
                )

                # Broadcast update
                result.add_command(BroadcastGameUpdateCommand(game_id=command.game_id))

                logger.info(f"Secret discovered: {command.secret_id}")
            else:
                raise ValueError("No current location to discover secrets in")

        elif isinstance(command, UpdateLocationStateCommand):
            if not game_state.current_location_id:
                raise ValueError("No current location to update")

            location_state = game_state.get_location_state(command.location_id or game_state.current_location_id)
            updates = []

            # Update danger level
            if command.danger_level:
                try:
                    location_state.danger_level = DangerLevel(command.danger_level)
                    updates.append(f"Danger level: {command.danger_level}")
                except ValueError as e:
                    raise ValueError(f"Invalid danger level: {command.danger_level}") from e

            # Add NPC
            if command.add_npc:
                location_state.add_npc(command.add_npc)
                updates.append(f"Added NPC: {command.add_npc}")

            # Remove NPC
            if command.remove_npc:
                location_state.remove_npc(command.remove_npc)
                updates.append(f"Removed NPC: {command.remove_npc}")

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
                location_id=command.location_id or game_state.current_location_id,
                updates=updates,
                message=f"Location state updated: {', '.join(updates)}",
            )

            # Broadcast update
            result.add_command(BroadcastGameUpdateCommand(game_id=command.game_id))

            logger.info(f"Location state updated: {updates}")

        return result

    def can_handle(self, command: BaseCommand) -> bool:
        """Check if this handler can process the given command."""
        return isinstance(command, ChangeLocationCommand | DiscoverSecretCommand | UpdateLocationStateCommand)
