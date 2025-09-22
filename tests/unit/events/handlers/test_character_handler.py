from unittest.mock import create_autospec

import pytest

from app.agents.core.types import AgentType
from app.events.commands.entity_commands import (
    LevelUpCommand,
    UpdateConditionCommand,
    UpdateHPCommand,
    UpdateSpellSlotsCommand,
)
from app.events.handlers.entity_handler import EntityHandler
from app.interfaces.services.character import IEntityStateService, ILevelProgressionService
from app.models.attributes import EntityType
from app.models.instances.character_instance import CharacterInstance
from app.models.tool_results import (
    AddConditionResult,
    LevelUpResult,
    RemoveConditionResult,
    UpdateHPResult,
    UpdateSpellSlotsResult,
)
from tests.factories import make_game_state


class TestCharacterHandler:
    def setup_method(self) -> None:
        self.entity_state_service = create_autospec(IEntityStateService, instance=True)
        self.level_service = create_autospec(ILevelProgressionService, instance=True)
        self.handler = EntityHandler(self.entity_state_service, self.level_service)
        self.game_state = make_game_state()

    @pytest.mark.asyncio
    async def test_update_hp_damage(self) -> None:
        gs = self.game_state
        cid = gs.character.instance_id
        initial_hp = gs.character.state.hit_points.current

        self.entity_state_service.update_hp.return_value = (
            initial_hp,
            initial_hp - 3,
            gs.character.state.hit_points.maximum,
        )

        command = UpdateHPCommand(
            game_id=gs.game_id,
            entity_id=cid,
            entity_type=EntityType.PLAYER,
            amount=-3,
        )
        result = await self.handler.handle(command, gs)

        assert isinstance(result.data, UpdateHPResult)
        assert result.data.new_hp == initial_hp - 3
        assert result.mutated
        self.entity_state_service.update_hp.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_hp_healing(self) -> None:
        gs = self.game_state
        cid = gs.character.instance_id
        gs.character.state.hit_points.current = 5

        self.entity_state_service.update_hp.return_value = (5, 10, gs.character.state.hit_points.maximum)

        command = UpdateHPCommand(
            game_id=gs.game_id,
            entity_id=cid,
            entity_type=EntityType.PLAYER,
            amount=5,
        )
        result = await self.handler.handle(command, gs)

        assert isinstance(result.data, UpdateHPResult)
        assert result.data.new_hp == 10
        assert result.data.is_healing

    @pytest.mark.asyncio
    async def test_update_hp_combat_only_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        caplog.set_level("WARNING")
        gs = self.game_state
        gs.combat.is_active = True
        cid = gs.character.instance_id

        self.entity_state_service.update_hp.return_value = (12, 9, 12)

        command = UpdateHPCommand(
            game_id=gs.game_id,
            entity_id=cid,
            entity_type=EntityType.PLAYER,
            amount=-3,
            agent_type=AgentType.NARRATIVE,
        )
        await self.handler.handle(command, gs)
        assert "COMBAT agent only" in caplog.text

    @pytest.mark.asyncio
    async def test_add_condition(self) -> None:
        gs = self.game_state
        cid = gs.character.instance_id

        self.entity_state_service.add_condition.return_value = True

        command = UpdateConditionCommand(
            game_id=gs.game_id,
            entity_id=cid,
            entity_type=EntityType.PLAYER,
            condition="blessed",
            action="add",
        )
        result = await self.handler.handle(command, gs)

        assert isinstance(result.data, AddConditionResult)
        assert result.data.condition == "blessed"
        assert result.mutated
        self.entity_state_service.add_condition.assert_called_once()

    @pytest.mark.asyncio
    async def test_remove_condition(self) -> None:
        gs = self.game_state
        cid = gs.character.instance_id
        gs.character.state.conditions = ["blessed", "poisoned"]

        self.entity_state_service.remove_condition.return_value = True

        command = UpdateConditionCommand(
            game_id=gs.game_id,
            entity_id=cid,
            entity_type=EntityType.PLAYER,
            condition="poisoned",
            action="remove",
        )
        result = await self.handler.handle(command, gs)

        assert isinstance(result.data, RemoveConditionResult)
        assert result.data.removed
        assert result.data.condition == "poisoned"

    @pytest.mark.asyncio
    async def test_update_spell_slots(self) -> None:
        gs = self.game_state

        self.entity_state_service.update_spell_slots.return_value = (3, 2, 3)

        command = UpdateSpellSlotsCommand(game_id=gs.game_id, level=2, amount=-1)
        result = await self.handler.handle(command, gs)

        assert isinstance(result.data, UpdateSpellSlotsResult)
        assert result.data.new_slots == 2
        assert result.data.old_slots == 3
        assert result.data.level == 2

    @pytest.mark.asyncio
    async def test_level_up(self) -> None:
        gs = self.game_state
        old_level = gs.character.state.level
        old_max_hp = gs.character.state.hit_points.maximum

        def _level_up(_: object, character_instance: CharacterInstance) -> None:
            character_instance.state.level = old_level + 1
            character_instance.state.hit_points.maximum = old_max_hp + 5

        self.level_service.level_up_character.side_effect = _level_up

        command = LevelUpCommand(game_id=gs.game_id)
        result = await self.handler.handle(command, gs)

        assert isinstance(result.data, LevelUpResult)
        assert result.data.hp_increase == 5
        assert result.data.new_level == old_level + 1
        assert gs.character.state.level == old_level + 1
        assert result.mutated
