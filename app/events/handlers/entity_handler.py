"""Handler for character-related commands."""

import logging

from app.agents.core.types import AgentType
from app.events.base import BaseCommand, CommandResult
from app.events.commands.broadcast_commands import BroadcastGameUpdateCommand
from app.events.commands.entity_commands import (
    LevelUpCommand,
    UpdateConditionCommand,
    UpdateHPCommand,
    UpdateSpellSlotsCommand,
)
from app.events.handlers.base_handler import BaseHandler
from app.interfaces.services.character import IEntityStateService, ILevelProgressionService
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


class EntityHandler(BaseHandler):
    """Handler for character-related commands."""

    # Declarative list of supported commands for verification
    supported_commands = (
        UpdateHPCommand,
        UpdateConditionCommand,
        UpdateSpellSlotsCommand,
        LevelUpCommand,
    )

    def __init__(
        self,
        entity_state_service: IEntityStateService,
        level_service: ILevelProgressionService,
    ):
        self.entity_state_service = entity_state_service
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
            # Resolve entity with fallback and fuzzy matching
            entity, resolved_type = resolve_entity_with_fallback(game_state, command.entity_id, command.entity_type)
            if not entity or not resolved_type:
                etype = command.entity_type.value if command.entity_type else "unknown"
                raise ValueError(f"Entity with ID '{command.entity_id}' of type '{etype}' not found")

            old_hp, new_hp, max_hp = self.entity_state_service.update_hp(game_state, entity.instance_id, command.amount)

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

            added = self.entity_state_service.add_condition(game_state, entity.instance_id, command.condition)

            result.mutated = added

            result.data = AddConditionResult(
                target=entity.display_name,
                condition=command.condition,
                duration=command.duration,
            )

            result.add_command(BroadcastGameUpdateCommand(game_id=command.game_id))
            logger.debug(f"Condition Added: {entity.display_name} is now {command.condition}")

        elif isinstance(command, UpdateConditionCommand) and command.action == "remove":
            entity, resolved_type = resolve_entity_with_fallback(game_state, command.entity_id, command.entity_type)
            if not entity or not resolved_type:
                etype = command.entity_type.value if command.entity_type else "unknown"
                raise ValueError(f"Entity with ID '{command.entity_id}' of type '{etype}' not found")

            removed = self.entity_state_service.remove_condition(game_state, entity.instance_id, command.condition)

            result.mutated = removed

            result.data = RemoveConditionResult(
                target=entity.display_name,
                condition=command.condition,
                removed=removed,
            )

            result.add_command(BroadcastGameUpdateCommand(game_id=command.game_id))
            logger.debug(f"Condition Removed: {entity.display_name} is no longer {command.condition}")

        elif isinstance(command, UpdateSpellSlotsCommand):
            entity, resolved_type = resolve_entity_with_fallback(game_state, command.entity_id, command.entity_type)
            if not entity or not resolved_type:
                etype = command.entity_type.value if command.entity_type else "unknown"
                raise ValueError(f"Entity with ID '{command.entity_id}' of type '{etype}' not found")

            old_slots, new_slots, max_slots = self.entity_state_service.update_spell_slots(
                game_state, entity.instance_id, command.level, command.amount
            )

            result.mutated = old_slots != new_slots

            result.data = UpdateSpellSlotsResult(
                target=entity.display_name,
                level=command.level,
                old_slots=old_slots,
                new_slots=new_slots,
                max_slots=max_slots,
                change=command.amount,
            )

            result.add_command(BroadcastGameUpdateCommand(game_id=command.game_id))
            logger.debug(f"Spell Slots: Level {command.level} - {old_slots} → {new_slots}/{max_slots}")

        elif isinstance(command, LevelUpCommand):
            entity, resolved_type = resolve_entity_with_fallback(game_state, command.entity_id, command.entity_type)
            if not entity or not resolved_type:
                etype = command.entity_type.value if command.entity_type else "unknown"
                raise ValueError(f"Entity with ID '{command.entity_id}' of type '{etype}' not found")

            old_level = entity.state.level
            old_max_hp = entity.state.hit_points.maximum

            self.level_service.level_up_entity(game_state, entity.instance_id)

            new_level = entity.state.level
            new_max_hp = entity.state.hit_points.maximum
            hp_increase = max(0, new_max_hp - old_max_hp)

            result.mutated = True

            result.data = LevelUpResult(
                target=entity.display_name,
                old_level=old_level,
                new_level=new_level,
                old_max_hp=old_max_hp,
                new_max_hp=new_max_hp,
                hp_increase=hp_increase,
                message=f"{entity.display_name} leveled up to {new_level}! HP +{hp_increase}",
            )

            result.add_command(BroadcastGameUpdateCommand(game_id=command.game_id))
            logger.debug(f"Level Up: {old_level} -> {new_level}, HP {old_max_hp}->{new_max_hp}")

        return result
