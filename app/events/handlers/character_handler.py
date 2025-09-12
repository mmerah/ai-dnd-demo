"""Handler for character-related commands."""

import logging

from app.agents.core.types import AgentType
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
from app.utils.entity_resolver import resolve_entity_with_fallback

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

        # Validate agent type during combat for HP and condition updates
        if (
            game_state.combat.is_active
            and isinstance(command, UpdateHPCommand | UpdateConditionCommand)
            and command.agent_type
            and command.agent_type != AgentType.COMBAT
        ):
            logger.warning(
                f"{command.__class__.__name__} called by {command.agent_type.value} agent during active combat - should be COMBAT agent only"
            )

        if isinstance(command, UpdateHPCommand):
            old_hp = 0
            new_hp = 0
            max_hp = 0

            # Resolve entity with fallback and fuzzy matching
            entity, resolved_type = resolve_entity_with_fallback(game_state, command.entity_id, command.entity_type)
            if not entity or not resolved_type:
                etype = command.entity_type.value if command.entity_type else "unknown"
                raise ValueError(f"Entity with ID '{command.entity_id}' of type '{etype}' not found")

            state = entity.state
            old_hp = state.hit_points.current
            max_hp = state.hit_points.maximum
            new_hp = min(old_hp + command.amount, max_hp) if command.amount > 0 else max(0, old_hp + command.amount)
            state.hit_points.current = new_hp

            # Update combat participant active status if in combat and HP reaches 0
            if game_state.combat.is_active and new_hp == 0:
                for participant in game_state.combat.participants:
                    if participant.entity_id == entity.instance_id:
                        participant.is_active = False
                        logger.debug(f"Combat participant {participant.name} marked as inactive (0 HP)")
                        break

            result.mutated = old_hp != new_hp

            result.data = UpdateHPResult(
                target=entity.display_name,
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

            logger.debug(
                f"HP Update: {entity.display_name} "
                f"{'healed' if command.amount > 0 else 'took'} "
                f"{abs(command.amount)} {command.damage_type} - HP: {old_hp} → {new_hp}/{max_hp}",
            )

        elif isinstance(command, UpdateConditionCommand) and command.action == "add":
            entity, resolved_type = resolve_entity_with_fallback(game_state, command.entity_id, command.entity_type)
            if not entity or not resolved_type:
                etype = command.entity_type.value if command.entity_type else "unknown"
                raise ValueError(f"Entity with ID '{command.entity_id}' of type '{etype}' not found")

            if command.condition not in entity.state.conditions:
                entity.state.conditions.append(command.condition)

            result.mutated = True

            result.data = AddConditionResult(
                target=entity.display_name,
                condition=command.condition,
                duration=command.duration,
            )

            result.add_command(BroadcastGameUpdateCommand(game_id=command.game_id))
            logger.debug(f"Condition Added: {entity.display_name} is now {command.condition}")

        elif isinstance(command, UpdateConditionCommand) and command.action == "remove":
            removed = False
            entity, resolved_type = resolve_entity_with_fallback(game_state, command.entity_id, command.entity_type)
            if not entity or not resolved_type:
                etype = command.entity_type.value if command.entity_type else "unknown"
                raise ValueError(f"Entity with ID '{command.entity_id}' of type '{etype}' not found")

            if command.condition in entity.state.conditions:
                entity.state.conditions.remove(command.condition)
                removed = True

            result.mutated = removed

            result.data = RemoveConditionResult(
                target=entity.display_name,
                condition=command.condition,
                removed=removed,
            )

            result.add_command(BroadcastGameUpdateCommand(game_id=command.game_id))
            logger.debug(f"Condition Removed: {entity.display_name} is no longer {command.condition}")

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

            result.mutated = old_slots != new_slots

            result.data = UpdateSpellSlotsResult(
                level=command.level,
                old_slots=old_slots,
                new_slots=new_slots,
                max_slots=max_slots,
                change=command.amount,
            )

            result.add_command(BroadcastGameUpdateCommand(game_id=command.game_id))
            logger.debug(f"Spell Slots: Level {command.level} - {old_slots} → {new_slots}/{max_slots}")

        elif isinstance(command, LevelUpCommand):
            character_instance = game_state.character

            old_level = character_instance.state.level
            old_max_hp = character_instance.state.hit_points.maximum

            self.level_service.level_up_character(character_instance)

            new_level = character_instance.state.level
            new_max_hp = character_instance.state.hit_points.maximum
            hp_increase = max(0, new_max_hp - old_max_hp)

            result.mutated = True

            result.data = LevelUpResult(
                old_level=old_level,
                new_level=new_level,
                old_max_hp=old_max_hp,
                new_max_hp=new_max_hp,
                hp_increase=hp_increase,
                message=f"Leveled up to {new_level}! HP +{hp_increase}",
            )

            result.add_command(BroadcastGameUpdateCommand(game_id=command.game_id))
            logger.debug(f"Level Up: {old_level} -> {new_level}, HP {old_max_hp}->{new_max_hp}")

        return result
