"""Unit tests for EntityStateService."""

from unittest.mock import MagicMock, create_autospec

import pytest

from app.interfaces.services.character import ICharacterComputeService
from app.models.attributes import EntityType
from app.models.character import Currency
from app.models.combat import CombatParticipant, CombatState
from app.models.equipment_slots import EquipmentSlots, EquipmentSlotType
from app.models.instances.entity_state import EntityState
from app.models.item import InventoryItem
from app.models.spell import Spellcasting, SpellcastingAbility, SpellSlot
from app.services.character.entity_state_service import EntityStateService
from tests.factories import make_game_state, make_monster_instance, make_npc_instance


class TestEntityStateService:
    def setup_method(self) -> None:
        self.compute_service = create_autospec(ICharacterComputeService, instance=True)
        self.service = EntityStateService(self.compute_service)
        self.game_state = make_game_state()
        self.character = self.game_state.character
        self.character_id = self.character.instance_id

    @pytest.mark.asyncio
    async def test_update_hp_damage_player(self) -> None:
        """Test HP damage for player character."""
        initial_hp = self.character.state.hit_points.current

        old_hp, new_hp, max_hp = self.service.update_hp(self.game_state, self.character_id, -10)

        assert old_hp == initial_hp
        assert new_hp == initial_hp - 10
        assert max_hp == self.character.state.hit_points.maximum
        assert self.character.state.hit_points.current == new_hp

    @pytest.mark.asyncio
    async def test_update_hp_healing_player(self) -> None:
        """Test HP healing for player character."""
        self.character.state.hit_points.current = 5
        max_hp = self.character.state.hit_points.maximum

        old_hp, new_hp, returned_max = self.service.update_hp(self.game_state, self.character_id, 7)

        assert old_hp == 5
        assert new_hp == 12
        assert returned_max == max_hp
        assert self.character.state.hit_points.current == new_hp

    @pytest.mark.asyncio
    async def test_update_hp_cannot_exceed_maximum(self) -> None:
        """Test that healing cannot exceed maximum HP."""
        max_hp = self.character.state.hit_points.maximum
        self.character.state.hit_points.current = max_hp - 2

        old_hp, new_hp, returned_max = self.service.update_hp(self.game_state, self.character_id, 10)

        assert old_hp == max_hp - 2
        assert new_hp == max_hp
        assert returned_max == max_hp

    @pytest.mark.asyncio
    async def test_update_hp_cannot_go_below_zero(self) -> None:
        """Test that damage cannot reduce HP below zero."""
        self.character.state.hit_points.current = 5

        old_hp, new_hp, max_hp = self.service.update_hp(self.game_state, self.character_id, -10)

        assert old_hp == 5
        assert new_hp == 0
        assert self.character.state.hit_points.current == 0

    @pytest.mark.asyncio
    async def test_update_hp_marks_combat_participant_inactive(self) -> None:
        """Test that reducing HP to 0 marks combat participant as inactive."""
        self.character.state.hit_points.current = 5
        self.game_state.combat = CombatState(
            is_active=True,
            round_number=1,
            participants=[
                CombatParticipant(
                    entity_id=self.character_id,
                    name=self.character.display_name,
                    entity_type=EntityType.PLAYER,
                    initiative=15,
                    is_active=True,
                )
            ],
        )

        self.service.update_hp(self.game_state, self.character_id, -5)

        assert self.game_state.combat.participants[0].is_active is False

    @pytest.mark.asyncio
    async def test_update_hp_npc(self) -> None:
        """Test HP update for NPC."""
        npc = make_npc_instance()
        self.game_state.npcs.append(npc)
        initial_hp = npc.state.hit_points.current

        old_hp, new_hp, max_hp = self.service.update_hp(self.game_state, npc.instance_id, -5)

        assert old_hp == initial_hp
        assert new_hp == initial_hp - 5
        assert npc.state.hit_points.current == new_hp

    @pytest.mark.asyncio
    async def test_update_hp_monster(self) -> None:
        """Test HP update for monster."""
        monster = make_monster_instance()
        self.game_state.monsters.append(monster)
        initial_hp = monster.state.hit_points.current

        old_hp, new_hp, max_hp = self.service.update_hp(self.game_state, monster.instance_id, -8)

        assert old_hp == initial_hp
        assert new_hp == initial_hp - 8
        assert monster.state.hit_points.current == new_hp

    @pytest.mark.asyncio
    async def test_update_hp_entity_not_found(self) -> None:
        """Test update_hp with non-existent entity."""
        with pytest.raises(ValueError, match="Entity 'nonexistent' not found"):
            self.service.update_hp(self.game_state, "nonexistent", -5)

    @pytest.mark.asyncio
    async def test_add_condition_player(self) -> None:
        """Test adding condition to player."""
        assert "poisoned" not in self.character.state.conditions

        added = self.service.add_condition(self.game_state, self.character_id, "poisoned")

        assert added is True
        assert "poisoned" in self.character.state.conditions

    @pytest.mark.asyncio
    async def test_add_condition_already_exists(self) -> None:
        """Test adding condition that already exists."""
        self.character.state.conditions.append("poisoned")

        added = self.service.add_condition(self.game_state, self.character_id, "poisoned")

        assert added is False
        assert self.character.state.conditions.count("poisoned") == 1

    @pytest.mark.asyncio
    async def test_add_condition_npc(self) -> None:
        """Test adding condition to NPC."""
        npc = make_npc_instance()
        self.game_state.npcs.append(npc)

        added = self.service.add_condition(self.game_state, npc.instance_id, "stunned")

        assert added is True
        assert "stunned" in npc.state.conditions

    @pytest.mark.asyncio
    async def test_remove_condition_player(self) -> None:
        """Test removing condition from player."""
        self.character.state.conditions = ["poisoned", "prone"]

        removed = self.service.remove_condition(self.game_state, self.character_id, "poisoned")

        assert removed is True
        assert "poisoned" not in self.character.state.conditions
        assert "prone" in self.character.state.conditions

    @pytest.mark.asyncio
    async def test_remove_condition_not_present(self) -> None:
        """Test removing condition that doesn't exist."""
        removed = self.service.remove_condition(self.game_state, self.character_id, "poisoned")

        assert removed is False

    @pytest.mark.asyncio
    async def test_modify_currency_player(self) -> None:
        """Test modifying player currency."""
        self.character.state.currency = Currency(gold=10, silver=5, copper=20)

        old_currency, new_currency = self.service.modify_currency(
            self.game_state, self.character_id, gold=5, silver=-2, copper=10
        )

        assert old_currency.gold == 10
        assert old_currency.silver == 5
        assert old_currency.copper == 20
        assert new_currency.gold == 15
        assert new_currency.silver == 3
        assert new_currency.copper == 30
        assert self.character.state.currency.gold == 15

    @pytest.mark.asyncio
    async def test_modify_currency_cannot_go_negative(self) -> None:
        """Test that currency cannot go negative."""
        self.character.state.currency = Currency(gold=5, silver=3, copper=10)

        old_currency, new_currency = self.service.modify_currency(
            self.game_state, self.character_id, gold=-10, silver=-5, copper=-20
        )

        assert new_currency.gold == 0
        assert new_currency.silver == 0
        assert new_currency.copper == 0

    @pytest.mark.asyncio
    async def test_equip_item_player(self) -> None:
        """Test equipping item for player."""
        item = InventoryItem(index="longsword", name="Longsword", quantity=1)
        self.character.state.inventory.append(item)

        # Mock the compute service to return updated state
        updated_state = EntityState(
            abilities=self.character.state.abilities,
            level=self.character.state.level,
            hit_points=self.character.state.hit_points,
            hit_dice=self.character.state.hit_dice,
            currency=self.character.state.currency,
            equipment_slots=EquipmentSlots(),
        )
        updated_state.equipment_slots.set_slot(EquipmentSlotType.MAIN_HAND, "longsword")
        self.compute_service.equip_item_to_slot.return_value = updated_state

        self.service.equip_item(self.game_state, self.character_id, "longsword", EquipmentSlotType.MAIN_HAND)

        self.compute_service.equip_item_to_slot.assert_called_once()
        assert self.character.state == updated_state

    @pytest.mark.asyncio
    async def test_equip_item_npc(self) -> None:
        """Test equipping item for NPC."""
        npc = make_npc_instance()
        self.game_state.npcs.append(npc)
        item = InventoryItem(index="shortsword", name="Shortsword", quantity=1)
        npc.state.inventory.append(item)

        # Mock the compute service
        updated_state = EntityState(
            abilities=npc.state.abilities,
            level=npc.state.level,
            hit_points=npc.state.hit_points,
            hit_dice=npc.state.hit_dice,
            currency=npc.state.currency,
            equipment_slots=EquipmentSlots(),
        )
        updated_state.equipment_slots.set_slot(EquipmentSlotType.MAIN_HAND, "shortsword")
        self.compute_service.equip_item_to_slot.return_value = updated_state

        self.service.equip_item(self.game_state, npc.instance_id, "shortsword", EquipmentSlotType.MAIN_HAND)

        assert npc.state == updated_state

    @pytest.mark.asyncio
    async def test_equip_item_entity_not_found(self) -> None:
        """Test equipping item for non-existent entity."""
        with pytest.raises(ValueError, match="Entity 'invalid_id' not found"):
            self.service.equip_item(self.game_state, "invalid_id", "sword", None)

    @pytest.mark.asyncio
    async def test_update_spell_slots_player(self) -> None:
        """Test updating spell slots for player."""
        # Setup spellcasting
        self.character.state.spellcasting = Spellcasting(
            ability=SpellcastingAbility.INTELLIGENCE,
            spell_save_dc=15,
            spell_attack_bonus=7,
            spell_slots={
                1: SpellSlot(level=1, total=4, current=3),
                2: SpellSlot(level=2, total=3, current=2),
            },
            spells_known=[],
        )

        old_slots, new_slots, max_slots = self.service.update_spell_slots(self.game_state, self.character_id, 1, -1)

        assert old_slots == 3
        assert new_slots == 2
        assert max_slots == 4
        assert self.character.state.spellcasting.spell_slots[1].current == 2

    @pytest.mark.asyncio
    async def test_update_spell_slots_restore(self) -> None:
        """Test restoring spell slots."""
        self.character.state.spellcasting = Spellcasting(
            ability=SpellcastingAbility.INTELLIGENCE,
            spell_save_dc=15,
            spell_attack_bonus=7,
            spell_slots={
                1: SpellSlot(level=1, total=4, current=1),
            },
            spells_known=[],
        )

        old_slots, new_slots, max_slots = self.service.update_spell_slots(self.game_state, self.character_id, 1, 2)

        assert old_slots == 1
        assert new_slots == 3
        assert max_slots == 4

    @pytest.mark.asyncio
    async def test_update_spell_slots_cannot_exceed_max(self) -> None:
        """Test that spell slots cannot exceed maximum."""
        self.character.state.spellcasting = Spellcasting(
            ability=SpellcastingAbility.WISDOM,
            spell_save_dc=14,
            spell_attack_bonus=6,
            spell_slots={
                2: SpellSlot(level=2, total=3, current=2),
            },
            spells_known=[],
        )

        old_slots, new_slots, max_slots = self.service.update_spell_slots(self.game_state, self.character_id, 2, 5)

        assert new_slots == 3  # Capped at maximum

    @pytest.mark.asyncio
    async def test_update_spell_slots_no_spellcasting(self) -> None:
        """Test updating spell slots when entity has no spellcasting."""
        self.character.state.spellcasting = None

        with pytest.raises(ValueError, match="has no spellcasting ability"):
            self.service.update_spell_slots(self.game_state, self.character_id, 1, -1)

    @pytest.mark.asyncio
    async def test_update_spell_slots_invalid_level(self) -> None:
        """Test updating spell slots with invalid spell level."""
        self.character.state.spellcasting = Spellcasting(
            ability=SpellcastingAbility.INTELLIGENCE,
            spell_save_dc=15,
            spell_attack_bonus=7,
            spell_slots={1: SpellSlot(level=1, total=4, current=3)},
            spells_known=[],
        )

        with pytest.raises(ValueError, match="No spell slots for level 3"):
            self.service.update_spell_slots(self.game_state, self.character_id, 3, -1)

    @pytest.mark.asyncio
    async def test_recompute_entity_state_player(self) -> None:
        """Test recomputing entity state for player."""
        new_state = MagicMock(spec=EntityState)
        self.compute_service.recompute_entity_state.return_value = new_state

        self.service.recompute_entity_state(self.game_state, self.character_id)

        # Check that compute service was called
        self.compute_service.recompute_entity_state.assert_called_once()
        assert self.character.state == new_state

    @pytest.mark.asyncio
    async def test_recompute_entity_state_npc(self) -> None:
        """Test recomputing entity state for NPC."""
        npc = make_npc_instance()
        self.game_state.npcs.append(npc)
        new_state = MagicMock(spec=EntityState)
        self.compute_service.recompute_entity_state.return_value = new_state

        self.service.recompute_entity_state(self.game_state, npc.instance_id)

        # Check that compute service was called
        self.compute_service.recompute_entity_state.assert_called_once()
        assert npc.state == new_state

    @pytest.mark.asyncio
    async def test_recompute_entity_state_monster(self) -> None:
        """Test recomputing entity state for monster (should log debug)."""
        monster = make_monster_instance()
        self.game_state.monsters.append(monster)

        # Should not raise, just log debug
        self.service.recompute_entity_state(self.game_state, monster.instance_id)

        # Compute service should not be called for monsters
        self.compute_service.recompute_entity_state.assert_not_called()

    @pytest.mark.asyncio
    async def test_recompute_entity_state_not_found(self) -> None:
        """Test recomputing entity state for non-existent entity."""
        with pytest.raises(ValueError, match="Entity 'invalid_id' not found"):
            self.service.recompute_entity_state(self.game_state, "invalid_id")

    @pytest.mark.asyncio
    async def test_touch_mechanism_for_player_updates(self) -> None:
        """Test that player character is touched when modified."""
        # Get the initial updated_at timestamp
        initial_updated = self.character.updated_at

        # Any modification should update the timestamp
        self.service.update_hp(self.game_state, self.character_id, -5)

        assert self.character.updated_at > initial_updated
