"""Handler for quest management commands."""

import logging

from app.events.base import BaseCommand, CommandResult
from app.events.commands.broadcast_commands import BroadcastGameUpdateCommand
from app.events.commands.quest_commands import (
    CompleteObjectiveCommand,
    CompleteQuestCommand,
    StartQuestCommand,
)
from app.events.handlers.base_handler import BaseHandler
from app.interfaces.services.game import IActAndQuestService
from app.interfaces.services.memory import IMemoryService
from app.models.game_state import GameState
from app.models.memory import MemoryEventKind, WorldEventContext
from app.models.quest import ObjectiveStatus, QuestStatus
from app.models.tool_results import (
    CompleteObjectiveResult,
    CompleteQuestResult,
    StartQuestResult,
)

logger = logging.getLogger(__name__)


class QuestHandler(BaseHandler):
    """Handler for quest management commands."""

    def __init__(self, memory_service: IMemoryService, act_and_quest_service: IActAndQuestService) -> None:
        self.memory_service = memory_service
        self.act_and_quest_service = act_and_quest_service

    supported_commands = (
        StartQuestCommand,
        CompleteObjectiveCommand,
        CompleteQuestCommand,
    )

    async def handle(self, command: BaseCommand, game_state: GameState) -> CommandResult:
        """Handle quest commands."""
        result = CommandResult()

        if isinstance(command, StartQuestCommand):
            # Get scenario from embedded sheet
            scenario = game_state.scenario_instance.sheet

            # Get quest from scenario
            quest = scenario.get_quest(command.quest_id)
            if not quest:
                raise ValueError(f"Quest '{command.quest_id}' not found")

            # Check prerequisites
            completed = game_state.scenario_instance.completed_quest_ids
            if not quest.is_available(completed):
                missing = [prereq for prereq in quest.prerequisites if prereq not in completed]
                raise ValueError(f"Quest prerequisites not met. Missing: {', '.join(missing)}")

            # Create a copy of the quest for the game state
            quest_copy = quest.model_copy(deep=True)
            quest_copy.status = QuestStatus.ACTIVE

            # Mark first objective as active
            if quest_copy.objectives:
                quest_copy.objectives[0].status = ObjectiveStatus.ACTIVE

            # Add to game state
            self.act_and_quest_service.add_quest(game_state, quest_copy)

            result.mutated = True

            result.data = StartQuestResult(
                quest_id=command.quest_id,
                quest_name=quest.name,
                objectives=[
                    {"id": obj.id, "description": obj.description, "status": obj.status.value}
                    for obj in quest_copy.objectives
                ],
                message=f"Quest started: {quest.name}",
            )

            # Broadcast update
            result.add_command(BroadcastGameUpdateCommand(game_id=command.game_id))
            logger.debug(f"Quest started: {quest.name}")

        elif isinstance(command, CompleteObjectiveCommand):
            # Get active quest
            quest = self.act_and_quest_service.get_active_quest(game_state, command.quest_id)
            if not quest:
                raise ValueError(f"Quest '{command.quest_id}' not found in active quests")

            # Update objective
            if quest.update_objective(command.objective_id, ObjectiveStatus.COMPLETED):
                # Check if quest is now complete
                quest_complete = quest.status == QuestStatus.COMPLETED

                result.mutated = True

                result.data = CompleteObjectiveResult(
                    quest_id=command.quest_id,
                    objective_id=command.objective_id,
                    quest_complete=quest_complete,
                    progress=quest.get_progress_percentage(),
                    message=f"Objective completed: {command.objective_id}",
                )

                # Broadcast update
                result.add_command(BroadcastGameUpdateCommand(game_id=command.game_id))
                logger.debug(f"Objective completed: {command.objective_id} in quest {command.quest_id}")

                # If quest is complete, move it to completed list and auto-progress act if ready
                if quest_complete:
                    self.act_and_quest_service.complete_quest(game_state, command.quest_id)

                await self.memory_service.on_world_event(
                    game_state,
                    event_kind=MemoryEventKind.OBJECTIVE_COMPLETED,
                    context=WorldEventContext(
                        quest_id=command.quest_id,
                        objective_id=command.objective_id,
                    ),
                )
            else:
                raise ValueError(f"Objective '{command.objective_id}' not found in quest")

        elif isinstance(command, CompleteQuestCommand):
            # Get active quest
            quest = self.act_and_quest_service.get_active_quest(game_state, command.quest_id)
            if not quest:
                raise ValueError(f"Quest '{command.quest_id}' not found in active quests")

            # Mark all required objectives as completed
            for obj in quest.objectives:
                if obj.required:
                    obj.status = ObjectiveStatus.COMPLETED
            quest.status = QuestStatus.COMPLETED

            # Move to completed quests and auto-progress act if ready
            if self.act_and_quest_service.complete_quest(game_state, command.quest_id):
                result.mutated = True

                result.data = CompleteQuestResult(
                    quest_id=command.quest_id,
                    quest_name=quest.name,
                    rewards=quest.rewards_description,
                    message=f"Quest completed: {quest.name}",
                )

                # Broadcast update
                result.add_command(BroadcastGameUpdateCommand(game_id=command.game_id))
                logger.debug(f"Quest completed: {quest.name}")
            else:
                raise RuntimeError(f"Failed to complete quest '{command.quest_id}'")

            await self.memory_service.on_world_event(
                game_state,
                event_kind=MemoryEventKind.QUEST_COMPLETED,
                context=WorldEventContext(quest_id=command.quest_id),
            )

        return result
