from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any

import pytest
from pydantic import BaseModel

from app.agents.core.types import AgentType
from app.common.types import JSONSerializable
from app.events.base import BaseCommand
from app.models.attributes import Abilities, AbilityModifiers
from app.models.game_state import GameEventType
from app.services.game.event_manager import EventManager
from app.tools.decorators import tool_handler
from app.tools.dice_tools import _prepare_roll_command_kwargs
from app.utils.ability_utils import (
    ABILITY_NAME_TO_CODE,
    get_ability_modifier,
    normalize_ability_name,
    set_ability_value,
)
from app.utils.names import dedupe_display_name
from tests.factories import make_game_state, make_monster_sheet


class SimpleResult(BaseModel):
    status: str


class DummyActionService:
    def __init__(self) -> None:
        self.calls: list[SimpleNamespace] = []
        self.raise_error = False
        self.error_message = "error"
        self.result = SimpleResult(status="ok")

    async def execute_command_as_action(
        self,
        tool_name: str,
        command: BaseCommand,
        game_state: object,
        agent_type: AgentType,
        broadcast_parameters: dict[str, object] | None = None,
    ) -> BaseModel:
        self.calls.append(
            SimpleNamespace(
                tool_name=tool_name,
                command=command,
                game_state=game_state,
                broadcast=broadcast_parameters,
                agent_type=agent_type,
            )
        )
        if self.raise_error:
            raise ValueError(self.error_message)
        return self.result


class DummyEventBus:
    def __init__(self) -> None:
        self.submissions: list[list[object]] = []

    async def submit_and_wait(self, commands: list[object]) -> None:
        self.submissions.append(commands)


@dataclass
class DummyCommand(BaseCommand):
    value: int = 0
    agent_type: AgentType | None = None

    def get_handler_name(self) -> str:
        return "dummy"


class TestDiceTools:
    def setup_method(self) -> None:
        self.base_kwargs: dict[str, str | int] = dict(
            dice=" 2d6 ",
            modifier=3,
            roll_type="attack",
            purpose="Pack tactics",
            ability="Strength",
            skill="Athletics",
        )

    def test_prepare_roll_command(self) -> None:
        command_kwargs, broadcast_kwargs = _prepare_roll_command_kwargs(self.base_kwargs)
        assert command_kwargs["dice"] == str(self.base_kwargs["dice"]).strip()
        assert command_kwargs["ability"] == self.base_kwargs["ability"]
        assert command_kwargs["skill"] == self.base_kwargs["skill"]
        assert broadcast_kwargs == {k: v for k, v in self.base_kwargs.items()}

        minimal_kwargs: dict[str, str | int] = {
            k: v for k, v in self.base_kwargs.items() if k not in {"ability", "skill"}
        }
        minimal_kwargs["purpose"] = "Non-combat scouting"
        trimmed, broadcast = _prepare_roll_command_kwargs(minimal_kwargs)
        assert "ability" not in trimmed and "skill" not in trimmed
        assert trimmed["dice"] == str(minimal_kwargs["dice"]).strip()
        assert broadcast == {k: v for k, v in minimal_kwargs.items()}


class TestEventManager:
    def setup_method(self) -> None:
        self.manager = EventManager()
        self.game_state = make_game_state()

    def test_add_event_records_payload_and_defaults(self) -> None:
        parameters: dict[str, JSONSerializable] = {"dice": "1d20", "modifier": 5}
        result_payload: dict[str, JSONSerializable] = {"total": 18}
        tool_name = "roll_dice"
        initial_events = len(self.game_state.game_events)

        self.manager.add_event(
            self.game_state,
            GameEventType.TOOL_CALL,
            tool_name,
            parameters,
            result_payload,
        )
        recorded = self.game_state.game_events[-1]
        assert len(self.game_state.game_events) == initial_events + 1
        assert recorded.event_type is GameEventType.TOOL_CALL
        assert recorded.tool_name == tool_name
        assert recorded.parameters == parameters
        assert recorded.result == result_payload

        self.manager.add_event(self.game_state, GameEventType.TOOL_RESULT, tool_name="update_hp")
        defaults = self.game_state.game_events[-1]
        assert defaults.parameters == {}
        assert defaults.result == {}


