"""Quest and objective models for scenario progression."""

from enum import Enum

from pydantic import BaseModel, Field


class ObjectiveStatus(str, Enum):
    """Status of a quest objective."""

    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"


class QuestObjective(BaseModel):
    """Individual objective within a quest."""

    id: str
    description: str
    status: ObjectiveStatus = ObjectiveStatus.PENDING
    required: bool = True  # If false, objective is optional


class QuestStatus(str, Enum):
    """Status of a quest."""

    NOT_STARTED = "not_started"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"


class Quest(BaseModel):
    """Quest definition and tracking."""

    id: str
    name: str
    description: str
    objectives: list[QuestObjective]
    status: QuestStatus = QuestStatus.NOT_STARTED
    rewards_description: str  # Narrative description of rewards
    prerequisites: list[str] = Field(default_factory=list)  # Quest IDs that must be completed first
    act: str | None = None  # Which act this quest belongs to

    def is_available(self, completed_quests: list[str]) -> bool:
        """Check if quest is available based on prerequisites."""
        return all(prereq in completed_quests for prereq in self.prerequisites)

    def update_objective(self, objective_id: str, status: ObjectiveStatus) -> bool:
        """Update an objective's status. Returns True if found."""
        for obj in self.objectives:
            if obj.id == objective_id:
                obj.status = status
                self._check_quest_completion()
                return True
        return False

    def _check_quest_completion(self) -> None:
        """Check if quest should be marked as completed."""
        required_objectives = [obj for obj in self.objectives if obj.required]
        if all(obj.status == ObjectiveStatus.COMPLETED for obj in required_objectives):
            self.status = QuestStatus.COMPLETED
        elif any(obj.status == ObjectiveStatus.FAILED for obj in required_objectives):
            self.status = QuestStatus.FAILED

    def get_active_objectives(self) -> list[QuestObjective]:
        """Get all active or pending objectives."""
        return [obj for obj in self.objectives if obj.status in [ObjectiveStatus.ACTIVE, ObjectiveStatus.PENDING]]

    def get_progress_percentage(self) -> float:
        """Get quest completion percentage."""
        if not self.objectives:
            return 0.0
        completed = sum(1 for obj in self.objectives if obj.status == ObjectiveStatus.COMPLETED)
        return (completed / len(self.objectives)) * 100
