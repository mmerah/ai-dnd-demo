"""Handler for combat commands."""

import logging
import random

from app.events.base import BaseCommand, CommandResult
from app.events.commands.broadcast_commands import BroadcastGameUpdateCommand
from app.events.commands.combat_commands import (
    AddParticipantCommand,
    EndCombatCommand,
    NextTurnCommand,
    RemoveParticipantCommand,
    SpawnMonstersCommand,
    StartCombatCommand,
    TriggerScenarioEncounterCommand,
)
from app.events.handlers.base_handler import BaseHandler
from app.interfaces.services import ICombatService, IGameService, IMonsterRepository, IScenarioService
from app.models.combat import CombatParticipant
from app.models.game_state import GameState
from app.models.tool_results import (
    AddParticipantResult,
    EndCombatResult,
    NextTurnResult,
    RemoveParticipantResult,
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
        combat_service: ICombatService,
    ):
        super().__init__(game_service)
        self.scenario_service = scenario_service
        self.monster_repository = monster_repository
        self.combat_service = combat_service

    supported_commands = (
        StartCombatCommand,
        TriggerScenarioEncounterCommand,
        SpawnMonstersCommand,
        NextTurnCommand,
        EndCombatCommand,
        AddParticipantCommand,
        RemoveParticipantCommand,
    )

    async def handle(self, command: BaseCommand, game_state: GameState) -> CommandResult:
        """Handle combat commands."""
        result = CommandResult()

        if isinstance(command, StartCombatCommand):
            # Initialize combat if not already active
            if not game_state.combat:
                game_state.start_combat()

            participants_added: list[CombatParticipant] = []

            # Add provided entities to combat (IDs required, fail fast on missing)
            for npc_def in command.npcs:
                entity_id = npc_def.entity_id
                entity_type = npc_def.entity_type
                if not entity_id:
                    raise ValueError("StartCombat requires entity_id for each participant")
                combat = game_state.combat
                if not combat:
                    raise RuntimeError("Combat state not initialized")
                entity = game_state.get_entity_by_id(entity_type, entity_id)
                if not entity:
                    raise ValueError(f"Entity not found for id {entity_id}")
                participant = self.combat_service.add_participant(combat, entity)
                participants_added.append(participant)

            # Add player if not already in combat
            if game_state.combat and not any(p.is_player for p in game_state.combat.participants):
                # Roll player initiative (d20 + dex modifier)
                player_entity = game_state.character
                combat = game_state.combat
                participant = self.combat_service.add_participant(combat, player_entity)
                participants_added.append(participant)

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
                            # Create runtime instance and add to game state (dedup name)
                            inst = self.game_service.create_monster_instance(
                                monster_data, game_state.scenario_instance.current_location_id
                            )
                            _ = game_state.add_monster_instance(inst)

                            # Add to combat
                            combat = game_state.combat
                            if combat:
                                monster_entity = inst
                                participant = self.combat_service.add_participant(combat, monster_entity)
                                monsters_spawned.append(participant)
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
                            # Create runtime instance and add to game state (dedup name)
                            inst = self.game_service.create_monster_instance(
                                monster_data, game_state.scenario_instance.current_location_id
                            )
                            _ = game_state.add_monster_instance(inst)

                            # If in combat, add to combat
                            if game_state.combat:
                                monster_entity = inst
                                combat = game_state.combat
                                participant = self.combat_service.add_participant(combat, monster_entity)
                                spawned_monsters.append(participant)
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

        elif isinstance(command, NextTurnCommand):
            if not game_state.combat or not game_state.combat.is_active:
                result.data = NextTurnResult(round_number=0, current_turn=None, message="No active combat")
                return result

            # Advance turn
            game_state.combat.next_turn()
            current = game_state.combat.get_current_turn()

            # Save and broadcast
            self.game_service.save_game(game_state)
            result.data = NextTurnResult(
                round_number=game_state.combat.round_number,
                current_turn=current,
                message=f"Turn advanced to {current.name if current else 'N/A'} (Round {game_state.combat.round_number})",
            )
            result.add_command(BroadcastGameUpdateCommand(game_id=command.game_id))

        elif isinstance(command, EndCombatCommand):
            if game_state.combat:
                game_state.end_combat()
                self.game_service.save_game(game_state)
                result.data = EndCombatResult(message="Combat ended")
                result.add_command(BroadcastGameUpdateCommand(game_id=command.game_id))
            else:
                result.data = EndCombatResult(message="No active combat")

        elif isinstance(command, AddParticipantCommand):
            if not game_state.combat:
                raise ValueError("Cannot add participant: no active combat. Use start_combat first.")
            entity = game_state.get_entity_by_id(command.entity_type, command.entity_id)
            if not entity:
                raise ValueError("Entity not found")
            combat = game_state.combat
            participant = self.combat_service.add_participant(combat, entity)
            self.game_service.save_game(game_state)
            result.data = AddParticipantResult(participant=participant, message=f"Added {participant.name} to combat")
            result.add_command(BroadcastGameUpdateCommand(game_id=command.game_id))

        elif isinstance(command, RemoveParticipantCommand):
            if not game_state.combat:
                raise ValueError("Cannot remove participant: no active combat")
            game_state.combat.remove_participant_by_id(command.entity_id)
            self.game_service.save_game(game_state)
            result.data = RemoveParticipantResult(entity_id=command.entity_id, message="Removed from combat")
            result.add_command(BroadcastGameUpdateCommand(game_id=command.game_id))

        return result

    def can_handle(self, command: BaseCommand) -> bool:
        """Check if this handler can process the given command."""
        return isinstance(command, self.supported_commands)