@pytest.mark.asyncio
class TestToolHandlerDecorator:
    def setup_method(self) -> None:
        self.game_state = make_game_state()
        self.event_bus, self.action_service = DummyEventBus(), DummyActionService()
        self.deps = SimpleNamespace(
            game_state=self.game_state,
            event_bus=self.event_bus,
            agent_type=AgentType.COMBAT,
            action_service=self.action_service,
        )
        self.ctx = SimpleNamespace(deps=self.deps)

    async def test_tool_handler_scenarios(self) -> None:
        def prepare(kwargs: dict[str, Any]) -> tuple[dict[str, Any], dict[str, JSONSerializable]]:
            return {"value": kwargs["value"]}, {"value": kwargs["value"], "note": kwargs["note"]}

        async def roll(ctx: object, **_: Any) -> None:  # pragma: no cover - original should not run
            raise AssertionError

        wrapped = tool_handler(command_class=DummyCommand, prepare=prepare)(roll)
        payload = {"value": 7, "note": "Scouting"}
        result = await wrapped(self.ctx, **payload)

        call = self.action_service.calls[-1]
        assert isinstance(result, SimpleResult)
        assert call.tool_name == roll.__name__
        assert isinstance(call.command, DummyCommand)
        assert call.command.value == payload["value"]
        assert call.command.agent_type == AgentType.COMBAT
        assert call.broadcast == {"value": payload["value"], "note": payload["note"]}

        async def roll_dice(ctx: object, **_: Any) -> None:  # pragma: no cover - original should not run
            raise AssertionError

        # Test policy violation handling, ActionService raise with "BLOCKED"
        blocked_tool = tool_handler(command_class=DummyCommand)(roll_dice)
        self.game_state.combat.is_active = True
        self.deps.agent_type = AgentType.NARRATIVE
        self.action_service.raise_error = True
        self.action_service.error_message = (
            "BLOCKED: Narrative agent attempted to use 'roll_dice' during active combat."
        )

        # Dummy command expect value parameter
        blocked_result: Any = await blocked_tool(
            self.ctx,
            value=5,
        )
        assert getattr(blocked_result, "type", "") == "tool_error"  # ToolErrorResult is used for policy violations
        assert getattr(blocked_result, "tool_name", "") == roll_dice.__name__
        assert "BLOCKED:" in getattr(blocked_result, "error", "")
        assert (
            getattr(blocked_result, "suggestion", "")
            == "This tool is not allowed in the current context. Check agent permissions."
        )

        async def move_tool(ctx: object, **_: Any) -> None:  # pragma: no cover - original should not run
            raise AssertionError

        error_tool = tool_handler(command_class=DummyCommand)(move_tool)
        self.action_service.raise_error = True
        self.action_service.error_message = "Creature not found"
        self.game_state.combat.is_active = False
        self.deps.agent_type = AgentType.COMBAT
        error_result: Any = await error_tool(self.ctx, value=3)
        assert getattr(error_result, "type", "") == "tool_error"
        assert "Check the ID" in (getattr(error_result, "suggestion", "") or "")


class TestAbilityUtils:
    def setup_method(self) -> None:
        self.modifiers = AbilityModifiers(STR=2, DEX=1, CON=-1, INT=0, WIS=3, CHA=-2)
        self.abilities = Abilities(STR=10, DEX=12, CON=14, INT=8, WIS=13, CHA=9)

    def test_normalize_variants(self) -> None:
        assert normalize_ability_name("Wisdom") == ABILITY_NAME_TO_CODE["wisdom"]
        assert normalize_ability_name("dex") == ABILITY_NAME_TO_CODE["dexterity"]
        assert normalize_ability_name("luck") is None

    def test_get_and_set_ability_value(self) -> None:
        original = get_ability_modifier(self.modifiers, "STR")
        set_ability_value(self.abilities, "STR", original + 4)
        updated = get_ability_modifier(self.abilities, "STR")
        assert original == self.modifiers.STR
        assert updated == original + 4


class TestNameUtils:
    def setup_method(self) -> None:
        base_sheet = make_monster_sheet(name="Shadow Hound")
        self.existing_names = [base_sheet.name, make_monster_sheet(name=f"{base_sheet.name} 2").name]

    def test_dedupe_behaviour(self) -> None:
        desired = self.existing_names[0]
        deduped = dedupe_display_name(self.existing_names, desired)
        expected_suffix = len(self.existing_names) + 1
        assert deduped == f"{desired} {expected_suffix}"

        new_name = "Glimmer Fox"
        result = dedupe_display_name(self.existing_names, new_name)
        assert result == new_name
