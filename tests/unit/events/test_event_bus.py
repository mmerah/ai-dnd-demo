"""Unit tests for EventBus command execution."""

from dataclasses import dataclass
from typing import cast

import pytest
from pydantic import BaseModel

from app.events.base import BaseCommand, CommandResult
from app.events.event_bus import EventBus
from app.events.handlers.base_handler import BaseHandler
from app.interfaces.services.character import ICharacterService
from app.interfaces.services.game import IGameService
from app.models.game_state import GameState
from tests.factories import make_game_state


@dataclass
class StubCommand(BaseCommand):
    handler: str = "core"
    add_follow_up: bool = False
    mutate: bool = False
    recompute: bool = False

    def get_handler_name(self) -> str:
        return self.handler


class StubResult(BaseModel):
    handled: str


class StubHandler(BaseHandler):
    supported_commands = (StubCommand,)

    def __init__(self) -> None:
        self.handled: list[StubCommand] = []

    async def handle(self, command: BaseCommand, game_state: GameState) -> CommandResult:
        stub_command = cast(StubCommand, command)
        self.handled.append(stub_command)
        result = CommandResult(data=StubResult(handled=stub_command.command_id))
        result.mutated = stub_command.mutate
        result.recompute_state = stub_command.recompute
        if stub_command.add_follow_up:
            result.add_command(StubCommand(game_id=stub_command.game_id, handler=stub_command.handler))
        return result


class StubGameService:
    def __init__(self, game_state: GameState) -> None:
        self.game_state = game_state
        self.saved = False

    def get_game(self, game_id: str) -> GameState:
        assert game_id == self.game_state.game_id
        return self.game_state

    def save_game(self, game_state: GameState) -> None:
        assert game_state is self.game_state
        self.saved = True


class StubCharacterService:
    def __init__(self) -> None:
        self.calls = 0

    def recompute_character_state(self, game_state: GameState) -> None:
        self.calls += 1


@pytest.mark.asyncio
class TestEventBus:
    def setup_method(self) -> None:
        self.game_state = make_game_state()
        self.game_service = StubGameService(self.game_state)
        self.character_service = StubCharacterService()
        self.bus = EventBus(
            cast(IGameService, self.game_service),
            cast(ICharacterService, self.character_service),
        )
        self.handler = StubHandler()
        self.bus.register_handler("core", self.handler)

    async def test_submit_and_follow_up_execution(self) -> None:
        command = StubCommand(
            game_id=self.game_state.game_id,
            mutate=True,
            recompute=True,
            add_follow_up=True,
        )

        await self.bus.submit_and_wait([command])

        assert len(self.handler.handled) == 2
        assert self.game_service.saved
        assert self.character_service.calls == 1

    async def test_execute_command_returns_model(self) -> None:
        command = StubCommand(game_id=self.game_state.game_id)
        result = await self.bus.execute_command(command)
        assert isinstance(result, StubResult)
        assert result.handled == command.command_id

    async def test_missing_handler_raises(self) -> None:
        bad_command = StubCommand(game_id=self.game_state.game_id, handler="unknown")
        with pytest.raises(ValueError):
            await self.bus.execute_command(bad_command)
