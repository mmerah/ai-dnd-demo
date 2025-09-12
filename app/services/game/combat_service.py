"""Combat service centralizing combat computations and operations."""

from __future__ import annotations

import logging
import random

from app.common.exceptions import RepositoryNotFoundError
from app.interfaces.services.data import IMonsterRepository
from app.interfaces.services.game import ICombatService, IGameService
from app.interfaces.services.scenario import IScenarioService
from app.models.attributes import EntityType
from app.models.combat import CombatParticipant, CombatState
from app.models.entity import IEntity
from app.models.game_state import GameState
from app.models.instances.character_instance import CharacterInstance
from app.models.instances.monster_instance import MonsterInstance
from app.models.instances.npc_instance import NPCInstance
from app.models.location import EncounterParticipantSpawn, SpawnType

logger = logging.getLogger(__name__)


class CombatService(ICombatService):
    """Default implementation of ICombatService."""

    def __init__(self) -> None:
        # Flow tracking to detect missing next_turn calls
        self._last_prompted_entity_id: str | None = None
        self._last_prompted_round: int = 0

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

    def add_participant(self, combat: CombatState, entity: IEntity) -> CombatParticipant:
        etype = self._infer_entity_type(entity)
        final_init = self.roll_initiative(entity)
        is_pl = etype == EntityType.PLAYER

        # Mutate combat state
        combat.add_participant(
            entity.display_name,
            final_init,
            is_player=is_pl,
            entity_id=entity.instance_id,
            entity_type=etype,
        )

        # Return a corresponding participant value-object for result payloads
        return CombatParticipant(
            name=entity.display_name,
            initiative=final_init,
            is_player=is_pl,
            entity_id=entity.instance_id,
            entity_type=etype,
        )

    def add_participants(self, combat: CombatState, entities: list[IEntity]) -> list[CombatParticipant]:
        """Add multiple entities to combat, returning their participant records."""
        participants: list[CombatParticipant] = []
        for ent in entities:
            participants.append(self.add_participant(combat, ent))
        return participants

    def realize_spawns(
        self,
        game_state: GameState,
        spawns: list[EncounterParticipantSpawn],
        scenario_service: IScenarioService,
        monster_repository: IMonsterRepository,
        game_service: IGameService,
    ) -> list[IEntity]:
        """Realize encounter participant spawns to concrete entities.

        - Honors probability per spawn definition
        - Selects random quantity within min/max
        - For scenario NPCs, reuses existing instance (warns if missing)
        - For monsters, materializes instances and adds them to game state
        - Logs warnings for any unresolved references
        """
        realized: list[IEntity] = []
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
                        npc_def = scenario_service.get_scenario_npc(game_state.scenario_id, spawn.entity_id)
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
                            monster_sheet = scenario_service.get_scenario_monster(
                                game_state.scenario_id, spawn.entity_id
                            )
                            if not monster_sheet:
                                logger.warning(
                                    f"Scenario monster not found: id={spawn.entity_id} in scenario {game_state.scenario_id}"
                                )
                                continue
                            inst = game_service.create_monster_instance(monster_sheet, current_loc)
                            _ = game_state.add_monster_instance(inst)
                            entity = inst
                        elif spawn.spawn_type == SpawnType.REPOSITORY:
                            try:
                                monster_sheet = monster_repository.get(spawn.entity_id)
                                inst = game_service.create_monster_instance(monster_sheet, current_loc)
                                _ = game_state.add_monster_instance(inst)
                                entity = inst
                            except RepositoryNotFoundError:
                                logger.warning(f"Monster not found in repository: '{spawn.entity_id}'")
                                continue
                    if entity is not None:
                        realized.append(entity)
                except Exception as e:
                    logger.warning(
                        f"Failed to realize spawn for entity_id={spawn.entity_id} ({spawn.spawn_type}/{spawn.entity_type}): {e}"
                    )

        return realized

    # Flow/prompt methods (fused from former CombatFlowService)
    def generate_combat_prompt(self, game_state: GameState) -> str:
        if not game_state.combat.is_active:
            return ""

        current_turn = game_state.combat.get_current_turn()
        if not current_turn:
            return "No active participants remain in combat. Use the end_combat tool to conclude the encounter."

        round_num = game_state.combat.round_number

        # Check if we're prompting for the same entity again (likely forgot next_turn)
        reminder = ""
        if self._last_prompted_entity_id == current_turn.entity_id and self._last_prompted_round == round_num:
            reminder = (
                "\n\nIMPORTANT: You are still processing the same turn. "
                "Did you forget to call next_turn after the previous action? "
                "Remember: You MUST call next_turn after EVERY turn to advance combat."
            )
            logger.warning(
                f"Same entity prompted twice: {current_turn.name} (Round {round_num}) - likely missing next_turn call"
            )

        # Update tracking
        self._last_prompted_entity_id = current_turn.entity_id
        self._last_prompted_round = round_num

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

    def get_combat_status(self, game_state: GameState) -> str:
        if not game_state.combat.is_active:
            return "No active combat"
        current = game_state.combat.get_current_turn()
        if not current:
            return "Combat active but no participants"
        return (
            f"Combat Round {game_state.combat.round_number} - "
            f"Current Turn: {current.name} {'(Player)' if current.is_player else '(NPC/Monster)'}"
        )

    def should_auto_end_combat(self, game_state: GameState) -> bool:
        if not game_state.combat.is_active:
            return False
        active_enemies = [p for p in game_state.combat.participants if p.is_active and not p.is_player]
        return len(active_enemies) == 0

    def reset_combat_tracking(self) -> None:
        self._last_prompted_entity_id = None
        self._last_prompted_round = 0
        logger.debug("Combat tracking state reset")
