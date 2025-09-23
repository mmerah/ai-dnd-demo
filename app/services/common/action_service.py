"""Common service to execute game actions (AI or player) with unified tracking.

Centralizes the sequence:
- Broadcast tool call
- Persist TOOL_CALL event
- Execute command
- Broadcast tool result (if ToolResult)
- Persist TOOL_RESULT event (if ToolResult)
"""

import logging

from pydantic import BaseModel

from app.agents.core.types import AgentType
from app.common.types import JSONSerializable
from app.events.base import BaseCommand
from app.events.commands.broadcast_commands import (
    BroadcastPolicyWarningCommand,
    BroadcastToolCallCommand,
    BroadcastToolResultCommand,
)
from app.interfaces.events import IEventBus
from app.interfaces.services.common import IActionService
from app.interfaces.services.game import IEventManager, ISaveManager
from app.models.game_state import GameEventType, GameState
from app.models.tool_results import ToolResult

logger = logging.getLogger(__name__)


class ActionService(IActionService):
    """Execute commands as actions with consistent broadcasting and persistence."""

    COMBAT_ONLY_TOOLS = frozenset(
        [
            "roll_dice",
            "update_hp",
            "update_condition",
            "next_turn",
            "end_combat",
            "add_combatant",
            "remove_combatant",
        ]
    )

    NPC_ALLOWED_TOOLS = frozenset(
        [
            "start_quest",
            "complete_objective",
            "complete_quest",
            "modify_inventory",
            "update_location_state",
            "discover_secret",
            "move_npc_to_location",
        ]
    )

    def __init__(self, event_bus: IEventBus, event_manager: IEventManager, save_manager: ISaveManager) -> None:
        self.event_bus = event_bus
        self.event_manager = event_manager
        self.save_manager = save_manager

    async def _validate_action_policy(
        self,
        tool_name: str,
        game_state: GameState,
        agent_type: AgentType,
    ) -> None:
        """Validate tool usage against policy rules.

        Raises:
            ValueError: If tool usage violates policy rules
        """
        if agent_type == AgentType.PLAYER:
            return

        # Validation: Prevent narrative agent from using combat tools during active combat
        if game_state.combat.is_active and agent_type == AgentType.NARRATIVE and tool_name in self.COMBAT_ONLY_TOOLS:
            error_msg = (
                f"BLOCKED: Narrative agent attempted to use '{tool_name}' during active combat. "
                f"This tool should only be used by the combat agent during combat. "
                f"The narrative agent must STOP after calling start_combat or start_encounter_combat."
            )
            logger.error(error_msg)
            # Broadcast policy warning
            try:
                await self.event_bus.submit_and_wait(
                    [
                        BroadcastPolicyWarningCommand(
                            game_id=game_state.game_id,
                            message="Blocked tool usage during combat",
                            tool_name=tool_name,
                            agent_type=agent_type.value,
                        )
                    ]
                )
            except Exception:
                logger.debug("Failed to broadcast blocked-tool system message", exc_info=True)
            raise ValueError(error_msg)

        # Validation: Restrict NPC agent to allowed tools only
        if agent_type == AgentType.NPC and tool_name not in self.NPC_ALLOWED_TOOLS:
            error_msg = (
                f"BLOCKED: NPC agent attempted to use '{tool_name}'. "
                "NPC agents may only use quest, inventory, or safe location tools."
            )
            logger.error(error_msg)
            try:
                await self.event_bus.submit_and_wait(
                    [
                        BroadcastPolicyWarningCommand(
                            game_id=game_state.game_id,
                            message="Blocked tool usage for NPC agent",
                            tool_name=tool_name,
                            agent_type=agent_type.value,
                        )
                    ]
                )
            except Exception:
                logger.debug("Failed to broadcast blocked-tool system message", exc_info=True)
            raise ValueError(error_msg)

    async def execute_command_as_action(
        self,
        tool_name: str,
        command: BaseCommand,
        game_state: GameState,
        agent_type: AgentType,
        broadcast_parameters: dict[str, JSONSerializable] | None = None,
    ) -> BaseModel:
        # Validate action policy before execution
        await self._validate_action_policy(tool_name, game_state, agent_type)

        # Extract parameters from command for persistence/broadcast if not provided
        if broadcast_parameters is None:
            broadcast_parameters = {
                k: v for k, v in command.__dict__.items() if k not in ("game_id", "priority", "timestamp")
            }

        # 1) Broadcast tool call
        await self.event_bus.submit_command(
            BroadcastToolCallCommand(
                game_id=game_state.game_id,
                tool_name=tool_name,
                parameters=broadcast_parameters,
            ),
        )

        # 2) Persist TOOL_CALL
        try:
            self.event_manager.add_event(
                game_state=game_state,
                event_type=GameEventType.TOOL_CALL,
                tool_name=tool_name,
                parameters=broadcast_parameters,
            )
            self.save_manager.save_game(game_state)
        except Exception as e:
            logger.error("Failed to persist TOOL_CALL for %s: %s", tool_name, e, exc_info=True)

        # 3) Execute
        result = await self.event_bus.execute_command(command)
        if not result:
            raise RuntimeError(f"Command {type(command).__name__} returned None for {tool_name}")

        # 4/5) Broadcast & persist TOOL_RESULT if appropriate
        if isinstance(result, ToolResult):
            await self.event_bus.submit_command(
                BroadcastToolResultCommand(
                    game_id=game_state.game_id,
                    tool_name=tool_name,
                    result=result,
                ),
            )

            try:
                self.event_manager.add_event(
                    game_state=game_state,
                    event_type=GameEventType.TOOL_RESULT,
                    tool_name=tool_name,
                    result=result.model_dump(mode="json"),
                )
                self.save_manager.save_game(game_state)
            except Exception as e:
                logger.error("Failed to persist TOOL_RESULT for %s: %s", tool_name, e, exc_info=True)

        return result
