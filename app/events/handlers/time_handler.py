"""Handler for time-related commands."""

import logging

from app.events.base import BaseCommand, CommandResult
from app.events.commands.broadcast_commands import (
    BroadcastGameUpdateCommand,
)
from app.events.commands.time_commands import (
    AdvanceTimeCommand,
    LongRestCommand,
    ShortRestCommand,
)
from app.events.handlers.base_handler import BaseHandler
from app.models.game_state import GameState
from app.models.tool_results import (
    AdvanceTimeResult,
    LongRestResult,
    ShortRestResult,
)

logger = logging.getLogger(__name__)


class TimeHandler(BaseHandler):
    """Handler for time-related commands."""

    supported_commands = (
        ShortRestCommand,
        LongRestCommand,
        AdvanceTimeCommand,
    )

    async def handle(self, command: BaseCommand, game_state: GameState) -> CommandResult:
        """Handle time commands."""
        result = CommandResult()
        character = game_state.character.state

        if isinstance(command, ShortRestCommand):
            # Short rest: restore some HP and reset abilities
            old_hp = character.hit_points.current

            # Spend hit dice for healing (simplified: use half of level)
            constitution_modifier = (game_state.character.state.abilities.CON - 10) // 2
            healing = game_state.character.state.level // 2 + constitution_modifier
            character.hit_points.current = min(character.hit_points.current + healing, character.hit_points.maximum)

            # Advance time by 1 hour
            game_state.game_time.minute += 60
            while game_state.game_time.minute >= 60:
                game_state.game_time.minute -= 60
                game_state.game_time.hour += 1
                while game_state.game_time.hour >= 24:
                    game_state.game_time.hour -= 24
                    game_state.game_time.day += 1

            # Refresh derived values
            self.game_service.recompute_character_state(game_state)
            self.game_service.save_game(game_state)

            result.data = ShortRestResult(
                old_hp=old_hp,
                new_hp=character.hit_points.current,
                healing=healing,
                time=f"Day {game_state.game_time.day}, {game_state.game_time.hour:02d}:{game_state.game_time.minute:02d}",
            )

            result.add_command(BroadcastGameUpdateCommand(game_id=command.game_id))

            logger.info(f"Short Rest: Healed {healing} HP, time advanced 1 hour")

        elif isinstance(command, LongRestCommand):
            # Long rest: restore all HP, spell slots, and remove conditions
            old_hp = character.hit_points.current
            old_conditions = character.conditions.copy()

            # Restore HP to maximum
            character.hit_points.current = character.hit_points.maximum

            # Restore all spell slots
            if character.spellcasting:
                for _slot_key, slot in character.spellcasting.spell_slots.items():
                    slot.current = slot.total

            # Remove most conditions (keep some like cursed)
            persistent_conditions = ["cursed"]
            character.conditions = [c for c in character.conditions if c in persistent_conditions]

            # Advance time by 8 hours
            game_state.game_time.hour += 8
            while game_state.game_time.hour >= 24:
                game_state.game_time.hour -= 24
                game_state.game_time.day += 1

            # Refresh derived values
            self.game_service.recompute_character_state(game_state)
            self.game_service.save_game(game_state)

            result.data = LongRestResult(
                old_hp=old_hp,
                new_hp=character.hit_points.current,
                conditions_removed=[c for c in old_conditions if c not in character.conditions],
                spell_slots_restored=True,
                time=f"Day {game_state.game_time.day}, {game_state.game_time.hour:02d}:{game_state.game_time.minute:02d}",
            )

            result.add_command(BroadcastGameUpdateCommand(game_id=command.game_id))

            logger.info("Long Rest: Full HP restored, spell slots restored, conditions cleared")

        elif isinstance(command, AdvanceTimeCommand):
            # Advance game time by specified minutes
            old_time = (
                f"Day {game_state.game_time.day}, {game_state.game_time.hour:02d}:{game_state.game_time.minute:02d}"
            )

            game_state.game_time.minute += command.minutes
            while game_state.game_time.minute >= 60:
                game_state.game_time.minute -= 60
                game_state.game_time.hour += 1
                while game_state.game_time.hour >= 24:
                    game_state.game_time.hour -= 24
                    game_state.game_time.day += 1

            new_time = (
                f"Day {game_state.game_time.day}, {game_state.game_time.hour:02d}:{game_state.game_time.minute:02d}"
            )

            # Refresh derived values (time passing may not affect derived stats, but ensures consistency)
            self.game_service.recompute_character_state(game_state)
            self.game_service.save_game(game_state)

            result.data = AdvanceTimeResult(
                old_time=old_time,
                new_time=new_time,
                minutes_advanced=command.minutes,
            )

            result.add_command(BroadcastGameUpdateCommand(game_id=command.game_id))

            logger.info(f"Time Advanced: {command.minutes} minutes - {old_time} → {new_time}")

        return result
