from typing import Any
from unittest.mock import create_autospec

import pytest

from app.events.commands.broadcast_commands import (
    BroadcastGameUpdateCommand,
    BroadcastNarrativeCommand,
    BroadcastPolicyWarningCommand,
    BroadcastToolCallCommand,
    BroadcastToolResultCommand,
)
from app.events.handlers.broadcast_handler import BroadcastHandler
from app.interfaces.services.ai import IMessageService
from app.models.tool_results import UpdateHPResult
from tests.factories import make_game_state


class TestBroadcastHandler:
    def setup_method(self) -> None:
        self.message_service = create_autospec(IMessageService, instance=True)
        self.handler = BroadcastHandler(self.message_service)
        self.game_state = make_game_state()

    @pytest.mark.asyncio
    async def test_broadcast_narrative_chunk(self) -> None:
        gs = self.game_state
        content = "The forest is dark and mysterious..."

        command = BroadcastNarrativeCommand(
            game_id=gs.game_id,
            content=content,
            is_chunk=True,
            is_complete=False,
        )
        result = await self.handler.handle(command, gs)

        assert not result.mutated
        self.message_service.send_narrative.assert_called_once_with(
            gs.game_id,
            content,
            is_chunk=True,
            is_complete=False,
        )

    @pytest.mark.asyncio
    async def test_broadcast_narrative_complete(self) -> None:
        gs = self.game_state
        content = "You enter the tavern."

        command = BroadcastNarrativeCommand(
            game_id=gs.game_id,
            content=content,
            is_chunk=False,
            is_complete=True,
        )
        await self.handler.handle(command, gs)

        self.message_service.send_narrative.assert_called_once_with(
            gs.game_id,
            content,
            is_chunk=False,
            is_complete=True,
        )

    @pytest.mark.asyncio
    async def test_broadcast_tool_call(self) -> None:
        gs = self.game_state
        tool_name = "roll_ability_check"
        parameters: dict[str, Any] = {"ability": "DEX", "skill": "stealth"}

        command = BroadcastToolCallCommand(
            game_id=gs.game_id,
            tool_name=tool_name,
            parameters=parameters,
        )
        await self.handler.handle(command, gs)

        self.message_service.send_tool_call.assert_called_once_with(
            gs.game_id,
            tool_name,
            parameters,
        )

    @pytest.mark.asyncio
    async def test_broadcast_tool_result(self) -> None:
        gs = self.game_state
        tool_name = "update_hp"
        tool_result = UpdateHPResult(
            target="player",
            old_hp=10,
            new_hp=7,
            max_hp=12,
            amount=-3,
            damage_type="slashing",
            is_healing=False,
            is_unconscious=False,
        )

        command = BroadcastToolResultCommand(
            game_id=gs.game_id,
            tool_name=tool_name,
            result=tool_result,
        )
        await self.handler.handle(command, gs)

        self.message_service.send_tool_result.assert_called_once()

    @pytest.mark.asyncio
    async def test_broadcast_tool_result_none_skipped(self, caplog: pytest.LogCaptureFixture) -> None:
        caplog.set_level("WARNING")
        gs = self.game_state
        tool_name = "some_tool"

        command = BroadcastToolResultCommand(
            game_id=gs.game_id,
            tool_name=tool_name,
            result=None,
        )
        await self.handler.handle(command, gs)

        self.message_service.send_tool_result.assert_not_called()
        assert "Tool result for some_tool is None" in caplog.text

    @pytest.mark.asyncio
    async def test_broadcast_game_update(self) -> None:
        gs = self.game_state

        command = BroadcastGameUpdateCommand(game_id=gs.game_id)
        await self.handler.handle(command, gs)

        self.message_service.send_game_update.assert_called_once_with(
            gs.game_id,
            gs,
        )

    @pytest.mark.asyncio
    async def test_broadcast_policy_warning(self) -> None:
        gs = self.game_state
        message = "This action violates game policy"
        tool_name = "invalid_tool"

        command = BroadcastPolicyWarningCommand(
            game_id=gs.game_id,
            message=message,
            tool_name=tool_name,
            agent_type="narrative",
        )
        await self.handler.handle(command, gs)

        self.message_service.send_policy_warning.assert_called_once_with(
            gs.game_id,
            message,
            tool_name,
            "narrative",
        )
