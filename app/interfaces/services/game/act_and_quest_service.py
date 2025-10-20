"""Interface for quest and act progression services."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.models.game_state import GameState
from app.models.quest import Quest


class IActAndQuestService(ABC):
    """Service for managing quests and automatic act progression."""

    @abstractmethod
    def complete_quest(self, game_state: GameState, quest_id: str) -> bool:
        """Complete a quest and automatically progress act if all act quests are done.

        Args:
            game_state: Mutable game state containing quest and scenario data.
            quest_id: ID of the quest to complete.

        Returns:
            True if quest was found and completed, False otherwise.
        """

    @abstractmethod
    def can_progress_act(self, game_state: GameState) -> bool:
        """Check if current act is ready to progress to next act.

        Args:
            game_state: Game state to check.

        Returns:
            True if all required quests for current act are completed.
        """

    @abstractmethod
    def auto_progress_act_if_ready(self, game_state: GameState) -> tuple[bool, str | None]:
        """Automatically progress to next act if conditions are met.

        This is called internally after quest completion to check if act should advance.

        Args:
            game_state: Mutable game state.

        Returns:
            Tuple of (progressed: bool, new_act_id: str | None).
        """

    @abstractmethod
    def get_available_quests(self, game_state: GameState) -> list[Quest]:
        """Get all quests available for the current act.

        Args:
            game_state: Game state to query.

        Returns:
            List of quests that can be started based on prerequisites.
        """

    @abstractmethod
    def add_quest(self, game_state: GameState, quest: Quest) -> None:
        """Add a quest to active quests.

        Args:
            game_state: Mutable game state.
            quest: Quest to add.
        """

    @abstractmethod
    def get_active_quest(self, game_state: GameState, quest_id: str) -> Quest | None:
        """Retrieve an active quest by ID without mutating state.

        Args:
            game_state: Game state to query.
            quest_id: Quest identifier.

        Returns:
            Quest if found, otherwise None.
        """
