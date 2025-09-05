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
from app.interfaces.services import IGameService, IMonsterRepository, IScenarioService
from app.models.combat import CombatParticipant
from app.models.game_state import GameState
from app.models.tool_results import (
    SpawnMonstersResult,
    StartCombatResult,
    TriggerEncounterResult,
)

logger = logging.getLogger(__name__)


class CombatHandler(BaseHandler):
    """Handler for combat commands."""

    def __init__(
        self,
        game_service: IGameService,
        scenario_service: IScenarioService,
        monster_repository: IMonsterRepository,
    ):
        super().__init__(game_service)
        self.scenario_service = scenario_service
        self.monster_repository = monster_repository

    supported_commands = (
        StartCombatCommand,
        TriggerScenarioEncounterCommand,
        SpawnMonstersCommand,
    )

    async def handle(self, command: BaseCommand, game_state: GameState) -> CommandResult:
        """Handle combat commands."""
        result = CommandResult()

        if isinstance(command, StartCombatCommand):
            # Initialize combat if not already active
            if not game_state.combat:
                game_state.start_combat()

            participants_added: list[CombatParticipant] = []

            # Add NPCs to combat
            for npc_def in command.npcs:
                name = npc_def.name
                # Roll initiative if not provided (d20 + dex modifier, assume +2 for now)
                initiative = npc_def.initiative if npc_def.initiative is not None else random.randint(1, 20) + 2

                if game_state.combat:
                    game_state.combat.add_participant(name, initiative, is_player=False)
                    participants_added.append(CombatParticipant(name=name, initiative=initiative, is_player=False))

            # Add player if not already in combat
            if game_state.combat and not any(p.is_player for p in game_state.combat.participants):
                # Roll player initiative (d20 + dex modifier)
                player_dex_mod = (game_state.character.state.abilities.DEX - 10) // 2
                player_initiative = random.randint(1, 20) + player_dex_mod
                game_state.combat.add_participant(game_state.character.sheet.name, player_initiative, is_player=True)
                participants_added.append(
                    CombatParticipant(
                        name=game_state.character.sheet.name, initiative=player_initiative, is_player=True
                    )
                )

            # Save game state
            self.game_service.save_game(game_state)

            result.data = StartCombatResult(
                combat_started=True,
                participants=participants_added,
                message="Combat has begun!",
            )

            # Broadcast combat update
            result.add_command(BroadcastGameUpdateCommand(game_id=command.game_id))

            logger.info(f"Combat started with {len(participants_added)} participants")

        elif isinstance(command, TriggerScenarioEncounterCommand):
            # Get scenario from embedded sheet
            scenario = game_state.scenario_instance.sheet if game_state.scenario_instance else None
            if not scenario:
                raise ValueError("No scenario loaded")

            # Find encounter
            encounter = scenario.get_encounter_by_id(command.encounter_id)
            if not encounter:
                raise ValueError(f"Encounter '{command.encounter_id}' not found")

            # Initialize combat
            if not game_state.combat:
                game_state.start_combat()

            monsters_spawned: list[CombatParticipant] = []

            # Spawn monsters from encounter
            for spawn in encounter.monster_spawns:
                # Determine quantity
                quantity = random.randint(spawn.quantity_min, spawn.quantity_max)

                # Check probability
                if random.random() > spawn.probability:
                    continue

                # Spawn each monster
                for _ in range(quantity):
                    try:
                        monster_data = None
                        # Prefer scenario-defined monster if provided
                        monster_id = spawn.scenario_monster_id
                        if monster_id and game_state.scenario_id:
                            monster_data = self.scenario_service.get_scenario_monster(
                                game_state.scenario_id, monster_id
                            )
                        # Fallback to repository by name
                        repo_name = spawn.monster_name
                        if not monster_data and repo_name:
                            monster_data = self.monster_repository.get(repo_name)
                        if monster_data:
                            # Add to game state (handles duplicate name suffixing)
                            name = game_state.add_monster(monster_data)

                            # Roll initiative
                            dex_mod = (monster_data.abilities.DEX - 10) // 2
                            initiative = random.randint(1, 20) + dex_mod

                            # Add to combat
                            if game_state.combat:
                                game_state.combat.add_participant(name, initiative, is_player=False)

                            monsters_spawned.append(
                                CombatParticipant(name=name, initiative=initiative, is_player=False)
                            )
                    except KeyError as e:
                        logger.error(
                            f"Failed to spawn monster '{getattr(spawn, 'monster_name', '') or getattr(spawn, 'scenario_monster_id', '')}': {e}"
                        )

            # Save game state
            self.game_service.save_game(game_state)

            result.data = TriggerEncounterResult(
                encounter_id=command.encounter_id,
                encounter_type=encounter.type,
                monsters_spawned=monsters_spawned,
                message=f"Encounter triggered: {encounter.description}",
            )

            # Broadcast combat update
            result.add_command(BroadcastGameUpdateCommand(game_id=command.game_id))

            logger.info(f"Triggered encounter '{command.encounter_id}' with {len(monsters_spawned)} monsters")

        elif isinstance(command, SpawnMonstersCommand):
            spawned_monsters: list[CombatParticipant] = []

            for monster_spec in command.monsters:
                monster_name = monster_spec.monster_name
                quantity = monster_spec.quantity

                for _ in range(quantity):
                    try:
                        monster_data = self.monster_repository.get(monster_name)
                        if monster_data:
                            # Add to game state (handles duplicate name suffixing)
                            name = game_state.add_monster(monster_data)

                            # Roll initiative for the monster
                            dex_mod = (monster_data.abilities.DEX - 10) // 2
                            initiative = random.randint(1, 20) + dex_mod

                            # If in combat, add to combat
                            if game_state.combat:
                                game_state.combat.add_participant(name, initiative, is_player=False)

                            spawned_monsters.append(
                                CombatParticipant(name=name, initiative=initiative, is_player=False)
                            )
                    except KeyError as e:
                        logger.error(f"Failed to spawn monster '{monster_name}': {e}")
                        raise ValueError(f"Monster '{monster_name}' not found in database") from e

            # Save game state
            self.game_service.save_game(game_state)

            result.data = SpawnMonstersResult(
                monsters_spawned=spawned_monsters,
                message=f"Spawned {len(spawned_monsters)} monster(s)",
            )

            # Broadcast update
            if game_state.combat:
                result.add_command(BroadcastGameUpdateCommand(game_id=command.game_id))

            logger.info(f"Spawned {len(spawned_monsters)} monsters")

        return result

    def can_handle(self, command: BaseCommand) -> bool:
        """Check if this handler can process the given command."""
        return isinstance(command, self.supported_commands)
