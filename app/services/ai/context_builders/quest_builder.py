from app.models.game_state import GameState
from app.models.quest import ObjectiveStatus

from .base import ContextBuilder


class QuestContextBuilder(ContextBuilder):
    """Build quest context with active quests and available new quests."""

    def build(self, game_state: GameState) -> str | None:
        if not game_state.scenario_instance.active_quests:
            return None

        scenario = game_state.scenario_instance.sheet
        context_parts: list[str] = ["Active Quests:"]

        for quest in game_state.scenario_instance.active_quests:
            context_parts.append(f"\n• {quest.name} [ID: {quest.id}] ({quest.get_progress_percentage():.0f}% complete)")

            active_objectives = quest.get_active_objectives()
            if active_objectives:
                context_parts.append("  Objectives:")
                for obj in active_objectives[:3]:
                    status_marker = "○" if obj.status == ObjectiveStatus.PENDING else "◐"
                    context_parts.append(f"    {status_marker} {obj.description} [ID: {obj.id}]")

        available_quests: list[str] = []
        for quest_def in scenario.quests:
            active_ids = [q.id for q in game_state.scenario_instance.active_quests]
            completed_ids = game_state.scenario_instance.completed_quest_ids
            if (
                quest_def.id not in active_ids
                and quest_def.id not in completed_ids
                and quest_def.is_available(completed_ids)
            ):
                available_quests.append(f"{quest_def.name} [ID: {quest_def.id}]")

        if available_quests:
            context_parts.append(f"\nAvailable New Quests: {', '.join(available_quests[:2])}")

        return "\n".join(context_parts)
