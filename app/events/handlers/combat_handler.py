"""Handler for combat commands."""

import logging

from app.agents.core.types import AgentType
from app.common.exceptions import RepositoryNotFoundError
from app.events.base import BaseCommand, CommandResult
from app.events.commands.broadcast_commands import BroadcastGameUpdateCommand
from app.events.commands.combat_commands import (
    AddParticipantCommand,
    EndCombatCommand,
    NextTurnCommand,
    RemoveParticipantCommand,
    SpawnMonstersCommand,
    StartCombatCommand,
    StartEncounterCombatCommand,
)
from app.events.handlers.base_handler import BaseHandler
from app.interfaces.services.data import IRepositoryProvider
from app.interfaces.services.game import ICombatService, IGameService
from app.interfaces.services.scenario import IScenarioService
from app.models.attributes import EntityType
from app.models.combat import CombatParticipant
from app.models.game_state import GameState
from app.models.tool_results import (
    AddParticipantResult,
    EndCombatResult,
    NextTurnResult,
    RemoveParticipantResult,
    SpawnMonstersResult,
    StartCombatResult,
    StartEncounterCombatResult,
)

logger = logging.getLogger(__name__)


class CombatHandler(BaseHandler):
    """Handler for combat commands."""

    def __init__(
        self,
        game_service: IGameService,
        scenario_service: IScenarioService,
        combat_service: ICombatService,
        repository_provider: IRepositoryProvider,
    ):
        super().__init__(game_service)
        self.scenario_service = scenario_service
        self.combat_service = combat_service
        self.repository_provider = repository_provider

    supported_commands = (
        StartCombatCommand,
        StartEncounterCombatCommand,
        SpawnMonstersCommand,
        NextTurnCommand,
        EndCombatCommand,
        AddParticipantCommand,
        RemoveParticipantCommand,
    )

    async def handle(self, command: BaseCommand, game_state: GameState) -> CommandResult:
        """Handle combat commands."""
        result = CommandResult()
        # Validate agent type for restricted commands
        if (
            isinstance(command, StartCombatCommand | StartEncounterCombatCommand | SpawnMonstersCommand)
            and command.agent_type
            and command.agent_type != AgentType.NARRATIVE
        ):
            logger.warning(
                f"{command.__class__.__name__} called by {command.agent_type.value} agent - should be NARRATIVE only"
            )
        elif (
            isinstance(command, NextTurnCommand | EndCombatCommand | AddParticipantCommand | RemoveParticipantCommand)
            and command.agent_type
            and command.agent_type != AgentType.COMBAT
        ):
            logger.warning(
                f"{command.__class__.__name__} called by {command.agent_type.value} agent - should be COMBAT only"
            )

        if isinstance(command, StartCombatCommand):
            if not game_state.combat.is_active:
                game_state.start_combat()
                game_state.active_agent = AgentType.COMBAT

            participants_added: list[CombatParticipant] = []
            for entity_id in command.entity_ids:
                # Try to find entity as monster first, then as NPC
                entity = game_state.get_entity_by_id(EntityType.MONSTER, entity_id)
                if not entity:
                    entity = game_state.get_entity_by_id(EntityType.NPC, entity_id)
                if not entity:
                    raise ValueError(f"Entity not found for id {entity_id}")

                combat = game_state.combat
                participant = self.combat_service.add_participant(combat, entity)
                participants_added.append(participant)

            # Add player if not already in combat
            if game_state.combat.is_active and not any(p.is_player for p in game_state.combat.participants):
                player_entity = game_state.character
                combat = game_state.combat
                participant = self.combat_service.add_participant(combat, player_entity)
                participants_added.append(participant)
                logger.debug(
                    f"Auto-added player '{player_entity.display_name}' to combat with ID: {player_entity.instance_id}, "
                    f"Initiative: {participant.initiative}"
                )

            # Mark state as mutated
            result.mutated = True

            result.data = StartCombatResult(
                combat_started=True,
                participants=participants_added,
                message="Combat has begun!",
            )

            # Broadcast combat update
            result.add_command(BroadcastGameUpdateCommand(game_id=command.game_id))

            # Log detailed participant info
            participant_names = [f"{p.name} (ID: {p.entity_id}, Init: {p.initiative})" for p in participants_added]
            logger.debug(f"Combat started with {len(participants_added)} participants: {', '.join(participant_names)}")

        elif isinstance(command, StartEncounterCombatCommand):
            scenario = game_state.scenario_instance.sheet
            encounter = scenario.get_encounter_by_id(command.encounter_id)
            if not encounter:
                raise ValueError(f"Encounter '{command.encounter_id}' not found")

            # Realize entities without starting combat yet
            entities = self.combat_service.realize_spawns(
                game_state,
                encounter.participant_spawns,
                self.scenario_service,
                self.game_service,
                self.repository_provider,
            )
            all_participants: list[CombatParticipant] = []
            if entities:
                if not game_state.combat.is_active:
                    game_state.start_combat()
                    game_state.active_agent = AgentType.COMBAT
                combat = game_state.combat

                # Add monsters/NPCs from the encounter
                encounter_participants = self.combat_service.add_participants(combat, entities)
                all_participants.extend(encounter_participants)

                # Auto-add player if not present
                if not any(p.is_player for p in game_state.combat.participants):
                    player_entity = game_state.character
                    player_participant = self.combat_service.add_participant(game_state.combat, player_entity)
                    all_participants.append(player_participant)
                    logger.debug(
                        f"Auto-added player '{player_entity.display_name}' to encounter combat with ID: {player_entity.instance_id}, "
                        f"Initiative: {player_participant.initiative}"
                    )

                # Mark state as mutated
                result.mutated = True

                # Create result with ALL participants
                result.data = StartEncounterCombatResult(
                    encounter_id=command.encounter_id,
                    encounter_type=encounter.type,
                    participants=all_participants,
                    message=f"Encounter started: {encounter.description}",
                )
                result.add_command(BroadcastGameUpdateCommand(game_id=command.game_id))

                # Log detailed participant info with initiative for ALL participants
                participant_names = [f"{p.name} (ID: {p.entity_id}, Init: {p.initiative})" for p in all_participants]
                logger.debug(
                    f"Started encounter '{command.encounter_id}' with all participants: {', '.join(participant_names)}"
                )
            else:
                # No participants spawned; no combat started
                result.data = StartEncounterCombatResult(
                    encounter_id=command.encounter_id,
                    encounter_type=encounter.type,
                    participants=[],
                    message=f"Encounter '{command.encounter_id}' had no participants (probabilities)",
                )
                logger.warning(
                    f"Encounter '{command.encounter_id}' produced no participants (check spawn probabilities); combat not started"
                )

        elif isinstance(command, SpawnMonstersCommand):
            spawned_monsters: list[CombatParticipant] = []
            total_spawned = 0

            for monster_spec in command.monsters:
                monster_name = monster_spec.monster_name
                quantity = monster_spec.quantity

                for _ in range(quantity):
                    try:
                        # Use per-game content packs
                        monster_repo = self.repository_provider.get_monster_repository_for(game_state)
                        monster_data = monster_repo.get(monster_name)
                        # Create runtime instance and add to game state (dedup name)
                        inst = self.game_service.create_monster_instance(
                            monster_data, game_state.scenario_instance.current_location_id
                        )
                        _ = game_state.add_monster_instance(inst)
                        total_spawned += 1

                        # If in combat, add to combat
                        if game_state.combat.is_active:
                            monster_entity = inst
                            combat = game_state.combat
                            participant = self.combat_service.add_participant(combat, monster_entity)
                            spawned_monsters.append(participant)
                    except (KeyError, RepositoryNotFoundError) as e:
                        logger.error(f"Failed to spawn monster '{monster_name}': {e}")
                        raise ValueError(f"Monster '{monster_name}' not found in database") from e

            if total_spawned > 0:
                result.mutated = True

            result.data = SpawnMonstersResult(
                monsters_spawned=spawned_monsters,
                message=f"Spawned {len(spawned_monsters)} monster(s)",
            )

            # Broadcast update
            if game_state.combat.is_active:
                result.add_command(BroadcastGameUpdateCommand(game_id=command.game_id))

            # Log detailed spawn info
            if spawned_monsters:
                monster_names = [f"{p.name} (ID: {p.entity_id})" for p in spawned_monsters]
                logger.debug(f"Spawned {len(spawned_monsters)} monsters: {', '.join(monster_names)}")
            else:
                logger.warning("SpawnMonstersCommand executed but no monsters were spawned")

        elif isinstance(command, NextTurnCommand):
            if not game_state.combat.is_active:
                logger.warning("NextTurnCommand called with no active combat")
                result.data = NextTurnResult(round_number=0, current_turn=None, message="No active combat")
                return result

            # Log current state before advancing
            old_turn = game_state.combat.get_current_turn()
            old_round = game_state.combat.round_number

            # Advance turn (this may set combat.is_active to False if no active participants)
            game_state.combat.next_turn()
            current = game_state.combat.get_current_turn()

            # Check if combat has no active participants
            if not game_state.combat.is_active or self.combat_service.should_auto_end_combat(game_state):
                # No enemies left or combat inactive - return a result indicating this
                logger.debug("No active enemies remaining - combat should be ended by AI")
                result.mutated = True
                # Return NextTurnResult indicating no enemies remain
                result.data = NextTurnResult(
                    round_number=game_state.combat.round_number,
                    current_turn=None,
                    message="No active enemies remain - use end_combat to conclude",
                )
                result.add_command(BroadcastGameUpdateCommand(game_id=command.game_id))
                return result

            if current:
                message = f"Turn advanced to {current.name} (Round {game_state.combat.round_number})"
                logger.debug(
                    f"Turn advanced: {old_turn.name if old_turn else 'None'} -> {current.name} (Round {old_round} -> {game_state.combat.round_number})"
                )
            else:
                message = "No active participants in combat"
                logger.warning("NextTurnCommand: No active participants remaining in combat")

            result.mutated = True
            result.data = NextTurnResult(
                round_number=game_state.combat.round_number,
                current_turn=current,
                message=message,
            )
            result.add_command(BroadcastGameUpdateCommand(game_id=command.game_id))

        elif isinstance(command, EndCombatCommand):
            if game_state.combat.is_active:
                # Log combat summary before ending
                participant_count = len(game_state.combat.participants)
                round_count = game_state.combat.round_number
                logger.debug(f"Ending combat after {round_count} rounds with {participant_count} participants")

                game_state.end_combat()
                game_state.active_agent = AgentType.NARRATIVE
                # Reset combat flow tracking
                self.combat_service.reset_combat_tracking()
                result.mutated = True
                result.data = EndCombatResult(message="Combat ended")
                result.add_command(BroadcastGameUpdateCommand(game_id=command.game_id))
            else:
                logger.warning("EndCombatCommand called with no active combat")
                result.data = EndCombatResult(message="No active combat")

        elif isinstance(command, AddParticipantCommand):
            if not game_state.combat.is_active:
                raise ValueError("Cannot add participant: no active combat. Use start_combat first.")
            entity = game_state.get_entity_by_id(command.entity_type, command.entity_id)
            if not entity:
                raise ValueError("Entity not found")
            combat = game_state.combat
            participant = self.combat_service.add_participant(combat, entity)
            result.mutated = True
            result.data = AddParticipantResult(participant=participant, message=f"Added {participant.name} to combat")
            result.add_command(BroadcastGameUpdateCommand(game_id=command.game_id))

        elif isinstance(command, RemoveParticipantCommand):
            if not game_state.combat.is_active:
                raise ValueError("Cannot remove participant: no active combat")
            game_state.combat.remove_participant_by_id(command.entity_id)
            result.mutated = True
            result.data = RemoveParticipantResult(entity_id=command.entity_id, message="Removed from combat")
            result.add_command(BroadcastGameUpdateCommand(game_id=command.game_id))

        return result
