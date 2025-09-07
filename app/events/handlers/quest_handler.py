"""Handler for quest management commands."""

import logging

from app.events.base import BaseCommand, CommandResult
from app.events.commands.broadcast_commands import BroadcastGameUpdateCommand
from app.events.commands.quest_commands import (
    CompleteObjectiveCommand,
    CompleteQuestCommand,
    ProgressActCommand,
    StartQuestCommand,
)
from app.events.handlers.base_handler import BaseHandler
from app.interfaces.services import IGameService, IItemRepository, IScenarioService
from app.models.game_state import GameState
from app.models.quest import ObjectiveStatus, QuestStatus
from app.models.tool_results import (
    CompleteObjectiveResult,
    CompleteQuestResult,
    ProgressActResult,
    StartQuestResult,
)

logger = logging.getLogger(__name__)


class QuestHandler(BaseHandler):
    """Handler for quest management commands."""

    def __init__(
        self,
        game_service: IGameService,
        scenario_service: IScenarioService,
        item_repository: IItemRepository,
    ):
        super().__init__(game_service)
        self.scenario_service = scenario_service
        self.item_repository = item_repository

    supported_commands = (
        StartQuestCommand,
        CompleteObjectiveCommand,
        CompleteQuestCommand,
        ProgressActCommand,
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
            game_state.add_quest(quest_copy)

            # Save game state
            self.game_service.save_game(game_state)

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

            logger.info(f"Quest started: {quest.name}")

        elif isinstance(command, CompleteObjectiveCommand):
            # Get active quest
            quest = game_state.get_active_quest(command.quest_id)
            if not quest:
                raise ValueError(f"Quest '{command.quest_id}' not found in active quests")

            # Update objective
            if quest.update_objective(command.objective_id, ObjectiveStatus.COMPLETED):
                # Check if quest is now complete
                quest_complete = quest.status == QuestStatus.COMPLETED

                # Save game state
                self.game_service.save_game(game_state)

                result.data = CompleteObjectiveResult(
                    quest_id=command.quest_id,
                    objective_id=command.objective_id,
                    quest_complete=quest_complete,
                    progress=quest.get_progress_percentage(),
                    message=f"Objective completed: {command.objective_id}",
                )

                # Broadcast update
                result.add_command(BroadcastGameUpdateCommand(game_id=command.game_id))

                logger.info(f"Objective completed: {command.objective_id} in quest {command.quest_id}")

                # If quest is complete, move it to completed list
                if quest_complete:
                    game_state.complete_quest(command.quest_id)
                    self.game_service.save_game(game_state)
            else:
                raise ValueError(f"Objective '{command.objective_id}' not found in quest")

        elif isinstance(command, CompleteQuestCommand):
            # Get active quest
            quest = game_state.get_active_quest(command.quest_id)
            if not quest:
                raise ValueError(f"Quest '{command.quest_id}' not found in active quests")

            # Mark all required objectives as completed
            for obj in quest.objectives:
                if obj.required:
                    obj.status = ObjectiveStatus.COMPLETED
            quest.status = QuestStatus.COMPLETED

            # Move to completed quests
            if game_state.complete_quest(command.quest_id):
                # Save game state
                self.game_service.save_game(game_state)

                result.data = CompleteQuestResult(
                    quest_id=command.quest_id,
                    quest_name=quest.name,
                    rewards=quest.rewards_description,
                    message=f"Quest completed: {quest.name}",
                )

                # Broadcast update
                result.add_command(BroadcastGameUpdateCommand(game_id=command.game_id))

                logger.info(f"Quest completed: {quest.name}")
            else:
                raise RuntimeError(f"Failed to complete quest '{command.quest_id}'")

        elif isinstance(command, ProgressActCommand):
            # Get scenario from embedded sheet
            scenario = game_state.scenario_instance.sheet

            # Check if can progress
            completed = game_state.scenario_instance.completed_quest_ids
            if not scenario.progression.can_progress_to_next_act(completed):
                current_act = scenario.progression.get_current_act()
                if current_act:
                    missing = [q for q in current_act.quests if q not in completed]
                    raise ValueError(f"Cannot progress to next act. Incomplete quests: {', '.join(missing)}")
                else:
                    raise ValueError("No current act found")

            # Progress to next act
            if scenario.progression.progress_to_next_act():
                new_act = scenario.progression.get_current_act()
                if new_act:
                    game_state.scenario_instance.current_act_id = new_act.id

                    # Save game state
                    self.game_service.save_game(game_state)

                    result.data = ProgressActResult(
                        new_act_id=new_act.id,
                        new_act_name=new_act.name,
                        message=f"Progressed to Act: {new_act.name}",
                    )

                    # Broadcast update
                    result.add_command(BroadcastGameUpdateCommand(game_id=command.game_id))

                    logger.info(f"Progressed to act: {new_act.name}")
                else:
                    raise RuntimeError("Failed to get new act after progression")
            else:
                raise ValueError("No more acts to progress to")

        return result
