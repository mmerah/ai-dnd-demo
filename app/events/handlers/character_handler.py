"""Handler for character-related commands."""

import logging

from app.events.base import BaseCommand, CommandResult
from app.events.commands.broadcast_commands import BroadcastCharacterUpdateCommand
from app.events.commands.character_commands import (
    AddConditionCommand,
    RemoveConditionCommand,
    UpdateHPCommand,
    UpdateSpellSlotsCommand,
)
from app.events.handlers.base_handler import BaseHandler
from app.models.game_state import GameState

logger = logging.getLogger(__name__)


class CharacterHandler(BaseHandler):
    """Handler for character-related commands."""

    async def handle(self, command: BaseCommand, game_state: GameState) -> CommandResult:
        """Handle character commands."""
        result = CommandResult(success=True)

        if isinstance(command, UpdateHPCommand):
            old_hp = 0
            new_hp = 0
            max_hp = 0

            if command.target == "player":
                character = game_state.character
                old_hp = character.hit_points.current
                max_hp = character.hit_points.maximum
                new_hp = min(old_hp + command.amount, max_hp) if command.amount > 0 else max(0, old_hp + command.amount)
                character.hit_points.current = new_hp
            else:
                npc = next((n for n in game_state.npcs if n.name.lower() == command.target.lower()), None)
                if npc:
                    old_hp = npc.hit_points.current
                    max_hp = npc.hit_points.maximum
                    new_hp = (
                        min(old_hp + command.amount, max_hp) if command.amount > 0 else max(0, old_hp + command.amount)
                    )
                    npc.hit_points.current = new_hp
                else:
                    result.success = False
                    result.error = f"Target {command.target} not found"
                    return result

            # Save game state
            self.game_service.save_game(game_state)

            result.data = {
                "type": "hp_update",
                "target": command.target,
                "old_hp": old_hp,
                "new_hp": new_hp,
                "max_hp": max_hp,
                "amount": command.amount,
                "damage_type": command.damage_type,
                "is_healing": command.amount > 0,
                "is_unconscious": new_hp == 0,
            }

            # Add broadcast command
            result.add_command(BroadcastCharacterUpdateCommand(game_id=command.game_id))

            logger.info(
                f"HP Update: {command.target} {'healed' if command.amount > 0 else 'took'} "
                f"{abs(command.amount)} {command.damage_type} - HP: {old_hp} → {new_hp}/{max_hp}"
            )

        elif isinstance(command, AddConditionCommand):
            if command.target == "player":
                character = game_state.character
                if command.condition not in character.conditions:
                    character.conditions.append(command.condition)
            else:
                if game_state.combat:
                    for participant in game_state.combat.participants:
                        if participant.name.lower() == command.target.lower():
                            if command.condition not in participant.conditions:
                                participant.conditions.append(command.condition)
                            break

            self.game_service.save_game(game_state)

            result.data = {
                "type": "add_condition",
                "target": command.target,
                "condition": command.condition,
                "duration": command.duration,
            }

            result.add_command(BroadcastCharacterUpdateCommand(game_id=command.game_id))

            logger.info(f"Condition Added: {command.target} is now {command.condition}")

        elif isinstance(command, RemoveConditionCommand):
            removed = False

            if command.target == "player":
                character = game_state.character
                if command.condition in character.conditions:
                    character.conditions.remove(command.condition)
                    removed = True
            else:
                if game_state.combat:
                    for participant in game_state.combat.participants:
                        if participant.name.lower() == command.target.lower():
                            if command.condition in participant.conditions:
                                participant.conditions.remove(command.condition)
                                removed = True
                            break

            self.game_service.save_game(game_state)

            result.data = {
                "type": "remove_condition",
                "target": command.target,
                "condition": command.condition,
                "removed": removed,
            }

            result.add_command(BroadcastCharacterUpdateCommand(game_id=command.game_id))

            logger.info(f"Condition Removed: {command.target} is no longer {command.condition}")

        elif isinstance(command, UpdateSpellSlotsCommand):
            character = game_state.character

            if not character.spellcasting:
                result.success = False
                result.error = "Character has no spellcasting ability"
                return result

            spell_slots = character.spellcasting.spell_slots
            level_key = f"level_{command.level}"

            if level_key not in spell_slots:
                result.success = False
                result.error = f"No spell slots for level {command.level}"
                return result

            slot = spell_slots[level_key]
            old_slots = slot.current
            slot.current = max(0, min(slot.total, old_slots + command.amount))
            new_slots = slot.current
            max_slots = slot.total

            self.game_service.save_game(game_state)

            result.data = {
                "type": "spell_slots_update",
                "level": command.level,
                "old_slots": old_slots,
                "new_slots": new_slots,
                "max_slots": max_slots,
                "change": command.amount,
            }

            result.add_command(BroadcastCharacterUpdateCommand(game_id=command.game_id))

            logger.info(f"Spell Slots: Level {command.level} - {old_slots} → {new_slots}/{max_slots}")

        return result

    def can_handle(self, command: BaseCommand) -> bool:
        """Check if this handler can process the given command."""
        return isinstance(
            command, (UpdateHPCommand, AddConditionCommand, RemoveConditionCommand, UpdateSpellSlotsCommand)
        )
