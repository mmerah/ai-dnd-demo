"""Combat service centralizing combat computations and operations."""

from __future__ import annotations

import random

from app.interfaces.services import ICombatService
from app.models.combat import CombatParticipant, CombatState
from app.models.entity import EntityType, ICombatEntity
from app.models.instances.character_instance import CharacterInstance
from app.models.instances.monster_instance import MonsterInstance
from app.models.instances.npc_instance import NPCInstance


class CombatService(ICombatService):
    """Default implementation of ICombatService."""

    def roll_initiative(self, entity: ICombatEntity) -> int:
        # d20 + initiative modifier from state
        return random.randint(1, 20) + int(entity.state.initiative_bonus or 0)

    def _infer_entity_type(self, entity: ICombatEntity) -> EntityType:
        if isinstance(entity, CharacterInstance):
            return EntityType.PLAYER
        if isinstance(entity, NPCInstance):
            return EntityType.NPC
        if isinstance(entity, MonsterInstance):
            return EntityType.MONSTER
        raise ValueError("Entity should be a player, NPC or monster")

    def add_participant(self, combat: CombatState, entity: ICombatEntity) -> CombatParticipant:
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
