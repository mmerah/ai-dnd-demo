"""ActAndQuestService: encapsulates quest and act progression logic with automatic act advancement."""

from __future__ import annotations

import logging

from app.interfaces.services.game import IActAndQuestService
from app.models.game_state import GameState
from app.models.quest import Quest, QuestStatus

logger = logging.getLogger(__name__)


class ActAndQuestService(IActAndQuestService):
    """Default implementation for quest and act progression with automatic act advancement."""

    def complete_quest(self, game_state: GameState, quest_id: str) -> bool:
        active_quests = game_state.scenario_instance.active_quests
        for index, quest in enumerate(active_quests):
            if quest.id != quest_id:
                continue

            removed = active_quests.pop(index)
            if removed.status != QuestStatus.COMPLETED:
                removed.status = QuestStatus.COMPLETED

            completed_ids = game_state.scenario_instance.completed_quest_ids
            if quest_id not in completed_ids:
                completed_ids.append(quest_id)

            game_state.add_story_note(f"Quest completed: {removed.name}")
            logger.debug(f"Quest '{quest_id}' completed and moved to completed quests")

            progressed, new_act_id = self.auto_progress_act_if_ready(game_state)
            if progressed and new_act_id:
                logger.info(f"Automatically progressed to act: {new_act_id}")

            return True

        logger.debug(f"Quest '{quest_id}' not found among active quests")
        return False

    def can_progress_act(self, game_state: GameState) -> bool:
        scenario = game_state.scenario_instance.sheet
        completed = game_state.scenario_instance.completed_quest_ids
        return scenario.progression.can_progress_to_next_act(completed)

    def auto_progress_act_if_ready(self, game_state: GameState) -> tuple[bool, str | None]:
        # Check if we can progress
        if not self.can_progress_act(game_state):
            return (False, None)

        # Get scenario progression
        scenario = game_state.scenario_instance.sheet

        # Progress to next act
        if scenario.progression.progress_to_next_act():
            new_act = scenario.progression.get_current_act()
            if new_act:
                # Update game state's current act
                game_state.scenario_instance.current_act_id = new_act.id

                # Add story note for the progression
                game_state.add_story_note(f"Progressed to Act: {new_act.name}")

                logger.info(f"Act progression: {new_act.name} (ID: {new_act.id})")
                return (True, new_act.id)
            else:
                logger.error("Failed to get new act after progression")
                return (False, None)
        else:
            # No more acts to progress to
            logger.debug("No more acts available for progression")
            return (False, None)

    def get_available_quests(self, game_state: GameState) -> list[Quest]:
        scenario = game_state.scenario_instance.sheet
        current_act = scenario.progression.get_current_act()

        if not current_act:
            return []

        completed = game_state.scenario_instance.completed_quest_ids
        active_ids = {q.id for q in game_state.scenario_instance.active_quests}

        available: list[Quest] = []

        for quest_id in current_act.quests:
            # Skip if already active or completed
            if quest_id in active_ids or quest_id in completed:
                continue

            quest = scenario.get_quest(quest_id)
            if quest and quest.is_available(completed):
                available.append(quest)

        return available

    def add_quest(self, game_state: GameState, quest: Quest) -> None:
        if self.get_active_quest(game_state, quest.id):
            logger.debug(f"Quest '{quest.id}' already active; skipping add")
            return

        if quest.status != QuestStatus.ACTIVE:
            quest.status = QuestStatus.ACTIVE

        game_state.scenario_instance.active_quests.append(quest)
        game_state.add_story_note(f"New quest started: {quest.name}")
        logger.debug(f"Quest '{quest.id}' added to active quests")

    def get_active_quest(self, game_state: GameState, quest_id: str) -> Quest | None:
        for quest in game_state.scenario_instance.active_quests:
            if quest.id == quest_id:
                return quest
        return None
