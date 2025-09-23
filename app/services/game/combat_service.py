"""Combat service centralizing combat computations and operations."""

from __future__ import annotations

import logging
import random

from app.common.exceptions import RepositoryNotFoundError
from app.interfaces.services.data import IRepositoryProvider
from app.interfaces.services.game import ICombatService, IMonsterManagerService
from app.interfaces.services.scenario import IScenarioService
from app.models.attributes import EntityType
from app.models.combat import CombatEntry, CombatFaction, CombatParticipant, CombatState
from app.models.entity import IEntity
from app.models.game_state import GameState
from app.models.instances.character_instance import CharacterInstance
from app.models.instances.monster_instance import MonsterInstance
from app.models.instances.npc_instance import NPCInstance
from app.models.location import EncounterParticipantSpawn, SpawnType

logger = logging.getLogger(__name__)


class CombatService(ICombatService):
    """Default implementation of ICombatService."""

    def __init__(
        self,
        scenario_service: IScenarioService,
        monster_manager_service: IMonsterManagerService,
        repository_provider: IRepositoryProvider,
    ) -> None:
        self.scenario_service = scenario_service
        self.monster_manager_service = monster_manager_service
        self.repository_provider = repository_provider

    def roll_initiative(self, entity: IEntity) -> int:
        # d20 + initiative modifier from state
        return random.randint(1, 20) + int(entity.state.initiative_bonus or 0)

    def _infer_entity_type(self, entity: IEntity) -> EntityType:
        if isinstance(entity, CharacterInstance):
            return EntityType.PLAYER
        if isinstance(entity, NPCInstance):
            return EntityType.NPC
        if isinstance(entity, MonsterInstance):
            return EntityType.MONSTER
        raise ValueError("Entity should be a player, NPC or monster")

    def _infer_faction(self, entity: IEntity, entity_type: EntityType, game_state: GameState) -> CombatFaction:
        """Infer faction based on entity type and party membership.

        - CharacterInstance: PLAYER
        - NPCInstance in party: ALLY
        - MonsterInstance: ENEMY
        - Else: NEUTRAL
        """
        match entity_type:
            case EntityType.PLAYER:
                return CombatFaction.PLAYER
            case EntityType.NPC:
                # Check if NPC is in party (will be ALLY when party system is implemented)
                if game_state.party.has_member(entity.instance_id):
                    return CombatFaction.ALLY
                return CombatFaction.NEUTRAL
            case EntityType.MONSTER:
                return CombatFaction.ENEMY

    def add_participant(self, game_state: GameState, entry: CombatEntry) -> CombatParticipant:
        combat = game_state.combat
        entity = entry.entity
        etype = self._infer_entity_type(entity)
        final_init = self.roll_initiative(entity)
        is_pl = etype == EntityType.PLAYER

        # Use explicit faction if provided, otherwise infer based on entity type and party membership
        faction = entry.faction if entry.faction else self._infer_faction(entity, etype, game_state)

        # Mutate combat state
        combat.add_participant(
            entity.display_name,
            final_init,
            is_player=is_pl,
            entity_id=entity.instance_id,
            entity_type=etype,
            faction=faction,
        )

        # Return a corresponding participant value-object for result payloads
        return CombatParticipant(
            name=entity.display_name,
            initiative=final_init,
            is_player=is_pl,
            entity_id=entity.instance_id,
            entity_type=etype,
            faction=faction,
        )

    def add_participants(self, game_state: GameState, entries: list[CombatEntry]) -> list[CombatParticipant]:
        participants: list[CombatParticipant] = []
        for entry in entries:
            participants.append(self.add_participant(game_state, entry))
        return participants

    def realize_spawns(
        self,
        game_state: GameState,
        spawns: list[EncounterParticipantSpawn],
    ) -> list[CombatEntry]:
        entries: list[CombatEntry] = []
        current_loc = game_state.scenario_instance.current_location_id

        for spawn in spawns:
            # Probability gate
            roll = random.random()
            if roll > (spawn.probability or 0):
                logger.debug(
                    f"Skipping spawn entity_id={spawn.entity_id} due to probability {spawn.probability} (roll={roll:.2f})"
                )
                continue

            qty = random.randint(max(1, spawn.quantity_min), max(spawn.quantity_min, spawn.quantity_max))

            for _ in range(qty):
                try:
                    entity: IEntity | None = None
                    if spawn.entity_type == EntityType.NPC:
                        if spawn.spawn_type != SpawnType.SCENARIO:
                            logger.warning(
                                f"NPC spawn requires scenario spawn_type; got {spawn.spawn_type} for {spawn.entity_id}"
                            )
                            continue

                        # Validate scenario NPC exists in content
                        npc_def = self.scenario_service.get_scenario_npc(game_state.scenario_id, spawn.entity_id)
                        if not npc_def:
                            logger.warning(
                                f"Scenario NPC definition not found: id={spawn.entity_id} in scenario {game_state.scenario_id}"
                            )
                            continue

                        # Get existing NPC instance by scenario id
                        npc_inst = game_state.get_npc_by_scenario_id(spawn.entity_id)
                        if not npc_inst:
                            logger.warning(
                                f"NPC instance not found for scenario_npc_id={spawn.entity_id}; cannot add to encounter"
                            )
                            continue
                        entity = npc_inst
                    else:
                        # Monsters: scenario-defined or repository
                        if spawn.spawn_type == SpawnType.SCENARIO:
                            monster_sheet = self.scenario_service.get_scenario_monster(
                                game_state.scenario_id, spawn.entity_id
                            )
                            if not monster_sheet:
                                logger.warning(
                                    f"Scenario monster not found: id={spawn.entity_id} in scenario {game_state.scenario_id}"
                                )
                                continue
                            inst = self.monster_manager_service.create(monster_sheet, current_loc)
                            _ = self.monster_manager_service.add_monster_to_game(game_state, inst)
                            entity = inst
                        elif spawn.spawn_type == SpawnType.REPOSITORY:
                            try:
                                monster_repo = self.repository_provider.get_monster_repository_for(game_state)
                                monster_sheet = monster_repo.get(spawn.entity_id)
                                inst = self.monster_manager_service.create(monster_sheet, current_loc)
                                _ = self.monster_manager_service.add_monster_to_game(game_state, inst)
                                entity = inst
                            except RepositoryNotFoundError:
                                logger.warning(f"Monster not found in repository: '{spawn.entity_id}'")
                                continue
                    if entity is not None:
                        entries.append(CombatEntry(entity=entity, faction=spawn.faction))
                except Exception as e:
                    logger.warning(
                        f"Failed to realize spawn for entity_id={spawn.entity_id} ({spawn.spawn_type}/{spawn.entity_type}): {e}"
                    )

        return entries

    def generate_combat_prompt(
        self,
        game_state: GameState,
        last_entity_id: str | None = None,
        last_round: int = 0,
    ) -> str:
        if not game_state.combat.is_active:
            return ""

        current_turn = game_state.combat.get_current_turn()
        if not current_turn:
            return "No active participants remain in combat. Use the end_combat tool to conclude the encounter."

        round_num = game_state.combat.round_number

        # Check for duplicate prompt
        reminder = ""
        if last_entity_id == current_turn.entity_id and last_round == round_num:
            reminder = (
                "\n\nIMPORTANT: You are still processing the same turn. "
                "Did you forget to call next_turn after the previous action? "
                "Remember: You MUST call next_turn after EVERY turn to advance combat."
            )
            logger.warning(
                f"Same entity prompted twice: {current_turn.name} (Round {round_num}) - likely missing next_turn call"
            )

        if current_turn.is_player:
            return (
                f"Round {round_num}: It is {current_turn.name}'s turn (the player). "
                f"Ask them what they want to do for their combat action. "
                f"After resolving their action, you MUST call next_turn to advance combat."
                f"{reminder}"
            )
        else:
            entity_type = "NPC" if "npc" in current_turn.entity_type.value.lower() else "Monster"
            return (
                f"Round {round_num}: It is {current_turn.name}'s turn ({entity_type}). "
                f"Narrate their combat action (attack, movement, abilities, etc.) appropriately for this creature. "
                f"Roll any necessary dice for their actions. "
                f"After resolving the turn, you MUST call next_turn to advance combat."
                f"{reminder}"
            )

    def should_auto_continue(self, game_state: GameState) -> bool:
        if not game_state.combat.is_active:
            return False
        current_turn = game_state.combat.get_current_turn()
        return current_turn is not None and not current_turn.is_player

    def should_auto_end_combat(self, game_state: GameState) -> bool:
        if not game_state.combat.is_active:
            return False
        active_enemies = [p for p in game_state.combat.participants if p.is_active and not p.is_player]
        return len(active_enemies) == 0

    def ensure_player_in_combat(self, game_state: GameState) -> CombatParticipant | None:
        if not game_state.combat.is_active:
            raise ValueError("Cannot add player to combat: no active combat")

        # Check if player already in combat
        if any(p.is_player for p in game_state.combat.participants):
            return None

        # Add player to combat
        player_entity = game_state.character
        participant = self.add_participant(game_state, CombatEntry(entity=player_entity))
        logger.debug(
            f"Auto-added player '{player_entity.display_name}' to combat with ID: {player_entity.instance_id}, "
            f"Initiative: {participant.initiative}"
        )
        return participant

    def spawn_free_monster(self, game_state: GameState, monster_name: str) -> IEntity | None:
        try:
            # Use per-game content packs
            monster_repo = self.repository_provider.get_monster_repository_for(game_state)
            monster_data = monster_repo.get(monster_name)
            # Create runtime instance and add to game state (dedup name)
            inst = self.monster_manager_service.create(monster_data, game_state.scenario_instance.current_location_id)
            _ = self.monster_manager_service.add_monster_to_game(game_state, inst)
            return inst
        except RepositoryNotFoundError:
            logger.warning(f"Monster '{monster_name}' not found in repository")
            return None

    def start_combat(self, game_state: GameState) -> CombatState:
        # Increment combat occurrence counter for tracking
        game_state.combat = CombatState(is_active=True, combat_occurrence=game_state.combat.combat_occurrence + 1)
        return game_state.combat

    def end_combat(self, game_state: GameState) -> None:
        if game_state.combat.is_active:
            game_state.combat.end_combat()
            # Remove dead monsters
            game_state.monsters = [m for m in game_state.monsters if m.is_alive()]
            # Set combat to inactive and clear participants
            game_state.combat.is_active = False
            game_state.combat.participants.clear()
            game_state.combat.round_number = 1
            game_state.combat.turn_index = 0
