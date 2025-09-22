"""Service for managing runtime entity state mutations."""

import logging

from app.interfaces.services.character import ICharacterComputeService, IEntityStateService
from app.models.character import Currency
from app.models.equipment_slots import EquipmentSlotType
from app.models.game_state import GameState
from app.utils.entity_resolver import resolve_entity_with_fallback

logger = logging.getLogger(__name__)


class EntityStateService(IEntityStateService):
    """Service for managing runtime entity state mutations.

    This service handles all state mutations for entities (player, NPCs, monsters),
    following the Single Responsibility Principle. It's separated from character
    sheet loading/validation concerns.
    """

    def __init__(
        self,
        compute_service: ICharacterComputeService,
    ):
        """Initialize entity state service.

        Args:
            compute_service: Service for computing character values
        """
        self.compute_service = compute_service

    def update_hp(
        self,
        game_state: GameState,
        entity_id: str,
        amount: int,
    ) -> tuple[int, int, int]:
        # Use centralized entity resolver
        entity, entity_type = resolve_entity_with_fallback(game_state, entity_id)
        if not entity:
            raise ValueError(f"Entity '{entity_id}' not found")

        # Get the state from the entity
        state = entity.state

        # Normalize entity_id for combat tracking (use actual instance_id)
        actual_entity_id = entity.instance_id

        old_hp = state.hit_points.current
        max_hp = state.hit_points.maximum
        new_hp = min(old_hp + amount, max_hp) if amount > 0 else max(0, old_hp + amount)
        state.hit_points.current = new_hp

        # Update combat participant active status if in combat and HP reaches 0
        if game_state.combat.is_active and new_hp == 0:
            for participant in game_state.combat.participants:
                if participant.entity_id == actual_entity_id:
                    participant.is_active = False
                    logger.debug(f"Combat participant {participant.name} marked as inactive (0 HP)")
                    break

        # Touch player if it was modified
        if actual_entity_id == game_state.character.instance_id:
            game_state.character.touch()

        return old_hp, new_hp, max_hp

    def add_condition(
        self,
        game_state: GameState,
        entity_id: str,
        condition: str,
    ) -> bool:
        # Use centralized entity resolver
        entity, entity_type = resolve_entity_with_fallback(game_state, entity_id)
        if not entity:
            raise ValueError(f"Entity '{entity_id}' not found")

        state = entity.state

        if condition not in state.conditions:
            state.conditions.append(condition)
            # Touch player if it was modified
            if entity.instance_id == game_state.character.instance_id:
                game_state.character.touch()
            return True
        return False

    def remove_condition(
        self,
        game_state: GameState,
        entity_id: str,
        condition: str,
    ) -> bool:
        # Use centralized entity resolver
        entity, entity_type = resolve_entity_with_fallback(game_state, entity_id)
        if not entity:
            raise ValueError(f"Entity '{entity_id}' not found")

        state = entity.state

        if condition in state.conditions:
            state.conditions.remove(condition)
            # Touch player if it was modified
            if entity.instance_id == game_state.character.instance_id:
                game_state.character.touch()
            return True
        return False

    def modify_currency(
        self,
        game_state: GameState,
        entity_id: str,
        gold: int = 0,
        silver: int = 0,
        copper: int = 0,
    ) -> tuple[Currency, Currency]:
        # Use centralized entity resolver
        entity, entity_type = resolve_entity_with_fallback(game_state, entity_id)
        if not entity:
            raise ValueError(f"Entity '{entity_id}' not found")

        state = entity.state

        # Capture old values
        old_currency = Currency(
            gold=state.currency.gold,
            silver=state.currency.silver,
            copper=state.currency.copper,
        )

        # Apply changes
        state.currency.gold = max(0, state.currency.gold + gold)
        state.currency.silver = max(0, state.currency.silver + silver)
        state.currency.copper = max(0, state.currency.copper + copper)

        # Capture new values
        new_currency = Currency(
            gold=state.currency.gold,
            silver=state.currency.silver,
            copper=state.currency.copper,
        )

        # Touch player if it was modified
        if entity.instance_id == game_state.character.instance_id:
            game_state.character.touch()

        return old_currency, new_currency

    def equip_item(
        self,
        game_state: GameState,
        entity_id: str,
        item_index: str,
        slot: EquipmentSlotType | None = None,
        unequip: bool = False,
    ) -> None:
        # Check if this is the player
        if entity_id == game_state.character.instance_id:
            state = game_state.character.state
            updated = self.compute_service.equip_item_to_slot(game_state, state, item_index, slot, unequip)
            game_state.character.state = updated
            game_state.character.touch()
        else:
            # NPC only, monsters don't have equipment
            npc = next((n for n in game_state.npcs if n.instance_id == entity_id), None)
            if not npc:
                raise ValueError(f"Entity '{entity_id}' not found")
            updated = self.compute_service.equip_item_to_slot(game_state, npc.state, item_index, slot, unequip)
            npc.state = updated

    def update_spell_slots(
        self,
        game_state: GameState,
        entity_id: str,
        level: int,
        amount: int,
    ) -> tuple[int, int, int]:
        entity, entity_type = resolve_entity_with_fallback(game_state, entity_id)
        if not entity:
            raise ValueError(f"Entity '{entity_id}' not found")

        state = entity.state

        if not state.spellcasting:
            raise ValueError(f"Entity '{entity_id}' has no spellcasting ability")

        spell_slots = state.spellcasting.spell_slots

        if level not in spell_slots:
            raise ValueError(f"No spell slots for level {level}")

        slot = spell_slots[level]
        old_slots = slot.current
        slot.current = max(0, min(slot.total, old_slots + amount))
        new_slots = slot.current
        max_slots = slot.total

        # Touch player if it was modified
        if entity.instance_id == game_state.character.instance_id:
            game_state.character.touch()

        return old_slots, new_slots, max_slots

    def recompute_entity_state(self, game_state: GameState, entity_id: str) -> None:
        entity, entity_type = resolve_entity_with_fallback(game_state, entity_id)
        if not entity:
            raise ValueError(f"Entity '{entity_id}' not found")

        # For player character, use the character sheet
        if entity.instance_id == game_state.character.instance_id:
            char = game_state.character
            new_state = self.compute_service.recompute_entity_state(game_state, char.sheet, char.state)
            char.state = new_state
            char.touch()
        else:
            # For NPCs, use the NPC's character sheet from NPCSheet
            npc = next((n for n in game_state.npcs if n.instance_id == entity_id), None)
            if npc:
                new_state = self.compute_service.recompute_entity_state(game_state, npc.sheet.character, npc.state)
                npc.state = new_state
            else:
                # Monsters don't have character sheets to recompute from
                logger.debug(f"Cannot recompute state for monster '{entity_id}' - no character sheet")
