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
from app.interfaces.services import IGameService, ILevelProgressionService
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
                    # Try monsters by display name
                    monster = next(
                        (m for m in game_state.monsters if m.sheet.name.lower() == command.target.lower()), None
                    )
                    if monster:
                        old_hp = monster.state.hit_points.current
                        max_hp = monster.state.hit_points.maximum
                        new_hp = (
                            min(old_hp + command.amount, max_hp)
                            if command.amount > 0
                            else max(0, old_hp + command.amount)
                        )
                        monster.state.hit_points.current = new_hp
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
                        # Mirror to monster instance state if applicable
                        monster = next(
                            (m for m in game_state.monsters if m.sheet.name.lower() == command.target.lower()), None
                        )
                        if monster and command.condition not in monster.state.conditions:
                            monster.state.conditions.append(command.condition)
                        break
            else:
                # Also update monster state conditions if applicable
                monster = next((m for m in game_state.monsters if m.sheet.name.lower() == command.target.lower()), None)
                if monster and command.condition not in monster.state.conditions:
                    monster.state.conditions.append(command.condition)

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
                        # Mirror to monster instance state if applicable
                        monster = next(
                            (m for m in game_state.monsters if m.sheet.name.lower() == command.target.lower()), None
                        )
                        if monster and command.condition in monster.state.conditions:
                            monster.state.conditions.remove(command.condition)
                            removed = True
                        break
            else:
                # Also update monster state conditions if applicable
                monster = next((m for m in game_state.monsters if m.sheet.name.lower() == command.target.lower()), None)
                if monster and command.condition in monster.state.conditions:
                    monster.state.conditions.remove(command.condition)
                    removed = True

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

    def can_handle(self, command: BaseCommand) -> bool:
        """Check if this handler can process the given command."""
        return isinstance(command, self.supported_commands)
