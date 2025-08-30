"""Centralized message display service following SOLID principles."""

import logging

from app.common.types import JSONSerializable
from app.interfaces.services import IBroadcastService, IMessageService
from app.models.character import CharacterSheet
from app.models.combat import CombatState
from app.models.game_state import GameState
from app.models.quest import Quest
from app.models.sse_events import (
    ActUpdateData,
    CharacterUpdateData,
    CombatUpdateData,
    ConnectionInfo,
    DiceRollData,
    ErrorData,
    GameUpdateData,
    InitialNarrativeData,
    LocationUpdateData,
    NarrativeData,
    QuestUpdateData,
    ScenarioInfoData,
    ScenarioSummary,
    SSEEventType,
    SystemMessageData,
    ToolCallData,
    ToolResultData,
)

logger = logging.getLogger(__name__)


class MessageService(IMessageService):
    """Service for managing and broadcasting all game messages."""

    def __init__(self, broadcast_service: IBroadcastService) -> None:
        """Initialize with broadcast service dependency."""
        self.broadcast_service = broadcast_service

    async def send_narrative(
        self,
        game_id: str,
        content: str,
        is_chunk: bool = False,
        is_complete: bool = False,
    ) -> None:
        """
        Send narrative content to the chat.

        Args:
            game_id: Game identifier
            content: Narrative text or chunk
            is_chunk: Whether this is a streaming chunk
            is_complete: Whether the narrative is complete
        """
        data = NarrativeData(
            word=content if is_chunk else None,
            complete=True if is_complete else None,
            start=True if not is_chunk and not is_complete else None,
            content=content if not is_chunk and not is_complete and content else None,
        )
        await self.broadcast_service.publish(game_id, SSEEventType.NARRATIVE.value, data)

    async def send_initial_narrative(self, game_id: str, scenario_title: str, narrative: str) -> None:
        """
        Send the initial narrative when a game starts.

        Args:
            game_id: Game identifier
            scenario_title: Title of the scenario
            narrative: Initial narrative text
        """
        data = InitialNarrativeData(scenario_title=scenario_title, narrative=narrative)
        await self.broadcast_service.publish(game_id, SSEEventType.INITIAL_NARRATIVE.value, data)

    async def send_tool_call(self, game_id: str, tool_name: str, parameters: dict[str, JSONSerializable]) -> None:
        """
        Send tool call information to the chat.

        Args:
            game_id: Game identifier
            tool_name: Name of the tool being called
            parameters: Tool parameters
        """
        data = ToolCallData(tool_name=tool_name, parameters=parameters)
        await self.broadcast_service.publish(game_id, SSEEventType.TOOL_CALL.value, data)

    async def send_tool_result(self, game_id: str, tool_name: str, result: JSONSerializable) -> None:
        """
        Send tool result information to the chat.

        Args:
            game_id: Game identifier
            tool_name: Name of the tool that was called
            result: Result from the tool
        """
        data = ToolResultData(tool_name=tool_name, result=result)
        await self.broadcast_service.publish(game_id, SSEEventType.TOOL_RESULT.value, data)

    async def send_dice_roll(
        self,
        game_id: str,
        roll_type: str,
        dice: str,
        modifier: int,
        result: int,
        details: dict[str, JSONSerializable] | None = None,
    ) -> None:
        """
        Send dice roll result to the chat.

        Args:
            game_id: Game identifier
            roll_type: Type of roll (attack, damage, save, etc.)
            dice: Dice notation (e.g., "1d20")
            modifier: Modifier applied to the roll
            result: Final result
            details: Additional details about the roll
        """
        data = DiceRollData(roll_type=roll_type, dice=dice, modifier=modifier, result=result, details=details or {})
        await self.broadcast_service.publish(game_id, SSEEventType.DICE_ROLL.value, data)

    async def send_character_update(self, game_id: str, character: CharacterSheet) -> None:
        """
        Send character sheet update.

        Args:
            game_id: Game identifier
            character: CharacterSheet instance
        """
        data = CharacterUpdateData(character=character)
        await self.broadcast_service.publish(game_id, SSEEventType.CHARACTER_UPDATE.value, data)

    async def send_combat_update(self, game_id: str, combat: CombatState) -> None:
        """
        Send combat state update.

        Args:
            game_id: Game identifier
            combat: CombatState instance
        """
        data = CombatUpdateData(combat=combat)
        await self.broadcast_service.publish(game_id, SSEEventType.COMBAT_UPDATE.value, data)

    async def send_system_message(self, game_id: str, message: str, level: str = "info") -> None:
        """
        Send system message to the chat.

        Args:
            game_id: Game identifier
            message: System message text
            level: Message level (info, warning, error)
        """
        data = SystemMessageData(message=message, level=level)  # type: ignore[arg-type]
        await self.broadcast_service.publish(game_id, SSEEventType.SYSTEM.value, data)

    async def send_error(self, game_id: str, error: str, error_type: str | None = None) -> None:
        """
        Send error message to the chat.

        Args:
            game_id: Game identifier
            error: Error message
            error_type: Type of error if available
        """
        data = ErrorData(error=error, type=error_type)
        await self.broadcast_service.publish(game_id, SSEEventType.ERROR.value, data)

    async def send_game_update(self, game_id: str, game_state: GameState) -> None:
        """
        Send complete game state update.

        Args:
            game_id: Game identifier
            game_state: GameState instance
        """
        data = GameUpdateData(game_state=game_state)
        await self.broadcast_service.publish(game_id, SSEEventType.GAME_UPDATE.value, data)

    async def send_location_update(
        self,
        game_id: str,
        location_id: str,
        location_name: str,
        description: str,
        connections: list[ConnectionInfo],
        danger_level: str,
        npcs_present: list[str],
    ) -> None:
        """
        Send detailed location update.

        Args:
            game_id: Game identifier
            location_id: Location identifier
            location_name: Name of the location
            description: Location description
            connections: Available connections/exits
            danger_level: Danger level of the location
            npcs_present: NPCs currently at the location
        """
        data = LocationUpdateData(
            location_id=location_id,
            location_name=location_name,
            description=description,
            connections=connections,
            danger_level=danger_level,
            npcs_present=npcs_present,
        )
        await self.broadcast_service.publish(game_id, SSEEventType.LOCATION_UPDATE.value, data)

    async def send_quest_update(
        self,
        game_id: str,
        active_quests: list[Quest],
        completed_quest_ids: list[str],
    ) -> None:
        """
        Send quest status update.

        Args:
            game_id: Game identifier
            active_quests: List of active Quest instances
            completed_quest_ids: List of completed quest IDs
        """
        data = QuestUpdateData(active_quests=active_quests, completed_quest_ids=completed_quest_ids)
        await self.broadcast_service.publish(game_id, SSEEventType.QUEST_UPDATE.value, data)

    async def send_act_update(self, game_id: str, act_id: str, act_name: str, act_index: int) -> None:
        """
        Send act/chapter update.

        Args:
            game_id: Game identifier
            act_id: Act identifier
            act_name: Name of the act
            act_index: Current act index
        """
        data = ActUpdateData(act_id=act_id, act_name=act_name, act_index=act_index)
        await self.broadcast_service.publish(game_id, SSEEventType.ACT_UPDATE.value, data)

    async def send_scenario_info(
        self,
        game_id: str,
        scenario_title: str,
        scenario_id: str,
        available_scenarios: list[dict[str, str]],
    ) -> None:
        """
        Send scenario information to the frontend.

        Args:
            game_id: Game identifier
            scenario_title: Title of current scenario
            scenario_id: ID of current scenario
            available_scenarios: List of available scenarios
        """
        current = ScenarioSummary(id=scenario_id, title=scenario_title)
        available = [ScenarioSummary(**s) for s in available_scenarios]
        data = ScenarioInfoData(current_scenario=current, available_scenarios=available)
        await self.broadcast_service.publish(game_id, SSEEventType.SCENARIO_INFO.value, data)
