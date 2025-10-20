from unittest.mock import create_autospec

import pytest

from app.events.commands.quest_commands import (
    CompleteObjectiveCommand,
    CompleteQuestCommand,
    StartQuestCommand,
)
from app.events.handlers.quest_handler import QuestHandler
from app.interfaces.services.game import IActAndQuestService
from app.interfaces.services.memory import IMemoryService
from app.models.memory import MemoryEventKind, WorldEventContext
from app.models.quest import ObjectiveStatus, Quest, QuestObjective, QuestStatus
from app.models.scenario import ScenarioAct
from app.models.tool_results import CompleteObjectiveResult, CompleteQuestResult
from tests.factories import make_game_state
from tests.factories.scenario import make_scenario


class TestQuestHandler:
    def setup_method(self) -> None:
        self.memory_service = create_autospec(IMemoryService, instance=True)
        self.act_and_quest_service = create_autospec(IActAndQuestService, instance=True)
        self.handler = QuestHandler(self.memory_service, self.act_and_quest_service)
        self.game_state = make_game_state()
        locations = self.game_state.scenario_instance.sheet.locations
        location_ids = [loc.id for loc in locations]

        self.quest_intro = Quest(
            id="rescue",
            name="Rescue the Scout",
            description="Find and rescue the missing scout",
            objectives=[
                QuestObjective(id="track", description="Find trail"),
                QuestObjective(id="rescue", description="Rescue scout"),
            ],
            rewards_description="Gratitude",
        )

        self.quest_finale = Quest(
            id="ambush",
            name="Stop the Ambush",
            description="Prevent the goblin ambush",
            objectives=[QuestObjective(id="foil", description="Foil ambush")],
            rewards_description="Safety",
            prerequisites=[self.quest_intro.id],
        )

        scenario = make_scenario(
            scenario_id="rescue-run",
            title="Rescue Run",
            description="A rescue mission",
            starting_location_id=self.game_state.scenario_instance.sheet.starting_location_id,
            locations=locations,
            quests=[self.quest_intro, self.quest_finale],
            acts=[
                ScenarioAct(
                    id="act1",
                    name="Act 1",
                    locations=location_ids,
                    objectives=[],
                    quests=[self.quest_intro.id],
                ),
                ScenarioAct(
                    id="act2",
                    name="Act 2",
                    locations=location_ids,
                    objectives=[],
                    quests=[self.quest_finale.id],
                ),
            ],
        )

        instance = self.game_state.scenario_instance
        instance.sheet = scenario
        instance.current_act_id = "act1"
        instance.active_quests.clear()
        instance.completed_quest_ids.clear()

    @pytest.mark.asyncio
    async def test_start_quest(self) -> None:
        gs = self.game_state

        command = StartQuestCommand(game_id=gs.game_id, quest_id=self.quest_intro.id)
        result = await self.handler.handle(command, gs)

        assert result.mutated
        self.act_and_quest_service.add_quest.assert_called_once()
        add_args, _ = self.act_and_quest_service.add_quest.call_args
        quest_arg = add_args[1]
        assert quest_arg.id == self.quest_intro.id
        assert quest_arg.status == QuestStatus.ACTIVE
        assert quest_arg.objectives[0].status == ObjectiveStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_cannot_start_quest_with_unmet_prerequisites(self) -> None:
        gs = self.game_state

        command = StartQuestCommand(game_id=gs.game_id, quest_id=self.quest_finale.id)

        with pytest.raises(ValueError, match="prerequisites"):
            await self.handler.handle(command, gs)
        self.act_and_quest_service.add_quest.assert_not_called()

    @pytest.mark.asyncio
    async def test_complete_objective(self) -> None:
        gs = self.game_state
        active_quest = self.quest_intro.model_copy(deep=True)
        active_quest.objectives[0].status = ObjectiveStatus.ACTIVE
        self.act_and_quest_service.get_active_quest.return_value = active_quest

        command = CompleteObjectiveCommand(
            game_id=gs.game_id,
            quest_id=self.quest_intro.id,
            objective_id="track",
        )
        result = await self.handler.handle(command, gs)

        assert isinstance(result.data, CompleteObjectiveResult)
        assert not result.data.quest_complete
        objective = next(o for o in active_quest.objectives if o.id == "track")
        assert objective.status == ObjectiveStatus.COMPLETED
        calls = self.memory_service.on_world_event.await_args_list
        assert len(calls) == 1
        call = calls[0]
        assert call.kwargs["event_kind"] == MemoryEventKind.OBJECTIVE_COMPLETED
        context = call.kwargs["context"]
        assert isinstance(context, WorldEventContext)
        assert context.quest_id == self.quest_intro.id
        assert context.objective_id == "track"

    @pytest.mark.asyncio
    async def test_complete_all_objectives_completes_quest(self) -> None:
        gs = self.game_state
        active_quest = self.quest_intro.model_copy(deep=True)
        active_quest.objectives[0].status = ObjectiveStatus.ACTIVE
        active_quest.objectives[1].status = ObjectiveStatus.PENDING
        self.act_and_quest_service.get_active_quest.return_value = active_quest
        self.act_and_quest_service.complete_quest.return_value = True
        self.act_and_quest_service.complete_quest.reset_mock()

        # Complete all objectives
        for objective in active_quest.objectives:
            result = await self.handler.handle(
                CompleteObjectiveCommand(
                    game_id=gs.game_id,
                    quest_id=self.quest_intro.id,
                    objective_id=objective.id,
                ),
                gs,
            )

        assert isinstance(result.data, CompleteObjectiveResult)
        assert result.data.quest_complete
        self.act_and_quest_service.complete_quest.assert_called_once_with(gs, self.quest_intro.id)
        calls = self.memory_service.on_world_event.await_args_list
        assert len(calls) == len(active_quest.objectives)
        assert all(call.kwargs["event_kind"] == MemoryEventKind.OBJECTIVE_COMPLETED for call in calls)

    @pytest.mark.asyncio
    async def test_complete_quest_directly(self) -> None:
        gs = self.game_state
        active_quest = self.quest_intro.model_copy(deep=True)
        active_quest.objectives[0].status = ObjectiveStatus.ACTIVE
        active_quest.objectives[1].status = ObjectiveStatus.PENDING
        self.act_and_quest_service.get_active_quest.return_value = active_quest
        self.act_and_quest_service.complete_quest.return_value = True

        result = await self.handler.handle(CompleteQuestCommand(game_id=gs.game_id, quest_id=self.quest_intro.id), gs)

        assert isinstance(result.data, CompleteQuestResult)
        assert result.data.quest_name == self.quest_intro.name
        # Verify the service was called to complete the quest (which handles auto-progression)
        self.act_and_quest_service.complete_quest.assert_called()
        calls = self.memory_service.on_world_event.await_args_list
        event_kinds = [call.kwargs["event_kind"] for call in calls]
        assert MemoryEventKind.QUEST_COMPLETED in event_kinds

    @pytest.mark.asyncio
    async def test_cannot_complete_nonexistent_quest(self) -> None:
        gs = self.game_state

        command = CompleteQuestCommand(game_id=gs.game_id, quest_id="nonexistent")
        self.act_and_quest_service.get_active_quest.return_value = None

        with pytest.raises(ValueError, match="Quest .* not found in active"):
            await self.handler.handle(command, gs)
