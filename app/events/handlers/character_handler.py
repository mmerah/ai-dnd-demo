"""Handler for character-related commands."""

import logging

from app.events.base import BaseCommand, CommandResult
from app.events.commands.broadcast_commands import BroadcastGameUpdateCommand
from app.events.commands.character_commands import (
    LevelUpCommand,
    UpdateConditionCommand,
    UpdateHPCommand,
    UpdateSpellSlotsCommand,
)
from app.events.handlers.base_handler import BaseHandler
from app.interfaces.services.character import ILevelProgressionService
from app.interfaces.services.game import IGameService
from app.models.game_state import GameState
from app.models.tool_results import (
    AddConditionResult,
    LevelUpResult,
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
        LevelUpCommand,
    )

    def __init__(self, game_service: IGameService, level_service: ILevelProgressionService):
        super().__init__(game_service)
        self.level_service = level_service

    async def handle(self, command: BaseCommand, game_state: GameState) -> CommandResult:
        """Handle character commands."""
        result = CommandResult()

        if isinstance(command, UpdateHPCommand):
            old_hp = 0
            new_hp = 0
            max_hp = 0

            entity = game_state.get_entity_by_id(command.entity_type, command.entity_id)
            if not entity:
                raise ValueError(
                    f"Entity with ID '{command.entity_id}' of type '{command.entity_type.value}' not found"
                )

            state = entity.state
            old_hp = state.hit_points.current
            max_hp = state.hit_points.maximum
            new_hp = min(old_hp + command.amount, max_hp) if command.amount > 0 else max(0, old_hp + command.amount)
            state.hit_points.current = new_hp

            # Save game state
            self.game_service.save_game(game_state)

            result.data = UpdateHPResult(
                target=getattr(entity, "display_name", "unknown"),
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
                f"HP Update: {getattr(entity, 'display_name', 'unknown')} "
                f"{'healed' if command.amount > 0 else 'took'} "
                f"{abs(command.amount)} {command.damage_type} - HP: {old_hp} → {new_hp}/{max_hp}",
            )

        elif isinstance(command, UpdateConditionCommand) and command.action == "add":
            entity = game_state.get_entity_by_id(command.entity_type, command.entity_id)
            if not entity:
                raise ValueError(
                    f"Entity with ID '{command.entity_id}' of type '{command.entity_type.value}' not found"
                )

            if command.condition not in entity.state.conditions:
                entity.state.conditions.append(command.condition)

            self.game_service.save_game(game_state)

            result.data = AddConditionResult(
                target=getattr(entity, "display_name", "unknown"),
                condition=command.condition,
                duration=command.duration,
            )

            result.add_command(BroadcastGameUpdateCommand(game_id=command.game_id))

            logger.info(f"Condition Added: {getattr(entity, 'display_name', 'unknown')} is now {command.condition}")

        elif isinstance(command, UpdateConditionCommand) and command.action == "remove":
            removed = False

            entity = game_state.get_entity_by_id(command.entity_type, command.entity_id)
            if not entity:
                raise ValueError(
                    f"Entity with ID '{command.entity_id}' of type '{command.entity_type.value}' not found"
                )

            if command.condition in entity.state.conditions:
                entity.state.conditions.remove(command.condition)
                removed = True

            self.game_service.save_game(game_state)

            result.data = RemoveConditionResult(
                target=getattr(entity, "display_name", "unknown"),
                condition=command.condition,
                removed=removed,
            )

            result.add_command(BroadcastGameUpdateCommand(game_id=command.game_id))

            logger.info(
                f"Condition Removed: {getattr(entity, 'display_name', 'unknown')} is no longer {command.condition}"
            )

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

        elif isinstance(command, LevelUpCommand):
            character_instance = game_state.character

            old_level = character_instance.state.level
            old_max_hp = character_instance.state.hit_points.maximum

            self.level_service.level_up_character(character_instance)

            new_level = character_instance.state.level
            new_max_hp = character_instance.state.hit_points.maximum
            hp_increase = max(0, new_max_hp - old_max_hp)

            self.game_service.save_game(game_state)

            result.data = LevelUpResult(
                old_level=old_level,
                new_level=new_level,
                old_max_hp=old_max_hp,
                new_max_hp=new_max_hp,
                hp_increase=hp_increase,
                message=f"Leveled up to {new_level}! HP +{hp_increase}",
            )

            result.add_command(BroadcastGameUpdateCommand(game_id=command.game_id))
            logger.info(f"Level Up: {old_level} -> {new_level}, HP {old_max_hp}->{new_max_hp}")

        return result
