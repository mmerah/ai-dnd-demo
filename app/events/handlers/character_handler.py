"""Handler for character-related commands."""

import logging

from app.events.base import BaseCommand, CommandResult
from app.events.commands.broadcast_commands import BroadcastGameUpdateCommand
from app.events.commands.character_commands import (
    UpdateConditionCommand,
    UpdateHPCommand,
    UpdateSpellSlotsCommand,
)
from app.events.handlers.base_handler import BaseHandler
from app.models.game_state import GameState
from app.models.tool_results import (
    AddConditionResult,
    RemoveConditionResult,
    UpdateHPResult,
    UpdateSpellSlotsResult,
)

logger = logging.getLogger(__name__)


class CharacterHandler(BaseHandler):
    """Handler for character-related commands."""

    # Declarative list of supported commands for verification
    supported_commands = (
        UpdateHPCommand,
        UpdateConditionCommand,
        UpdateSpellSlotsCommand,
    )

    async def handle(self, command: BaseCommand, game_state: GameState) -> CommandResult:
        """Handle character commands."""
        result = CommandResult()

        if isinstance(command, UpdateHPCommand):
            old_hp = 0
            new_hp = 0
            max_hp = 0

            if command.target == "player":
                character = game_state.character.state
                old_hp = character.hit_points.current
                max_hp = character.hit_points.maximum
                new_hp = min(old_hp + command.amount, max_hp) if command.amount > 0 else max(0, old_hp + command.amount)
                character.hit_points.current = new_hp
            else:
                npc = next(
                    (n for n in game_state.npcs if n.sheet.character.name.lower() == command.target.lower()), None
                )
                if npc:
                    old_hp = npc.state.hit_points.current
                    max_hp = npc.state.hit_points.maximum
                    new_hp = (
                        min(old_hp + command.amount, max_hp) if command.amount > 0 else max(0, old_hp + command.amount)
                    )
                    npc.state.hit_points.current = new_hp
                else:
                    raise ValueError(f"Target {command.target} not found")

            # Save game state
            self.game_service.save_game(game_state)

            result.data = UpdateHPResult(
                target=command.target,
                old_hp=old_hp,
                new_hp=new_hp,
                max_hp=max_hp,
                amount=command.amount,
                damage_type=command.damage_type,
                is_healing=command.amount > 0,
                is_unconscious=new_hp == 0,
            )

            # Add broadcast commands
            result.add_command(BroadcastGameUpdateCommand(game_id=command.game_id))

            logger.info(
                f"HP Update: {command.target} {'healed' if command.amount > 0 else 'took'} "
                f"{abs(command.amount)} {command.damage_type} - HP: {old_hp} → {new_hp}/{max_hp}",
            )

        elif isinstance(command, UpdateConditionCommand) and command.action == "add":
            if command.target == "player":
                character = game_state.character.state
                if command.condition not in character.conditions:
                    character.conditions.append(command.condition)
            elif game_state.combat:
                for participant in game_state.combat.participants:
                    if participant.name.lower() == command.target.lower():
                        if command.condition not in participant.conditions:
                            participant.conditions.append(command.condition)
                        break

            self.game_service.save_game(game_state)

            result.data = AddConditionResult(
                target=command.target,
                condition=command.condition,
                duration=command.duration,
            )

            result.add_command(BroadcastGameUpdateCommand(game_id=command.game_id))

            logger.info(f"Condition Added: {command.target} is now {command.condition}")

        elif isinstance(command, UpdateConditionCommand) and command.action == "remove":
            removed = False

            if command.target == "player":
                character = game_state.character.state
                if command.condition in character.conditions:
                    character.conditions.remove(command.condition)
                    removed = True
            elif game_state.combat:
                for participant in game_state.combat.participants:
                    if participant.name.lower() == command.target.lower():
                        if command.condition in participant.conditions:
                            participant.conditions.remove(command.condition)
                            removed = True
                        break

            self.game_service.save_game(game_state)

            result.data = RemoveConditionResult(
                target=command.target,
                condition=command.condition,
                removed=removed,
            )

            result.add_command(BroadcastGameUpdateCommand(game_id=command.game_id))

            logger.info(f"Condition Removed: {command.target} is no longer {command.condition}")

        elif isinstance(command, UpdateSpellSlotsCommand):
            character = game_state.character.state

            if not character.spellcasting:
                raise ValueError("Character has no spellcasting ability")

            spell_slots = character.spellcasting.spell_slots

            if command.level not in spell_slots:
                raise ValueError(f"No spell slots for level {command.level}")

            slot = spell_slots[command.level]
            old_slots = slot.current
            slot.current = max(0, min(slot.total, old_slots + command.amount))
            new_slots = slot.current
            max_slots = slot.total

            self.game_service.save_game(game_state)

            result.data = UpdateSpellSlotsResult(
                level=command.level,
                old_slots=old_slots,
                new_slots=new_slots,
                max_slots=max_slots,
                change=command.amount,
            )

            result.add_command(BroadcastGameUpdateCommand(game_id=command.game_id))

            logger.info(f"Spell Slots: Level {command.level} - {old_slots} → {new_slots}/{max_slots}")

        return result

    def can_handle(self, command: BaseCommand) -> bool:
        """Check if this handler can process the given command."""
        return isinstance(command, self.supported_commands)
