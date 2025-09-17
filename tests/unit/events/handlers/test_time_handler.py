import pytest

from app.events.commands.time_commands import AdvanceTimeCommand, LongRestCommand, ShortRestCommand
from app.events.handlers.time_handler import TimeHandler
from app.models.spell import Spellcasting, SpellcastingAbility, SpellSlot
from app.models.tool_results import AdvanceTimeResult, LongRestResult, ShortRestResult
from tests.factories import make_game_state


class TestTimeHandler:
    def setup_method(self) -> None:
        self.handler = TimeHandler()
        self.game_state = make_game_state()
        self.character_state = self.game_state.character.state

    @pytest.mark.asyncio
    async def test_short_rest_heals_hit_dice(self) -> None:
        gs = self.game_state
        self.character_state.hit_points.current = 4
        self.character_state.hit_points.maximum = 12
        gs.game_time.hour = 10
        gs.game_time.minute = 45

        command = ShortRestCommand(game_id=gs.game_id)
        result = await self.handler.handle(command, gs)

        assert isinstance(result.data, ShortRestResult)
        assert result.data.new_hp == self.character_state.hit_points.current
        assert result.data.old_hp == 4
        assert result.mutated
        # Time should advance by 1 hour
        assert gs.game_time.hour == 11
        assert gs.game_time.minute == 45
        assert result.data.time == f"Day {gs.game_time.day}, 11:45"

    @pytest.mark.asyncio
    async def test_short_rest_advances_time(self) -> None:
        gs = self.game_state
        gs.game_time.hour = 10
        gs.game_time.minute = 45

        command = ShortRestCommand(game_id=gs.game_id)
        result = await self.handler.handle(command, gs)

        assert isinstance(result.data, ShortRestResult)
        assert gs.game_time.hour == 11
        assert gs.game_time.minute == 45

    @pytest.mark.asyncio
    async def test_long_rest_full_healing(self) -> None:
        gs = self.game_state
        self.character_state.hit_points.current = 3
        self.character_state.hit_points.maximum = 12

        command = LongRestCommand(game_id=gs.game_id)
        result = await self.handler.handle(command, gs)

        assert isinstance(result.data, LongRestResult)
        assert result.data.new_hp == 12
        assert result.data.old_hp == 3
        assert self.character_state.hit_points.current == 12

    @pytest.mark.asyncio
    async def test_long_rest_removes_conditions(self) -> None:
        gs = self.game_state
        self.character_state.conditions = ["poisoned", "cursed", "exhaustion"]

        command = LongRestCommand(game_id=gs.game_id)
        result = await self.handler.handle(command, gs)

        assert isinstance(result.data, LongRestResult)
        assert "poisoned" in result.data.conditions_removed
        # Cursed should remain
        assert "cursed" in self.character_state.conditions
        assert "poisoned" not in self.character_state.conditions

    @pytest.mark.asyncio
    async def test_long_rest_restores_spell_slots(self) -> None:
        gs = self.game_state
        self.character_state.spellcasting = Spellcasting(
            ability=SpellcastingAbility.INT,
            spells_known=[],
            spell_slots={
                1: SpellSlot(level=1, total=2, current=0),
                2: SpellSlot(level=2, total=1, current=0),
            },
        )

        command = LongRestCommand(game_id=gs.game_id)
        result = await self.handler.handle(command, gs)

        assert isinstance(result.data, LongRestResult)
        assert result.data.spell_slots_restored
        assert self.character_state.spellcasting.spell_slots[1].current == 2
        assert self.character_state.spellcasting.spell_slots[2].current == 1

    @pytest.mark.asyncio
    async def test_long_rest_advances_time_8_hours(self) -> None:
        gs = self.game_state
        gs.game_time.day = 1
        gs.game_time.hour = 22
        gs.game_time.minute = 30

        command = LongRestCommand(game_id=gs.game_id)
        result = await self.handler.handle(command, gs)

        assert isinstance(result.data, LongRestResult)
        assert gs.game_time.day == 2
        assert gs.game_time.hour == 6
        assert gs.game_time.minute == 30

    @pytest.mark.asyncio
    async def test_advance_time_minutes(self) -> None:
        gs = self.game_state
        gs.game_time.day = 1
        gs.game_time.hour = 10
        gs.game_time.minute = 15

        command = AdvanceTimeCommand(game_id=gs.game_id, minutes=45)
        result = await self.handler.handle(command, gs)

        assert isinstance(result.data, AdvanceTimeResult)
        assert result.data.minutes_advanced == 45
        assert gs.game_time.hour == 11
        assert gs.game_time.minute == 0

    @pytest.mark.asyncio
    async def test_advance_time_multiple_days(self) -> None:
        gs = self.game_state
        gs.game_time.day = 1
        gs.game_time.hour = 16
        gs.game_time.minute = 30
        previous_time = f"Day {gs.game_time.day}, {gs.game_time.hour:02d}:{gs.game_time.minute:02d}"

        # Advance 1100 minutes (18 hours 20 minutes)
        command = AdvanceTimeCommand(game_id=gs.game_id, minutes=1100)
        result = await self.handler.handle(command, gs)

        assert isinstance(result.data, AdvanceTimeResult)
        assert result.data.old_time == previous_time
        assert gs.game_time.day == 2
        assert gs.game_time.hour == 10
        assert gs.game_time.minute == 50
