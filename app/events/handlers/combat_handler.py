"""Handler for combat commands."""

import logging
import random

from app.events.base import BaseCommand, CommandResult
from app.events.commands.broadcast_commands import BroadcastGameUpdateCommand
from app.events.commands.combat_commands import (
    SpawnMonstersCommand,
    StartCombatCommand,
    TriggerScenarioEncounterCommand,
)
from app.events.handlers.base_handler import BaseHandler
from app.interfaces.services import IDataService, IGameService, IScenarioService
from app.models.game_state import GameState

logger = logging.getLogger(__name__)


class CombatHandler(BaseHandler):
    """Handler for combat commands."""

    def __init__(self, game_service: IGameService, scenario_service: IScenarioService, data_service: IDataService):
        super().__init__(game_service)
        self.scenario_service = scenario_service
        self.data_service = data_service

    async def handle(self, command: BaseCommand, game_state: GameState) -> CommandResult:
        """Handle combat commands."""
        result = CommandResult(success=True)

        if isinstance(command, StartCombatCommand):
            # Initialize combat if not already active
            if not game_state.combat:
                game_state.start_combat()

            participants_added = []

            # Add NPCs to combat
            for npc_def in command.npcs:
                name = str(npc_def.get("name", "Unknown"))
                # Roll initiative if not provided
                if "initiative" in npc_def and isinstance(npc_def["initiative"], int):
                    initiative = npc_def["initiative"]
                else:
                    # Roll d20 + dex modifier (assume +2 for now)
                    initiative = random.randint(1, 20) + 2

                if game_state.combat:
                    game_state.combat.add_participant(name, initiative, is_player=False)
                    participants_added.append({"name": name, "initiative": initiative})

            # Add player if not already in combat
            if game_state.combat and not any(p.is_player for p in game_state.combat.participants):
                # Roll player initiative (d20 + dex modifier)
                player_dex_mod = (game_state.character.abilities.DEX - 10) // 2
                player_initiative = random.randint(1, 20) + player_dex_mod
                game_state.combat.add_participant(game_state.character.name, player_initiative, is_player=True)
                participants_added.append(
                    {"name": game_state.character.name, "initiative": player_initiative, "is_player": True}
                )

            # Save game state
            self.game_service.save_game(game_state)

            result.data = {
                "combat_started": True,
                "participants": participants_added,
                "message": "Combat has begun!",
            }

            # Broadcast combat update
            result.add_command(BroadcastGameUpdateCommand(game_id=command.game_id))

            logger.info(f"Combat started with {len(participants_added)} participants")

        elif isinstance(command, TriggerScenarioEncounterCommand):
            # Get scenario
            scenario = self.scenario_service.get_scenario(game_state.scenario_id) if game_state.scenario_id else None
            if not scenario:
                result.success = False
                result.error = "No scenario loaded"
                return result

            # Find encounter
            encounter = scenario.get_encounter_by_id(command.encounter_id)
            if not encounter:
                result.success = False
                result.error = f"Encounter '{command.encounter_id}' not found"
                return result

            # Initialize combat
            if not game_state.combat:
                game_state.start_combat()

            monsters_spawned = []

            # Spawn monsters from encounter
            for spawn in encounter.monster_spawns:
                # Determine quantity
                quantity = random.randint(spawn.quantity_min, spawn.quantity_max)

                # Check probability
                if random.random() > spawn.probability:
                    continue

                # Spawn each monster
                for i in range(quantity):
                    try:
                        monster_data = self.data_service.get_monster(spawn.monster_name)
                        if monster_data:
                            # Add number suffix if multiple
                            name = monster_data.name
                            if quantity > 1:
                                name = f"{name} {i + 1}"

                            # Add to game state
                            game_state.add_npc(monster_data)

                            # Roll initiative
                            dex_mod = (monster_data.abilities.DEX - 10) // 2
                            initiative = random.randint(1, 20) + dex_mod

                            # Add to combat
                            if game_state.combat:
                                game_state.combat.add_participant(name, initiative, is_player=False)

                            monsters_spawned.append({"name": name, "initiative": initiative})
                    except KeyError as e:
                        logger.error(f"Failed to spawn monster '{spawn.monster_name}': {e}")

            # Save game state
            self.game_service.save_game(game_state)

            result.data = {
                "encounter_id": command.encounter_id,
                "encounter_type": encounter.type,
                "monsters_spawned": monsters_spawned,
                "message": f"Encounter triggered: {encounter.description}",
            }

            # Broadcast combat update
            result.add_command(BroadcastGameUpdateCommand(game_id=command.game_id))

            logger.info(f"Triggered encounter '{command.encounter_id}' with {len(monsters_spawned)} monsters")

        elif isinstance(command, SpawnMonstersCommand):
            monsters_spawned = []

            for monster_spec in command.monsters:
                monster_name = str(monster_spec.get("monster_name", ""))
                quantity = int(monster_spec.get("quantity", 1))

                for i in range(quantity):
                    try:
                        monster_data = self.data_service.get_monster(monster_name)
                        if monster_data:
                            # Add number suffix if multiple
                            name = monster_data.name
                            if quantity > 1:
                                name = f"{name} {i + 1}"

                            # Add to game state
                            game_state.add_npc(monster_data)

                            # If in combat, add to combat
                            if game_state.combat:
                                dex_mod = (monster_data.abilities.DEX - 10) // 2
                                initiative = random.randint(1, 20) + dex_mod
                                game_state.combat.add_participant(name, initiative, is_player=False)
                                monsters_spawned.append({"name": name, "initiative": initiative})
                            else:
                                monsters_spawned.append({"name": name})
                    except KeyError as e:
                        logger.error(f"Failed to spawn monster '{monster_name}': {e}")
                        result.success = False
                        result.error = f"Monster '{monster_name}' not found in database"
                        return result

            # Save game state
            self.game_service.save_game(game_state)

            result.data = {
                "monsters_spawned": monsters_spawned,
                "message": f"Spawned {len(monsters_spawned)} monster(s)",
            }

            # Broadcast update
            if game_state.combat:
                result.add_command(BroadcastGameUpdateCommand(game_id=command.game_id))

            logger.info(f"Spawned {len(monsters_spawned)} monsters")

        return result

    def can_handle(self, command: BaseCommand) -> bool:
        """Check if this handler can process the given command."""
        return isinstance(command, StartCombatCommand | TriggerScenarioEncounterCommand | SpawnMonstersCommand)
