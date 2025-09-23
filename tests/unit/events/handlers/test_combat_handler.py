"""Unit tests for CombatHandler."""

from unittest.mock import create_autospec

import pytest

from app.agents.core.types import AgentType
from app.events.commands.combat_commands import (
    EndCombatCommand,
    NextTurnCommand,
    SpawnMonstersCommand,
    StartCombatCommand,
)
from app.events.handlers.combat_handler import CombatHandler
from app.interfaces.services.game import ICombatService
from app.models.attributes import EntityType
from app.models.combat import CombatFaction, CombatParticipant, CombatState, MonsterSpawnInfo
from app.models.entity import IEntity
from app.models.game_state import GameState
from app.models.tool_results import (
    EndCombatResult,
    NextTurnResult,
    SpawnMonstersResult,
    StartCombatResult,
)
from tests.factories import make_game_state, make_monster_instance, make_monster_sheet


class TestCombatHandler:
    """Test CombatHandler command processing."""

    def setup_method(self) -> None:
        """Set up test environment."""
        self.combat_service = create_autospec(spec=ICombatService, instance=True)
        self.handler = CombatHandler(self.combat_service)
        self.game_state = make_game_state()

    @pytest.mark.asyncio
    async def test_start_combat(self) -> None:
        monster_sheet = make_monster_sheet(index="goblin", name="Goblin")
        monster_instance = make_monster_instance(
            sheet=monster_sheet, instance_id="goblin-1", current_location_id="test-location"
        )
        self.game_state.monsters.append(monster_instance)

        # Mock start_combat to update game_state as the real service would
        def start_combat_side_effect(game_state: GameState) -> CombatState:
            game_state.combat = CombatState(is_active=True, combat_occurrence=1)
            return game_state.combat

        self.combat_service.start_combat.side_effect = start_combat_side_effect
        participant = CombatParticipant(
            name="Goblin",
            initiative=15,
            is_player=False,
            entity_id=monster_instance.instance_id,
            entity_type=EntityType.MONSTER,
            faction=CombatFaction.ENEMY,
        )
        player_participant = CombatParticipant(
            name="Test Character",
            initiative=12,
            is_player=True,
            entity_id=self.game_state.character.instance_id,
            entity_type=EntityType.PLAYER,
            faction=CombatFaction.PLAYER,
        )
        self.combat_service.add_participant.return_value = participant
        self.combat_service.ensure_player_in_combat.return_value = player_participant

        command = StartCombatCommand(
            game_id=self.game_state.game_id,
            entity_ids=[monster_instance.instance_id],
            agent_type=AgentType.NARRATIVE,
        )

        # Set combat to inactive initially to trigger start_combat
        self.game_state.combat.is_active = False

        result = await self.handler.handle(command, self.game_state)

        # Verify the handler called the service methods correctly
        self.combat_service.start_combat.assert_called_once_with(self.game_state)
        self.combat_service.add_participant.assert_called_once()
        self.combat_service.ensure_player_in_combat.assert_called_once_with(self.game_state)

        # Verify the handler set the active agent
        assert self.game_state.active_agent == AgentType.COMBAT

        # Verify the result structure
        assert result.mutated
        assert isinstance(result.data, StartCombatResult)
        assert result.data.combat_started
        assert len(result.data.participants) == 2
        participant_ids = {p.entity_id for p in result.data.participants}
        assert self.game_state.character.instance_id in participant_ids
        assert monster_instance.instance_id in participant_ids

    @pytest.mark.asyncio
    async def test_spawn_monsters(self) -> None:
        self.game_state.combat.is_active = True

        mock_monster = create_autospec(spec=IEntity, instance=True)
        mock_monster.display_name = "Wolf"
        mock_monster.instance_id = "wolf-1"
        self.combat_service.spawn_free_monster.return_value = mock_monster

        participant = CombatParticipant(
            name="Wolf",
            initiative=14,
            is_player=False,
            entity_id=mock_monster.instance_id,
            entity_type=EntityType.MONSTER,
            faction=CombatFaction.ENEMY,
        )
        self.combat_service.add_participant.return_value = participant

        command = SpawnMonstersCommand(
            game_id=self.game_state.game_id,
            monsters=[MonsterSpawnInfo(monster_index="wolf", quantity=2)],
            agent_type=AgentType.NARRATIVE,
        )

        result = await self.handler.handle(command, self.game_state)

        assert result.mutated
        assert isinstance(result.data, SpawnMonstersResult)
        assert len(result.data.monsters_spawned) == 2
        assert self.combat_service.spawn_free_monster.call_count == 2

    @pytest.mark.asyncio
    async def test_next_turn(self) -> None:
        self.game_state.combat.is_active = True
        current_participant = CombatParticipant(
            name="Goblin",
            initiative=15,
            is_player=False,
            entity_id="goblin-1",
            entity_type=EntityType.MONSTER,
            faction=CombatFaction.ENEMY,
            is_active=True,
        )
        self.game_state.combat.participants = [current_participant]
        self.combat_service.should_auto_end_combat.return_value = False

        command = NextTurnCommand(
            game_id=self.game_state.game_id,
            agent_type=AgentType.COMBAT,
        )

        # Set turn index so current participant is the current turn
        self.game_state.combat.turn_index = 0
        result = await self.handler.handle(command, self.game_state)

        assert result.mutated
        assert isinstance(result.data, NextTurnResult)
        assert result.data.current_turn == current_participant

    @pytest.mark.asyncio
    async def test_end_combat(self) -> None:
        self.game_state.combat.is_active = True
        self.game_state.active_agent = AgentType.COMBAT

        command = EndCombatCommand(
            game_id=self.game_state.game_id,
            agent_type=AgentType.COMBAT,
        )

        result = await self.handler.handle(command, self.game_state)

        # Verify the handler called the service method
        self.combat_service.end_combat.assert_called_once_with(self.game_state)

        # Verify the handler set the active agent
        assert self.game_state.active_agent == AgentType.NARRATIVE

        # Verify the result structure
        assert result.mutated
        assert isinstance(result.data, EndCombatResult)

    @pytest.mark.asyncio
    async def test_invalid_entity_error(self) -> None:
        command = StartCombatCommand(
            game_id=self.game_state.game_id,
            entity_ids=["non-existent"],
            agent_type=AgentType.NARRATIVE,
        )

        with pytest.raises(ValueError, match="Entity not found"):
            await self.handler.handle(command, self.game_state)

    @pytest.mark.asyncio
    async def test_agent_type_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test warning for wrong agent type."""
        self.game_state.combat.is_active = True
        command = NextTurnCommand(
            game_id=self.game_state.game_id,
            agent_type=AgentType.NARRATIVE,
        )
        self.combat_service.should_auto_end_combat.return_value = False
        await self.handler.handle(command, self.game_state)

        assert "should be COMBAT only" in caplog.text
